import asyncio
import json

import pytest

from evals.judge import CRITERIA, JudgeError, judge_call, parse_verdict
from evals.simulator import Persona, SimulationResult
from tests.fakes import FakeChatModel

PERSONA = Persona(id="test", description="Your name is Ana.", expected={"name": "Ana"})
TRANSCRIPT = [
    {"speaker": "agent", "text": "Hi, who am I speaking with?"},
    {"speaker": "caller", "text": "I'm Ana"},
    {"speaker": "agent", "text": "Thanks Ana, bye!"},
]
RESULT = SimulationResult("test", TRANSCRIPT, "agent_ended")


def verdict_json(passed: bool = True) -> str:
    return json.dumps(
        {"criteria": [{"name": n, "reason": "ok", "pass": passed} for n in CRITERIA]}
    )


def test_parses_a_valid_verdict():
    verdict = asyncio.run(judge_call(PERSONA, RESULT, FakeChatModel([verdict_json()])))
    assert verdict.error is None
    assert [c.name for c in verdict.criteria] == CRITERIA
    assert all(c.passed for c in verdict.criteria)


def test_tolerates_text_around_the_json():
    criteria = parse_verdict("Here is my verdict:\n" + verdict_json() + "\nDone.")
    assert len(criteria) == 4


def test_missing_criterion_is_invalid():
    data = json.loads(verdict_json())
    data["criteria"].pop()
    with pytest.raises(JudgeError):
        parse_verdict(json.dumps(data))


def test_retries_once_on_invalid_reply():
    judge = FakeChatModel(["not json", verdict_json()])
    verdict = asyncio.run(judge_call(PERSONA, RESULT, judge))
    assert verdict.error is None
    assert len(judge.calls) == 2


def test_marks_error_when_retry_also_fails():
    judge = FakeChatModel(["not json", "still not json"])
    verdict = asyncio.run(judge_call(PERSONA, RESULT, judge))
    assert verdict.error is not None
    assert verdict.criteria == []


def test_turn_limit_fails_ended_correctly():
    result = SimulationResult("test", TRANSCRIPT, "max_turns")
    verdict = asyncio.run(judge_call(PERSONA, result, FakeChatModel([verdict_json()])))
    ended = next(c for c in verdict.criteria if c.name == "ended_correctly")
    assert not ended.passed


def test_judge_sees_profile_and_transcript():
    judge = FakeChatModel([verdict_json()])
    asyncio.run(judge_call(PERSONA, RESULT, judge))
    _, messages = judge.calls[0]
    assert "Your name is Ana." in messages[0]["content"]
    assert "Caller: I'm Ana" in messages[0]["content"]