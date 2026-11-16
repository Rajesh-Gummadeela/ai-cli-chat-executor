"""
Chat Route Handler
==================
Main entry point for conversational CLI execution requests.
Implements the 7-step pipeline required by the BuildSprint Round 2 specification:
1. Understand user intent
2. Validate & sanitize URL (SSRF protection)
3. Launch CLI crawler from backend
4. Capture stdout, stderr, exit code, duration
5. Parse the output
6. Generate clean summary using LLM
7. Return structured JSON with execution metadata
"""

import json
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from backend.services.intent_parser import parse_intent_heuristics, UserIntent
from backend.utils.url_validator import validate_and_sanitize_url
from backend.services.cli_executor import cli_executor, CLIExecutionResult
from backend.services.llm_service import llm_service


router = APIRouter(prefix="", tags=["Chat & Execution"])


class ChatRequest(BaseModel):
    message: str = Field(..., description="Natural language user request", json_schema_extra={"example": "Crawl https://example.com, summarize the website and return extracted information in JSON."})
    history: Optional[List[Dict[str, str]]] = Field(default=[], description="Prior chat conversation turns")
    options: Optional[Dict[str, Any]] = Field(default=None, description="Optional overrides for max_pages, max_depth, timeout")


class ExecutionMeta(BaseModel):
    exitCode: int
    duration: str
    command: Optional[str] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    timedOut: bool = False


class ChatResponse(BaseModel):
    status: str = Field(..., description="'success', 'error', 'clarification', or 'timeout'")
    summary: str = Field(..., description="Markdown summary of the website")
    pages: List[Dict[str, Any]] = Field(default=[], description="Structured crawled pages data")
    structured_json: Optional[Dict[str, Any]] = Field(default=None, description="Clean AI-extracted JSON")
    execution: Optional[ExecutionMeta] = Field(default=None, description="CLI execution metrics")
    intent: Optional[Dict[str, Any]] = Field(default=None, description="Parsed user intent")
    ai_provider: Optional[str] = Field(default=None, description="AI engine used for synthesis")
    error: Optional[str] = Field(default=None, description="Error message if execution failed")


@router.post("/chat", response_model=ChatResponse)
@router.post("/api/chat", response_model=ChatResponse)
async def handle_chat(request: ChatRequest):
    """
    Primary endpoint: Converts natural language request into real CLI execution.
    """
    raw_prompt = request.message.strip()
    if not raw_prompt:
        raise HTTPException(status_code=400, detail="User message cannot be empty.")

    # 1. Understand user intent
    intent: UserIntent = parse_intent_heuristics(raw_prompt)

    # If conversational or URL missing, prompt user for clarification
    if intent.clarification_needed or not intent.requires_cli:
        return ChatResponse(
            status="clarification",
            summary=intent.clarification_message or "Please provide a valid website URL to crawl.",
            pages=[],
            structured_json=None,
            execution=None,
            intent=intent.model_dump(),
            ai_provider=llm_service.get_active_provider()
        )

    # Apply any overrides from request options
    max_pages = intent.max_pages
    max_depth = intent.max_depth
    timeout = intent.timeout

    if request.options:
        if "max_pages" in request.options:
            max_pages = min(max(int(request.options["max_pages"]), 1), 10)
        if "max_depth" in request.options:
            max_depth = min(max(int(request.options["max_depth"]), 0), 3)
        if "timeout" in request.options:
            timeout = min(max(float(request.options["timeout"]), 2.0), 60.0)

    # 2. Validate URL (SSRF & schema protection)
    is_valid, sanitized_url, val_error = validate_and_sanitize_url(intent.url, check_dns=True)
    if not is_valid:
        return ChatResponse(
            status="error",
            summary=f"### Security / Validation Error\n\nCould not process the provided URL: `{intent.url}`.\n\n**Reason:** {val_error}",
            pages=[],
            structured_json={"error": val_error, "input_url": intent.url},
            execution=ExecutionMeta(
                exitCode=2,
                duration="0.0s",
                command=f"validate_url('{intent.url}')",
                stderr=val_error
            ),
            intent=intent.model_dump(),
            error=val_error
        )

    # 3. Launch CLI crawler from backend via subprocess
    cli_result: CLIExecutionResult = await cli_executor.run_crawler(
        url=sanitized_url,
        max_pages=max_pages,
        max_depth=max_depth,
        timeout=timeout
    )

    execution_meta = ExecutionMeta(
        exitCode=cli_result.exit_code,
        duration=cli_result.duration_formatted,
        command=cli_result.command,
        stdout=cli_result.stdout,
        stderr=cli_result.stderr,
        timedOut=cli_result.timed_out
    )

    # 4. Handle CLI execution failures or timeouts
    if cli_result.timed_out:
        return ChatResponse(
            status="timeout",
            summary=f"### Execution Timeout\n\nThe CLI crawler timed out while attempting to crawl `{sanitized_url}` after {timeout} seconds. The target server may be slow or unresponsive.",
            pages=[],
            structured_json={"error": "TIMEOUT", "url": sanitized_url},
            execution=execution_meta,
            intent=intent.model_dump(),
            error=cli_result.error_message
        )

    if not cli_result.success or not cli_result.parsed_json:
        err_msg = cli_result.error_message or "CLI process exited with an error."
        return ChatResponse(
            status="error",
            summary=f"### Crawl Failed\n\nThe backend CLI process encountered an error while accessing `{sanitized_url}`.\n\n**Details:** {err_msg}",
            pages=[],
            structured_json=cli_result.parsed_json or {"error": err_msg},
            execution=execution_meta,
            intent=intent.model_dump(),
            error=err_msg
        )

    # 5. Extract website content and pass to LLM
    crawl_data = cli_result.parsed_json
    pages = crawl_data.get("pages", [])

    # 6. Generate clean summary and structured JSON using LLM / Semantic synthesizer
    ai_output = await llm_service.generate_summary_and_json(
        url=sanitized_url,
        crawl_data=crawl_data,
        user_prompt=raw_prompt
    )

    # 7. Return complete response
    return ChatResponse(
        status="success",
        summary=ai_output.get("summary", ""),
        pages=pages,
        structured_json=ai_output.get("structured_json", {}),
        execution=execution_meta,
        intent=intent.model_dump(),
        ai_provider=llm_service.get_active_provider()
    )


@router.post("/api/chat/stream")
async def handle_chat_stream(request: ChatRequest):
    """
    Streaming endpoint: Emits Server-Sent Events (SSE) representing each stage
    of the intent extraction, URL validation, CLI subprocess execution, and AI synthesis.
    """
    raw_prompt = request.message.strip()
    if not raw_prompt:
        raise HTTPException(status_code=400, detail="User message cannot be empty.")

    async def event_generator():
        # Step 1: Intent Understanding
        yield f"data: {json.dumps({'type': 'step', 'step': 'intent', 'status': 'running', 'label': 'Interpreting natural language request...'})}\n\n"
        intent = parse_intent_heuristics(raw_prompt)

        if intent.clarification_needed or not intent.requires_cli:
            payload = {
                "type": "result",
                "data": {
                    "status": "clarification",
                    "summary": intent.clarification_message or "Please provide a valid website URL.",
                    "pages": [],
                    "structured_json": None,
                    "execution": None,
                    "intent": intent.model_dump()
                }
            }
            yield f"data: {json.dumps(payload)}\n\n"
            return

        yield f"data: {json.dumps({'type': 'step', 'step': 'intent', 'status': 'done', 'label': f'Target URL: {intent.url} (Task: {intent.task})'})}\n\n"

        # Step 2: Validate URL
        yield f"data: {json.dumps({'type': 'step', 'step': 'validate', 'status': 'running', 'label': 'Validating URL & running SSRF security checks...'})}\n\n"
        is_valid, sanitized_url, val_error = validate_and_sanitize_url(intent.url, check_dns=True)

        if not is_valid:
            yield f"data: {json.dumps({'type': 'step', 'step': 'validate', 'status': 'error', 'label': f'Validation Failed: {val_error}'})}\n\n"
            payload = {
                "type": "result",
                "data": {
                    "status": "error",
                    "summary": f"### Security / Validation Error\n\nCould not process URL `{intent.url}`.\n\n**Reason:** {val_error}",
                    "pages": [],
                    "structured_json": {"error": val_error},
                    "execution": {"exitCode": 2, "duration": "0.0s", "stderr": val_error},
                    "intent": intent.model_dump(),
                    "error": val_error
                }
            }
            yield f"data: {json.dumps(payload)}\n\n"
            return

        yield f"data: {json.dumps({'type': 'step', 'step': 'validate', 'status': 'done', 'label': f'Sanitized & Verified: {sanitized_url}'})}\n\n"

        # Step 3: Launch CLI
        yield f"data: {json.dumps({'type': 'step', 'step': 'cli', 'status': 'running', 'label': 'Spawning CLI crawler process from backend...'})}\n\n"
        cli_result = await cli_executor.run_crawler(
            url=sanitized_url,
            max_pages=intent.max_pages,
            max_depth=intent.max_depth,
            timeout=intent.timeout
        )

        exec_meta = {
            "exitCode": cli_result.exit_code,
            "duration": cli_result.duration_formatted,
            "command": cli_result.command,
            "stdout": cli_result.stdout,
            "stderr": cli_result.stderr,
            "timedOut": cli_result.timed_out
        }

        if cli_result.timed_out or not cli_result.success or not cli_result.parsed_json:
            yield f"data: {json.dumps({'type': 'step', 'step': 'cli', 'status': 'error', 'label': f'CLI failed with exit code {cli_result.exit_code}'})}\n\n"
            payload = {
                "type": "result",
                "data": {
                    "status": "timeout" if cli_result.timed_out else "error",
                    "summary": f"### CLI Execution Failed\n\nProcess exited with code `{cli_result.exit_code}`.\n\n{cli_result.error_message}",
                    "pages": [],
                    "structured_json": cli_result.parsed_json or {},
                    "execution": exec_meta,
                    "intent": intent.model_dump(),
                    "error": cli_result.error_message
                }
            }
            yield f"data: {json.dumps(payload)}\n\n"
            return

        yield f"data: {json.dumps({'type': 'step', 'step': 'cli', 'status': 'done', 'label': f'CLI finished in {cli_result.duration_formatted} (Exit code: 0)'})}\n\n"

        # Step 4: AI Synthesis
        yield f"data: {json.dumps({'type': 'step', 'step': 'llm', 'status': 'running', 'label': f'Synthesizing summary & structured JSON ({llm_service.get_active_provider()})...'})}\n\n"
        crawl_data = cli_result.parsed_json
        pages = crawl_data.get("pages", [])

        ai_output = await llm_service.generate_summary_and_json(
            url=sanitized_url,
            crawl_data=crawl_data,
            user_prompt=raw_prompt
        )

        yield f"data: {json.dumps({'type': 'step', 'step': 'llm', 'status': 'done', 'label': 'Synthesis complete'})}\n\n"

        # Final complete payload
        payload = {
            "type": "result",
            "data": {
                "status": "success",
                "summary": ai_output.get("summary", ""),
                "pages": pages,
                "structured_json": ai_output.get("structured_json", {}),
                "execution": exec_meta,
                "intent": intent.model_dump(),
                "ai_provider": llm_service.get_active_provider()
            }
        }
        yield f"data: {json.dumps(payload)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
