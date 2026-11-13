"""Client for the private Unix-socket code sandbox; source never reaches Ollama or logs."""
from __future__ import annotations

import httpx

from .config import settings


class CodeRunnerUnavailable(RuntimeError):
    pass


async def run_code(language: str, source: str, stdin: str) -> dict:
    if not settings.code_execution_enabled:
        raise CodeRunnerUnavailable("Code execution is disabled by this server.")
    transport = httpx.AsyncHTTPTransport(uds=settings.code_runner_socket)
    try:
        async with httpx.AsyncClient(transport=transport, base_url="http://java-runner", timeout=settings.code_execution_timeout_seconds) as client:
            response = await client.post("/run", json={"language": language, "source": source, "stdin": stdin})
    except httpx.HTTPError as error:
        raise CodeRunnerUnavailable("The isolated code runner is unavailable. Try again in a moment.") from error
    if response.status_code >= 500:
        raise CodeRunnerUnavailable("The isolated code runner is unavailable. Try again in a moment.")
    if response.status_code >= 400:
        detail = response.json().get("detail", "The code request was rejected.")
        raise ValueError(str(detail))
    payload = response.json()
    required = {"status", "stdout", "stderr", "elapsed_ms"}
    if not required.issubset(payload) or not isinstance(payload["elapsed_ms"], int):
        raise CodeRunnerUnavailable("The isolated code runner returned an invalid result.")
    return {key: payload[key] for key in required}
