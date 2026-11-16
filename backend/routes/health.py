"""
Health Check & Diagnostic Route
"""

import sys
import platform
from fastapi import APIRouter
from backend.services.llm_service import llm_service
from backend.services.cli_executor import cli_executor


router = APIRouter(prefix="", tags=["Diagnostics"])


@router.get("/health")
@router.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "BuildSprint Round 2 CLI Execution Backend",
        "python_version": sys.version.split(" ")[0],
        "platform": platform.platform(),
        "ai_engine": llm_service.get_active_provider(),
        "cli_executor": {
            "default_timeout": cli_executor.default_timeout,
            "whitelisted_tools": sorted(list(cli_executor.WHITELISTED_TOOLS))
        }
    }
