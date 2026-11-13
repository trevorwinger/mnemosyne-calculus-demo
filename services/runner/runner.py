"""A deliberately narrow multi-language sandbox served only through a Unix socket."""
from __future__ import annotations

import os
import resource
import signal
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel, Field

Language = Literal["java", "python", "javascript", "c", "cpp"]
SOURCE_LIMIT = 20_000
INPUT_LIMIT = 4_000
OUTPUT_LIMIT = 12_000
FILE_LIMIT = 256 * 1024
CPU_SECONDS = 2
COMPILE_TIMEOUT_SECONDS = 4
RUN_TIMEOUT_SECONDS = 3

app = FastAPI(title="Mnemosyne Code Sandbox", docs_url=None, redoc_url=None, openapi_url=None)


class RunRequest(BaseModel):
    language: Language
    source: str = Field(min_length=1, max_length=SOURCE_LIMIT)
    stdin: str = Field(default="", max_length=INPUT_LIMIT)


class RunResult(BaseModel):
    status: str
    stdout: str = ""
    stderr: str = ""
    elapsed_ms: int


def _limits() -> None:
    resource.setrlimit(resource.RLIMIT_CPU, (CPU_SECONDS, CPU_SECONDS))
    resource.setrlimit(resource.RLIMIT_FSIZE, (FILE_LIMIT, FILE_LIMIT))
    resource.setrlimit(resource.RLIMIT_NOFILE, (32, 32))
    resource.setrlimit(resource.RLIMIT_NPROC, (48, 48))


def _read_limited(path: Path) -> str:
    return path.read_bytes()[:OUTPUT_LIMIT].decode("utf-8", errors="replace")


def _process(command: list[str], directory: Path, stdin: str, timeout: int) -> tuple[int | None, str, str, bool]:
    stdout_path, stderr_path = directory / "stdout.txt", directory / "stderr.txt"
    environment = {"PATH": "/usr/local/bin:/usr/bin:/bin", "HOME": str(directory), "TMPDIR": str(directory), "LANG": "C.UTF-8"}
    with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
        process = subprocess.Popen(command, cwd=directory, stdin=subprocess.PIPE, stdout=stdout, stderr=stderr, text=True, env=environment, start_new_session=True, preexec_fn=_limits)
        try:
            process.communicate(stdin, timeout=timeout)
            timed_out = False
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.communicate()
            timed_out = True
    return process.returncode, _read_limited(stdout_path), _read_limited(stderr_path), timed_out


def _commands(language: Language, directory: Path, source: str) -> tuple[list[str], list[str]]:
    if language == "java":
        (directory / "Main.java").write_text(source, encoding="utf-8")
        return (["javac", "-J-Xmx128m", "-J-XX:ReservedCodeCacheSize=32m", "-J-XX:MaxMetaspaceSize=128m", "--release", "21", "-encoding", "UTF-8", "-d", str(directory), "Main.java"], ["java", "-XX:ActiveProcessorCount=1", "-Xmx64m", "-XX:ReservedCodeCacheSize=32m", "-XX:MaxMetaspaceSize=96m", f"-Djava.io.tmpdir={directory}", "-cp", str(directory), "Main"])
    if language == "python":
        (directory / "main.py").write_text(source, encoding="utf-8")
        return (["python3", "-I", "-B", "-m", "py_compile", "main.py"], ["python3", "-I", "-B", "main.py"])
    if language == "javascript":
        (directory / "main.js").write_text(source, encoding="utf-8")
        return (["node", "--check", "main.js"], ["node", "--disable-proto=throw", "main.js"])
    if language == "c":
        (directory / "main.c").write_text(source, encoding="utf-8")
        return (["gcc", "-std=c17", "-O0", "-Wall", "-Wextra", "main.c", "-o", "program"], ["./program"])
    (directory / "main.cpp").write_text(source, encoding="utf-8")
    return (["g++", "-std=c++20", "-O0", "-Wall", "-Wextra", "main.cpp", "-o", "program"], ["./program"])


def execute(request: RunRequest) -> RunResult:
    started = time.monotonic()
    with tempfile.TemporaryDirectory(dir="/work", prefix="mnemosyne-code-") as raw_directory:
        directory = Path(raw_directory)
        compile_command, run_command = _commands(request.language, directory, request.source)
        code, stdout, stderr, timed_out = _process(compile_command, directory, "", COMPILE_TIMEOUT_SECONDS)
        elapsed_ms = round((time.monotonic() - started) * 1000)
        if timed_out:
            return RunResult(status="compile_timeout", stderr="Compilation exceeded the 4-second limit.", elapsed_ms=elapsed_ms)
        if code != 0:
            return RunResult(status="compile_error", stdout=stdout, stderr=stderr or f"{request.language} compiler exited with status {code}.", elapsed_ms=elapsed_ms)
        code, stdout, stderr, timed_out = _process(run_command, directory, request.stdin, RUN_TIMEOUT_SECONDS)
        elapsed_ms = round((time.monotonic() - started) * 1000)
        if timed_out:
            return RunResult(status="timeout", stdout=stdout, stderr="Program exceeded the 3-second limit.", elapsed_ms=elapsed_ms)
        if code != 0:
            return RunResult(status="runtime_error", stdout=stdout, stderr=stderr or "Program exited with an error.", elapsed_ms=elapsed_ms)
        return RunResult(status="completed", stdout=stdout, stderr=stderr, elapsed_ms=elapsed_ms)


@app.post("/run", response_model=RunResult)
def run(request: RunRequest) -> RunResult:
    return execute(request)
