class MockLLMCLient:
    """Esto es una implementacion de prueba para hacer test, no se llama al LLM"""

    def __init__(self, fixed_response: str = "Esta es una respuesta pre-echa."):
        self._fixed_response = fixed_response

    async def complete(self, messages: list[dict]) -> dict:
        return {
            "content": self._fixed_response,
            "usage": {"prompt_tokens": 5, "completion_tokens": 3},
        }

    async def aclose(self):
        pass