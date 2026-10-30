from evals.judge import CRITERIA, CriterionResult, Verdict
from evals.run import build_report


def verdict(persona_id: str, passed: bool) -> Verdict:
    return Verdict(persona_id, [CriterionResult(n, passed, "ok") for n in CRITERIA])


def test_counts_passes_per_persona():
    report = build_report([verdict("renter", True), verdict("renter", False)])
    assert "| renter | 1/2 | 1/2 | 1/2 | 1/2 | 0 |" in report
    assert "Overall pass rate: 50%" in report


def test_errors_are_counted_separately():
    report = build_report([verdict("rude", True), Verdict("rude", error="bad json")])
    assert "| rude | 1/1 | 1/1 | 1/1 | 1/1 | 1 |" in report
    assert "Overall pass rate: 100%" in report