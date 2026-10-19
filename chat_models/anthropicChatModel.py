from anthropic import AsyncAnthropic
  
from .base import Message

class AnthropicChatModel:
    """ChatModel backed by Anthropic's Messages API.""" 
    def __init__(self, model: str = "claude-haiku-5-5", max_tokens: int = 300):
        self._client = AsyncAnthropic()
        self._model = model
        self._max_tokens = max_tokens

    async def reply(self, system: str, messages: list[Message]) -> str:
        response = await self._client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            system=system,
            messages=messages,
            thinking={"type": "disabled"}
        )
        return response.content[0].text