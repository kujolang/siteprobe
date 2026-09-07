#!/usr/bin/env python3
"""Legacy SiteProbe product implementation; native migration is tracked in the audit."""

from __future__ import annotations

import argparse
import concurrent.futures
import copy
import ctypes
import errno
import gzip
import hashlib
import heapq
import hmac
import http.client
import ipaddress
import json
import math
import os
import platform
import re
import socket
import stat
import ssl
import sys
import tempfile
import threading
import time
import urllib.parse
import urllib.robotparser
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict, deque
from contextlib import ExitStack
from dataclasses import dataclass, field
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[2]
VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
RUN_SCHEMA = "siteprobe.run/v1"
PAGE_SCHEMA = "siteprobe.page/v1"
UA = f"Kujo-SiteProbe/{VERSION} (+https://github.com/kujolang/siteprobe)"
MAX_BYTES = 5 * 1024 * 1024
MAX_SITEMAP_URLS = 100_000
MAX_REDIRECTS = 10
MAX_VALIDATION_FILE_BYTES = 256 * 1024 * 1024
DETERMINISTIC_TIME = "1970-01-01T00:00:00Z"
REQUIRED = [
    "run.json", "site.json", "pages.jsonl", "links.json", "redirects.json",
    "metadata.json", "structured-data.json", "sitemap.json", "robots.json",
    "findings.json", "report.md",
]
URL_QUERY_MODE = "preserve"
URL_DENY_PARAMS: set[str] = set()


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def slug_time() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def dump(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_signing_key(path_value: str | None) -> bytes | None:
    if not path_value:
        return None
    candidate = Path(path_value).expanduser()
    initial = candidate.lstat()
    if not stat.S_ISREG(initial.st_mode):
        raise ValueError("signing key must be a regular file")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    descriptor = os.open(candidate, flags)
    with os.fdopen(descriptor, "rb") as stream:
        opened = os.fstat(stream.fileno())
        if not stat.S_ISREG(opened.st_mode) or (opened.st_dev, opened.st_ino) != (initial.st_dev, initial.st_ino):
            raise ValueError("signing key changed during open")
        if opened.st_size < 32 or opened.st_size > 64 * 1024:
            raise ValueError("signing key must contain between 32 and 65536 bytes")
        key = stream.read(64 * 1024 + 1)
        if len(key) < 32 or len(key) > 64 * 1024:
            raise ValueError("signing key must contain between 32 and 65536 bytes")
        return key



def write_manifest(run: Path, signing_key: bytes | None) -> None:
    artifacts = {
        path.name: {"bytes": path.stat().st_size, "sha256": sha256_file(path)}
        for path in sorted(run.iterdir(), key=lambda value: value.name)
        if path.is_file() and path.name != "manifest.json"
    }
    payload = json.dumps(artifacts, separators=(",", ":"), sort_keys=True).encode()
    manifest = {
        "schema": "siteprobe.manifest/v1",
        "digest_algorithm": "sha256",
        "artifacts": artifacts,
        "signature": {
            "algorithm": "hmac-sha256" if signing_key else "none",
            "value": hmac.new(signing_key, payload, hashlib.sha256).hexdigest() if signing_key else "",
        },
    }
    dump(run / "manifest.json", manifest)


def verify_manifest(run: Path, signing_key: bytes | None = None) -> list[str]:
    path = run / "manifest.json"
    if not path.is_file() or path.is_symlink():
        return ["missing or unsafe manifest.json"]
    errors: list[str] = []
    try:
        if path.stat().st_size > MAX_VALIDATION_FILE_BYTES:
            return ["manifest exceeds validation limit"]
        manifest = load(path)
        if manifest.get("schema") != "siteprobe.manifest/v1":
            errors.append("unsupported manifest schema")
        if manifest.get("digest_algorithm") != "sha256":
            errors.append("unsupported manifest digest algorithm")
        artifacts = manifest.get("artifacts")
        if not isinstance(artifacts, dict):
            return errors + ["manifest artifacts must be an object"]
        missing = sorted(set(REQUIRED) - artifacts.keys())
        if missing:
            errors.append("manifest missing required artifacts: " + ", ".join(missing))
        for name, expected in artifacts.items():
            artifact = run / name
            if Path(name).name != name or artifact.is_symlink() or not artifact.is_file():
                errors.append(f"manifest artifact missing or unsafe: {name}")
                continue
            if artifact.stat().st_size > MAX_VALIDATION_FILE_BYTES:
                errors.append(f"manifest artifact exceeds validation limit: {name}")
                continue
            if artifact.stat().st_size != expected.get("bytes"):
                errors.append(f"manifest byte count mismatch: {name}")
            if not hmac.compare_digest(sha256_file(artifact), str(expected.get("sha256", ""))):
                errors.append(f"manifest digest mismatch: {name}")
        unlisted = sorted(
            item.name for item in run.iterdir()
            if item.is_file() and item.name != "manifest.json" and item.name not in artifacts
        )
        if unlisted:
            errors.append("manifest does not cover artifacts: " + ", ".join(unlisted))
        unsafe_entries = sorted(
            item.name for item in run.iterdir()
            if item.name != "manifest.json" and (item.is_symlink() or not item.is_file())
        )
        if unsafe_entries:
            errors.append("manifest run contains unsafe entries: " + ", ".join(unsafe_entries))
        signature = manifest.get("signature", {})
        algorithm = signature.get("algorithm")
        signature_value = str(signature.get("value", ""))
        if algorithm not in {"none", "hmac-sha256"}:
            errors.append("unsupported manifest signature algorithm")
        elif algorithm == "none" and signature_value:
            errors.append("unsigned manifest has a signature value")
        elif algorithm == "hmac-sha256" and not re.fullmatch(r"[a-f0-9]{64}", signature_value):
            errors.append("invalid manifest signature value")
        if signing_key:
            if algorithm != "hmac-sha256":
                errors.append("manifest is not signed with hmac-sha256")
            else:
                payload = json.dumps(artifacts, separators=(",", ":"), sort_keys=True).encode()
                expected_signature = hmac.new(signing_key, payload, hashlib.sha256).hexdigest()
                if not hmac.compare_digest(expected_signature, signature_value):
                    errors.append("manifest signature mismatch")
    except (AttributeError, OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        errors.append(f"invalid manifest: {exc}")
    return errors


def normalize_url(url: str, base: str | None = None) -> str:
    try:
        if any(ord(char) < 32 or ord(char) == 127 for char in url):
            return ""
        joined = urllib.parse.urljoin(base or "", url.strip())
        parsed = urllib.parse.urlsplit(joined)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
            return ""
        raw_host = parsed.hostname
        try:
            address = ipaddress.ip_address(raw_host)
            host = str(address)
            authority_host = f"[{host}]" if address.version == 6 else host
        except ValueError:
            host = raw_host.encode("idna").decode("ascii").lower()
            authority_host = host
        port = parsed.port
    except (TypeError, UnicodeError, ValueError):
        return ""
    netloc = authority_host
    if port and not ((parsed.scheme == "http" and port == 80) or (parsed.scheme == "https" and port == 443)):
        netloc = f"{authority_host}:{port}"
    path = re.sub(r"/{2,}", "/", parsed.path or "/")
    path = urllib.parse.quote(urllib.parse.unquote(path), safe="/%:@!$&'()*+,;=-._~")
    pairs = [pair for pair in urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
             if pair[0].lower() not in URL_DENY_PARAMS]
    if URL_QUERY_MODE == "drop":
        pairs = []
    elif URL_QUERY_MODE == "sort":
        pairs.sort(key=lambda pair: (pair[0], pair[1]))
    query = urllib.parse.urlencode(pairs, doseq=True)
    return urllib.parse.urlunsplit((parsed.scheme.lower(), netloc, path, query, ""))


def configure_url_policy(mode: str, denied_params: list[str]) -> None:
    global URL_QUERY_MODE, URL_DENY_PARAMS
    URL_QUERY_MODE = mode
    URL_DENY_PARAMS = {value.strip().lower() for value in denied_params if value.strip()}


def origin(url: str) -> str:
    p = urllib.parse.urlsplit(url)
    return f"{p.scheme}://{p.netloc}"


def same_origin(a: str, b: str) -> bool:
    return origin(a) == origin(b)


def resolve_addresses(hostname: str, port: int, allow_private_network: bool) -> tuple[list[str], str]:
    """Resolve once and return only addresses allowed for the imminent connection."""
    try:
        addresses = sorted({row[4][0] for row in socket.getaddrinfo(hostname, port, type=socket.SOCK_STREAM)})
    except socket.gaierror as exc:
        return [], f"DNS resolution failed: {exc}"
    if not addresses:
        return [], "DNS resolution returned no addresses"
    rejected: list[str] = []
    for raw in addresses:
        address = ipaddress.ip_address(raw)
        if not allow_private_network and not address.is_global:
            rejected.append(raw)
    if rejected:
        return [], "host resolves to non-public address " + ", ".join(rejected)
    return addresses, ""


def private_network_reason(url: str) -> str:
    parsed = urllib.parse.urlsplit(url)
    if not parsed.hostname:
        return "missing hostname"
    _, reason = resolve_addresses(parsed.hostname, parsed.port or (443 if parsed.scheme == "https" else 80), False)
    return reason if "non-public" in reason else ""


def text_fingerprint(text: str) -> str:
    normalized = re.sub(r"\s+", " ", text).strip().lower()
    return hashlib.sha256(normalized.encode()).hexdigest() if normalized else ""


class PinnedHTTPConnection(http.client.HTTPConnection):
    def __init__(self, hostname: str, port: int, address: str, timeout: float) -> None:
        super().__init__(hostname, port, timeout=timeout)
        self._pinned_address = address

    def connect(self) -> None:
        self.sock = socket.create_connection((self._pinned_address, self.port), self.timeout)


class PinnedHTTPSConnection(http.client.HTTPSConnection):
    def __init__(self, hostname: str, port: int, address: str, timeout: float) -> None:
        super().__init__(hostname, port, timeout=timeout, context=ssl.create_default_context())
        self._pinned_address = address

    def connect(self) -> None:
        raw = socket.create_connection((self._pinned_address, self.port), self.timeout)
        try:
            self.sock = self._context.wrap_socket(raw, server_hostname=self.host)
        except BaseException:
            raw.close()
            raise


class RequestPacer:
    def __init__(self, delay_seconds: float) -> None:
        self.delay_seconds = delay_seconds
        self._lock = threading.Lock()
        self._next_start = 0.0

    def wait(self) -> None:
        if self.delay_seconds <= 0:
            return
        with self._lock:
            now = time.monotonic()
            if now < self._next_start:
                time.sleep(self._next_start - now)
            self._next_start = time.monotonic() + self.delay_seconds


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
    hreflang: list[dict[str, str]] = field(default_factory=list)
    refresh: dict[str, Any] = field(default_factory=dict)
    robots: list[str] = field(default_factory=list)
    text_parts: list[str] = field(default_factory=list)


class PageParser(HTMLParser):
    def __init__(self, base: str, max_links: int) -> None:
        super().__init__(convert_charrefs=True)
        self.base = base
        self.max_links = max_links
        self.page = ParsedPage()
        self._skip = 0
        self._jsonld = False
        self._json_parts: list[str] = []
        self._link: dict[str, str] | None = None
        self._title_depth = 0
        self._heading_tag = ""
        self._heading_parts: list[str] = []
        self.links_truncated = False
        self.images_truncated = False

    def handle_starttag(self, tag: str, attrs_list: list[tuple[str, str | None]]) -> None:
        attrs = {k.lower(): (v or "") for k, v in attrs_list}
        tag = tag.lower()
        if tag in {"script", "style", "noscript", "template"}:
            self._skip += 1
        if tag == "title":
            self._title_depth += 1
        elif tag in {"h1", "h2", "h3", "h4", "h5", "h6"} and not self._heading_tag:
            self._heading_tag = tag
            self._heading_parts = []
        elif tag == "html":
            self.page.language = attrs.get("lang", "")
        elif tag == "meta":
            name = (attrs.get("name") or attrs.get("property") or attrs.get("http-equiv") or "").lower()
            value = attrs.get("content", "").strip()
            if name == "description": self.page.description = value
            if name in {"robots", "googlebot", "bingbot"}:
                self.page.robots.extend(x.strip().lower() for x in value.split(",") if x.strip())
            if name == "refresh" and value:
                match = re.match(r"\s*(\d+(?:\.\d+)?)\s*(?:;\s*url\s*=\s*(.+))?$", value, re.I)
                if match:
                    destination = normalize_url((match.group(2) or "").strip(" \"'"), self.base)
                    self.page.refresh = {"delay_seconds": float(match.group(1)), "url": destination}
            if name and value: self.page.metadata[name] = value
        elif tag == "link":
            rels = {x.lower() for x in attrs.get("rel", "").split()}
            href = normalize_url(attrs.get("href", ""), self.base)
            if "canonical" in rels: self.page.canonical = href
            if "next" in rels and href: self.page.pagination["next"] = href
            if "prev" in rels and href: self.page.pagination["prev"] = href
            if "alternate" in rels and attrs.get("hreflang") and href:
                self.page.hreflang.append({"language": attrs["hreflang"].lower(), "url": href})
        elif tag == "a":
            if len(self.page.links) >= self.max_links:
                self.links_truncated = True
            else:
                href = normalize_url(attrs.get("href", ""), self.base)
                if href: self._link = {"url": href, "text": "", "rel": attrs.get("rel", "")}
        elif tag == "img":
            if len(self.page.images) >= self.max_links:
                self.images_truncated = True
            else:
                src = normalize_url(attrs.get("src", ""), self.base)
                if src:
                    self.page.images.append({"url": src, "alt": attrs.get("alt", ""), "missing_alt": "alt" not in attrs})
        elif tag == "script" and attrs.get("type", "").lower() == "application/ld+json":
            self._jsonld = True

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "title" and self._title_depth:
            self._title_depth -= 1
        if tag == self._heading_tag:
            heading = re.sub(r"\s+", " ", " ".join(self._heading_parts)).strip()
            if heading:
                self.page.headings[self._heading_tag].append(heading)
            self._heading_tag = ""
            self._heading_parts = []
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

    def handle_data(self, data: str) -> None:
        if self._jsonld:
            self._json_parts.append(data)
            return
        clean = re.sub(r"\s+", " ", data).strip()
        if not clean or self._skip: return
        if self._title_depth:
            self.page.title += (" " if self.page.title else "") + clean
        if self._heading_tag:
            self._heading_parts.append(clean)
        if self._link is not None: self._link["text"] += " " + clean
        self.page.text_parts.append(clean)


def fetch(url: str, timeout: float, retries: int = 0, allow_private_network: bool = False,
          extra_headers: dict[str, str] | None = None, max_bytes: int = MAX_BYTES,
          pacer: RequestPacer | None = None,
          can_fetch: Callable[[str], bool] | None = None) -> tuple[int, str, dict[str, str], bytes, list[dict[str, Any]], str]:
    """GET a URL using DNS-pinned connections and same-origin redirect enforcement."""
    last_error = ""
    allowed_origin = origin(url)
    current = url
    redirects: list[dict[str, Any]] = []
    for attempt in range(retries + 1):
        retry_after = 0.0
        try:
            current = url
            redirects = []
            for _ in range(MAX_REDIRECTS + 1):
                if can_fetch is not None and not can_fetch(current):
                    return 0, current, {}, b"", redirects, "blocked by robots.txt"
                parsed = urllib.parse.urlsplit(current)
                hostname = parsed.hostname or ""
                port = parsed.port or (443 if parsed.scheme == "https" else 80)
                addresses, reason = resolve_addresses(hostname, port, allow_private_network)
                if reason:
                    raise OSError(reason)
                headers = {
                    "User-Agent": UA,
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.5",
                    "Host": parsed.netloc,
                    **(extra_headers or {}),
                }
                path = urllib.parse.urlunsplit(("", "", parsed.path or "/", parsed.query, ""))
                response = None
                connection = None
                connection_error = ""
                for address in addresses:
                    try:
                        if pacer:
                            pacer.wait()
                        factory = PinnedHTTPSConnection if parsed.scheme == "https" else PinnedHTTPConnection
                        connection = factory(hostname, port, address, timeout)
                        connection.request("GET", path, headers=headers)
                        response = connection.getresponse()
                        break
                    except (OSError, ssl.SSLError, http.client.HTTPException) as exc:
                        connection_error = str(exc)
                        if connection:
                            connection.close()
                if response is None or connection is None:
                    raise OSError(connection_error or "connection failed")
                response_headers: dict[str, str] = {}
                for key, value in response.getheaders():
                    normalized_key = key.lower()
                    if normalized_key == "link" and normalized_key in response_headers:
                        response_headers[normalized_key] += ", " + value
                    else:
                        response_headers[normalized_key] = value
                try:
                    body = response.read(max_bytes + 1)
                    status = response.status
                finally:
                    connection.close()
                if len(body) > max_bytes:
                    raise ValueError(f"response exceeded {max_bytes} byte limit")
                if status in {301, 302, 303, 307, 308} and response_headers.get("location"):
                    destination = normalize_url(response_headers["location"], current)
                    redirects.append({"from": current, "status": status, "to": destination or response_headers["location"]})
                    if not destination or origin(destination) != allowed_origin:
                        return 0, current, response_headers, b"", redirects, "cross-origin redirect blocked"
                    current = destination
                    continue
                if len(redirects) > MAX_REDIRECTS:
                    return 0, current, response_headers, b"", redirects, "redirect limit exceeded"
                if status not in {429, 500, 502, 503, 504} or attempt >= retries:
                    error = f"HTTP {status}" if status >= 400 else ""
                    return status, current, response_headers, body, redirects, error
                last_error = f"HTTP {status}"
                try: retry_after = float(response_headers.get("retry-after", "0"))
                except ValueError: retry_after = 0.0
                break
            else:
                return 0, current, {}, b"", redirects, "redirect limit exceeded"
        except (TimeoutError, ValueError, OSError, ssl.SSLError, http.client.HTTPException) as exc:
            last_error = str(exc)
            if attempt >= retries: return 0, current, {}, b"", redirects, last_error
        time.sleep(min(max(0.25 * (2 ** attempt), retry_after), 2.0))
    return 0, current, {}, b"", redirects, last_error


def decode_body(body: bytes, content_type: str) -> str:
    match = re.search(r"charset=([^;\s]+)", content_type, re.I)
    charset = match.group(1).strip('"\'') if match else "utf-8"
    try: return body.decode(charset, errors="replace")
    except LookupError: return body.decode("utf-8", errors="replace")


def parse_http_link_headers(value: str, base: str) -> list[dict[str, Any]]:
    links: list[dict[str, Any]] = []
    for part in re.split(r",\s*(?=<)", value):
        match = re.match(r"\s*<([^>]+)>(.*)$", part)
        if not match:
            continue
        target = normalize_url(match.group(1), base)
        if not target:
            continue
        params: dict[str, str] = {}
        for key, quoted, bare in re.findall(r";\s*([\w-]+)\s*=\s*(?:\"([^\"]*)\"|([^;\s]+))", match.group(2)):
            params[key.lower()] = quoted or bare
        links.append({"url": target, "rel": params.pop("rel", ""), "params": params})
    return links


def decode_gzip_bounded(body: bytes, max_expanded_bytes: int) -> bytes:
    with gzip.GzipFile(fileobj=__import__("io").BytesIO(body)) as stream:
        expanded = stream.read(max_expanded_bytes + 1)
    if len(expanded) > max_expanded_bytes:
        raise ValueError(f"expanded sitemap exceeded {max_expanded_bytes} byte limit")
    return expanded


def discover_sitemaps(base_url: str, robots_text: str, timeout: float, retries: int = 0,
                      allow_private_network: bool = False, pacer: RequestPacer | None = None,
                      max_compressed_bytes: int = MAX_BYTES,
                      max_expanded_bytes: int = 20 * 1024 * 1024) -> dict[str, Any]:
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
        status, _, headers, body, _, error = fetch(
            sitemap_url, timeout, retries, allow_private_network,
            extra_headers={"Accept-Encoding": "gzip"}, max_bytes=max_compressed_bytes, pacer=pacer,
        )
        if status != 200:
            errors.append({"url": sitemap_url, "error": error or f"HTTP {status}"})
            continue
        try:
            if headers.get("content-encoding", "").lower() == "gzip" or sitemap_url.lower().endswith(".gz"):
                body = decode_gzip_bounded(body, max_expanded_bytes)
            elif len(body) > max_expanded_bytes:
                raise ValueError(f"sitemap exceeded {max_expanded_bytes} byte expanded limit")
            root = ET.fromstring(decode_body(body, headers.get("content-type", "")))
            locs = [normalize_url((node.text or "").strip()) for node in root.iter() if node.tag.rsplit("}", 1)[-1] == "loc"]
            if root.tag.rsplit("}", 1)[-1] == "sitemapindex": queue.extend([x for x in locs if x])
            else:
                for value in locs:
                    if value and same_origin(value, base_url) and len(urls) < MAX_SITEMAP_URLS:
                        urls.add(value)
        except (ET.ParseError, OSError, ValueError) as exc:
            errors.append({"url": sitemap_url, "error": f"invalid sitemap: {exc}"})
    return {"schema": "siteprobe.sitemap/v1", "sitemaps": sorted(seen), "urls": sorted(urls), "errors": errors}


def inspect_page(url: str, depth: int, timeout: float, sitemap_urls: set[str], retries: int = 0,
                 allow_private_network: bool = False, max_links_per_page: int = 10_000,
                 pacer: RequestPacer | None = None, baseline_page: dict[str, Any] | None = None,
                 can_fetch: Callable[[str], bool] | None = None) -> dict[str, Any]:
    started = time.monotonic()
    conditional_headers: dict[str, str] = {}
    if baseline_page:
        if baseline_page.get("etag"):
            conditional_headers["If-None-Match"] = baseline_page["etag"]
        if baseline_page.get("last_modified"):
            conditional_headers["If-Modified-Since"] = baseline_page["last_modified"]
    status, final_url, headers, body, redirects, error = fetch(
        url, timeout, retries, allow_private_network,
        extra_headers=conditional_headers, pacer=pacer, can_fetch=can_fetch,
    )
    if status == 304 and baseline_page:
        reused = copy.deepcopy(baseline_page)
        reused.update({
            "url": url, "normalized_url": normalize_url(url), "final_url": normalize_url(final_url),
            "redirect_chain": redirects, "depth": depth, "not_modified": True,
            "response_status": 304, "etag": headers.get("etag", baseline_page.get("etag", "")),
            "last_modified": headers.get("last-modified", baseline_page.get("last_modified", "")),
            "error": "", "elapsed_ms": round((time.monotonic() - started) * 1000),
        })
        return reused
    content_type = headers.get("content-type", "").split(";", 1)[0].lower()
    parser = PageParser(final_url, max_links_per_page)
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
    http_links = parse_http_link_headers(headers.get("link", ""), final_url)
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
        "structured_data": page.structured_data, "pagination": page.pagination,
        "hreflang": page.hreflang, "refresh": page.refresh, "http_links": http_links, "depth": depth,
        "etag": headers.get("etag", ""), "last_modified": headers.get("last-modified", ""),
        "not_modified": False, "response_status": status,
        "truncated": {"links": parser.links_truncated, "images": parser.images_truncated},
        "incoming_link_count": 0, "outgoing_link_count": len(page.links), "error": error,
        "elapsed_ms": round((time.monotonic() - started) * 1000),
    }


def finding_id(check: str, target: str) -> str:
    return "SP-" + hashlib.sha256(f"{check}\0{target}".encode()).hexdigest()[:16].upper()


def analyze_stream(pages_path: Path, updated_pages_path: Path, sitemap: dict[str, Any],
                   start_url: str, link_spool: Path) -> dict[str, Any]:
    """Analyze sorted pages in two passes without retaining complete page/link arrays."""
    incoming: Counter[str] = Counter()
    crawled: set[str] = set()
    titles: defaultdict[str, list[str]] = defaultdict(list)
    descriptions: defaultdict[str, list[str]] = defaultdict(list)
    fingerprints: defaultdict[str, list[str]] = defaultdict(list)
    display_titles: defaultdict[str, list[str]] = defaultdict(list)
    display_descriptions: defaultdict[str, list[str]] = defaultdict(list)
    structured_pages: list[dict[str, Any]] = []
    link_count = 0
    page_count = 0
    crawlable_pages = 0
    indexable_pages = 0
    with link_spool.open("w", encoding="utf-8") as stream, pages_path.open(encoding="utf-8") as page_stream:
        for line in page_stream:
            page = json.loads(line)
            page_count += 1
            url = page["normalized_url"]
            crawled.add(url)
            crawlable_pages += int(page["status"] == 200)
            indexable_pages += int(page["indexable"])
            if page["title"]:
                titles[page["title"].strip().lower()].append(url)
                display_titles[page["title"]].append(url)
            if page["meta_description"]:
                descriptions[page["meta_description"].strip().lower()].append(url)
                display_descriptions[page["meta_description"]].append(url)
            if page["content_fingerprint"]:
                fingerprints[page["content_fingerprint"]].append(url)
            if page["structured_data"]:
                structured_pages.append({"url": url, "items": page["structured_data"]})
            for link in page["links"]:
                row = {"source": page["normalized_url"], "target": link["url"], "text": link["text"], "rel": link["rel"], "internal": same_origin(link["url"], start_url)}
                stream.write(json.dumps(row, sort_keys=True) + "\n")
                link_count += 1
                if row["internal"]: incoming[link["url"]] += 1
    findings: list[dict[str, Any]] = []

    def add(check: str, target: str, severity: str, evidence: Any) -> None:
        findings.append({"id": finding_id(check, target), "check": check, "target": target, "severity": severity, "evidence": evidence})

    with pages_path.open(encoding="utf-8") as source, updated_pages_path.open("w", encoding="utf-8") as destination:
        for line in source:
            page = json.loads(line)
            url = page["normalized_url"]
            page["incoming_link_count"] = incoming[url]
            destination.write(json.dumps(page, sort_keys=True) + "\n")
            if not page["title"] and page["status"] == 200 and "html" in page["content_type"]: add("missing-title", url, "warning", {})
            if not page["meta_description"] and page["status"] == 200 and "html" in page["content_type"]: add("missing-description", url, "warning", {})
            if page["status"] == 0 or page["status"] >= 400: add("broken-url", url, "error", {"status": page["status"], "error": page["error"]})
            if page["canonical"] and normalize_url(page["canonical"]) != normalize_url(page["final_url"]): add("canonical-conflict", url, "warning", {"canonical": page["canonical"], "final_url": page["final_url"]})
            if page["missing_alt_count"]: add("missing-image-alt", url, "warning", {"count": page["missing_alt_count"]})
            if not page["indexable"] and page["status"] == 200: add("not-indexable", url, "info", {"directives": page["robots_directives"]})
            if any(isinstance(x, dict) and x.get("invalid") for x in page["structured_data"]): add("invalid-structured-data", url, "warning", {})
            if any(page.get("truncated", {}).values()): add("page-structure-truncated", url, "info", page["truncated"])
    for check, groups in (("duplicate-title", titles), ("duplicate-description", descriptions), ("duplicate-content", fingerprints)):
        for value, urls in groups.items():
            if len(urls) > 1: add(check, urls[0], "warning", {"urls": sorted(urls), "value_fingerprint": text_fingerprint(value)})
    for url in sitemap["urls"]:
        if url not in crawled or (url != normalize_url(start_url) and incoming[url] == 0): add("orphan-candidate", url, "warning", {"sitemap_member": True, "incoming_links": incoming[url], "crawled": url in crawled})
    return {
        "page_count": page_count, "link_count": link_count,
        "crawlable_pages": crawlable_pages, "indexable_pages": indexable_pages,
        "titles": display_titles, "descriptions": display_descriptions,
        "structured_pages": structured_pages,
        "findings": sorted(findings, key=lambda x: (x["severity"], x["check"], x["target"])),
    }


def external_sort_jsonl(source: Path, destination: Path, key_fields: tuple[str, ...],
                        max_buffer_bytes: int) -> None:
    """Sort JSONL with bounded in-memory chunks and a deterministic k-way merge."""
    # Limit merge fan-in independently of crawl size and sort-buffer size.
    # Opening one descriptor per chunk exhausted the process limit on big runs.
    with tempfile.TemporaryDirectory(prefix="siteprobe-sort-", dir=source.parent) as temporary:
        chunk_dir = Path(temporary)
        chunk_paths: list[Path] = []
        rows: list[tuple[tuple[str, ...], str]] = []
        buffered = 0

        def keyed(line: str) -> tuple[tuple[str, ...], str]:
            value = json.loads(line)
            return tuple(str(value.get(field, "")) for field in key_fields), line

        def flush() -> None:
            nonlocal rows, buffered
            if not rows:
                return
            rows.sort(key=lambda item: item[0])
            path = chunk_dir / f"chunk-{len(chunk_paths):06d}.jsonl"
            with path.open("w", encoding="utf-8") as output:
                output.writelines(item[1] for item in rows)
            chunk_paths.append(path)
            rows = []
            buffered = 0

        with source.open(encoding="utf-8") as stream:
            for line in stream:
                rows.append(keyed(line))
                buffered += len(line.encode())
                if buffered >= max_buffer_bytes:
                    flush()
        flush()

        def merge(paths: list[Path], target: Path) -> None:
            with ExitStack() as stack:
                inputs = [stack.enter_context(path.open(encoding="utf-8")) for path in paths]
                output = stack.enter_context(target.open("w", encoding="utf-8"))
                for _, line in heapq.merge(*(map(keyed, stream) for stream in inputs)):
                    output.write(line)

        generation = 0
        while len(chunk_paths) > 32:
            next_paths: list[Path] = []
            for offset in range(0, len(chunk_paths), 32):
                group = chunk_paths[offset:offset + 32]
                target = chunk_dir / f"merge-{generation}-{offset}.jsonl"
                merge(group, target)
                next_paths.append(target)
                for path in group:
                    path.unlink()
            chunk_paths = next_paths
            generation += 1
        merge(chunk_paths, destination)



def write_json_array_from_jsonl(path: Path, schema: str, array_name: str, destination: Path) -> None:
    with destination.open("w", encoding="utf-8") as output, path.open(encoding="utf-8") as source:
        output.write('{\n  "schema": ' + json.dumps(schema) + ',\n  ' + json.dumps(array_name) + ': [')
        first = True
        for line in source:
            if not line.strip():
                continue
            output.write(("\n    " if first else ",\n    ") + line.strip())
            first = False
        output.write("\n  ]\n}\n" if not first else "]\n}\n")


def publish_directory(source: Path, destination: Path) -> None:
    """Atomically publish without replacing any existing destination entry.

    Ordinary os.replace can overwrite an empty directory created after preflight.
    Use the OS no-replace operation; never fall back to a check-then-rename race.
    """
    if os.name == "nt":
        os.rename(source, destination)  # Windows rename fails when target exists.
        return
    libc = ctypes.CDLL(None, use_errno=True)
    if sys.platform == "darwin" and hasattr(libc, "renamex_np"):
        rename = libc.renamex_np
        rename.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint]
        rename.restype = ctypes.c_int
        rc = rename(os.fsencode(source), os.fsencode(destination), 4)  # RENAME_EXCL
    elif sys.platform.startswith("linux") and hasattr(libc, "renameat2"):
        rename = libc.renameat2
        rename.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
        rename.restype = ctypes.c_int
        rc = rename(-100, os.fsencode(source), -100, os.fsencode(destination), 1)  # AT_FDCWD, RENAME_NOREPLACE
    else:
        raise OSError(errno.ENOTSUP, "atomic no-replace directory publication is unavailable")
    if rc != 0:
        code = ctypes.get_errno()
        raise OSError(code, os.strerror(code), str(destination))


def crawl(args: argparse.Namespace) -> int:
    configure_url_policy(args.query_policy, args.query_deny_param)
    target = normalize_url(args.url)
    if not target:
        print("SiteProbe: target must be an http(s) URL without credentials", file=sys.stderr); return 2
    if not args.allow_private_network:
        reason = private_network_reason(target)
        if reason:
            print(f"SiteProbe: private network target blocked: {reason}; use --allow-private-network for an authorized target", file=sys.stderr); return 2
    candidate_out = Path(args.out or f".siteprobe/{slug_time()}").expanduser()
    final_out = candidate_out.parent.resolve() / candidate_out.name
    if final_out.exists() or final_out.is_symlink():
        print(f"SiteProbe: output path already exists: {final_out}", file=sys.stderr); return 2
    final_out.parent.mkdir(parents=True, exist_ok=True)
    staging = tempfile.TemporaryDirectory(prefix=f".{final_out.name}.tmp-", dir=final_out.parent)
    out = Path(staging.name)
    baseline_pages: dict[str, dict[str, Any]] = {}
    if args.baseline:
        baseline_path = Path(args.baseline).expanduser().resolve()
        baseline_rc, baseline_errors = validate_run(baseline_path)
        if baseline_rc:
            staging.cleanup()
            for baseline_error in baseline_errors:
                print(f"SiteProbe: invalid baseline: {baseline_error}", file=sys.stderr)
            return 2
        baseline_pages = {page["normalized_url"]: page for page in read_pages(baseline_path)}
    robots_url = urllib.parse.urljoin(origin(target), "/robots.txt")
    robots_status, _, robots_headers, robots_body, _, robots_error = fetch(robots_url, args.timeout, args.retries, args.allow_private_network)
    if args.respect_robots and robots_status not in {200, 404, 410}:
        staging.cleanup()
        print(f"SiteProbe: robots policy unavailable or denied (HTTP {robots_status}): {robots_error}; no run was published", file=sys.stderr)
        return 1
    robots_text = decode_body(robots_body, robots_headers.get("content-type", "")) if robots_status == 200 and robots_body else ""
    robot = urllib.robotparser.RobotFileParser(); robot.set_url(robots_url); robot.parse(robots_text.splitlines())
    robots_delay = robot.crawl_delay(UA)
    if robots_delay is None:
        robots_delay = robot.crawl_delay("*")
    bounded_robots_delay = min(float(robots_delay or 0), args.max_crawl_delay)
    effective_delay = max(args.request_delay, bounded_robots_delay)
    pacer = RequestPacer(effective_delay)
    sitemap = discover_sitemaps(
        target, robots_text, args.timeout, args.retries, args.allow_private_network, pacer,
        args.max_sitemap_compressed_bytes, args.max_sitemap_expanded_bytes,
    )
    sitemap_urls = set(sitemap["urls"])
    queue = deque([(target, 0)])
    queued = {target}
    page_spool = out / "_pages.unsorted.jsonl"
    page_count = 0
    redirects: list[dict[str, Any]] = []
    started = utc_now()
    with page_spool.open("w", encoding="utf-8") as page_stream, concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        while queue and page_count < args.max_pages:
            batch: list[tuple[str, int]] = []
            while queue and len(batch) < args.concurrency and page_count + len(batch) < args.max_pages:
                url, depth = queue.popleft()
                if depth > args.max_depth: continue
                if args.respect_robots and not robot.can_fetch(UA, url):
                    blocked_page = {"schema": PAGE_SCHEMA, "url": url, "normalized_url": url, "status": 0, "response_status": 0, "redirect_chain": [], "final_url": url, "canonical": "", "indexable": False, "robots_directives": ["blocked-by-robots"], "sitemap_member": url in sitemap_urls, "title": "", "meta_description": "", "headings": {}, "language": "", "content_type": "", "content_fingerprint": "", "word_count": 0, "internal_links": [], "external_links": [], "links": [], "images": [], "missing_alt_count": 0, "open_graph": {}, "social_metadata": {}, "structured_data": [], "pagination": {}, "hreflang": [], "refresh": {}, "http_links": [], "etag": "", "last_modified": "", "not_modified": False, "truncated": {"links": False, "images": False}, "depth": depth, "incoming_link_count": 0, "outgoing_link_count": 0, "error": "blocked by robots.txt", "elapsed_ms": 0}
                    page_stream.write(json.dumps(blocked_page, sort_keys=True) + "\n")
                    page_count += 1
                    continue
                batch.append((url, depth))
            futures = [pool.submit(
                inspect_page, url, depth, args.timeout, sitemap_urls, args.retries,
                args.allow_private_network, args.max_links_per_page, pacer, baseline_pages.get(url),
                (lambda candidate: robot.can_fetch(UA, candidate)) if args.respect_robots else None,
            ) for url, depth in batch]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
            for page in sorted(results, key=lambda p: p["normalized_url"]):
                if args.deterministic:
                    page["elapsed_ms"] = 0
                page_stream.write(json.dumps(page, sort_keys=True) + "\n")
                page_count += 1
                redirects.extend(page["redirect_chain"])
                if page["depth"] >= args.max_depth: continue
                for link in page["internal_links"]:
                    url = link["url"]
                    if same_origin(url, target) and url not in queued and len(queued) < args.max_pages * 10:
                        queued.add(url); queue.append((url, page["depth"] + 1))
    external_sort_jsonl(page_spool, out / "pages.jsonl", ("normalized_url",), args.sort_buffer_bytes)
    page_spool.unlink()
    updated_pages = out / "_pages.updated.jsonl"
    link_spool = out / "_links.unsorted.jsonl"
    sorted_link_spool = out / "_links.sorted.jsonl"
    analysis = analyze_stream(out / "pages.jsonl", updated_pages, sitemap, target, link_spool)
    os.replace(updated_pages, out / "pages.jsonl")
    findings = analysis["findings"]
    external_sort_jsonl(link_spool, sorted_link_spool, ("source", "target", "text", "rel"), args.sort_buffer_bytes)
    write_json_array_from_jsonl(sorted_link_spool, "siteprobe.links/v1", "links", out / "links.json")
    link_spool.unlink(); sorted_link_spool.unlink()
    completed = DETERMINISTIC_TIME if args.deterministic else utc_now()
    if args.deterministic: started = DETERMINISTIC_TIME
    severity_counts = dict(sorted(Counter(f["severity"] for f in findings).items()))
    run = {"schema": RUN_SCHEMA, "run_id": final_out.name, "started_at": started, "completed_at": completed, "target": target,
           "configuration": {"max_pages": args.max_pages, "max_depth": args.max_depth, "concurrency": args.concurrency, "timeout": args.timeout, "retries": args.retries, "respect_robots": args.respect_robots, "same_origin": True, "allow_private_network": args.allow_private_network, "max_links_per_page": args.max_links_per_page, "max_sitemap_compressed_bytes": args.max_sitemap_compressed_bytes, "max_sitemap_expanded_bytes": args.max_sitemap_expanded_bytes, "sort_buffer_bytes": args.sort_buffer_bytes, "query_policy": args.query_policy, "query_deny_params": sorted(URL_DENY_PARAMS), "request_pacing": {"operator_delay_seconds": args.request_delay, "robots_crawl_delay_seconds": float(robots_delay or 0), "max_crawl_delay_seconds": args.max_crawl_delay, "effective_delay_seconds": effective_delay}, "baseline": args.baseline, "conditional_fetch": bool(args.baseline), "offline": False, "max_output_bytes": args.max_output_bytes, "max_report_tokens": args.max_report_tokens, "deterministic": args.deterministic, "fail_on": args.fail_on},
           "counts": {"pages": analysis["page_count"], "links": analysis["link_count"], "redirects": len(redirects), "findings": len(findings), "findings_by_severity": severity_counts}}
    site = {"schema": "siteprobe.site/v1", "target": target, "origin": origin(target), "robots_url": robots_url, "sitemaps": sitemap["sitemaps"], "crawlable_pages": analysis["crawlable_pages"], "indexable_pages": analysis["indexable_pages"]}
    metadata = {"schema": "siteprobe.metadata/v1", "titles": analysis["titles"], "descriptions": analysis["descriptions"]}
    structured = {"schema": "siteprobe.structured-data/v1", "pages": analysis["structured_pages"]}
    robots = {"schema": "siteprobe.robots/v1", "url": robots_url, "status": robots_status, "text_fingerprint": text_fingerprint(robots_text), "error": robots_error, "sitemaps": sitemap["sitemaps"]}
    dump(out / "run.json", run); dump(out / "site.json", site); dump(out / "redirects.json", {"schema": "siteprobe.redirects/v1", "redirects": redirects}); dump(out / "metadata.json", metadata); dump(out / "structured-data.json", structured); dump(out / "sitemap.json", sitemap); dump(out / "robots.json", robots); dump(out / "findings.json", {"schema": "siteprobe.findings/v1", "findings": findings})
    report_text = render_report(run, findings, args.max_report_tokens)
    (out / "report.md").write_text(report_text, encoding="utf-8")
    if args.baseline:
        rc, comparison = compare_runs(Path(args.baseline), out)
        comparison["new_run"] = str(final_out)
        dump(out / "comparison.json", comparison)
        if rc:
            staging.cleanup()
            return rc
    try:
        signing_key = read_signing_key(args.signing_key_file)
    except ValueError as exc:
        staging.cleanup()
        print(f"SiteProbe: {exc}", file=sys.stderr)
        return 2
    write_manifest(out, signing_key)
    output_bytes = sum(path.stat().st_size for path in out.iterdir() if path.is_file())
    if output_bytes > args.max_output_bytes:
        staging.cleanup()
        print(f"SiteProbe: output budget exceeded ({output_bytes} > {args.max_output_bytes} bytes); no run was published", file=sys.stderr); return 1
    try:
        publish_directory(out, final_out)
    except FileExistsError:
        print(f"SiteProbe: output path already exists: {final_out}", file=sys.stderr)
        return 2
    finally:
        staging.cleanup()
    if args.json: print(json.dumps({"run": str(final_out), "counts": run["counts"]}, sort_keys=True))
    else: print(f"SiteProbe crawl complete: {final_out}\nPages: {analysis['page_count']}  Findings: {len(findings)}")
    fail_rank = {"none": 99, "error": 2, "warning": 1, "info": 0}[args.fail_on]
    severity_rank = {"error": 2, "warning": 1, "info": 0}
    return 1 if any(severity_rank.get(f["severity"], -1) >= fail_rank for f in findings) else 0


def read_pages(run: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in (run / "pages.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]


def render_report(run: dict[str, Any], findings: list[dict[str, Any]], max_tokens: int = 2000) -> str:
    # A byte budget is deterministic and conservative for the documented
    # four-bytes-per-token approximation. Full evidence stays in JSON artifacts.
    budget = max_tokens * 4
    def safe(value: Any) -> str:
        return "".join(char if ord(char) >= 32 and ord(char) != 127 else " " for char in str(value))

    lines = ["# SiteProbe Report", "", "## Coverage", "",
             f"- Pages inspected: {run['counts']['pages']}",
             f"- Links recorded: {run['counts']['links']}",
             f"- Findings retained: {run['counts']['findings']}", "",
             "Full machine evidence remains in the run directory.", ""]
    result = "\n".join(lines)
    for line in [f"Target: {safe(run['target'])}", f"Run: {safe(run['run_id'])}", "", "## Attention", ""]:
        if len((result + line + "\n").encode()) <= budget:
            result += line + "\n"
    important = [f for f in findings if f["severity"] in {"error", "warning"}]
    omitted = "Additional findings omitted by report token budget; see findings.json.\n"
    if not important:
        line = "- No error or warning findings.\n"
        if len((result + line).encode()) <= budget:
            result += line
    for finding in important:
        line = f"- [{safe(finding['severity'])}] {safe(finding['check'])}: {safe(finding['target'])}\n"
        if len((result + line + omitted).encode()) > budget:
            if len((result + omitted).encode()) <= budget:
                result += omitted
            break
        result += line
    return result



def validate_run(run: Path) -> tuple[int, list[str]]:
    errors: list[str] = []
    if not run.is_dir(): return 1, [f"run directory not found: {run}"]
    for name in REQUIRED:
        artifact = run / name
        if artifact.is_symlink(): errors.append(f"symbolic-link artifact rejected: {name}")
        elif not artifact.is_file(): errors.append(f"missing {name}")
    if errors: return 1, errors
    try:
        for name in REQUIRED:
            if (run / name).stat().st_size > MAX_VALIDATION_FILE_BYTES:
                errors.append(f"artifact exceeds validation limit: {name}")
        if errors: return 1, errors
        data = load(run / "run.json")
        if data.get("schema") != RUN_SCHEMA: errors.append("unsupported run schema")
        pages = read_pages(run)
        if len(pages) != data.get("counts", {}).get("pages"): errors.append("page count mismatch")
        if any(page.get("schema") != PAGE_SCHEMA for page in pages): errors.append("unsupported page schema")
        links = load(run / "links.json").get("links", [])
        redirects = load(run / "redirects.json").get("redirects", [])
        findings = load(run / "findings.json").get("findings", [])
        counts = data.get("counts", {})
        if len(links) != counts.get("links"): errors.append("link count mismatch")
        if len(redirects) != counts.get("redirects"): errors.append("redirect count mismatch")
        if len(findings) != counts.get("findings"): errors.append("finding count mismatch")
        finding_ids = [x["id"] for x in findings]
        if len(finding_ids) != len(set(finding_ids)): errors.append("duplicate finding IDs")
        configured_budget = data.get("configuration", {}).get("max_output_bytes")
        output_bytes = sum(path.stat().st_size for path in run.iterdir() if path.is_file())
        if isinstance(configured_budget, int) and output_bytes > configured_budget:
            errors.append("run exceeds declared output budget")
        if (run / "manifest.json").exists():
            errors.extend(verify_manifest(run))
    except (AttributeError, OSError, TypeError, ValueError, KeyError, json.JSONDecodeError) as exc: errors.append(str(exc))
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
    configure_url_policy(args.query_policy, args.query_deny_param)
    url = normalize_url(args.url)
    if not url: print("invalid URL", file=sys.stderr); return 2
    if not args.allow_private_network:
        reason = private_network_reason(url)
        if reason:
            print(f"SiteProbe: private network target blocked: {reason}; use --allow-private-network for an authorized target", file=sys.stderr); return 2
    print(json.dumps(inspect_page(url, 0, args.timeout, set(), args.retries, args.allow_private_network, args.max_links_per_page), indent=2, sort_keys=True)); return 0


def command_validate(args: argparse.Namespace) -> int:
    rc, errors = validate_run(Path(args.run).resolve())
    if errors:
        for error in errors: print(f"ERROR: {error}", file=sys.stderr)
    else: print(f"Valid SiteProbe run: {Path(args.run).resolve()}")
    return rc


def command_compare(args: argparse.Namespace) -> int:
    rc, result = compare_runs(Path(args.old).resolve(), Path(args.new).resolve())
    print(json.dumps(result, indent=2, sort_keys=True)); return rc


def command_verify(args: argparse.Namespace) -> int:
    run = Path(args.run).resolve()
    try:
        key = read_signing_key(args.signing_key_file)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    errors = verify_manifest(run, key)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"Verified SiteProbe manifest: {run / 'manifest.json'}")
    return 0


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="siteprobe", description="Deterministic, bounded website intelligence with Kujo validation")
    sub = root.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor", help="check local runtime prerequisites"); sub.add_parser("version", help="print versioned contract metadata")
    crawl_p = sub.add_parser("crawl", help="crawl a bounded same-origin surface"); crawl_p.add_argument("url"); crawl_p.add_argument("--out"); crawl_p.add_argument("--max-pages", type=int, default=100); crawl_p.add_argument("--max-depth", type=int, default=4); crawl_p.add_argument("--concurrency", type=int, default=4); crawl_p.add_argument("--timeout", type=float, default=15); crawl_p.add_argument("--retries", type=int, default=2); crawl_p.add_argument("--request-delay", type=float, default=0); crawl_p.add_argument("--max-crawl-delay", type=float, default=10); crawl_p.add_argument("--max-links-per-page", type=int, default=10_000); crawl_p.add_argument("--max-sitemap-compressed-bytes", type=int, default=5 * 1024 * 1024); crawl_p.add_argument("--max-sitemap-expanded-bytes", type=int, default=20 * 1024 * 1024); crawl_p.add_argument("--sort-buffer-bytes", type=int, default=8 * 1024 * 1024); crawl_p.add_argument("--max-output-bytes", type=int, default=100 * 1024 * 1024); crawl_p.add_argument("--max-report-tokens", type=int, default=2000); crawl_p.add_argument("--query-policy", choices=("preserve", "sort", "drop"), default="preserve"); crawl_p.add_argument("--query-deny-param", action="append", default=[]); crawl_p.add_argument("--offline", action="store_true"); crawl_p.add_argument("--deterministic", action="store_true"); crawl_p.add_argument("--respect-robots", dest="respect_robots", action="store_true", default=True); crawl_p.add_argument("--ignore-robots", dest="respect_robots", action="store_false"); crawl_p.add_argument("--same-origin", action="store_true", default=True, help=argparse.SUPPRESS); crawl_p.add_argument("--allow-private-network", action="store_true"); crawl_p.add_argument("--json", action="store_true"); crawl_p.add_argument("--baseline"); crawl_p.add_argument("--signing-key-file"); crawl_p.add_argument("--metrics-file", help=argparse.SUPPRESS); crawl_p.add_argument("--fail-on", choices=("none", "info", "warning", "error"), default="none")
    inspect_p = sub.add_parser("inspect", help="inspect one URL without writing a run"); inspect_p.add_argument("url"); inspect_p.add_argument("--timeout", type=float, default=15); inspect_p.add_argument("--retries", type=int, default=0); inspect_p.add_argument("--max-links-per-page", type=int, default=10_000); inspect_p.add_argument("--query-policy", choices=("preserve", "sort", "drop"), default="preserve"); inspect_p.add_argument("--query-deny-param", action="append", default=[]); inspect_p.add_argument("--allow-private-network", action="store_true")
    validate_p = sub.add_parser("validate", help="validate a run's artifact integrity"); validate_p.add_argument("run")
    verify_p = sub.add_parser("verify", help="verify run digests and an optional HMAC signature"); verify_p.add_argument("run"); verify_p.add_argument("--signing-key-file")
    compare_p = sub.add_parser("compare", help="compare two valid runs"); compare_p.add_argument("old"); compare_p.add_argument("new")
    for name in ("report", "links", "sitemap"):
        p = sub.add_parser(name, help=f"print a run's {name} artifact"); p.add_argument("run")
    return root


def dispatch() -> int:
    wall_started = time.monotonic()
    cpu_started = time.process_time()
    args = parser().parse_args()
    if args.command == "version": print(json.dumps({"name": "siteprobe", "version": VERSION, "contract": RUN_SCHEMA})); return 0
    if args.command == "doctor":
        writable = os.access(Path.cwd(), os.W_OK); print(json.dumps({"ok": writable, "python": sys.version.split()[0], "kujo_entrypoint": "src/main.kujo", "network_credentials_required": False, "same_origin_default": True, "respect_robots_default": True, "private_network_default": "blocked"}, sort_keys=True)); return 0 if writable else 1
    if args.command in {"crawl", "inspect"}:
        values = [args.timeout]
        if args.command == "crawl":
            values.extend([args.request_delay, args.max_crawl_delay])
        if not all(math.isfinite(value) for value in values):
            print("SiteProbe: bounds exceeded (values must be finite)", file=sys.stderr)
            return 2
    if args.command == "crawl":
        if args.offline:
            print("SiteProbe: crawl requires network access; use validate/compare/report in offline mode", file=sys.stderr); return 2
        if args.max_pages < 1 or args.max_pages > 10000 or args.max_depth < 0 or args.max_depth > 20 or args.concurrency < 1 or args.concurrency > 32 or args.timeout <= 0 or args.timeout > 120 or args.retries < 0 or args.retries > 5 or args.request_delay < 0 or args.request_delay > 60 or args.max_crawl_delay < 0 or args.max_crawl_delay > 60 or args.max_links_per_page < 1 or args.max_links_per_page > 100_000 or args.max_sitemap_compressed_bytes < 1024 or args.max_sitemap_expanded_bytes < 1024 or args.max_sitemap_expanded_bytes > 512 * 1024 * 1024 or args.sort_buffer_bytes < 64 * 1024 or args.sort_buffer_bytes > 512 * 1024 * 1024 or args.max_output_bytes < 1024 or args.max_report_tokens < 64:
            print("SiteProbe: bounds exceeded", file=sys.stderr); return 2
        rc = crawl(args)
        if args.metrics_file:
            peak_rss_bytes = None
            try:
                import resource
                peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
                peak_rss_bytes = int(peak if platform.system() == "Darwin" else peak * 1024)
            except (ImportError, OSError):
                pass
            dump(Path(args.metrics_file), {"schema": "siteprobe.process-metrics/v1", "wall_seconds": round(time.monotonic() - wall_started, 6), "cpu_seconds": round(time.process_time() - cpu_started, 6), "peak_rss_bytes": peak_rss_bytes})
        return rc
    if args.command == "inspect":
        if args.timeout <= 0 or args.timeout > 120 or args.retries < 0 or args.retries > 5 or args.max_links_per_page < 1 or args.max_links_per_page > 100_000:
            print("SiteProbe: bounds exceeded", file=sys.stderr); return 2
        return command_inspect(args)
    if args.command == "validate": return command_validate(args)
    if args.command == "verify": return command_verify(args)
    if args.command == "compare": return command_compare(args)
    run = Path(args.run).resolve(); rc, errors = validate_run(run)
    if rc:
        for error in errors: print(f"ERROR: {error}", file=sys.stderr)
        return rc
    if args.command == "report": print((run / "report.md").read_text(encoding="utf-8"), end="")
    elif args.command == "links": print(json.dumps(load(run / "links.json"), indent=2, sort_keys=True))
    elif args.command == "sitemap": print(json.dumps(load(run / "sitemap.json"), indent=2, sort_keys=True))
    return 0


def main() -> int:
    try:
        return dispatch()
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(f"SiteProbe: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
