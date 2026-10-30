import uuid
from dataclasses import dataclass
from pathlib import Path

import yaml

from app.call_handler import CallHandler
from chat_models.base import ChatModel, Message
from evals.prompts import CALLER_PROMPT

PERSONAS_FILE = Path(__file__).parent / "personas.yaml"
MAX_TURNS = 12


@dataclass
class Persona:
    id: str
    description: str
    expected: dict | None = None


@dataclass
class SimulationResult:
    persona_id: str
    transcript: list[dict[str, str]]
    stop_reason: str  # "agent_ended" or "max_turns"


def load_personas(path: Path = PERSONAS_FILE) -> list[Persona]:
    with path.open() as f:
        return [Persona(**item) for item in yaml.safe_load(f)]


async def simulate_call(
    persona: Persona,
    agent_model: ChatModel,
    caller_model: ChatModel,
    max_turns: int = MAX_TURNS,
) -> SimulationResult:
    """Let a simulated caller talk to the agent until it ends the call."""
    handler = CallHandler(chat_model=agent_model)
    call_id = f"eval-{uuid.uuid4().hex[:8]}"

    agent_line = handler.start_call(call_id)
    transcript = [{"speaker": "agent", "text": agent_line}]

    # From the caller's point of view, the agent is the "user".
    caller_history: list[Message] = []
    system = CALLER_PROMPT.format(persona=persona.description)

    for _ in range(max_turns):
        caller_history.append({"role": "user", "content": agent_line})
        caller_line = await caller_model.reply(system, caller_history)
        caller_history.append({"role": "assistant", "content": caller_line})
        transcript.append({"speaker": "caller", "text": caller_line})

        agent_line, done = await handler.handle_speech(call_id, caller_line)
        transcript.append({"speaker": "agent", "text": agent_line})
        if done:
            return SimulationResult(persona.id, transcript, "agent_ended")

    return SimulationResult(persona.id, transcript, "max_turns")