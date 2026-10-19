import re
from .config import HANDBOOK_MD
from .llm import chat_json

_chunks = []

def _load():
    global _chunks
    if _chunks: return
    text = HANDBOOK_MD.read_text(encoding="utf-8")
    parts = re.split(r"\n\*\*(\d+\.\d+)\s", text)
    for i in range(1, len(parts), 2):
        sec = parts[i]
        body = parts[i+1].strip().split("\n\n---")[0].strip().replace("**", "")
        _chunks.append({"section": sec, "text": body})

# Massive list of English and Hindi filler words to ignore during search
STOPWORDS = {"what", "is", "the", "for", "a", "an", "of", "in", "to", "and", 
             "how", "long", "when", "will", "my", "i", "can", "do", "you", 
             "does", "it", "are", "me", "tell", "about", "much", "kya", "hai", "mera",
             "main", "kar", "sakta", "hoon", "ka", "ki", "se", "ko", "hain", 
             "aayega", "aayegi", "kitna", "chahiye", "batao", "karna", "hoga"}

# All variations of Hindi words (including typos) mapped to the English handbook words
TRANSLATIONS = {
    "रिफंड": "refund", "वापसी": "return", "वापस": "return", "वापिस": "return", "वापिसी": "return",
    "डिलीवरी": "delivery", "कब": "when", "कितने": "how long", 
    "दिन": "days", "पैसे": "money", "शुल्क": "charge", "ग्राहक": "customer",
    "खराब": "damaged", "गलत": "wrong", "रद्द": "cancel", "टूट": "broken", "टूटा": "broken",
    "जूता": "fashion", "जूते": "fashion", "जुता": "fashion", "जुते": "fashion", 
    "जूदा": "fashion", "जुदा": "fashion", "शूज": "fashion", "शूज़": "fashion",
    "कपड़ा": "fashion", "कपड़े": "fashion", "सामान": "item", "ऑर्डर": "order",
    "वॉलेट": "wallet", "बटुआ": "wallet"
}

def _score(query: str, chunk: dict) -> float:
    query = query.lower()
    # Translate Hindi words to English for the search
    for hi, en in TRANSLATIONS.items():
        query = query.replace(hi, en)
        
    q = set(re.findall(r"\w+", query)) - STOPWORDS
    c = set(re.findall(r"\w+", chunk["text"].lower())) - STOPWORDS
    if not q: return 0
    return len(q & c) / len(q)

def retrieve(query: str, top_k: int = 3, threshold: float = 0.15):
    _load()
    scored = [(c, _score(query, c)) for c in _chunks]
    scored.sort(key=lambda x: x[1], reverse=True)
    return [(c, s) for c, s in scored[:top_k] if s >= threshold]

REFUSAL = ("I'm sorry, the QuickCart policy handbook doesn't cover that. "
           "I can help with delivery, returns, refunds, payments, warranty, "
           "cancellation, privacy, or complaints.")

def answer(query: str, language: str = "en", short: bool = False):
    hits = retrieve(query)
    if not hits:
        return {"reply": REFUSAL, "citations": [], "refused": True}

    passages = "\n".join(f"[§{c['section']}] {c['text']}" for c, _ in hits)
    lang_instr = "Answer in Hindi." if language == "hi" else "Answer in English."
    len_instr = "Keep it to 1 or 2 short sentences." if short else "Keep it to 2-3 sentences."

    system = (
        "You are a bilingual (English/Hindi) QuickCart customer support assistant. "
        "The user may ask questions in Hindi or Hinglish. You must translate their intent and answer using ONLY the provided English policy passages. "
        "Do not say 'According to our policy'. Just give the direct answer. "
        "If the provided passages contain relevant information, you MUST use it to answer. Only refuse if the topic is completely absent. "
        "If you refuse, say EXACTLY: 'I don't have that information in the handbook.' "
        "If you give an answer, end it with the section number like '(§3.1)'. "
        f"{len_instr} {lang_instr}\n"
        "Return a valid json object with a single key 'reply' containing your answer.\n"
        f"Passages:\n{passages}"
    )
    result = chat_json(system, query)
    reply = result.get("reply") or _fallback(hits, language)

    # STRICT REFUSAL CHECK: Catch any variation of "I can't help"
    reply_lower = reply.lower()
    if any(phrase in reply_lower for phrase in ("don't have", "sorry", "cannot", "can't help", "not in the handbook")):
        return {"reply": "I don't have that information in the handbook.", "citations": [], "refused": True}

    citations = [{"section": f"§{c['section']}", "passage": c["text"]} for c, _ in hits]
    return {"reply": reply, "citations": citations, "refused": False}

def _fallback(hits, language):
    c = hits[0][0]
    clean_text = c['text'].split('.', 1)[-1].strip() 
    prefix = "नीचे दी गई जानकारी के अनुसार: " if language == "hi" else "Here is the policy: "
    return f"{prefix}{clean_text} (§{c['section']})"