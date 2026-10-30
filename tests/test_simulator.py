import asyncio

from evals.simulator import Persona, load_personas, simulate_call


class FakeChatModel:
    """Returns scripted replies and records what it was asked."""

    def __init__(self, replies: list[str]):
        self.replies = list(replies)
        self.calls = []

    async def reply(self, system, messages):
        self.calls.append((system, list(messages)))
        return self.replies.pop(0)


PERSONA = Persona(id="test", description="Your name is Ana. You own your home.")


def test_stops_when_agent_ends_call():
    agent = FakeChatModel(["Do you own your home?", "Thanks Ana, bye! [END]"])
    caller = FakeChatModel(["Hi, I'm Ana", "Yes, I do"])

    result = asyncio.run(simulate_call(PERSONA, agent, caller))

    assert result.stop_reason == "agent_ended"
    assert result.transcript[-1] == {"speaker": "agent", "text": "Thanks Ana, bye!"}
    speakers = [turn["speaker"] for turn in result.transcript]
    assert speakers == ["agent", "caller", "agent", "caller", "agent"]


def test_stops_at_max_turns():
    agent = FakeChatModel(["Sorry, can you repeat?"] * 3)
    caller = FakeChatModel(["Hmm"] * 3)

    result = asyncio.run(simulate_call(PERSONA, agent, caller, max_turns=3))

    assert result.stop_reason == "max_turns"
    assert len(result.transcript) == 7 


def test_caller_receives_persona_and_agent_lines():
    agent = FakeChatModel(["Bye [END]"])
    caller = FakeChatModel(["Hello"])

    asyncio.run(simulate_call(PERSONA, agent, caller))

    system, messages = caller.calls[0]
    assert "Ana" in system
    assert messages[0]["role"] == "user"


def test_personas_file_is_valid():
    personas = load_personas()
    assert len(personas) == 6
    assert len({p.id for p in personas}) == 6