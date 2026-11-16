"""
Unit tests for CLI Executor Service
"""

import asyncio
import sys
import pytest
from backend.services.cli_executor import cli_executor, CommandNotAllowedError


def test_cli_executor_spawns_process():
    # Spawns Python -c "print('CLI_OUTPUT_OK')"
    result = asyncio.run(cli_executor.execute(
        executable=sys.executable,
        args=["-c", "import sys; sys.stdout.write('CLI_OUTPUT_OK'); sys.stderr.write('LOG_INFO')"]
    ))
    assert result.exit_code == 0
    assert result.success is True
    assert "CLI_OUTPUT_OK" in result.stdout
    assert "LOG_INFO" in result.stderr
    assert result.timed_out is False


def test_cli_executor_command_whitelist_blocks_unauthorized():
    with pytest.raises(CommandNotAllowedError):
        asyncio.run(cli_executor.execute(
            executable="rm",
            args=["-rf", "/"]
        ))


def test_cli_executor_timeout_enforcement():
    # Attempt to sleep for 5 seconds with a 0.5s timeout
    result = asyncio.run(cli_executor.execute(
        executable=sys.executable,
        args=["-c", "import time; time.sleep(5)"],
        timeout=0.5
    ))
    assert result.timed_out is True
    assert result.exit_code == 124
    assert result.success is False
    assert "timeout" in result.stderr.lower() or "timeout" in (result.error_message or "").lower()


def test_cli_executor_crawler_run():
    # Real execution of crawler_cli on example.com
    result = asyncio.run(cli_executor.run_crawler(
        url="https://example.com",
        max_pages=1,
        max_depth=0,
        timeout=10.0
    ))
    assert result.exit_code == 0
    assert result.success is True
    assert result.parsed_json is not None
    assert result.parsed_json.get("status") == "success"
    assert len(result.parsed_json.get("pages", [])) >= 1
