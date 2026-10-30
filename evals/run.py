import argparse
import asyncio
import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from chat_models.anthropic import AnthropicChatModel
from evals.judge import CRITERIA, Verdict, judge_call
from evals.simulator import load_personas, simulate_call

RESULTS_DIR = Path(__file__).parent / "results"


def build_report(verdicts: list[Verdict]) -> str:
    """Markdown table: passes per persona and criterion, plus errors."""
    persona_ids = list(dict.fromkeys(v.persona_id for v in verdicts))
    lines = [
        "| Persona | " + " | ".join(CRITERIA) + " | Errors |",
        "|" + "---|" * (len(CRITERIA) + 2),
    ]
    total_passed = total_checks = 0

    for persona_id in persona_ids:
        runs = [v for v in verdicts if v.persona_id == persona_id]
        judged = [v for v in runs if v.error is None]
        cells = []
        for name in CRITERIA:
            passed = sum(c.passed for v in judged for c in v.criteria if c.name == name)
            cells.append(f"{passed}/{len(judged)}")
            total_passed += passed
            total_checks += len(judged)
        errors = len(runs) - len(judged)
        lines.append(f"| {persona_id} | " + " | ".join(cells) + f" | {errors} |")

    rate = 100 * total_passed / total_checks if total_checks else 0
    lines += ["", f"Overall pass rate: {rate:.0f}% ({total_passed}/{total_checks} checks)"]
    return "\n".join(lines)


async def run(runs: int, only: str | None) -> Path:
    load_dotenv()  # before creating the models, so the API key is set
    agent = AnthropicChatModel()  # same model the app uses
    no_thinking = {"type": "between_tools"}
    caller = AnthropicChatModel(model="claude-sonnet-5-5", thinking=no_thinking)
    judge = AnthropicChatModel(model="claude-sonnet-5-5", max_tokens=1000, thinking=no_thinking)

    out_dir = RESULTS_DIR / datetime.now().strftime("%Y%m%d-%H%M%S")
    out_dir.mkdir(parents=True)
    verdicts: list[Verdict] = []

    for persona in load_personas():
        if only and persona.id != only:
            continue
        for i in range(1, runs + 1):
            print(f"{persona.id} run {i}/{runs}...", flush=True)
            transcript: list[dict[str, str]] = []
            try:
                result = await simulate_call(persona, agent, caller)
                transcript = result.transcript
                verdict = await judge_call(persona, result, judge)
            except Exception as exc:  # one broken run shouldn't stop the rest
                verdict = Verdict(persona.id, error=f"{type(exc).__name__}: {exc}")

            verdicts.append(verdict)
            record = {
                "persona": persona.id,
                "run": i,
                "transcript": transcript,
                "verdict": asdict(verdict),
            }
            path = out_dir / f"{persona.id}_{i}.json"
            path.write_text(json.dumps(record, indent=2, ensure_ascii=False))

    report = build_report(verdicts)
    (out_dir / "report.md").write_text(report)
    print("\n" + report + f"\n\nResults saved in {out_dir}")
    return out_dir


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the voice agent evals.")
    parser.add_argument("--runs", type=int, default=3, help="runs per persona")
    parser.add_argument("--persona", help="run only this persona id")
    args = parser.parse_args()
    asyncio.run(run(args.runs, args.persona))


if __name__ == "__main__":
    main()