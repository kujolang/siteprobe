#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "bridge" / "siteprobe.py"


class FixtureHandler(BaseHTTPRequestHandler):
    def log_message(self, *_args):
        pass

    def do_GET(self):
        port = self.server.server_port
        routes = {
            "/robots.txt": (200, "text/plain", f"User-agent: *\nDisallow: /private\nSitemap: http://127.0.0.1:{port}/sitemap-index.xml\n"),
            "/sitemap-index.xml": (200, "application/xml", f"<sitemapindex><sitemap><loc>http://127.0.0.1:{port}/sitemap.xml</loc></sitemap></sitemapindex>"),
            "/sitemap.xml": (200, "application/xml", f"<urlset><url><loc>http://127.0.0.1:{port}/</loc></url><url><loc>http://127.0.0.1:{port}/orphan</loc></url><url><loc>http://127.0.0.1:{port}/noindex</loc></url></urlset>"),
            "/": (200, "text/html", f'''<html lang="en"><head><title>Home</title><meta name="description" content="Shared description"><link rel="canonical" href="http://127.0.0.1:{port}/"><meta property="og:title" content="Home"><script type="application/ld+json">{{"@type":"WebSite"}}</script></head><body><h1>Home</h1><a href="/duplicate">Duplicate</a><a href="/redirect">Redirect</a><a href="/broken">Broken</a><a href="https://example.net/">External</a><img src="/image.png"></body></html>'''),
            "/duplicate": (200, "text/html", '<html><head><title>Home</title><meta name="description" content="Shared description"></head><body><h1>Other</h1><a href="/noindex">Noindex</a></body></html>'),
            "/noindex": (200, "text/html", '<html><head><title>Noindex</title><meta name="robots" content="noindex"></head><body>Hidden</body></html>'),
            "/orphan": (200, "text/html", '<html><head><title>Orphan</title></head><body>Orphan content</body></html>'),
            "/private": (200, "text/html", '<html><head><title>Private</title></head><body>Private</body></html>'),
            "/image.png": (200, "image/png", "not-really-an-image"),
        }
        if self.path == "/redirect":
            self.send_response(302); self.send_header("Location", "/duplicate"); self.end_headers(); return
        status, ctype, body = routes.get(self.path, (404, "text/html", "<title>Not found</title>"))
        encoded = body.encode(); self.send_response(status); self.send_header("Content-Type", ctype); self.send_header("Content-Length", str(len(encoded))); self.end_headers(); self.wfile.write(encoded)


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
            self.run_cli("crawl", self.base, "--out", run1, "--max-pages", "20", "--max-depth", "3", "--json")
            self.run_cli("validate", run1)
            data = json.loads((run1 / "run.json").read_text())
            self.assertEqual("siteprobe.run/v1", data["schema"])
            self.assertGreaterEqual(data["counts"]["pages"], 5)
            checks = {x["check"] for x in json.loads((run1 / "findings.json").read_text())["findings"]}
            self.assertTrue({"broken-url", "duplicate-title", "duplicate-description", "not-indexable", "missing-image-alt", "orphan-candidate"} <= checks)
            pages = [json.loads(x) for x in (run1 / "pages.jsonl").read_text().splitlines()]
            self.assertFalse(any(x["normalized_url"].endswith("/private") and x["status"] == 200 for x in pages))
            self.run_cli("crawl", self.base, "--out", run2, "--max-pages", "4", "--max-depth", "1")
            comparison = json.loads(self.run_cli("compare", run1, run2).stdout)
            self.assertTrue(comparison["changes"])

    def test_inspect_and_doctor(self):
        self.assertTrue(json.loads(self.run_cli("doctor").stdout)["ok"])
        page = json.loads(self.run_cli("inspect", self.base).stdout)
        self.assertEqual(200, page["status"])
        self.assertEqual("Home", page["title"])

    def test_rejects_credentials_and_bad_bounds(self):
        self.run_cli("crawl", "https://user:pass@example.com", expected=2)
        self.run_cli("crawl", self.base, "--max-pages", "10001", expected=2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
