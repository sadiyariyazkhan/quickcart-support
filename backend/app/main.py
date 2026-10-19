import base64, time, tempfile
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from .models import ChatRequest
from . import engine, db, stt, tts
from .language import mask_mobile

app = FastAPI(title="QuickCart Support")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.on_event("startup")
def _startup():
    db.init_db()

@app.post("/chat")
def chat(req: ChatRequest):
    return engine.handle(req.session_id, req.text, voice_mode=False)

@app.post("/voice")
async def voice(session_id: str = Form(...), audio: UploadFile = File(...)):
    total_start = time.time()
    
    # 1) STT
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    tmp.write(await audio.read()); tmp.close()
    stt_res = stt.transcribe(tmp.name)
    
    # 2) Same engine as /chat
    bot_res = engine.handle(session_id, stt_res["text"], voice_mode=True)
    
    # 3) TTS
    tts_res = tts.synthesize(bot_res["reply"], bot_res["language"])
    with open(tts_res["path"], "rb") as f:
        audio_b64 = base64.b64encode(f.read()).decode()
        
    return {
        "transcript": stt_res["text"],
        "language": bot_res["language"],
        "reply": bot_res["reply"],
        "reply_audio": audio_b64,
        "intent": bot_res["intent"],
        "state": bot_res["state"],
        "collected_fields": bot_res["collected_fields"],
        "citations": bot_res["citations"],
        "ticket_id": bot_res.get("ticket_id"),
        "timings_ms": {
            "stt": stt_res["ms"],
            "bot": int((time.time() - total_start - stt_res["ms"]/1000 - tts_res["ms"]/1000) * 1000),
            "tts": tts_res["ms"],
            "total": int((time.time() - total_start) * 1000),
        },
    }

@app.get("/tickets")
def tickets(category: str = None, status: str = None, page: int = 1, page_size: int = 20):
    rows, total = db.list_tickets(category, status, page, page_size)
    for r in rows:
        if r.get("mobile"): r["mobile"] = mask_mobile(r["mobile"])
    return {"items": rows, "total": total, "page": page, "page_size": page_size}

@app.get("/tickets/{ticket_id}")
def ticket(ticket_id: str):
    t = db.get_ticket(ticket_id)
    if not t: return JSONResponse({"error": "not found"}, status_code=404)
    if t.get("mobile"): t["mobile"] = mask_mobile(t["mobile"])
    return t

@app.get("/sessions/{session_id}")
def session(session_id: str):
    state = db.get_state(session_id)
    turns = db.get_turns(session_id)
    return {"session_id": session_id, "state": state, "turns": turns}