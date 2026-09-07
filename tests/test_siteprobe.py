#!/usr/bin/env python3
from __future__ import annotations

import json
import gzip
import os
import random
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import importlib.util
import io
from contextlib import redirect_stdout, redirect_stderr
from unittest import mock
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "tests" / "legacy" / "siteprobe.py"
KUJO = Path(os.environ.get("KUJO_BIN", ROOT.parent / "kujo" / "target" / "release" / ("kujo.exe" if os.name == "nt" else "kujo")))
SPEC = importlib.util.spec_from_file_location("siteprobe_runtime", CLI)
SITEPROBE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = SITEPROBE
SPEC.loader.exec_module(SITEPROBE)


class FixtureHandler(BaseHTTPRequestHandler):
    paths = []
    methods = []
    request_times = []
    flaky_hits = 0
    robots_status = 200
    parallel_barrier = None
    wide_sitemap = False
    crawl_delay = 0
    def log_message(self, *_args):
        pass

    def do_GET(self):
        type(self).paths.append(self.path)
        type(self).methods.append("GET")
        type(self).request_times.append(time.monotonic())
        port = self.server.server_port
        routes = {
            "/robots.txt": (200, "text/plain", f"User-agent: *\nDisallow: /private\n" + (f"Crawl-delay: {type(self).crawl_delay}\n" if type(self).crawl_delay else "") + f"Sitemap: http://127.0.0.1:{port}/sitemap-index.xml\n"),
            "/sitemap-index.xml": (200, "application/xml", f"<sitemapindex><sitemap><loc>http://127.0.0.1:{port}/sitemap.xml.gz</loc></sitemap></sitemapindex>"),
            "/sitemap.xml": (200, "application/xml", f"<urlset><url><loc>http://127.0.0.1:{port}/</loc></url><url><loc>http://127.0.0.1:{port}/orphan</loc></url><url><loc>http://127.0.0.1:{port}/noindex</loc></url></urlset>"),
            "/": (200, "text/html", f'''<html lang="en"><head><title>Home</title><meta name="description" content="Shared description"><link rel="canonical" href="http://127.0.0.1:{port}/"><link rel="alternate" hreflang="fr" href="/fr"><meta http-equiv="refresh" content="30; url=/fresh"><meta property="og:title" content="Home"><script type="application/ld+json">{{"@type":"WebSite"}}</script></head><body><h1>Home</h1><a href="/duplicate">Duplicate</a><a href="/redirect">Redirect</a><a href="/broken">Broken</a><a href="https://example.net/">External</a><img src="/image.png"></body></html>'''),
            "/duplicate": (200, "text/html", '<html><head><title>Home</title><meta name="description" content="Shared description"></head><body><h1>Other</h1><a href="/noindex">Noindex</a><a href="/">Cycle</a><script type="application/ld+json">{"bad":</script></body></html>'),
            "/noindex": (200, "text/html", '<html><head><title>Noindex</title><meta name="robots" content="noindex"></head><body>Hidden</body></html>'),
            "/orphan": (200, "text/html", '<html><head><title>Orphan</title></head><body>Orphan content</body></html>'),
            "/private": (200, "text/html", '<html><head><title>Private</title></head><body>Private</body></html>'),
            "/image.png": (200, "image/png", "not-really-an-image"),
            "/nested": (200, "text/html", "<title>Nested <span>title</span></title><h1>Useful <em>heading</em></h1>"),
            "/many": (200, "text/html", "<title>Many</title>" + "".join(f'<a href=\"/p/{i}\">{i}</a>' for i in range(5))),
            "/queries": (200, "text/html", '<title>Queries</title><a href="/next?utm_source=x&b=2&a=1">next</a>'),
            "/etag": (200, "text/html", '<title>ETag</title><a href="/etag-next">next</a>'),
            "/etag-next": (200, "text/html", '<title>ETag next</title>'),
        }
        if self.path == '/parallel-root':
            routes[self.path]=(200,'text/html','<title>Parallel</title>'+''.join(f'<a href="/parallel/{i}">page</a>' for i in range(3)))
        if self.path.startswith('/parallel/') and type(self).parallel_barrier is not None:
            try:
                type(self).parallel_barrier.wait(timeout=5)
                routes[self.path]=(200,'text/html','<title>Concurrent</title>')
            except threading.BrokenBarrierError:
                routes[self.path]=(500,'text/html','<title>Concurrency barrier failed</title>')
        if type(self).wide_sitemap:
            if self.path == '/sitemap-index.xml':
                locations=['https://example.invalid/foreign.xml']+[f'http://127.0.0.1:{port}/map-{i}.xml' for i in range(100) for _ in range(2)]
                routes[self.path]=(200,'application/xml','<sitemapindex>'+''.join(f'<sitemap><loc>{url}</loc></sitemap>' for url in locations)+'</sitemapindex>')
            elif self.path.startswith('/map-'):
                routes[self.path]=(200,'application/xml','<urlset/>')
        if self.path == "/robots.txt" and type(self).robots_status != 200:
            self.send_response(type(self).robots_status); self.end_headers(); return
        if self.path == "/sitemap.xml.gz":
            raw = gzip.compress(routes["/sitemap.xml"][2].encode())
            self.send_response(200); self.send_header("Content-Type", "application/gzip"); self.send_header("Content-Length", str(len(raw))); self.end_headers(); self.wfile.write(raw); return
        if self.path == "/blocked-links":
            routes[self.path] = (200, "text/html", '<title>Blocked</title><a href="/private/a">a</a><a href="/private/b">b</a><a href="/private/c">c</a>')
        if self.path == "/private-redirect":
            self.send_response(302); self.send_header("Location", "/private"); self.end_headers(); return
        if self.path == "/redirect":
            self.send_response(302); self.send_header("Location", "/duplicate"); self.end_headers(); return
        if self.path == "/cross-origin-redirect":
            self.send_response(302); self.send_header("Location", "https://example.net/escaped"); self.end_headers(); return
        if self.path == "/flaky":
            type(self).flaky_hits += 1
            if type(self).flaky_hits < 2:
                self.send_response(429); self.send_header("Retry-After", "0"); self.end_headers(); return
            routes["/flaky"] = (200, "text/html", "<title>Recovered</title>")
        if self.path == "/slow":
            time.sleep(0.2); routes["/slow"] = (200, "text/html", "<title>Slow</title>")
        if self.path.startswith("/etag"):
            if self.headers.get("If-None-Match") == '"fixture-v1"':
                self.send_response(304); self.send_header("ETag", '"fixture-v1"'); self.end_headers(); return
        status, ctype, body = routes.get(self.path, (404, "text/html", "<title>Not found</title>"))
        encoded = body.encode(); self.send_response(status); self.send_header("Content-Type", ctype)
        if self.path.startswith("/etag"): self.send_header("ETag", '"fixture-v1"')
        if self.path == "/":
            self.send_header("Link", '</api>; rel="alternate"; type="application/json"')
            self.send_header("Link", '</feed>; rel="alternate"; type="application/rss+xml"')
        self.send_header("Content-Length", str(len(encoded))); self.end_headers()
        try: self.wfile.write(encoded)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError): pass


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
        result = subprocess.run([str(KUJO), "run", "src/main.kujo", "--", *map(str, args)], cwd=ROOT, text=True, encoding="utf-8", capture_output=True)
        self.assertEqual(expected, result.returncode, result.stderr + result.stdout)
        return result

    def run_cli_in_process(self, *args, expected=0):
        # Exercise the same parser and dispatch without a fresh interpreter for
        # each deterministic fuzz sample. Subprocess CLI smoke tests stay above.
        stdout, stderr = io.StringIO(), io.StringIO()
        with mock.patch.object(sys, 'argv', ['siteprobe', *map(str, args)]), redirect_stdout(stdout), redirect_stderr(stderr):
            try:
                rc = SITEPROBE.main()
            except SystemExit as exc:
                rc = exc.code
        result = subprocess.CompletedProcess(args, rc, stdout.getvalue(), stderr.getvalue())
        self.assertEqual(expected, result.returncode, result.stderr + result.stdout)
        return result

    def run_kujo_cli(self, *args, expected=0):
        result = subprocess.run([str(KUJO), "run", "src/main.kujo", "--", *map(str, args)], cwd=ROOT, text=True, encoding="utf-8", capture_output=True)
        self.assertEqual(expected, result.returncode, result.stderr + result.stdout)
        return result

    def test_full_fixture_contract_and_compare(self):
        with tempfile.TemporaryDirectory() as tmp:
            run1 = Path(tmp) / "run1"; run2 = Path(tmp) / "run2"
            self.run_cli("crawl", self.base, "--out", run1, "--max-pages", "20", "--max-depth", "3", "--allow-private-network", "--json")
            self.run_cli("validate", run1)
            self.run_kujo_cli("validate", run1)
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
            for example in ("contentgraph.kujo", "runledger.kujo"):
                result = subprocess.run([str(KUJO), "run", f"examples/{example}", "--", str(run1)], cwd=ROOT, text=True, encoding="utf-8", capture_output=True)
                self.assertEqual(0, result.returncode, result.stderr + result.stdout)
                self.assertTrue(json.loads(result.stdout)["schema"].startswith("siteprobe."))
            eval_result = subprocess.run([str(KUJO), "run", "examples/eval.kujo", "--", str(run1)], cwd=ROOT, text=True, encoding="utf-8", capture_output=True)
            self.assertEqual(1, eval_result.returncode)
            ci_result = subprocess.run([str(KUJO), "run", "examples/ci_baseline.kujo", "--", str(run1), str(run2), str(KUJO)], cwd=ROOT, text=True, encoding="utf-8", capture_output=True)
            self.assertEqual(0, ci_result.returncode, ci_result.stderr + ci_result.stdout)
            schema_pages = [json.loads(line) for line in (run2 / "pages.jsonl").read_text().splitlines()]
            schema_pages[0]["status"] = "not-an-integer"
            (run2 / "pages.jsonl").write_text("".join(json.dumps(page) + "\n" for page in schema_pages))
            (run2 / "manifest.json").unlink()
            native_failure = self.run_kujo_cli("validate", run2, expected=1)
            self.assertIn("schema validation failed", native_failure.stderr)

    def test_inspect_and_doctor(self):
        self.assertTrue(json.loads(self.run_cli("doctor").stdout)["ok"])
        blocked = self.run_cli("inspect", self.base, expected=2)
        self.assertIn("private network target blocked", blocked.stderr)
        page = json.loads(self.run_cli("inspect", self.base, "--allow-private-network").stdout)
        self.assertEqual(200, page["status"])
        self.assertEqual("Home", page["title"])
        self.assertEqual("fr", page["hreflang"][0]["language"])
        self.assertTrue(page["refresh"]["url"].endswith("/fresh"))
        self.assertEqual("alternate", page["http_links"][0]["rel"])
        self.assertEqual(2, len(page["http_links"]))
        blocked_redirect = json.loads(self.run_cli("inspect", self.base + "cross-origin-redirect", "--allow-private-network").stdout)
        self.assertEqual(0, blocked_redirect["status"])
        self.assertEqual("cross-origin redirect blocked", blocked_redirect["error"])
        self.assertTrue(blocked_redirect["redirect_chain"])
        nested = json.loads(self.run_cli("inspect", self.base + "nested", "--allow-private-network").stdout)
        self.assertEqual("Nested title", nested["title"])
        self.assertEqual(["Useful heading"], nested["headings"]["h1"])
        capped = json.loads(self.run_cli("inspect", self.base + "many", "--allow-private-network", "--max-links-per-page", "2").stdout)
        self.assertEqual(2, capped["outgoing_link_count"])
        self.assertTrue(capped["truncated"]["links"])

    def test_rejects_credentials_and_bad_bounds(self):
        self.assertEqual("https://xn--bcher-kva.example/a", SITEPROBE.normalize_url("HTTPS://BÜCHER.example:443//a"))
        self.assertEqual("http://[::1]/", SITEPROBE.normalize_url("http://[::1]:80"))
        self.run_cli("crawl", "https://user:pass@example.com", expected=2)
        self.run_cli("crawl", self.base, "--max-pages", "10001", expected=2)
        self.run_cli("crawl", self.base, "--offline", expected=2)
        self.run_cli("crawl", "http://example.com:99999/", expected=2)
        self.run_cli("crawl", self.base, expected=2)

    def test_fuzz_urls_redirects_retries_cycles_and_read_only_boundary(self):
        rng = random.Random(20260811)
        malformed = ["", "ftp://example.com", "http://[::1", "http://example.com:99999", "https://u:p@example.com"]
        malformed.extend("".join(rng.choice("%[]:/?@\\abc") for _ in range(20)) for _ in range(100))
        for index, value in enumerate(malformed):
            runner = self.run_cli if index < 5 else self.run_cli_in_process
            result = runner("inspect", value, expected=2)
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
            second = Path(tmp) / "unsafe-entry"
            self.run_cli("crawl", self.base, "--out", second, "--max-pages", "1", "--allow-private-network")
            (second / "unexpected").mkdir()
            result = self.run_cli("verify", second, expected=1)
            self.assertIn("unsafe entries", result.stderr)

    def test_signed_manifest_query_policy_pacing_and_conditional_fetch(self):
        with tempfile.TemporaryDirectory() as tmp:
            key = Path(tmp) / "key"
            key.write_bytes(b"siteprobe-test-signing-key-material-32-bytes")
            signed = Path(tmp) / "signed"
            self.run_cli("crawl", self.base + "queries", "--out", signed, "--max-pages", "2", "--allow-private-network", "--query-policy", "sort", "--query-deny-param", "utm_source", "--signing-key-file", key)
            self.run_cli("verify", signed, "--signing-key-file", key)
            links = json.loads((signed / "links.json").read_text())["links"]
            self.assertTrue(any(row["target"].endswith("/next?a=1&b=2") for row in links))
            (signed / "report.md").write_text("tampered")
            tampered = self.run_cli("verify", signed, "--signing-key-file", key, expected=1)
            self.assertIn("manifest", tampered.stderr)

            manifest = json.loads((signed / "manifest.json").read_text())
            manifest["digest_algorithm"] = "md5"
            (signed / "manifest.json").write_text(json.dumps(manifest))
            unsupported = self.run_cli("verify", signed, expected=1)
            self.assertIn("digest algorithm", unsupported.stderr)

            FixtureHandler.request_times = []
            FixtureHandler.crawl_delay = 1
            paced = Path(tmp) / "paced"
            try:
                self.run_cli("crawl", self.base + "etag", "--out", paced, "--max-pages", "2", "--max-depth", "1", "--allow-private-network", "--max-crawl-delay", "0.04")
            finally:
                FixtureHandler.crawl_delay = 0
            intervals = [b - a for a, b in zip(FixtureHandler.request_times[1:], FixtureHandler.request_times[2:])]
            self.assertTrue(any(value >= 0.03 for value in intervals), intervals)
            pacing = json.loads((paced / "run.json").read_text())["configuration"]["request_pacing"]
            self.assertEqual(1.0, pacing["robots_crawl_delay_seconds"])
            self.assertEqual(0.04, pacing["effective_delay_seconds"])

            conditional = Path(tmp) / "conditional"
            self.run_cli("crawl", self.base + "etag", "--out", conditional, "--max-pages", "2", "--max-depth", "1", "--allow-private-network", "--baseline", paced)
            pages = [json.loads(line) for line in (conditional / "pages.jsonl").read_text().splitlines()]
            self.assertTrue(pages)
            self.assertTrue(all(page["not_modified"] for page in pages))
            self.assertTrue(all(page["response_status"] == 304 for page in pages))

    def test_gzip_expansion_limit(self):
        compressed = gzip.compress(b"x" * 8192)
        with self.assertRaisesRegex(ValueError, "expanded sitemap exceeded"):
            SITEPROBE.decode_gzip_bounded(compressed, 1024)


if __name__ == "__main__":
    unittest.main(verbosity=2)
