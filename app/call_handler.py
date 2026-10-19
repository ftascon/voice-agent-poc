from chat_models.base import ChatModel, Message


GREETING = "Hi, thanks for calling EXAMPLE COMPANY! Are you interested in solar panels for your home?"

SYSTEM_PROMPT = """You are a friendly phone assistant for EXAMPLE COMPANY, a solar panel installer.
You already greeted the caller with: "{GREETING}"
Your goal is to collect, one question at a time: their first name, whether they own their home,
their approximate monthly electricity bill, and the best time for a specialist to call back.
This is a phone call: keep every reply to one or two short sentences, with no lists or emojis.
Never invent prices or promises; say a specialist will explain."""

class CallHandler:
    def __init__(self, chat_model: ChatModel):
        self._chat_model = chat_model
        # Nest the conversation messages by call_id
        self._conversations: dict[str, list[Message]] = {}

    def start_call(self, call_id: str) -> str:
        """A new call came in. Returns what the agent says first."""
        self._conversations[call_id] = []
        return GREETING

    async def handle_speech(self, call_id: str, speech: str) -> str:
        """The caller said something. Returns the agent's reply."""
        history = self._conversations.setdefault(call_id, [])
        history.append({"role": "user", "content": speech})

        reply = await self._chat_model.reply(SYSTEM_PROMPT, history)

        history.append({"role": "assistant", "content": reply})
        return reply