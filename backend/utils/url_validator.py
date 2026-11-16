"""
URL Validation and SSRF (Server-Side Request Forgery) Protection Utility.
Ensures that all URLs passed to the CLI crawler are valid, well-formed,
and safe from private network access or malicious schemes.
"""

import ipaddress
import re
import socket
from typing import Optional, Tuple
from urllib.parse import urlparse, urlunparse


BLOCKED_SCHEMES = {"file", "ftp", "gopher", "data", "javascript", "vbscript", "dict", "ldap", "tftp"}
ALLOWED_SCHEMES = {"http", "https"}

# Cloud metadata and localhost hostnames to explicitly block
BLOCKED_HOSTNAMES = {
    "localhost",
    "localhost.localdomain",
    "ip6-localhost",
    "ip6-loopback",
    "169.254.169.254",          # AWS, GCP, Azure metadata
    "metadata.google.internal",   # GCP metadata
    "metadata.internal",
    "instance-data",
}

# Regex to quickly detect IPv4 or IPv6 literals in hostnames
IP_LITERAL_REGEX = re.compile(r"^\[?([0-9a-fA-F:.]+)\]?$")


class URLValidationError(ValueError):
    """Raised when URL fails validation or security checks."""
    pass


def is_ip_private_or_restricted(ip_str: str) -> bool:
    """
    Check if an IP address belongs to private, loopback, link-local,
    multicast, or reserved address ranges.
    """
    try:
        ip = ipaddress.ip_address(ip_str)
        return (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        )
    except ValueError:
        return False


def validate_and_sanitize_url(raw_url: str, check_dns: bool = True) -> Tuple[bool, str, Optional[str]]:
    """
    Validates and sanitizes a URL for safe CLI crawling.

    Args:
        raw_url: The raw URL string from user input or LLM extraction.
        check_dns: Whether to perform DNS resolution to block private IP addresses.

    Returns:
        Tuple of (is_valid: bool, sanitized_url: str, error_message: Optional[str])
    """
    if not raw_url or not isinstance(raw_url, str):
        return False, "", "URL cannot be empty."

    url = raw_url.strip()

    # Pre-check for raw scheme before prepending https://
    if ":" in url:
        raw_scheme = url.split(":", 1)[0].lower().strip()
        if raw_scheme in BLOCKED_SCHEMES:
            return False, "", f"Blocked scheme '{raw_scheme}'. Only 'http://' and 'https://' are permitted."
        if "://" in url and raw_scheme not in ALLOWED_SCHEMES:
            return False, "", f"Unsupported protocol '{raw_scheme}://'. Only 'http://' and 'https://' are permitted."

    # Prepend https:// if no scheme is provided (e.g. user typed 'example.com')
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url

    try:
        parsed = urlparse(url)
    except Exception as e:
        return False, "", f"Malformed URL: {str(e)}"

    scheme = parsed.scheme.lower()
    if scheme not in ALLOWED_SCHEMES:
        return False, "", f"Invalid scheme '{scheme}'. Only HTTP and HTTPS are permitted."

    hostname = (parsed.hostname or "").lower().strip()
    if not hostname:
        return False, "", "URL must include a valid hostname or domain name."

    # Check blocked hostnames
    if hostname in BLOCKED_HOSTNAMES:
        return False, "", f"Access to '{hostname}' is restricted for security reasons (SSRF prevention)."

    # Strip userinfo (username:password@) to prevent credential leakage or tricks
    sanitized_netloc = hostname
    try:
        port = parsed.port
        if port:
            if port not in {80, 443, 8080, 8443}:
                return False, "", f"Port {port} is restricted. Only standard web ports (80, 443, 8080, 8443) are allowed."
            sanitized_netloc = f"{hostname}:{port}"
    except ValueError:
        return False, "", "Invalid or malformed port in URL."

    # Check for direct IP address literal
    ip_match = IP_LITERAL_REGEX.match(hostname)
    if ip_match:
        ip_candidate = ip_match.group(1)
        if is_ip_private_or_restricted(ip_candidate):
            return False, "", f"Direct IP address '{ip_candidate}' is private/restricted and cannot be crawled."

    # DNS check to resolve hostname and verify destination IP
    if check_dns:
        try:
            # Resolve IPv4 and IPv6 addresses
            addr_info = socket.getaddrinfo(hostname, None)
            resolved_ips = {item[4][0] for item in addr_info}

            for ip_str in resolved_ips:
                if is_ip_private_or_restricted(ip_str):
                    return False, "", (
                        f"Domain '{hostname}' resolves to restricted IP '{ip_str}' "
                        f"(SSRF / Private network protection triggered)."
                    )
        except socket.gaierror:
            # Domain cannot be resolved via DNS
            return False, "", f"DNS lookup failed for hostname '{hostname}'. Domain may not exist."
        except Exception as e:
            return False, "", f"DNS resolution error: {str(e)}"

    # Reconstruct clean sanitized URL (strip fragment, preserve path and query)
    sanitized_url = urlunparse((
        scheme,
        sanitized_netloc,
        parsed.path or "/",
        "",
        parsed.query,
        ""  # Strip fragments like #section
    ))

    return True, sanitized_url, None
