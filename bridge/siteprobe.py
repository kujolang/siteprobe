#!/usr/bin/env python3
"""Bounded standard-library HTTP/HTML bridge for SiteProbe's Kujo CLI."""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
import re
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Iterable

VERSION = "0.1.0"
RUN_SCHEMA = "siteprobe.run/v1"
PAGE_SCHEMA = "siteprobe.page/v1"
UA = f"Kujo-SiteProbe/{VERSION} (+https://github.com/kujolang/siteprobe)"
MAX_BYTES = 5 * 1024 * 1024
REQUIRED = [
    "run.json", "site.json", "pages.jsonl", "links.json", "redirects.json",
    "metadata.json", "structured-data.json", "sitemap.json", "robots.json",
    "findings.json", "report.md",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def slug_time() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def dump(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_url(url: str, base: str | None = None) -> str:
    joined = urllib.parse.urljoin(base or "", url.strip())
    parsed = urllib.parse.urlsplit(joined)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
        return ""
    host = parsed.hostname.lower()
    port = parsed.port
    netloc = host
    if port and not ((parsed.scheme == "http" and port == 80) or (parsed.scheme == "https" and port == 443)):
        netloc = f"{host}:{port}"
    path = re.sub(r"/{2,}", "/", parsed.path or "/")
    path = urllib.parse.quote(urllib.parse.unquote(path), safe="/%:@!$&'()*+,;=-._~")
    query = urllib.parse.urlencode(urllib.parse.parse_qsl(parsed.query, keep_blank_values=True), doseq=True)
    return urllib.parse.urlunsplit((parsed.scheme.lower(), netloc, path, query, ""))


def origin(url: str) -> str:
    p = urllib.parse.urlsplit(url)
    return f"{p.scheme}://{p.netloc}"


def same_origin(a: str, b: str) -> bool:
    return origin(a) == origin(b)


def text_fingerprint(text: str) -> str:
    normalized = re.sub(r"\s+", " ", text).strip().lower()
    return hashlib.sha256(normalized.encode()).hexdigest() if normalized else ""


class RedirectRecorder(urllib.request.HTTPRedirectHandler):
    def __init__(self) -> None:
        self.chain: list[dict[str, Any]] = []

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        self.chain.append({"from": req.full_url, "status": code, "to": newurl})
        return super().redirect_request(req, fp, code, msg, headers, newurl)


@dataclass
class ParsedPage:
    title: str = ""
    description: str = ""
    canonical: str = ""
    language: str = ""
    headings: dict[str, list[str]] = field(default_factory=lambda: defaultdict(list))
    links: list[dict[str, str]] = field(default_factory=list)
    images: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, str] = field(default_factory=dict)
    structured_data: list[Any] = field(default_factory=list)
    pagination: dict[str, str] = field(default_factory=dict)
    robots: list[str] = field(default_factory=list)
    text_parts: list[str] = field(default_factory=list)


class PageParser(HTMLParser):
    def __init__(self, base: str) -> None:
        super().__init__(convert_charrefs=True)
        self.base = base
        self.page = ParsedPage()
        self._tag = ""
        self._skip = 0
        self._jsonld = False
        self._json_parts: list[str] = []
        self._link: dict[str, str] | None = None

    def handle_starttag(self, tag: str, attrs_list: list[tuple[str, str | None]]) -> None:
        attrs = {k.lower(): (v or "") for k, v in attrs_list}
        tag = tag.lower()
        self._tag = tag
        if tag in {"script", "style", "noscript", "template"}:
            self._skip += 1
        if tag == "html":
            self.page.language = attrs.get("lang", "")
        elif tag == "meta":
            name = (attrs.get("name") or attrs.get("property") or attrs.get("http-equiv") or "").lower()
            value = attrs.get("content", "").strip()
            if name == "description": self.page.description = value
            if name in {"robots", "googlebot", "bingbot"}:
                self.page.robots.extend(x.strip().lower() for x in value.split(",") if x.strip())
            if name and value: self.page.metadata[name] = value
        elif tag == "link":
            rels = {x.lower() for x in attrs.get("rel", "").split()}
            href = normalize_url(attrs.get("href", ""), self.base)
            if "canonical" in rels: self.page.canonical = href
            if "next" in rels and href: self.page.pagination["next"] = href
            if "prev" in rels and href: self.page.pagination["prev"] = href
        elif tag == "a":
            href = normalize_url(attrs.get("href", ""), self.base)
            if href: self._link = {"url": href, "text": "", "rel": attrs.get("rel", "")}
        elif tag == "img":
            src = normalize_url(attrs.get("src", ""), self.base)
            if src:
                self.page.images.append({"url": src, "alt": attrs.get("alt", ""), "missing_alt": "alt" not in attrs})
        elif tag == "script" and attrs.get("type", "").lower() == "application/ld+json":
            self._jsonld = True

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "a" and self._link:
            self._link["text"] = re.sub(r"\s+", " ", self._link["text"]).strip()
            self.page.links.append(self._link)
            self._link = None
        if tag == "script" and self._jsonld:
            raw = "".join(self._json_parts).strip()
            if raw:
                try: self.page.structured_data.append(json.loads(raw))
                except json.JSONDecodeError: self.page.structured_data.append({"invalid": True, "raw_fingerprint": text_fingerprint(raw)})
            self._jsonld = False
            self._json_parts = []
        if tag in {"script", "style", "noscript", "template"} and self._skip:
            self._skip -= 1
        self._tag = ""

    def handle_data(self, data: str) -> None:
        if self._jsonld:
            self._json_parts.append(data)
            return
        clean = re.sub(r"\s+", " ", data).strip()
        if not clean or self._skip: return
        if self._tag == "title": self.page.title += clean
        if self._tag in {"h1", "h2", "h3", "h4", "h5", "h6"}: self.page.headings[self._tag].append(clean)
        if self._link is not None: self._link["text"] += " " + clean
        self.page.text_parts.append(clean)


def fetch(url: str, timeout: float) -> tuple[int, str, dict[str, str], bytes, list[dict[str, Any]], str]:
    recorder = RedirectRecorder()
    opener = urllib.request.build_opener(recorder)
    request = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.5"})
    try:
        with opener.open(request, timeout=timeout) as response:
            body = response.read(MAX_BYTES + 1)
            if len(body) > MAX_BYTES: raise ValueError("response exceeded 5 MiB limit")
            return response.status, response.geturl(), {k.lower(): v for k, v in response.headers.items()}, body, recorder.chain, ""
    except urllib.error.HTTPError as exc:
        body = exc.read(MAX_BYTES + 1)
        return exc.code, exc.geturl(), {k.lower(): v for k, v in exc.headers.items()}, body[:MAX_BYTES], recorder.chain, str(exc)
    except (urllib.error.URLError, TimeoutError, ValueError, OSError) as exc:
        return 0, url, {}, b"", recorder.chain, str(exc)


def decode_body(body: bytes, content_type: str) -> str:
    match = re.search(r"charset=([^;\s]+)", content_type, re.I)
    charset = match.group(1).strip('"\'') if match else "utf-8"
    try: return body.decode(charset, errors="replace")
    except LookupError: return body.decode("utf-8", errors="replace")


def discover_sitemaps(base_url: str, robots_text: str, timeout: float) -> dict[str, Any]:
    candidates = [line.split(":", 1)[1].strip() for line in robots_text.splitlines() if line.lower().startswith("sitemap:")]
    if not candidates: candidates = [urllib.parse.urljoin(origin(base_url), "/sitemap.xml")]
    seen: set[str] = set()
    urls: set[str] = set()
    errors: list[dict[str, str]] = []
    queue = deque(candidates[:20])
    while queue and len(seen) < 50:
        sitemap_url = normalize_url(queue.popleft())
        if not sitemap_url or sitemap_url in seen or not same_origin(sitemap_url, base_url): continue
        seen.add(sitemap_url)
        status, _, headers, body, _, error = fetch(sitemap_url, timeout)
        if status != 200:
            errors.append({"url": sitemap_url, "error": error or f"HTTP {status}"})
            continue
        try:
            root = ET.fromstring(decode_body(body, headers.get("content-type", "")))
            locs = [normalize_url((node.text or "").strip()) for node in root.iter() if node.tag.rsplit("}", 1)[-1] == "loc"]
            if root.tag.rsplit("}", 1)[-1] == "sitemapindex": queue.extend([x for x in locs if x])
            else: urls.update(x for x in locs if x and same_origin(x, base_url))
        except ET.ParseError as exc:
            errors.append({"url": sitemap_url, "error": f"invalid XML: {exc}"})
    return {"schema": "siteprobe.sitemap/v1", "sitemaps": sorted(seen), "urls": sorted(urls), "errors": errors}


def inspect_page(url: str, depth: int, timeout: float, sitemap_urls: set[str]) -> dict[str, Any]:
    started = time.monotonic()
    status, final_url, headers, body, redirects, error = fetch(url, timeout)
    content_type = headers.get("content-type", "").split(";", 1)[0].lower()
    parser = PageParser(final_url)
    if body and ("html" in content_type or body.lstrip().startswith(b"<")):
        try: parser.feed(decode_body(body, headers.get("content-type", "")))
        except (UnicodeError, ValueError): pass
    page = parser.page
    text = " ".join(page.text_parts)
    xrobots = [x.strip().lower() for x in headers.get("x-robots-tag", "").split(",") if x.strip()]
    directives = sorted(set(page.robots + xrobots))
    indexable = status == 200 and "noindex" not in directives and content_type in {"text/html", "application/xhtml+xml", ""}
    internal = [link for link in page.links if same_origin(link["url"], final_url)]
    external = [link for link in page.links if not same_origin(link["url"], final_url)]
    return {
        "schema": PAGE_SCHEMA, "url": url, "normalized_url": normalize_url(url), "status": status,
        "redirect_chain": redirects, "final_url": normalize_url(final_url), "canonical": page.canonical,
        "indexable": indexable, "robots_directives": directives, "sitemap_member": normalize_url(final_url) in sitemap_urls,
        "title": page.title.strip(), "meta_description": page.description, "headings": dict(page.headings),
        "language": page.language, "content_type": content_type, "content_fingerprint": text_fingerprint(text),
        "word_count": len(re.findall(r"\b[\w'-]+\b", text)), "internal_links": internal, "external_links": external,
        "links": page.links, "images": page.images, "missing_alt_count": sum(1 for image in page.images if image["missing_alt"]),
        "open_graph": {k: v for k, v in page.metadata.items() if k.startswith("og:")},
        "social_metadata": {k: v for k, v in page.metadata.items() if k.startswith("twitter:")},
        "structured_data": page.structured_data, "pagination": page.pagination, "depth": depth,
        "incoming_link_count": 0, "outgoing_link_count": len(page.links), "error": error,
        "elapsed_ms": round((time.monotonic() - started) * 1000),
    }


def finding_id(check: str, target: str) -> str:
    return "SP-" + hashlib.sha256(f"{check}\0{target}".encode()).hexdigest()[:16].upper()


def analyze(pages: list[dict[str, Any]], sitemap: dict[str, Any], start_url: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    by_url = {p["normalized_url"]: p for p in pages}
    incoming: Counter[str] = Counter()
    all_links: list[dict[str, Any]] = []
    for page in pages:
        for link in page["links"]:
            row = {"source": page["normalized_url"], "target": link["url"], "text": link["text"], "rel": link["rel"], "internal": same_origin(link["url"], start_url)}
            all_links.append(row)
            if row["internal"]: incoming[link["url"]] += 1
    for page in pages: page["incoming_link_count"] = incoming[page["normalized_url"]]
    titles: defaultdict[str, list[str]] = defaultdict(list)
    descriptions: defaultdict[str, list[str]] = defaultdict(list)
    fingerprints: defaultdict[str, list[str]] = defaultdict(list)
    findings: list[dict[str, Any]] = []

    def add(check: str, target: str, severity: str, evidence: Any) -> None:
        findings.append({"id": finding_id(check, target), "check": check, "target": target, "severity": severity, "evidence": evidence})

    for page in pages:
        url = page["normalized_url"]
        if page["title"]: titles[page["title"].strip().lower()].append(url)
        elif page["status"] == 200 and "html" in page["content_type"]: add("missing-title", url, "warning", {})
        if page["meta_description"]: descriptions[page["meta_description"].strip().lower()].append(url)
        elif page["status"] == 200 and "html" in page["content_type"]: add("missing-description", url, "warning", {})
        if page["content_fingerprint"]: fingerprints[page["content_fingerprint"]].append(url)
        if page["status"] == 0 or page["status"] >= 400: add("broken-url", url, "error", {"status": page["status"], "error": page["error"]})
        if page["canonical"] and normalize_url(page["canonical"]) != normalize_url(page["final_url"]): add("canonical-conflict", url, "warning", {"canonical": page["canonical"], "final_url": page["final_url"]})
        if page["missing_alt_count"]: add("missing-image-alt", url, "warning", {"count": page["missing_alt_count"]})
        if not page["indexable"] and page["status"] == 200: add("not-indexable", url, "info", {"directives": page["robots_directives"]})
        if any(isinstance(x, dict) and x.get("invalid") for x in page["structured_data"]): add("invalid-structured-data", url, "warning", {})
    for check, groups in (("duplicate-title", titles), ("duplicate-description", descriptions), ("duplicate-content", fingerprints)):
        for value, urls in groups.items():
            if len(urls) > 1: add(check, urls[0], "warning", {"urls": sorted(urls), "value_fingerprint": text_fingerprint(value)})
    crawled = set(by_url)
    for url in sitemap["urls"]:
        if url not in crawled or (url != normalize_url(start_url) and incoming[url] == 0): add("orphan-candidate", url, "warning", {"sitemap_member": True, "incoming_links": incoming[url], "crawled": url in crawled})
    return {"schema": "siteprobe.links/v1", "links": sorted(all_links, key=lambda x: (x["source"], x["target"]))}, sorted(findings, key=lambda x: (x["severity"], x["check"], x["target"]))


def crawl(args: argparse.Namespace) -> int:
    target = normalize_url(args.url)
    if not target:
        print("SiteProbe: target must be an http(s) URL without credentials", file=sys.stderr); return 2
    out = Path(args.out or f".siteprobe/{slug_time()}").expanduser().resolve()
    if out.exists() and not out.is_dir():
        print(f"SiteProbe: output is not a directory: {out}", file=sys.stderr); return 2
    out.mkdir(parents=True, exist_ok=True)
    robots_url = urllib.parse.urljoin(origin(target), "/robots.txt")
    robots_status, _, robots_headers, robots_body, _, robots_error = fetch(robots_url, args.timeout)
    robots_text = decode_body(robots_body, robots_headers.get("content-type", "")) if robots_body else ""
    robot = urllib.robotparser.RobotFileParser(); robot.set_url(robots_url); robot.parse(robots_text.splitlines())
    sitemap = discover_sitemaps(target, robots_text, args.timeout)
    sitemap_urls = set(sitemap["urls"])
    queue = deque([(target, 0)])
    queued = {target}
    pages: list[dict[str, Any]] = []
    redirects: list[dict[str, Any]] = []
    started = utc_now()
    while queue and len(pages) < args.max_pages:
        batch: list[tuple[str, int]] = []
        while queue and len(batch) < min(args.concurrency, args.max_pages - len(pages)):
            url, depth = queue.popleft()
            if depth > args.max_depth: continue
            if args.respect_robots and not robot.can_fetch(UA, url):
                pages.append({"schema": PAGE_SCHEMA, "url": url, "normalized_url": url, "status": 0, "redirect_chain": [], "final_url": url, "canonical": "", "indexable": False, "robots_directives": ["blocked-by-robots"], "sitemap_member": url in sitemap_urls, "title": "", "meta_description": "", "headings": {}, "language": "", "content_type": "", "content_fingerprint": "", "word_count": 0, "internal_links": [], "external_links": [], "links": [], "images": [], "missing_alt_count": 0, "open_graph": {}, "social_metadata": {}, "structured_data": [], "pagination": {}, "depth": depth, "incoming_link_count": 0, "outgoing_link_count": 0, "error": "blocked by robots.txt", "elapsed_ms": 0})
                continue
            batch.append((url, depth))
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as pool:
            futures = {pool.submit(inspect_page, url, depth, args.timeout, sitemap_urls): (url, depth) for url, depth in batch}
            results = [future.result() for future in futures]
        for page in sorted(results, key=lambda p: p["normalized_url"]):
            pages.append(page); redirects.extend(page["redirect_chain"])
            if page["depth"] >= args.max_depth: continue
            for link in page["internal_links"]:
                url = link["url"]
                if same_origin(url, target) and url not in queued and len(queued) < args.max_pages * 10:
                    queued.add(url); queue.append((url, page["depth"] + 1))
    pages.sort(key=lambda p: p["normalized_url"])
    links, findings = analyze(pages, sitemap, target)
    titles = defaultdict(list); descriptions = defaultdict(list)
    for p in pages:
        if p["title"]: titles[p["title"]].append(p["normalized_url"])
        if p["meta_description"]: descriptions[p["meta_description"]].append(p["normalized_url"])
    run = {"schema": RUN_SCHEMA, "run_id": out.name, "started_at": started, "completed_at": utc_now(), "target": target,
           "configuration": {"max_pages": args.max_pages, "max_depth": args.max_depth, "concurrency": args.concurrency, "timeout": args.timeout, "respect_robots": args.respect_robots, "same_origin": True, "baseline": args.baseline},
           "counts": {"pages": len(pages), "links": len(links["links"]), "redirects": len(redirects), "findings": len(findings)}}
    site = {"schema": "siteprobe.site/v1", "target": target, "origin": origin(target), "robots_url": robots_url, "sitemaps": sitemap["sitemaps"], "crawlable_pages": sum(1 for p in pages if p["status"] == 200), "indexable_pages": sum(1 for p in pages if p["indexable"])}
    metadata = {"schema": "siteprobe.metadata/v1", "titles": titles, "descriptions": descriptions}
    structured = {"schema": "siteprobe.structured-data/v1", "pages": [{"url": p["normalized_url"], "items": p["structured_data"]} for p in pages if p["structured_data"]]}
    robots = {"schema": "siteprobe.robots/v1", "url": robots_url, "status": robots_status, "text_fingerprint": text_fingerprint(robots_text), "error": robots_error, "sitemaps": sitemap["sitemaps"]}
    dump(out / "run.json", run); dump(out / "site.json", site); dump(out / "links.json", links); dump(out / "redirects.json", {"schema": "siteprobe.redirects/v1", "redirects": redirects}); dump(out / "metadata.json", metadata); dump(out / "structured-data.json", structured); dump(out / "sitemap.json", sitemap); dump(out / "robots.json", robots); dump(out / "findings.json", {"schema": "siteprobe.findings/v1", "findings": findings})
    (out / "pages.jsonl").write_text("".join(json.dumps(p, sort_keys=True) + "\n" for p in pages), encoding="utf-8")
    report_text = render_report(run, findings)
    (out / "report.md").write_text(report_text, encoding="utf-8")
    if args.baseline:
        rc, comparison = compare_runs(Path(args.baseline), out)
        dump(out / "comparison.json", comparison)
        if rc: return rc
    if args.json: print(json.dumps({"run": str(out), "counts": run["counts"]}, sort_keys=True))
    else: print(f"SiteProbe crawl complete: {out}\nPages: {len(pages)}  Findings: {len(findings)}")
    return 0


def read_pages(run: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in (run / "pages.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]


def render_report(run: dict[str, Any], findings: list[dict[str, Any]]) -> str:
    important = [f for f in findings if f["severity"] in {"error", "warning"}]
    lines = ["# SiteProbe Report", "", f"Target: {run['target']}", f"Run: {run['run_id']}", "", "## Attention", ""]
    if important:
        lines.extend(f"- [{f['severity']}] {f['check']}: {f['target']}" for f in important)
    else: lines.append("- No error or warning findings.")
    lines += ["", "## Coverage", "", f"- Pages inspected: {run['counts']['pages']}", f"- Links recorded: {run['counts']['links']}", f"- Findings retained: {run['counts']['findings']}", "", "Full machine evidence remains in the run directory.", ""]
    return "\n".join(lines)


def validate_run(run: Path) -> tuple[int, list[str]]:
    errors: list[str] = []
    if not run.is_dir(): return 1, [f"run directory not found: {run}"]
    for name in REQUIRED:
        if not (run / name).is_file(): errors.append(f"missing {name}")
    if errors: return 1, errors
    try:
        data = load(run / "run.json")
        if data.get("schema") != RUN_SCHEMA: errors.append("unsupported run schema")
        pages = read_pages(run)
        if len(pages) != data.get("counts", {}).get("pages"): errors.append("page count mismatch")
        if any(page.get("schema") != PAGE_SCHEMA for page in pages): errors.append("unsupported page schema")
        finding_ids = [x["id"] for x in load(run / "findings.json").get("findings", [])]
        if len(finding_ids) != len(set(finding_ids)): errors.append("duplicate finding IDs")
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc: errors.append(str(exc))
    return (1 if errors else 0), errors


def compare_runs(old: Path, new: Path) -> tuple[int, dict[str, Any]]:
    for path in (old, new):
        rc, errors = validate_run(path)
        if rc: return 1, {"schema": "siteprobe.comparison/v1", "errors": [f"{path}: {e}" for e in errors], "changes": []}
    before = {p["normalized_url"]: p for p in read_pages(old)}; after = {p["normalized_url"]: p for p in read_pages(new)}
    changes: list[dict[str, Any]] = []
    for url in sorted(after.keys() - before.keys()): changes.append({"type": "NEW URL", "url": url})
    for url in sorted(before.keys() - after.keys()): changes.append({"type": "REMOVED URL", "url": url})
    fields = [("status", "STATUS CHANGED"), ("canonical", "CANONICAL CHANGED"), ("title", "TITLE CHANGED"), ("indexable", "INDEXABILITY CHANGED"), ("meta_description", "METADATA REGRESSION"), ("content_fingerprint", "CONTENT MATERIALLY CHANGED")]
    for url in sorted(before.keys() & after.keys()):
        for field_name, label in fields:
            if before[url].get(field_name) != after[url].get(field_name): changes.append({"type": label, "url": url, "before": before[url].get(field_name), "after": after[url].get(field_name)})
        had_schema = bool(before[url].get("structured_data")); has_schema = bool(after[url].get("structured_data"))
        if had_schema and not has_schema: changes.append({"type": "SCHEMA REGRESSION", "url": url})
        was_broken = before[url].get("status", 0) == 0 or before[url].get("status", 0) >= 400
        is_broken = after[url].get("status", 0) == 0 or after[url].get("status", 0) >= 400
        if not was_broken and is_broken: changes.append({"type": "LINK BROKEN", "url": url})
        if was_broken and not is_broken: changes.append({"type": "LINK RESTORED", "url": url})
    return 0, {"schema": "siteprobe.comparison/v1", "old_run": str(old), "new_run": str(new), "changes": changes}


def command_inspect(args: argparse.Namespace) -> int:
    url = normalize_url(args.url)
    if not url: print("invalid URL", file=sys.stderr); return 2
    print(json.dumps(inspect_page(url, 0, args.timeout, set()), indent=2, sort_keys=True)); return 0


def command_validate(args: argparse.Namespace) -> int:
    rc, errors = validate_run(Path(args.run).resolve())
    if errors:
        for error in errors: print(f"ERROR: {error}", file=sys.stderr)
    else: print(f"Valid SiteProbe run: {Path(args.run).resolve()}")
    return rc


def command_compare(args: argparse.Namespace) -> int:
    rc, result = compare_runs(Path(args.old).resolve(), Path(args.new).resolve())
    print(json.dumps(result, indent=2, sort_keys=True)); return rc


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="siteprobe", description="Deterministic website intelligence for Kujo WebOps")
    sub = root.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor"); sub.add_parser("version")
    crawl_p = sub.add_parser("crawl"); crawl_p.add_argument("url"); crawl_p.add_argument("--out"); crawl_p.add_argument("--max-pages", type=int, default=100); crawl_p.add_argument("--max-depth", type=int, default=4); crawl_p.add_argument("--concurrency", type=int, default=4); crawl_p.add_argument("--timeout", type=float, default=15); crawl_p.add_argument("--respect-robots", dest="respect_robots", action="store_true", default=True); crawl_p.add_argument("--ignore-robots", dest="respect_robots", action="store_false"); crawl_p.add_argument("--same-origin", action="store_true", default=True); crawl_p.add_argument("--json", action="store_true"); crawl_p.add_argument("--baseline")
    inspect_p = sub.add_parser("inspect"); inspect_p.add_argument("url"); inspect_p.add_argument("--timeout", type=float, default=15)
    validate_p = sub.add_parser("validate"); validate_p.add_argument("run")
    compare_p = sub.add_parser("compare"); compare_p.add_argument("old"); compare_p.add_argument("new")
    for name in ("report", "links", "sitemap"):
        p = sub.add_parser(name); p.add_argument("run")
    return root


def main() -> int:
    args = parser().parse_args()
    if args.command == "version": print(json.dumps({"name": "siteprobe", "version": VERSION, "contract": RUN_SCHEMA})); return 0
    if args.command == "doctor":
        writable = os.access(Path.cwd(), os.W_OK); print(json.dumps({"ok": writable, "python": sys.version.split()[0], "kujo_entrypoint": "siteprobe.kujo", "network_credentials_required": False, "same_origin_default": True, "respect_robots_default": True}, sort_keys=True)); return 0 if writable else 1
    if args.command == "crawl":
        if args.max_pages < 1 or args.max_pages > 10000 or args.max_depth < 0 or args.max_depth > 20 or args.concurrency < 1 or args.concurrency > 32 or args.timeout <= 0 or args.timeout > 120:
            print("SiteProbe: bounds exceeded", file=sys.stderr); return 2
        return crawl(args)
    if args.command == "inspect": return command_inspect(args)
    if args.command == "validate": return command_validate(args)
    if args.command == "compare": return command_compare(args)
    run = Path(args.run).resolve(); rc, errors = validate_run(run)
    if rc:
        for error in errors: print(f"ERROR: {error}", file=sys.stderr)
        return rc
    if args.command == "report": print((run / "report.md").read_text(encoding="utf-8"), end="")
    elif args.command == "links": print(json.dumps(load(run / "links.json"), indent=2, sort_keys=True))
    elif args.command == "sitemap": print(json.dumps(load(run / "sitemap.json"), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
