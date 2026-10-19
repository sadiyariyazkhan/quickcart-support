import json
from groq import Groq
from .config import GROQ_API_KEY, GROQ_MODEL

_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

def chat_json(system: str, user: str) -> dict:
    if not _client: return {}
    try:
        resp = _client.chat.completions.create(
            model="openai/gpt-oss-120b", # Forced to use .env
            messages=[{"role":"system","content":system},
                      {"role":"user","content":user}],
            response_format={"type": "json_object"},
            temperature=0.1,
        )
        return json.loads(resp.choices[0].message.content)
    except Exception as e:
        print(f"[llm error] {e}")
        return {}

def chat_text(system: str, user: str) -> str:
    if not _client: return ""
    try:
        resp = _client.chat.completions.create(
            model=GROQ_MODEL, # Forced to use .env
            messages=[{"role":"system","content":system},
                      {"role":"user","content":user}],
            temperature=0.2,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        print(f"[llm error] {e}")
        return ""