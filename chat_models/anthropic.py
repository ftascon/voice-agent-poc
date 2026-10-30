from anthropic import AsyncAnthropic

from chat_models.base import Message


class AnthropicChatModel:
    """ChatModel backed by Anthropic's Messages API."""

    def __init__(self, model: str = "claude-haiku-5-5", max_tokens: int = 300,thinking: dict | None = None):
        self._client = AsyncAnthropic()
        self._model = model
        self._max_tokens = max_tokens
        self._thinking = thinking or {"type": "disabled"}
        

    async def reply(self, system: str, messages: list[Message]) -> str:
        response = await self._client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            system=system,
            messages=messages,
            thinking=self._thinking,
        )
        return "".join(block.text for block in response.content if block.type == "text")
