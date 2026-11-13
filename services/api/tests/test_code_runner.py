import pytest

from app.code_runner import CodeRunnerUnavailable, run_code
from app.config import settings


@pytest.mark.asyncio
async def test_code_runner_is_explicitly_disabled_without_server_configuration(monkeypatch):
    monkeypatch.setattr(settings, "code_execution_enabled", False)
    with pytest.raises(CodeRunnerUnavailable, match="disabled"):
        await run_code("java", "public class Main {}", "")
