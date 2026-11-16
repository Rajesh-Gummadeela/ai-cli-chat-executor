# Root alias forwarding to backend.utils
from backend.utils.url_validator import validate_and_sanitize_url, URLValidationError

__all__ = ["validate_and_sanitize_url", "URLValidationError"]
