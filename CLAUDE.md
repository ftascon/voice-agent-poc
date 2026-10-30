# Voice agent POC

AI phone agent that qualifies solar leads. Twilio sends webhooks to a
FastAPI service, which runs the conversation with Claude. When a call
ends, the transcript is posted to n8n, which creates a HubSpot deal.

## Layout
- `app/main.py`: FastAPI routes. Only translates HTTP <> TwiML; no logic.
- `app/call_handler.py`: conversation state per call (`CallHandler`).
- `app/texts.py`: all prompts and spoken texts.
- `chat_models/base.py`: `ChatModel` protocol and `Message` type.
- `chat_models/anthropic.py`: the Claude implementation.
- `evals/`: automated evals (see `docs/specs/evals.md`).
- `docs/specs/`: feature specs. Read the relevant one before starting.

## Commands
- Install: `pip install -r requirements.txt`
- Run locally: `uvicorn app.main:app --reload --port 8000`
- Tests: `pytest -q`
- Evals (calls the real API, costs money): `python -m evals.run --runs 3`

## Conventions
- Python 3.12, type hints on all functions.
- Depend on the `ChatModel` protocol, never on Anthropic directly.
  Anything that talks to an LLM receives a `ChatModel`.
- Keep functions small; follow the existing style in `app/`.
- Configuration comes from environment variables via `os.getenv`.

## Tests
- Every change comes with tests.
- Tests must never call a real API: use a fake `ChatModel`.
- `pytest -q` must pass before you consider a task done.

## Rules
- Never read, print or commit `.env` or any secret.
- Don't add dependencies without asking first.
- Work on one task at a time, as listed in the spec. Keep changes small.
- If the spec is unclear or you disagree with it, stop and ask.
- When done, summarise what you changed and anything you're unsure about.