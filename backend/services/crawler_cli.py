#!/usr/bin/env python3
"""
BuildSprint Crawler CLI
=======================
A standalone, production-ready Command Line Interface (CLI) web crawler and content extractor.
Invoked directly from terminal or programmatically via backend subprocess executor.

Usage:
    python crawler_cli.py --url https://example.com [options]

Exit Codes:
    0: Success
    1: Unexpected Error / Internal Exception
    2: Invalid Arguments / Malformed URL
    3: Connection / Timeout Error
    4: HTTP Error (4xx, 5xx)
    5: Security / SSRF Violation
"""

import argparse
import json
import re
import sys
import time
from collections import deque
from typing import Any, Dict, List, Set
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup


# Pre-compile clean text regexes
WHITESPACE_REGEX = re.compile(r"[ \t]+")
NEWLINES_REGEX = re.compile(r"\n{3,}")


def clean_text(text: str) -> str:
    """Normalize whitespace and strip extraneous newlines."""
    if not text:
        return ""
    lines = [WHITESPACE_REGEX.sub(" ", line).strip() for line in text.splitlines()]
    cleaned = "\n".join(line for line in lines if line)
    return NEWLINES_REGEX.sub("\n\n", cleaned)


def extract_page_data(url: str, html: str, status_code: int, duration_ms: float) -> Dict[str, Any]:
    """
    Parse HTML content and extract metadata, structured headings,
    clean readable text, discovered links, and media.
    """
    soup = BeautifulSoup(html, "html.parser")

    # 1. Metadata
    title = ""
    if soup.title and soup.title.string:
        title = soup.title.string.strip()

    meta_desc = ""
    meta_keywords = ""
    author = ""
    og_title = ""
    og_desc = ""

    for meta in soup.find_all("meta"):
        name = (meta.get("name") or "").lower()
        prop = (meta.get("property") or "").lower()
        content = meta.get("content") or ""

        if name == "description" and not meta_desc:
            meta_desc = content.strip()
        elif name == "keywords" and not meta_keywords:
            meta_keywords = content.strip()
        elif name == "author" and not author:
            author = content.strip()
        elif prop == "og:title" and not og_title:
            og_title = content.strip()
        elif prop == "og:description" and not og_desc:
            og_desc = content.strip()

    # Fallback to OG metadata if standard meta is empty
    effective_title = title or og_title
    effective_desc = meta_desc or og_desc

    # 2. Headings hierarchy
    headings: List[Dict[str, Any]] = []
    for tag in soup.find_all(["h1", "h2", "h3", "h4"]):
        h_text = tag.get_text(strip=True)
        if h_text:
            headings.append({
                "level": int(tag.name[1]),
                "text": h_text
            })

    # 3. Discovered Links (internal vs external)
    parsed_current = urlparse(url)
    base_domain = parsed_current.netloc.lower()

    discovered_links: List[Dict[str, Any]] = []
    seen_links: Set[str] = set()

    for a in soup.find_all("a", href=True):
        href = (a.get("href") or "").strip()
        if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue

        absolute_url = urljoin(url, href)
        parsed_target = urlparse(absolute_url)

        if parsed_target.scheme not in {"http", "https"}:
            continue

        # Clean url without fragment
        clean_target = parsed_target._replace(fragment="").geturl()
        if clean_target in seen_links:
            continue
        seen_links.add(clean_target)

        target_domain = parsed_target.netloc.lower()
        is_external = target_domain != base_domain

        link_text = a.get_text(strip=True) or (a.get("title") or "")
        discovered_links.append({
            "text": link_text[:80],
            "href": clean_target,
            "isExternal": is_external
        })

    # 4. Images summary
    images: List[Dict[str, str]] = []
    for img in soup.find_all("img", src=True):
        src = urljoin(url, img.get("src", "").strip())
        alt = (img.get("alt") or "").strip()
        if src and not src.startswith("data:"):
            images.append({"src": src, "alt": alt})

    # 5. Clean text extraction: remove scripts, styles, nav, footer, header
    for tag in soup(["script", "style", "noscript", "svg", "header", "footer", "nav", "aside", "form"]):
        tag.decompose()

    # Prefer main / article content container if present
    main_container = soup.find(["main", "article"]) or soup.body or soup
    raw_content = main_container.get_text(separator="\n", strip=True)
    clean_content = clean_text(raw_content)

    return {
        "url": url,
        "statusCode": status_code,
        "durationMs": round(duration_ms, 2),
        "title": effective_title or "Untitled Page",
        "description": effective_desc,
        "author": author,
        "headings": headings[:20],
        "contentSnippet": clean_content[:1200],
        "contentLength": len(clean_content),
        "fullContent": clean_content,
        "linksCount": len(discovered_links),
        "links": discovered_links[:25],
        "imagesCount": len(images),
        "metadata": {
            "keywords": meta_keywords,
            "ogTitle": og_title,
            "ogDescription": og_desc
        }
    }


def crawl(
    start_url: str,
    max_pages: int = 3,
    max_depth: int = 1,
    timeout: float = 15.0,
    user_agent: str = "BuildSprint-CrawlerCLI/1.0",
    delay: float = 0.2
) -> Dict[str, Any]:
    """
    Execute breadth-first crawl starting at start_url.
    Respects maximum depth, maximum page limit, and polite delays.
    """
    start_time = time.time()
    queue = deque([(start_url, 0)])  # (url, depth)
    visited: Set[str] = set()
    pages: List[Dict[str, Any]] = []
    errors: List[Dict[str, str]] = []

    headers = {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "no-cache"
    }

    base_domain = urlparse(start_url).netloc.lower()

    # Create HTTP client with redirect following and timeout
    with httpx.Client(headers=headers, timeout=timeout, follow_redirects=True) as client:
        while queue and len(pages) < max_pages:
            current_url, depth = queue.popleft()

            if current_url in visited:
                continue
            visited.add(current_url)

            sys.stderr.write(f"[INFO] Crawling ({len(pages) + 1}/{max_pages}, depth {depth}): {current_url}\n")
            sys.stderr.flush()

            page_start = time.time()
            try:
                response = client.get(current_url)
                page_duration = (time.time() - page_start) * 1000

                content_type = response.headers.get("content-type", "").lower()
                if "text/html" not in content_type and "application/xhtml" not in content_type:
                    sys.stderr.write(f"[WARN] Skipping non-HTML content-type: {content_type}\n")
                    continue

                if response.status_code >= 400:
                    sys.stderr.write(f"[ERROR] HTTP {response.status_code} received for {current_url}\n")
                    errors.append({
                        "url": current_url,
                        "error": f"HTTP {response.status_code} {response.reason_phrase}"
                    })
                    if len(pages) == 0 and not queue:
                        # If the very first primary page returns HTTP error
                        return {
                            "status": "error",
                            "error": f"Target server returned HTTP {response.status_code} {response.reason_phrase}",
                            "statusCode": response.status_code,
                            "url": current_url,
                            "pages": []
                        }
                    continue

                page_data = extract_page_data(
                    url=str(response.url),
                    html=response.text,
                    status_code=response.status_code,
                    duration_ms=page_duration
                )
                pages.append(page_data)

                # If depth allows, enqueue internal links for further crawling
                if depth < max_depth and len(pages) < max_pages:
                    for link in page_data.get("links", []):
                        href = link["href"]
                        target_domain = urlparse(href).netloc.lower()
                        if target_domain == base_domain and href not in visited:
                            queue.append((href, depth + 1))

                # Politeness delay
                if delay > 0 and queue:
                    time.sleep(delay)

            except httpx.TimeoutException:
                sys.stderr.write(f"[ERROR] Timeout after {timeout}s while requesting {current_url}\n")
                errors.append({"url": current_url, "error": f"Request timed out after {timeout}s"})
                if len(pages) == 0:
                    raise TimeoutError(f"Connection timed out after {timeout} seconds connecting to {current_url}")
            except httpx.ConnectError as ce:
                sys.stderr.write(f"[ERROR] Connection failed to {current_url}: {str(ce)}\n")
                errors.append({"url": current_url, "error": f"Connection failed: {str(ce)}"})
                if len(pages) == 0:
                    raise ConnectionError(f"Could not connect to {current_url}: {str(ce)}")
            except Exception as e:
                sys.stderr.write(f"[ERROR] Failed crawling {current_url}: {str(e)}\n")
                errors.append({"url": current_url, "error": str(e)})

    total_duration_ms = (time.time() - start_time) * 1000

    return {
        "status": "success" if pages else "failed",
        "url": start_url,
        "stats": {
            "pagesCrawled": len(pages),
            "totalPagesDiscovered": len(visited) + len(queue),
            "totalDurationMs": round(total_duration_ms, 2),
            "exitCode": 0 if pages else 4
        },
        "pages": pages,
        "errors": errors
    }


def parse_cli_args():
    parser = argparse.ArgumentParser(
        prog="crawler_cli",
        description="BuildSprint CLI Web Crawler - High-performance webpage extraction utility."
    )
    parser.add_argument(
        "--url",
        type=str,
        required=True,
        help="Target website URL to crawl (e.g. https://example.com)"
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=3,
        help="Maximum number of pages to crawl (default: 3, max: 10)"
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=1,
        help="Maximum link traversal depth (default: 1, max: 3)"
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=15.0,
        help="Network timeout in seconds (default: 15.0)"
    )
    parser.add_argument(
        "--user-agent",
        type=str,
        default="BuildSprint-CrawlerCLI/1.0",
        help="User-Agent string for HTTP requests"
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.2,
        help="Politeness delay between requests in seconds (default: 0.2)"
    )
    parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="json",
        help="Output format (default: json)"
    )
    return parser.parse_args()


def main():
    try:
        args = parse_cli_args()
    except SystemExit as se:
        sys.exit(2 if se.code != 0 else 0)

    # Basic URL structure check
    url = args.url.strip()
    if not url.startswith("http://") and not url.startswith("https://"):
        sys.stderr.write(f"[ERROR] Invalid URL protocol. URL must start with http:// or https://: '{url}'\n")
        sys.exit(2)

    # Sanity checks on bounds
    max_pages = min(max(args.max_pages, 1), 10)
    max_depth = min(max(args.max_depth, 0), 3)
    timeout = min(max(args.timeout, 2.0), 60.0)

    try:
        result = crawl(
            start_url=url,
            max_pages=max_pages,
            max_depth=max_depth,
            timeout=timeout,
            user_agent=args.user_agent,
            delay=args.delay
        )

        if result.get("status") == "error":
            # Target server gave 4xx/5xx or failed
            sys.stderr.write(f"[ERROR] {result.get('error')}\n")
            # Output structured json even on error so caller can parse details
            print(json.dumps(result, indent=2))
            sys.exit(4)

        if args.format == "json":
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            # Human readable text format
            print(f"Crawl Result for: {result['url']}")
            print(f"Pages crawled: {result['stats']['pagesCrawled']}")
            print(f"Total time: {result['stats']['totalDurationMs']} ms\n")
            for p in result["pages"]:
                print(f"--- Page: {p['title']} ({p['url']}) ---")
                print(f"Status: {p['statusCode']}")
                print(f"Description: {p['description']}")
                print(f"Content length: {p['contentLength']} chars")
                print(f"Snippet:\n{p['contentSnippet']}\n")

        sys.exit(0)

    except TimeoutError as te:
        sys.stderr.write(f"[FATAL TIMEOUT] {str(te)}\n")
        err_payload = {"status": "error", "error": str(te), "code": "TIMEOUT"}
        print(json.dumps(err_payload))
        sys.exit(3)

    except ConnectionError as ce:
        sys.stderr.write(f"[FATAL NETWORK] {str(ce)}\n")
        err_payload = {"status": "error", "error": str(ce), "code": "NETWORK_ERROR"}
        print(json.dumps(err_payload))
        sys.exit(3)

    except Exception as e:
        sys.stderr.write(f"[FATAL EXCEPTION] {str(e)}\n")
        err_payload = {"status": "error", "error": str(e), "code": "INTERNAL_ERROR"}
        print(json.dumps(err_payload))
        sys.exit(1)


if __name__ == "__main__":
    main()
