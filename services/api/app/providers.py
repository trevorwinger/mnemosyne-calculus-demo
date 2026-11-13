"""Local-only model adapters. No provider URL is accepted from clients."""
from dataclasses import dataclass
import asyncio
import time
import httpx
from fastapi import HTTPException, status
from .config import settings
from .harness import SYSTEM_POLICY

@dataclass(frozen=True)
class AvailableModel:
    name: str
    digest: str | None
    size: int | None
    parameter_size: str | None
    quantization: str | None
    provider: str
    approved: bool
    reason: str | None = None

model_semaphore = asyncio.Semaphore(max(1, settings.max_model_concurrency))

def model_approval(capabilities: list[str] | None) -> tuple[bool, str | None]:
    """Every locally installed chat model is eligible; embedding models are not."""
    chat_capable = not capabilities or "completion" in capabilities
    if not chat_capable: return False, "This installed model is not chat-capable."
    return True, None

def bounded_messages(messages: list[dict[str, str]]) -> list[dict[str, str]]:
    """Keep the newest context within a server-controlled character budget."""
    remaining = settings.max_context_chars
    selected: list[dict[str, str]] = []
    for message in reversed(messages):
        content = message["content"]
        if len(content) > remaining: content = content[-remaining:]
        if content: selected.append({"role": message["role"], "content": content})
        remaining -= len(content)
        if remaining <= 0: break
    return list(reversed(selected))

async def provider_status() -> tuple[bool, str]:
    try:
        async with httpx.AsyncClient(timeout=4) as client:
            response = await client.get(f"{settings.ollama_base_url.rstrip('/')}/api/tags")
            response.raise_for_status()
        return True, "Local Ollama is reachable."
    except httpx.HTTPError:
        return False, "Local Ollama is unavailable; only the labeled demo provider can respond."

async def discover_models() -> list[AvailableModel]:
    results: list[AvailableModel] = []
    try:
        async with httpx.AsyncClient(timeout=4) as client:
            response = await client.get(f"{settings.ollama_base_url.rstrip('/')}/api/tags")
            response.raise_for_status()
        for item in response.json().get("models", []):
            details = item.get("details") or {}
            name = item.get("name", "")
            approved, reason = model_approval(item.get("capabilities"))
            results.append(AvailableModel(name, item.get("digest"), item.get("size"), details.get("parameter_size"), details.get("quantization_level"), "ollama", approved, reason))
    except httpx.HTTPError:
        pass
    if settings.demo_mode:
        results.append(AvailableModel("demo-tutor", "demo-v1", None, None, None, "demo", True, "Labeled deterministic demo provider."))
    return results

def demo_response(message: str) -> str:
    lowered = message.lower()
    if any(term in lowered for term in ("practice", "practice problem", "practice topics")):
        if any(term in lowered for term in ("series", "sequence", "taylor", "chapter 9")):
            return r"Let’s practice series reasoning. Consider \(\sum_{n=1}^{\infty} \frac{1}{n^3+2}\). Before choosing a test, what familiar comparison expression could help you decide whether it converges?"
        if any(term in lowered for term in ("parametric", "polar", "chapter 10", "curve")):
            return r"Let’s practice parametric curves. For \(x=t^2-1\) and \(y=2t+3\), what should you solve for first if the goal is to eliminate \(t\)? Show only that setup."
        if any(term in lowered for term in ("vector", "dot", "cross", "plane", "chapter 11")):
            return "Let’s practice a dot product. Let u = ⟨2, -1, 3⟩ and v = ⟨1, 4, -2⟩. Which matching component products belong in u · v before you add them?"
        if any(term in lowered for term in ("partial", "gradient", "multivariable", "directional", "chapter 13")):
            return r"Let’s practice partial derivatives. For \(f(x,y)=x^2y+3y^2\), which variable is held fixed when finding \(f_x\), and what is your first differentiation step?"
        if any(term in lowered for term in ("double integral", "triple integral", "multiple integration", "chapter 14", "volume")):
            return "Let’s practice a double integral setup. For the rectangle 0 ≤ x ≤ 2 and 1 ≤ y ≤ 4, what two bounds would you write for ∫∫_R (x+y) dA before evaluating?"
        return "Let’s practice a Calc III idea. Choose one focus: sequences and series, parametric/polar curves, vectors, vector-valued functions, multivariable derivatives, or multiple integration. Which chapter are you working on?"
    if "array" in lowered or "length" in lowered:
        return "For an array loop, pause at the boundary: `length` is a count, while the last valid index is one less. Write down the first and last index your loop would try, then compare them with the array length. What condition are you using now?"
    if "loop" in lowered or "for" in lowered or "while" in lowered:
        return "A helpful way to trace a loop is to make a three-column table: starting value, condition result, and value after the update. Try the first two passes. At which pass do you expect the condition to become false?"
    if any(term in lowered for term in ("vector", "dot product", "cross product", "plane")):
        return "Start by identifying the kind of vector result you need: a scalar for a dot product, a perpendicular vector for a cross product, or a direction/normal vector for a line or plane. What information have you already labeled?"
    if any(term in lowered for term in ("partial", "gradient", "multivariable", "double integral", "triple integral", "parametric", "polar", "series", "sequence")):
        return "Start by naming the object and the goal: a sequence/series test, a curve representation, a multivariable derivative, or an integral over a region. Show the smallest setup you have, and I’ll help with one next step."
    return "I can help you reason through that. First, state the goal in your own words and show the smallest part you have tried. I’ll respond with one focused next step rather than a finished solution."

async def generate(model: AvailableModel, messages: list[dict[str, str]]) -> tuple[str, int | None, int | None, int | None]:
    started = time.perf_counter()
    async with model_semaphore:
        messages = bounded_messages(messages)
        if model.provider == "demo":
            content = demo_response(messages[-1]["content"])
            return content, round((time.perf_counter() - started) * 1000), None, None
        if not model.approved: raise HTTPException(status.HTTP_403_FORBIDDEN, "This installed model cannot generate chat responses.")
        body = {"model": model.name, "stream": False, "think": False, "messages": [{"role": "system", "content": SYSTEM_POLICY}, *messages]}
        try:
            async with httpx.AsyncClient(timeout=settings.ollama_timeout_seconds) as client:
                response = await client.post(f"{settings.ollama_base_url.rstrip('/')}/api/chat", json=body)
                response.raise_for_status()
            data = response.json()
            return data.get("message", {}).get("content", ""), round((time.perf_counter() - started) * 1000), data.get("prompt_eval_count"), data.get("eval_count")
        except httpx.TimeoutException:
            raise HTTPException(status.HTTP_504_GATEWAY_TIMEOUT, "The local model timed out. Try a shorter question or another installed chat model.")
        except httpx.HTTPError:
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "The local Ollama service is unavailable. No cloud fallback is used.")
