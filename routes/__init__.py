# Root alias forwarding to backend.routes
from backend.routes.chat import router as chat_router
from backend.routes.health import router as health_router
from backend.routes.cli import router as cli_router

__all__ = ["chat_router", "health_router", "cli_router"]
