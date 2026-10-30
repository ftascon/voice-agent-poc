import json
from dataclasses import dataclass, field

from chat_models.base import ChatModel, Message
from evals.prompts import JUDGE_PROMPT
from evals.simulator import Persona, SimulationResult

CRITERIA = ["collected_fields", "no_hallucination", "ended_correctly", "polite"]


@dataclass
class CriterionResult:
    name: str
    passed: bool
    reason: str


@dataclass
class Verdict:
    persona_id: str
    criteria: list[CriterionResult] = field(default_factory=list)
    error: str | None = None


class JudgeError(ValueError):
    """The judge's reply couldn't be turned into a verdict."""


def format_call(persona: Persona, result: SimulationResult) -> str:
    lines = [f"{turn['speaker'].capitalize()}: {turn['text']}" for turn in result.transcript]
    return (
        f"Caller profile: {persona.description}\n"
        f"Expected facts: {persona.expected}\n"
        f"How the call stopped: {result.stop_reason}\n\n"
        "Transcript:\n" + "\n".join(lines)
    )


def parse_verdict(text: str) -> list[CriterionResult]:
    """Extract the JSON verdict, tolerating extra text around it."""
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise JudgeError("no JSON object in the reply")
    try:
        data = json.loads(text[start : end + 1])
        items = {item["name"]: item for item in data["criteria"]}
        return [
            CriterionResult(name, bool(items[name]["pass"]), str(items[name]["reason"]))
            for name in CRITERIA
        ]
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        raise JudgeError(f"invalid verdict: {exc}") from exc


async def judge_call(
    persona: Persona,
    result: SimulationResult,
    judge_model: ChatModel,
    retries: int = 1,
) -> Verdict:
    messages: list[Message] = [{"role": "user", "content": format_call(persona, result)}]
    last_error = ""

    for _ in range(retries + 1):
        reply = await judge_model.reply(JUDGE_PROMPT, messages)
        try:
            criteria = parse_verdict(reply)
        except JudgeError as exc:
            last_error = str(exc)
            continue

        # Spec rule: hitting the turn limit always fails ended_correctly.
        if result.stop_reason == "max_turns":
            for criterion in criteria:
                if criterion.name == "ended_correctly":
                    criterion.passed = False
                    criterion.reason = "Hit the turn limit without ending the call."
        return Verdict(persona.id, criteria)

    return Verdict(persona.id, error=last_error)