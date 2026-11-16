"""
BuildSprint Round 2 - Main FastAPI Application
===============================================
CLI-Driven AI Chat Execution for Complex Tasks
"""

import sys
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add backend directory to sys.path to ensure module imports resolve smoothly
backend_dir = Path(__file__).resolve().parent
if str(backend_dir.parent) not in sys.path:
    sys.path.insert(0, str(backend_dir.parent))

from backend.routes.chat import router as chat_router
from backend.routes.health import router as health_router
from backend.routes.cli import router as cli_router
from backend.services.llm_service import llm_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logging
    print("\n" + "=" * 60)
    print("🚀  BuildSprint Round 2: CLI-Driven AI Chat Backend")
    print("=" * 60)
    print(f"🤖  AI Engine: {llm_service.get_active_provider()}")
    print("⚡  CLI Execution: subprocess.create_subprocess_exec (real execution)")
    print("🛡️   Security: SSRF protection, URL sanitization, command whitelist")
    print("📖  Swagger API Docs: http://localhost:8000/docs")
    print("=" * 60 + "\n")
    yield
    print("\n🛑  Shutting down CLI Chat Backend...\n")


app = FastAPI(
    title="CLI-Driven AI Chat Execution API",
    description=(
        "Converts natural language user instructions into real backend CLI executions. "
        "Captures stdout, stderr, exit codes, and synthesizes structured JSON and summaries."
    ),
    version="2.0.0",
    lifespan=lifespan
)

# Configure CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "*"  # Open in development, restrict in production
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(chat_router)
app.include_router(health_router)
app.include_router(cli_router)


@app.get("/")
async def root():
    return {
        "project": "BuildSprint Round 2: CLI-Driven AI Chat Execution",
        "status": "online",
        "ai_engine": llm_service.get_active_provider(),
        "docs_url": "/docs",
        "health_check": "/api/health",
        "chat_endpoint": "/chat"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
