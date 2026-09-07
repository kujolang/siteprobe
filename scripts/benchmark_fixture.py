#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class FixtureServer(ThreadingHTTPServer):
    # Accept the entire supported batch without imposing the stdlib backlog of 5.
    request_queue_size = 32


class Handler(BaseHTTPRequestHandler):
    pages = 10_000

    def log_message(self, *_args):
        pass

    def do_GET(self):
        port = self.server.server_port
        if self.path == "/robots.txt":
            body = f"User-agent: *\nSitemap: http://127.0.0.1:{port}/sitemap.xml\n"
            content_type = "text/plain"
        elif self.path == "/sitemap.xml":
            body = "<urlset>" + "".join(
                f"<url><loc>http://127.0.0.1:{port}/p/{index}</loc></url>"
                for index in range(self.pages)
            ) + "</urlset>"
            content_type = "application/xml"
        else:
            try:
                index = int(self.path.rsplit("/", 1)[-1])
            except ValueError:
                index = 0
            links = "".join(f'<a href="/p/{value}">page {value}</a>' for value in range(1, self.pages)) if index == 0 else '<a href="/p/0">home</a>'
            body = f'<title>Page {index}</title><meta name="description" content="Page {index}">{links}'
            content_type = "text/html"
        raw = body.encode()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        try:
            self.wfile.write(raw)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pages", type=int, default=10_000)
    parser.add_argument("--concurrency-levels", default="1,4,8,16")
    parser.add_argument("--output")
    parser.add_argument("--legacy", action="store_true", help="measure the frozen compatibility oracle")
    args = parser.parse_args()
    levels = sorted({int(value) for value in args.concurrency_levels.split(",")})
    if args.pages < 1 or args.pages > 10_000 or not levels or levels[0] < 1 or levels[-1] > 32:
        parser.error("pages must be 1..10000 and concurrency levels 1..32")
    Handler.pages = args.pages
    server = FixtureServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    results = []
    try:
        with tempfile.TemporaryDirectory() as tmp:
            for concurrency in levels:
                run = Path(tmp) / f"run-{concurrency}"
                metrics = Path(tmp) / f"metrics-{concurrency}.json"
                command = [sys.executable, str(ROOT / "tests/legacy/siteprobe.py")] if args.legacy else [os.environ.get("KUJO_BIN", str(ROOT.parent / "kujo/target/release/kujo")), "run", "src/main.kujo", "--"]
                subprocess.run([
                    *command, "crawl",
                    f"http://127.0.0.1:{server.server_port}/p/0",
                    "--out", str(run), "--max-pages", str(args.pages), "--max-depth", "2",
                    "--concurrency", str(concurrency), "--allow-private-network", "--json",
                    "--metrics-file", str(metrics),
                ], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", check=True)
                actual_pages = json.loads((run / "run.json").read_text())["counts"]["pages"]
                if actual_pages != args.pages:
                    raise RuntimeError(f"incomplete benchmark crawl: expected {args.pages} pages, got {actual_pages}")
                with (run / "pages.jsonl").open(encoding="utf-8") as rows:
                    successful_pages = sum(json.loads(row)["status"] == 200 for row in rows)
                if successful_pages != args.pages:
                    raise RuntimeError(f"failed benchmark fetches: expected {args.pages} HTTP 200 pages, got {successful_pages}")
                measurement = json.loads(metrics.read_text())
                measurement.update({
                    "concurrency": concurrency,
                    "pages": actual_pages,
                    "successful_pages": successful_pages,
                    "output_bytes": sum(item.stat().st_size for item in run.iterdir() if item.is_file()),
                    "pages_per_second": round(args.pages / measurement["wall_seconds"], 3),
                })
                results.append(measurement)
    finally:
        server.shutdown()
        server.server_close()
    report = {
        "schema": "siteprobe.benchmark/v2",
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "platform": os.uname().sysname if hasattr(os, "uname") else os.name,
        "pages": args.pages,
        "results": results,
    }
    encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        Path(args.output).write_text(encoded, encoding="utf-8")
    print(encoded, end="")


if __name__ == "__main__":
    main()
