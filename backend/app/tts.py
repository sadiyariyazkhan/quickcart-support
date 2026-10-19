import time, subprocess, uuid, re
from pathlib import Path
from .config import TTS_ENGINE, PIPER_EN_VOICE, PIPER_HI_VOICE

OUT_DIR = Path(__file__).resolve().parent.parent / "tmp" / "quickcart_tts"
OUT_DIR.mkdir(parents=True, exist_ok=True)

def _strip_markdown(text: str) -> str:
    """TASK.md §1b: Voice answers short, speakable, no markdown."""
    text = re.sub(r"[•*_#>]", "", text)
    text = text.replace("§", "section ")
    text = re.sub(r"₹", " rupees ", text)
    return text.strip()

def synthesize(text: str, language: str = "en"):
    t0 = time.time()
    speakable = _strip_markdown(text)
    out = OUT_DIR / f"{uuid.uuid4().hex}.wav"

    if TTS_ENGINE == "piper":
        voice = PIPER_HI_VOICE if language == "hi" else PIPER_EN_VOICE
        subprocess.run(["piper", "--model", voice, "--output_file", str(out)],
                       input=speakable.encode(), check=True)
    else:
        # TASK.md §2: gTTS Limits - Requires internet, single voice per language, 
        # no SSML/emotion control, and slightly higher latency.
        from gtts import gTTS
        mp3 = out.with_suffix(".mp3")
        gTTS(speakable, lang="hi" if language == "hi" else "en", 
             tld="co.in" if language == "en" else "com").save(str(mp3))
        out = mp3

    return {"path": str(out), "ms": int((time.time() - t0) * 1000)}