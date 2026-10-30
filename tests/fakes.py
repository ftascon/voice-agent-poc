class FakeChatModel:
    """Returns scripted replies and records what it was asked."""

    def __init__(self, replies: list[str]):
        self.replies = list(replies)
        self.calls = []

    async def reply(self, system, messages):
        self.calls.append((system, list(messages)))
        return self.replies.pop(0)