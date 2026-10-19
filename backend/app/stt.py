import time
from faster_whisper import WhisperModel
from .config import WHISPER_MODEL, WHISPER_COMPUTE

print(f"Loading Whisper model: {WHISPER_MODEL} ...")
_model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type=WHISPER_COMPUTE)

def transcribe(audio_path: str, language: str = None):
    t0 = time.time()
    
    # Hint for Whisper to improve Hindi/Hinglish and domain-specific words
    prompt = "QuickCart customer support, order status, refund, return, damaged, Priya, Neha, Aarav, Rohan, QC-151998, kurta, jute, shoes, paise, wapas."
    
    segments, info = _model.transcribe(
        audio_path, 
        language=language, 
        beam_size=5, 
        initial_prompt=prompt, # <--- Helps STT hear specific words correctly
        vad_filter=False,      # <--- CRITICAL: Stops the audio from cutting off mid-sentence!
        vad_parameters=dict(min_silence_duration_ms=500) 
    )
    
    segments = list(segments)
    text = "".join(s.text for s in segments).strip()
    return {"text": text, "language": info.language, "ms": int((time.time() - t0) * 1000)}