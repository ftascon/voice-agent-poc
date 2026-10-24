from app.texts import END_MARKER, GREETING, SYSTEM_PROMPT
from chat_models.base import ChatModel, Message


class CallHandler:
    def __init__(self, chat_model: ChatModel):
        self._chat_model = chat_model
        # Nest the conversation messages by call_id
        self._conversations: dict[str, list[Message]] = {}

    def start_call(self, call_id: str) -> str:
        """A new call came in. Returns what the agent says first."""
        self._conversations[call_id] = []
        return GREETING

    async def handle_speech(self, call_id: str, speech: str) -> tuple[str, bool]:
        """The caller said something. Returns the agent's reply."""
        history = self._conversations.setdefault(call_id, [])
        history.append({"role": "user", "content": speech})

        reply = await self._chat_model.reply(SYSTEM_PROMPT, history)

        history.append({"role": "assistant", "content": reply})
        done = END_MARKER in reply
        return reply.replace(END_MARKER, "").strip(), done
    
    def transcript(self, call_id: str) -> list[Message]:
        return list(self._conversations.get(call_id, []))
