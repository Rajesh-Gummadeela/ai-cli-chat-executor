"""
Unit tests for URL Validator and SSRF Protection
"""

import pytest
from backend.utils.url_validator import validate_and_sanitize_url, is_ip_private_or_restricted


def test_valid_https_url():
    valid, url, err = validate_and_sanitize_url("https://example.com")
    assert valid is True
    assert url == "https://example.com/"
    assert err is None


def test_url_without_scheme():
    valid, url, err = validate_and_sanitize_url("example.com/test")
    assert valid is True
    assert url == "https://example.com/test"
    assert err is None


def test_blocked_schemes():
    for scheme in ["file:///etc/passwd", "ftp://example.com", "gopher://bad.com", "data:text/html,bad"]:
        valid, url, err = validate_and_sanitize_url(scheme)
        assert valid is False
        assert "Blocked scheme" in err or "Unsupported protocol" in err or "Invalid scheme" in err


def test_blocked_localhost():
    valid, url, err = validate_and_sanitize_url("http://localhost:8000")
    assert valid is False
    assert "restricted for security reasons" in err


def test_blocked_metadata_ip():
    valid, url, err = validate_and_sanitize_url("http://169.254.169.254/latest/meta-data/")
    assert valid is False
    assert "restricted" in err or "private" in err


def test_private_ip_detection():
    assert is_ip_private_or_restricted("127.0.0.1") is True
    assert is_ip_private_or_restricted("10.0.0.1") is True
    assert is_ip_private_or_restricted("192.168.1.1") is True
    assert is_ip_private_or_restricted("172.16.0.1") is True
    assert is_ip_private_or_restricted("8.8.8.8") is False
    assert is_ip_private_or_restricted("93.184.216.34") is False


def test_empty_or_whitespace_url():
    valid, url, err = validate_and_sanitize_url("")
    assert valid is False
    assert "cannot be empty" in err
