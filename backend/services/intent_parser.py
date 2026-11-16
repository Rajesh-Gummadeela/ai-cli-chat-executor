"""
Intent Parsing Service
======================
Extracts structured intent, target URL, and execution parameters from
natural language user requests. Supports both LLM extraction (OpenAI / Gemini)
and a robust deterministic heuristic fallback engine.
"""

import os
import re
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class UserIntent(BaseModel):
    """Structured representation of interpreted user intent."""
    task: str = Field(..., description="Action type: 'crawl_and_summarize', 'extract_json', etc.")
    url: Optional[str] = Field(None, description="Target website URL to crawl")
    expected_output: str = Field("summary_and_json", description="Expected output format")
    max_pages: int = Field(3, description="Maximum pages to crawl")
    max_depth: int = Field(1, description="Crawl depth")
    timeout: float = Field(20.0, description="Crawl timeout in seconds")
    requires_cli: bool = Field(True, description="Whether this request requires CLI tool execution")
    clarification_needed: bool = Field(False, description="Whether essential input like URL is missing")
    clarification_message: Optional[str] = Field(None, description="Message to prompt user for missing details")


# Regex to detect HTTP/HTTPS URLs or naked domains
URL_REGEX = re.compile(
    r"""(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))\)|[^\s`!()\[\]{};:'".,<>?«»“”‘’]))""",
    re.VERBOSE
)

DOMAIN_REGEX = re.compile(
    r"\b([a-zA-Z0-9][-a-zA-Z0-9]*\.)+(com|org|net|edu|gov|io|ai|dev|co|tech|app|me|info|biz)\b",
    re.IGNORECASE
)


def extract_url_from_text(text: str) -> Optional[str]:
    """Extract first valid HTTP/HTTPS URL or bare domain from input text."""
    # Look for http/https URLs first
    http_matches = re.findall(r"https?://[^\s'\"<>\),;]+", text, re.IGNORECASE)
    if http_matches:
        url = http_matches[0].rstrip(".,;:)")
        return url

    # Look for www. or domain.com patterns
    domain_match = DOMAIN_REGEX.search(text)
    if domain_match:
        matched_str = domain_match.group(0)
        # Avoid false positives on common words
        if "." in matched_str and len(matched_str) > 4:
            return f"https://{matched_str}"

    return None


def parse_intent_heuristics(prompt: str) -> UserIntent:
    """
    Deterministic rule-based intent parser for instant, offline,
    zero-dependency processing.
    """
    prompt_lower = prompt.lower()
    extracted_url = extract_url_from_text(prompt)

    # Detect max pages
    max_pages = 3
    pages_match = re.search(r"(\d+)\s*(?:pages|links)", prompt_lower)
    if pages_match:
        try:
            val = int(pages_match.group(1))
            max_pages = min(max(val, 1), 10)
        except ValueError:
            pass

    # Detect depth
    max_depth = 1
    depth_match = re.search(r"depth\s*(?:of\s*)?(\d+)", prompt_lower)
    if depth_match:
        try:
            val = int(depth_match.group(1))
            max_depth = min(max(val, 0), 3)
        except ValueError:
            pass

    # Detect expected output format
    expected_output = "summary_and_json"
    if "only json" in prompt_lower or "just json" in prompt_lower:
        expected_output = "json_only"
    elif "only summary" in prompt_lower or "just summary" in prompt_lower:
        expected_output = "summary_only"

    # Detect crawl/scrape action
    is_crawl_action = any(kw in prompt_lower for kw in [
        "crawl", "scrape", "extract", "fetch", "summarize", "analyze", "read", "inspect", "browse", "get"
    ])

    if not extracted_url:
        # Check if user is asking a conversational question or missing a URL
        if any(greet in prompt_lower for greet in ["hello", "hi", "hey", "help", "who are you", "what can you do"]):
            return UserIntent(
                task="general_inquiry",
                url=None,
                expected_output="text",
                requires_cli=False,
                clarification_needed=True,
                clarification_message=(
                    "Hello! I am your CLI-driven AI web crawler assistant. "
                    "Please provide a website URL and instruction, for example:\n\n"
                    "`Crawl https://example.com, summarize the website and return extracted information in JSON.`"
                )
            )

        return UserIntent(
            task="missing_url",
            url=None,
            expected_output=expected_output,
            requires_cli=False,
            clarification_needed=True,
            clarification_message=(
                "I'd love to help! Please include the target website URL in your request (e.g. `https://example.com`)."
            )
        )

    return UserIntent(
        task="crawl_and_summarize",
        url=extracted_url,
        expected_output=expected_output,
        max_pages=max_pages,
        max_depth=max_depth,
        timeout=20.0,
        requires_cli=True,
        clarification_needed=False
    )
