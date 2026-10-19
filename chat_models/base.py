from typing import Literal, Protocol, TypedDict


class Message(TypedDict):
    """A provider-neutral chat message."""

    role: Literal["user", "assistant"]
    content: str


class ChatModel(Protocol):
    """Anything that can produce the next reply in a conversation."""

    async def reply(self, system: str, messages: list[Message]) -> str:
        """Return the assistant's reply, based on the system prompt + the list of all the messages in the conversation."""