import httpx
import json
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from typing import Protocol

class LLMClient(Protocol):
    async def complete(self, messages: list[dict]) -> dict:
        """Devuelve {'content': str, 'usage': {'prompt_tokens': int, 'completion_tokens': int}}"""
        ...

    def stream_complete(self, messages: list[dict]):
        """Devuelve el chat mientras se genera, esto es mas para la consola que para el postgres, que ahi se guarda en cuando se complete aqui te ira mostrando poco a poco"""
        ...

class HttpxLLMClient:
    def __init__(
            self,
            base_url: str = "http://192.168.1.147:1234/v1",
            model: str = "qwen2.5-7b-instruct",
            timeout: float = 30.0,
    ):
        self._model = model
        self._client = httpx.AsyncClient(base_url=base_url, timeout=timeout)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
    )
    async def complete(self, messages: list[dict]) -> dict:
        payload = {
            "model": self._model,
            "messages": messages,
        }
        response = await self._client.post("/chat/completions", json=payload)
        response.raise_for_status()
        data = response.json()

        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})

        return {
            "content": content,
            "usage" : {
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
            },
        }

    async def stream_complete(self, messages: list[dict]):
        payload = {
            "model": self._model,
            "messages": messages,
            "stream": True,
        }

        async with self._client.stream("POST", "chat/completions", json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line or not line.startswith("data:"):
                    continue
                data_str = line.removeprefix("data:").strip()
                if data_str == ["DONE"]:
                    break
                try:
                    chunk = json.loads(data_str)
                except json.JSONDecodeError:
                    continue
                
                delta = chunk["choices"][0]["delta"].get("content", "")
                if delta:
                    yield delta

    async def aclose(self):
        await self._client.aclose()