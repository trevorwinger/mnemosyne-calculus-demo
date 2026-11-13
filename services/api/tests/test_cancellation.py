import asyncio

import pytest
from fastapi import HTTPException

import app.main as main
from app.providers import AvailableModel


class DisconnectedRequest:
    async def is_disconnected(self):
        return True


def test_disconnect_cancels_provider_before_a_turn_can_commit(monkeypatch):
    cancelled = False

    async def slow_generate(*_args):
        nonlocal cancelled
        try:
            await asyncio.sleep(10)
        except asyncio.CancelledError:
            cancelled = True
            raise

    monkeypatch.setattr(main, "generate", slow_generate)
    model = AvailableModel("demo-tutor", None, None, None, None, "demo", True)

    async def run():
        with pytest.raises(HTTPException) as error:
            await main.generate_until_disconnected(DisconnectedRequest(), model, [{"role": "user", "content": "hello"}])
        assert error.value.status_code == 499

    asyncio.run(run())
    assert cancelled
