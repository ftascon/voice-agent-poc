import logging
import os
import httpx

from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, Request, Response
from twilio.twiml.voice_response import Gather, VoiceResponse

from app.call_handler import CallHandler
from app.texts import REPROMPT
from chat_models.anthropic import AnthropicChatModel

load_dotenv()

PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "")
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "")

log = logging.getLogger(__name__)
app = FastAPI()
callHandler = CallHandler(chat_model=AnthropicChatModel())


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


def say_and_listen(text: str) -> Response:
    """Speak `text`, then listen for the caller's answer."""
    resp = VoiceResponse()
    gather = Gather(
        input="speech",
        action=f"{PUBLIC_BASE_URL}/voice/gather",
        method="POST",
        speech_timeout="auto",
        action_on_empty_result=True,
    )
    gather.say(text)
    resp.append(gather)
    return Response(content=str(resp), media_type="application/xml")


def say_and_hang_up(text: str) -> Response:
    resp = VoiceResponse()
    resp.say(text)
    resp.hangup()
    return Response(content=str(resp), media_type="application/xml")

async def notify_n8n(call_id: str, phone: str, transcript: list) -> None:
    """Send the finished call to n8n. Failures are logged, never raised."""
    if not N8N_WEBHOOK_URL:
        return
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                N8N_WEBHOOK_URL,
                json={"call_id": call_id, "phone": phone, "transcript": transcript},
            )
            response.raise_for_status()
    except httpx.HTTPError:
        log.exception("call=%s failed to notify n8n", call_id)

@app.post("/voice/incoming")
async def incoming_voice(request: Request):
    """Twilio webhook: we are receiving a call"""
    form = await request.form()
    return say_and_listen(callHandler.start_call(form["CallSid"]))


@app.post("/voice/gather")
async def gather_voice(request: Request, background: BackgroundTasks):
    """Twilio webhook: the caller said something."""
    form = await request.form()
    speech = form.get("SpeechResult", "")
    if not speech:
        return say_and_listen(REPROMPT)

    reply, done = await callHandler.handle_speech(form["CallSid"], speech)
    if done:
        background.add_task(notify_n8n, form["CallSid"], form.get("From", ""), callHandler.transcript(form["CallSid"]))
        return say_and_hang_up(reply)
    return say_and_listen(reply)
