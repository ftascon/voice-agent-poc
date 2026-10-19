import os

from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response
from twilio.twiml.voice_response import Gather, VoiceResponse

from app.call_handler import CallHandler
from app.texts import REPROMPT
from chat_models.anthropic import AnthropicChatModel

load_dotenv()

PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "")

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


@app.post("/voice/incoming")
async def incoming_voice(request: Request):
    """Twilio webhook: we are receiving a call"""
    form = await request.form()
    return say_and_listen(callHandler.start_call(form["CallSid"]))


@app.post("/voice/gather")
async def gather_voice(request: Request):
    """Twilio webhook: the caller said something."""
    form = await request.form()
    speech = form.get("SpeechResult", "")
    if not speech:
        return say_and_listen(REPROMPT)

    reply, done = await callHandler.handle_speech(form["CallSid"], speech)
    if done:
        return say_and_hang_up(reply)
    return say_and_listen(reply)
