from fastapi import FastAPI, Response
from twilio.twiml.voice_response import VoiceResponse


app = FastAPI()

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/voice/incoming")
async def incoming_voice():
    """Twilio webhook: we are receiving a call"""
    resp = VoiceResponse()
    resp.say("Hello, this is a test call from Felipe!")
    return Response(content=str(resp), media_type="application/xml")