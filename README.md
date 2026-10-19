# Voice Agent POC

An AI phone agent that answers calls. Built step by step as a proof of concept: Twilio Voice for the calls and Python FastAPI service for the logic.


## How it works



```
📞 Twilio number is called
      │
      ▼
Twilio > POST /voice/incoming > ngrok (public HTTPS URL) > FastAPI on localhost:8000
      ▲                                                              │
      └────────── TwiML: <Response><Say>Hello…</Say></Response> ◄────┘
      │
      ▼
Twilio speaks
```


## Endpoints

- **`GET /health`**: Health check. Returns `{"status": "healthy"}` as JSON. Used to confirm the service is up.

- **`POST /voice/incoming`**: Twilio webhook, called when someone dials the Twilio number.


## Running it locally

Requires Python 3.10+, a Twilio account and a free ngrok account.

```bash
# 1. Install
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Start the service
uvicorn app.main:app --reload --port 8000

# 3. Open the tunnel
ngrok http 8000
```

Then, in the Twilio console, point incoming calls at `https://<your-ngrok-url>/voice/incoming` (HTTP POST) and calls Twilio's number.


