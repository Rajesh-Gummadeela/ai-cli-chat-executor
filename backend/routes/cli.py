"""
Direct CLI Execution Route
==========================
Allows testing direct invocation of approved CLI commands and custom flags.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.services.cli_executor import cli_executor, CommandNotAllowedError
from backend.utils.url_validator import validate_and_sanitize_url


router = APIRouter(prefix="", tags=["CLI Tools"])


class DirectCLIRequest(BaseModel):
    url: str = Field(..., json_schema_extra={"example": "https://example.com"})
    max_pages: Optional[int] = Field(default=3, ge=1, le=10)
    max_depth: Optional[int] = Field(default=1, ge=0, le=3)
    timeout: Optional[float] = Field(default=20.0, ge=2.0, le=60.0)


@router.post("/api/cli/execute")
async def execute_cli_crawler(request: DirectCLIRequest):
    """
    Directly spawns the approved crawler CLI process with custom flags.
    """
    is_valid, sanitized_url, error = validate_and_sanitize_url(request.url, check_dns=True)
    if not is_valid:
        raise HTTPException(status_code=400, detail=f"Invalid URL: {error}")

    result = await cli_executor.run_crawler(
        url=sanitized_url,
        max_pages=request.max_pages or 3,
        max_depth=request.max_depth or 1,
        timeout=request.timeout or 20.0
    )

    return {
        "success": result.success,
        "exit_code": result.exit_code,
        "duration": result.duration_formatted,
        "command": result.command,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "parsed_json": result.parsed_json,
        "timed_out": result.timed_out,
        "error_message": result.error_message
    }
