#!/usr/bin/env python3
from __future__ import annotations

import json
import random
import subprocess
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "src" / "siteprobe.py"


class FixtureHandler(BaseHTTPRequestHandler):
    methods = []
    flaky_hits = 0
    def log_message(self, *_args):
        pass

    def do_GET(self):
        type(self).methods.append("GET")
        port = self.server.server_port
        routes = {
            "/robots.txt": (200, "text/plain", f"User-agent: *\nDisallow: /private\nSitemap: http://127.0.0.1:{port}/sitemap-index.xml\n"),
            "/sitemap-index.xml": (200, "application/xml", f"<sitemapindex><sitemap><loc>http://127.0.0.1:{port}/sitemap.xml</loc></sitemap></sitemapindex>"),
            "/sitemap.xml": (200, "application/xml", f"<urlset><url><loc>http://127.0.0.1:{port}/</loc></url><url><loc>http://127.0.0.1:{port}/orphan</loc></url><url><loc>http://127.0.0.1:{port}/noindex</loc></url></urlset>"),
            "/": (200, "text/html", f'''<html lang="en"><head><title>Home</title><meta name="description" content="Shared description"><link rel="canonical" href="http://127.0.0.1:{port}/"><meta property="og:title" content="Home"><script type="application/ld+json">{{"@type":"WebSite"}}</script></head><body><h1>Home</h1><a href="/duplicate">Duplicate</a><a href="/redirect">Redirect</a><a href="/broken">Broken</a><a href="https://example.net/">External</a><img src="/image.png"></body></html>'''),
            "/duplicate": (200, "text/html", '<html><head><title>Home</title><meta name="description" content="Shared description"></head><body><h1>Other</h1><a href="/noindex">Noindex</a><a href="/">Cycle</a><script type="application/ld+json">{"bad":</script></body></html>'),
            "/noindex": (200, "text/html", '<html><head><title>Noindex</title><meta name="robots" content="noindex"></head><body>Hidden</body></html>'),
            "/orphan": (200, "text/html", '<html><head><title>Orphan</title></head><body>Orphan content</body></html>'),
            "/private": (200, "text/html", '<html><head><title>Private</title></head><body>Private</body></html>'),
            "/image.png": (200, "image/png", "not-really-an-image"),
            "/nested": (200, "text/html", "<title>Nested <span>title</span></title><h1>Useful <em>heading</em></h1>"),
            "/many": (200, "text/html", "<title>Many</title>" + "".join(f'<a href=\"/p/{i}\">{i}</a>' for i in range(5))),
        }
        if self.path == "/redirect":
            self.send_response(302); self.send_header("Location", "/duplicate"); self.end_headers(); return
        if self.path == "/flaky":
            type(self).flaky_hits += 1
            if type(self).flaky_hits < 2:
                self.send_response(429); self.send_header("Retry-After", "0"); self.end_headers(); return
            routes["/flaky"] = (200, "text/html", "<title>Recovered</title>")
        if self.path == "/slow":
            time.sleep(0.2); routes["/slow"] = (200, "text/html", "<title>Slow</title>")
        status, ctype, body = routes.get(self.path, (404, "text/html", "<title>Not found</title>"))
        encoded = body.encode(); self.send_response(status); self.send_header("Content-Type", ctype); self.send_header("Content-Length", str(len(encoded))); self.end_headers()
        try: self.wfile.write(encoded)
        except (BrokenPipeError, ConnectionResetError): pass


class SiteProbeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), FixtureHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True); cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.server.server_port}/"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown(); cls.server.server_close()

    def run_cli(self, *args, expected=0):
        result = subprocess.run(["python3", str(CLI), *map(str, args)], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(expected, result.returncode, result.stderr + result.stdout)
        return result

    def test_full_fixture_contract_and_compare(self):
        with tempfile.TemporaryDirectory() as tmp:
            run1 = Path(tmp) / "run1"; run2 = Path(tmp) / "run2"
            self.run_cli("crawl", self.base, "--out", run1, "--max-pages", "20", "--max-depth", "3", "--allow-private-network", "--json")
            self.run_cli("validate", run1)
            data = json.loads((run1 / "run.json").read_text())
            self.assertEqual("siteprobe.run/v1", data["schema"])
            self.assertGreaterEqual(data["counts"]["pages"], 5)
            checks = {x["check"] for x in json.loads((run1 / "findings.json").read_text())["findings"]}
            self.assertTrue({"broken-url", "duplicate-title", "duplicate-description", "not-indexable", "missing-image-alt", "orphan-candidate"} <= checks)
            pages = [json.loads(x) for x in (run1 / "pages.jsonl").read_text().splitlines()]
            self.assertFalse(any(x["normalized_url"].endswith("/private") and x["status"] == 200 for x in pages))
            self.run_cli("crawl", self.base, "--out", run2, "--max-pages", "4", "--max-depth", "1", "--allow-private-network")
            comparison = json.loads(self.run_cli("compare", run1, run2).stdout)
            self.assertTrue(comparison["changes"])

    def test_inspect_and_doctor(self):
        self.assertTrue(json.loads(self.run_cli("doctor").stdout)["ok"])
        blocked = self.run_cli("inspect", self.base, expected=2)
        self.assertIn("private network target blocked", blocked.stderr)
        page = json.loads(self.run_cli("inspect", self.base, "--allow-private-network").stdout)
        self.assertEqual(200, page["status"])
        self.assertEqual("Home", page["title"])
        nested = json.loads(self.run_cli("inspect", self.base + "nested", "--allow-private-network").stdout)
        self.assertEqual("Nested title", nested["title"])
        self.assertEqual(["Useful heading"], nested["headings"]["h1"])
        capped = json.loads(self.run_cli("inspect", self.base + "many", "--allow-private-network", "--max-links-per-page", "2").stdout)
        self.assertEqual(2, capped["outgoing_link_count"])
        self.assertTrue(capped["truncated"]["links"])

    def test_rejects_credentials_and_bad_bounds(self):
        self.run_cli("crawl", "https://user:pass@example.com", expected=2)
        self.run_cli("crawl", self.base, "--max-pages", "10001", expected=2)
        self.run_cli("crawl", self.base, "--offline", expected=2)
        self.run_cli("crawl", "http://example.com:99999/", expected=2)
        self.run_cli("crawl", self.base, expected=2)

    def test_fuzz_urls_redirects_retries_cycles_and_read_only_boundary(self):
        rng = random.Random(20260811)
        malformed = ["", "ftp://example.com", "http://[::1", "http://example.com:99999", "https://u:p@example.com"]
        malformed.extend("".join(rng.choice("%[]:/?@\\abc") for _ in range(20)) for _ in range(100))
        for value in malformed:
            result = self.run_cli("inspect", value, expected=2)
            self.assertNotIn("Traceback", result.stderr)
        page = json.loads(self.run_cli("inspect", self.base + "flaky", "--timeout", "1", "--allow-private-network").stdout)
        self.assertIn(page["status"], {200, 429})
        with tempfile.TemporaryDirectory() as tmp:
            FixtureHandler.flaky_hits = 0
            retry_run = Path(tmp) / "retry"
            self.run_cli("crawl", self.base + "flaky", "--out", retry_run, "--max-pages", "1", "--retries", "2", "--allow-private-network")
            self.assertEqual(200, json.loads((retry_run / "pages.jsonl").read_text())["status"])
            slow = json.loads(self.run_cli("inspect", self.base + "slow", "--timeout", "0.05", "--allow-private-network").stdout)
            self.assertEqual(0, slow["status"])
            run = Path(tmp) / "run"
            self.run_cli("crawl", self.base, "--out", run, "--max-pages", "20", "--max-depth", "20", "--retries", "2", "--max-report-tokens", "64", "--allow-private-network")
            pages = [json.loads(x) for x in (run / "pages.jsonl").read_text().splitlines()]
            self.assertEqual(len({x["normalized_url"] for x in pages}), len(pages))
            self.assertIn("invalid-structured-data", {x["check"] for x in json.loads((run / "findings.json").read_text())["findings"]})
            self.run_cli("crawl", self.base, "--out", run, "--allow-private-network", expected=2)
        self.assertEqual({"GET"}, set(FixtureHandler.methods))

    def test_deterministic_semantic_rerun_and_output_budget(self):
        with tempfile.TemporaryDirectory() as tmp:
            first, second = Path(tmp) / "same", Path(tmp) / "same-copy"
            for run in (first, second):
                self.run_cli("crawl", self.base, "--out", run, "--max-pages", "8", "--deterministic", "--allow-private-network")
            for name in ("site.json", "links.json", "metadata.json", "structured-data.json", "sitemap.json", "robots.json", "findings.json"):
                self.assertEqual((first / name).read_bytes(), (second / name).read_bytes(), name)
            tiny = Path(tmp) / "tiny"
            self.run_cli("crawl", self.base, "--out", tiny, "--max-output-bytes", "1024", "--allow-private-network", expected=1)
            self.assertFalse(tiny.exists())

    def test_fail_on_and_cross_artifact_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp) / "gated"
            self.run_cli("crawl", self.base, "--out", run, "--max-pages", "8", "--allow-private-network", "--fail-on", "error", expected=1)
            self.run_cli("validate", run)
            data = json.loads((run / "run.json").read_text())
            data["counts"]["links"] += 1
            (run / "run.json").write_text(json.dumps(data))
            result = self.run_cli("validate", run, expected=1)
            self.assertIn("link count mismatch", result.stderr)

    def test_validation_rejects_symbolic_link_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp) / "run"
            self.run_cli("crawl", self.base, "--out", run, "--max-pages", "1", "--allow-private-network")
            report = run / "report.md"
            report.unlink()
            report.symlink_to(run / "run.json")
            result = self.run_cli("validate", run, expected=1)
            self.assertIn("symbolic-link artifact rejected", result.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
