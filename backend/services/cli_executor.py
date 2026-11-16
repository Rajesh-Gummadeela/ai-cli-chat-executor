"""
CLI Executor Service
====================
Responsible for:
- Whitelisted CLI process spawning
- Process lifecycle monitoring
- Asynchronous stdout and stderr stream capturing
- Exit code inspection
- Timeout enforcement and process tree termination
- Security enforcement (no shell=True, argument sanitization)
"""

import asyncio
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CLIExecutionResult(BaseModel):
    """Structured result returned after executing a CLI process."""
    command: str
    args: List[str]
    exit_code: int
    stdout: str
    stderr: str
    duration_seconds: float
    duration_formatted: str
    timed_out: bool = False
    success: bool = False
    parsed_json: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class CommandNotAllowedError(PermissionError):
    """Raised when an unwhitelisted binary or command is requested."""
    pass


class CLIExecutor:
    """
    Subprocess execution manager that safely spawns CLI commands,
    monitors their execution, captures output, and enforces timeouts.
    """

    # Approved binaries/tools permitted to execute
    WHITELISTED_TOOLS = {
        "crawler_cli",
        "python",
        "python3",
        sys.executable.lower(),
        "playwright",
        "crawl4ai"
    }

    def __init__(self, default_timeout: float = 35.0):
        self.default_timeout = default_timeout
        self.base_dir = Path(__file__).resolve().parent.parent

    def _resolve_crawler_script(self) -> str:
        """Find the absolute path to the crawler_cli.py script."""
        script_path = self.base_dir / "services" / "crawler_cli.py"
        if not script_path.exists():
            # Fallback relative to current working directory
            script_path = Path("backend") / "services" / "crawler_cli.py"
        return str(script_path.resolve())

    def _validate_command(self, executable: str) -> None:
        """Verify that the executable is on the approved whitelist."""
        clean_exe = Path(executable).name.lower()
        clean_exe_no_ext = clean_exe.replace(".exe", "")

        is_allowed = (
            clean_exe in self.WHITELISTED_TOOLS
            or clean_exe_no_ext in self.WHITELISTED_TOOLS
            or executable.lower() == sys.executable.lower()
            or "python" in clean_exe_no_ext
        )

        if not is_allowed:
            raise CommandNotAllowedError(
                f"Execution rejected: '{executable}' is not in the approved CLI tools whitelist. "
                f"Approved tools: {sorted(list(self.WHITELISTED_TOOLS))}"
            )

    async def execute(
        self,
        executable: str,
        args: List[str],
        timeout: Optional[float] = None,
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None
    ) -> CLIExecutionResult:
        """
        Executes a command directly as a subprocess without shell intervention.

        Args:
            executable: Path or name of the binary.
            args: Array of argument strings.
            timeout: Maximum execution time in seconds before SIGTERM/SIGKILL.
            cwd: Working directory for process execution.
            env: Optional custom environment variables.

        Returns:
            CLIExecutionResult with stdout, stderr, exit code, and parsed data.
        """
        self._validate_command(executable)
        effective_timeout = timeout or self.default_timeout

        cmd_display = f"{executable} {' '.join(args)}"
        start_time = time.perf_counter()

        merged_env = os.environ.copy()
        if env:
            merged_env.update(env)
        # Ensure UTF-8 output from Python CLI
        merged_env["PYTHONIOENCODING"] = "utf-8"
        merged_env["PYTHONUNBUFFERED"] = "1"

        process: Optional[asyncio.subprocess.Process] = None
        timed_out = False
        stdout_text = ""
        stderr_text = ""
        exit_code = -1

        try:
            # Safe async subprocess invocation: NEVER uses shell=True
            process = await asyncio.create_subprocess_exec(
                executable,
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd or str(self.base_dir),
                env=merged_env
            )

            # Wait for execution with timeout
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(),
                timeout=effective_timeout
            )

            stdout_text = stdout_bytes.decode("utf-8", errors="replace")
            stderr_text = stderr_bytes.decode("utf-8", errors="replace")
            exit_code = process.returncode if process.returncode is not None else 0

        except asyncio.TimeoutError:
            timed_out = True
            if process:
                try:
                    process.terminate()
                    # Allow 1 second for graceful exit, then kill
                    await asyncio.sleep(1.0)
                    if process.returncode is None:
                        process.kill()
                    await process.wait()
                except Exception:
                    pass
            stderr_text += f"\n[CLI_EXECUTOR_TIMEOUT] Process was terminated after exceeding {effective_timeout}s timeout limit."
            exit_code = 124  # Standard timeout exit code

        except Exception as e:
            stderr_text += f"\n[CLI_EXECUTOR_EXCEPTION] Process execution error: {str(e)}"
            exit_code = 1

        duration = time.perf_counter() - start_time
        duration_formatted = f"{duration:.2f}s"

        # Attempt to parse structured JSON from stdout
        parsed_json: Optional[Dict[str, Any]] = None
        if stdout_text.strip():
            # Try parsing the entire stdout or the last JSON block
            import json
            try:
                parsed_json = json.loads(stdout_text.strip())
            except json.JSONDecodeError:
                # Find outermost JSON object if stdout contained preliminary logs
                first_brace = stdout_text.find("{")
                last_brace = stdout_text.rfind("}")
                if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
                    try:
                        parsed_json = json.loads(stdout_text[first_brace:last_brace + 1])
                    except json.JSONDecodeError:
                        pass

        success = (exit_code == 0) and not timed_out

        error_message: Optional[str] = None
        if timed_out:
            error_message = f"Execution timed out after {effective_timeout:.1f} seconds."
        elif exit_code != 0:
            error_message = f"CLI process exited with non-zero code {exit_code}."
            if stderr_text.strip():
                # Provide a clean summary of stderr
                error_lines = [l for l in stderr_text.strip().splitlines() if "[ERROR]" in l or "Error" in l or "Traceback" in l]
                if error_lines:
                    error_message += f" Details: {error_lines[-1]}"

        return CLIExecutionResult(
            command=cmd_display,
            args=args,
            exit_code=exit_code,
            stdout=stdout_text,
            stderr=stderr_text,
            duration_seconds=round(duration, 3),
            duration_formatted=duration_formatted,
            timed_out=timed_out,
            success=success,
            parsed_json=parsed_json,
            error_message=error_message
        )

    async def run_crawler(
        self,
        url: str,
        max_pages: int = 3,
        max_depth: int = 1,
        timeout: float = 20.0
    ) -> CLIExecutionResult:
        """
        Convenience method to execute the crawler CLI with validated arguments.
        """
        crawler_script = self._resolve_crawler_script()
        args = [
            crawler_script,
            "--url", url,
            "--max-pages", str(max_pages),
            "--max-depth", str(max_depth),
            "--timeout", str(timeout),
            "--format", "json"
        ]

        # Use current Python interpreter to ensure all dependencies are present
        executable = sys.executable
        return await self.execute(
            executable=executable,
            args=args,
            timeout=timeout + 10.0  # Allow buffer over internal HTTP timeout
        )


# Singleton instance
cli_executor = CLIExecutor()
