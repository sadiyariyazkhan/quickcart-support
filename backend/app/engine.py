import re
from . import db, rag
from .config import RESOLUTION_TARGETS
from .language import detect_language, clean_mobile, clean_order_id, mask_mobile
from .escalation import check_escalation
from .llm import chat_json

DEFAULT_STATE = {
    "intent": "other",
    "stage": "idle",
    "collected": {"name": None, "mobile": None, "order_id": None, "issue": None},
    "summary": None,
    "category": None,
    "pending_intent": None,
    "escalated": False,
    "language": "en",
}

def classify_intent(text: str, state: dict) -> str:
    t = text.lower()

    # 1. PENDING STATUS CHECK (Highest priority for numbers)
    if state.get("pending_intent") == "check_order_status":
        if clean_mobile(text) or any(char.isdigit() for char in text):
            return "check_order_status"

    # 2. MID-COMPLAINT FLOW (Must handle corrections and details)
    if state["stage"] in ("collecting", "awaiting_confirmation"):
        # If it's a correction or providing details, STAY in complaint
        if any(w in t for w in ("no,", "correct", "change", "update", "my mobile", "my number", "order is", "name is", "yes", "haan", "ok", "confirm")):
            return "raise_complaint"
        
        # If it's a policy question without IDs, answer it
        if _looks_like_policy_q(text) and not re.search(r"qc[-\s]?\d+", t) and not clean_mobile(text):
            return "policy_question"
            
        return "raise_complaint"

    # 3. EXPLICIT NEW COMPLAINT (Must be caught BEFORE Status Check)
    if any(phrase in t for phrase in ("i want to complain", "raise a complaint", "shikayat")):
        state["collected"] = {"name": None, "mobile": None, "order_id": None, "issue": None}
        state["category"] = None
        state["summary"] = None
        state["stage"] = "collecting"
        return "raise_complaint"

    # 4. STATUS CHECK (Only if NOT complaining)
    if any(w in t for w in ("where is my order", "order status", "track")) or re.search(r"qc[-\s]?\d+", t):
        state["collected"] = {"name": None, "mobile": None, "order_id": None, "issue": None}
        state["category"] = None
        state["summary"] = None
        state["stage"] = "idle"
        return "check_order_status"

    # 5. POLICY QUESTION
    if _looks_like_policy_q(text):
        return "policy_question"

    # 6. IMPLICIT COMPLAINT (e.g., "My TV is broken")
    if any(w in t for w in ("damaged", "wrong", "missing", "not delivered", "toot", "phata")):
        state["collected"] = {"name": None, "mobile": None, "order_id": None, "issue": None}
        state["category"] = None
        state["summary"] = None
        state["stage"] = "collecting"
        return "raise_complaint"

    return "other"

def _looks_like_policy_q(t):
    t = t.lower()
    keywords = ("return", "refund", "how long", "policy", "kitne din", "kab tak", 
                "warranty", "cancel", "delivery charge", "emi", "otp", "ceo", "who is",
                "delay", "delayed", "late", "expire", "wallet", "assured", "report", 
                "damaged", "item", "check", "details", "number", "why", "how",
                "रिफंड", "वापस", "वापिस", "वापसी", "कितने", "कब", "पॉलिसी", "क्या", "किया", 
                "कैसे", "क्यों", "जूता", "जूते", "जुता", "जुते", "जूदा", "शूज", 
                "कपड़े", "सामान", "ऑर्डर", "वॉलेट", "बटुआ")
    return any(w in t for w in keywords)

EXTRACT_SYSTEM = """Extract ONLY fields the user actually mentioned.
Return a valid json object with these keys: name, mobile, order_id, issue.
If a field is not mentioned, return null. Do NOT guess or invent."""

def extract_fields(text: str, current: dict) -> dict:
    data = chat_json(EXTRACT_SYSTEM, text) or {}
    out = dict(current)
    
    if data.get("name") and not out["name"]: out["name"] = data["name"].strip().title()
    if data.get("mobile") and not out["mobile"]:
        m = clean_mobile(str(data["mobile"]))
        if m: out["mobile"] = m
    if data.get("order_id") and not out["order_id"]:
        oid = clean_order_id(str(data["order_id"]))
        if oid: out["order_id"] = oid

    issue_keywords = ("damaged", "torn", "broken", "toot", "phata", "wrong", "missing", "refund", "delayed", "late")
    if any(k in text.lower() for k in issue_keywords):
        out["issue"] = text
    elif data.get("issue") and not out["issue"]: 
        out["issue"] = data["issue"].strip()
    elif not out["issue"] and "complain" in text.lower():
        out["issue"] = text

    if not out["name"]:
        name_match = re.search(r"(?:I am|my name is|name is|मेरा नाम)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)", text, re.IGNORECASE)
        if name_match: out["name"] = name_match.group(1).title()

    if not out["mobile"]:
        m = clean_mobile(text)
        if m: out["mobile"] = m
    if not out["order_id"]:
        oid = clean_order_id(text)
        if oid: out["order_id"] = oid

    return out

CATEGORY_KEYWORDS = {
    # FIXED: Removed "der" because it matched "order", "border", etc.
    "Delivery delay": ["late", "delay", "not delivered", "kab tak", "der hai", "der se"],
    "Damaged item":   ["damaged", "torn", "broken", "cracked", "toota", "phata", "toot"],
    "Wrong item":     ["wrong", "different", "galat"],
    "Missing item":   ["missing", "not in box", "nahi mila"],
    "Refund":         ["refund", "paisa wapas", "money back"],
    "Payment":        ["payment", "deducted", "charged twice", "paisa kata"],
}

def categorise(issue: str) -> str:
    t = issue.lower()
    for cat, kws in CATEGORY_KEYWORDS.items():
        if any(k in t for k in kws): return cat
    return "Other"

def summarise(issue: str, order: dict) -> str:
    item = order.get("item", "item") if order else "item"
    return f"{item}: {issue[:80]}"

def read_back(collected: dict) -> str:
    return (f"Please confirm these details:\n"
            f"• Name: {collected['name']}\n"
            f"• Mobile: {mask_mobile(collected['mobile'])}\n"
            f"• Order: {collected['order_id']}\n"
            f"• Issue: {collected['issue']}\n"
            f"Is everything correct? (yes / no)")

def handle(session_id: str, text: str, voice_mode: bool = False) -> dict:
    state = db.get_state(session_id) or dict(DEFAULT_STATE)
    language = detect_language(text)
    state["language"] = language
    db.log_turn(session_id, "user", text)

    esc_type, esc_msg = check_escalation(text)
    if esc_type:
        state["escalated"] = True
        state["stage"] = "escalated"
        db.save_state(session_id, state, escalated=True, language=language)
        db.log_turn(session_id, "bot", esc_msg)
        return _resp(esc_msg, language, "escalation", state, [], None, True)

    intent = classify_intent(text, state)
    
    if intent == "check_order_status": 
        state["pending_intent"] = "check_order_status"
    elif intent != "other": 
        state["pending_intent"] = None

    if intent == "policy_question":
        res = rag.answer(text, language=language, short=voice_mode)
        db.save_state(session_id, state, escalated=state.get("escalated", False), language=language)
        db.log_turn(session_id, "bot", res["reply"])
        return _resp(res["reply"], language, "policy_question", state, res["citations"])

    if intent == "check_order_status":
        return _handle_status(session_id, text, state, language, voice_mode)

    if intent == "check_ticket_status":
        return _handle_ticket_status(text, language)

    if intent == "raise_complaint" or state["stage"] in ("collecting", "awaiting_confirmation"):
        return _handle_complaint(session_id, text, state, language, voice_mode)

    msg = "I can help you raise a complaint, answer policy questions, or check order/ticket status. What would you like?"
    db.save_state(session_id, state, language=language)
    db.log_turn(session_id, "bot", msg)
    return _resp(msg, language, "other", state)

def _handle_complaint(session_id, text, state, language, voice_mode):
    collected = state["collected"]

    if state["stage"] == "awaiting_confirmation":
        low = text.lower()
        if any(w in low for w in ("yes", "correct", "haan", "sahi", "ok", "confirm")):
            return _finalize_ticket(session_id, state, language)
        if any(w in low for w in ("no", "nahi", "galat", "wrong")):
            updated = extract_fields(text, collected)
            if updated != collected:
                state["collected"] = updated
                msg = "Thanks, I've updated that. " + read_back(updated)
                state["stage"] = "awaiting_confirmation"
                db.save_state(session_id, state, language=language)
                db.log_turn(session_id, "bot", msg)
                return _resp(msg, language, "raise_complaint", state)
            msg = "Which field would you like to correct? " + read_back(collected)
            db.save_state(session_id, state, language=language)
            db.log_turn(session_id, "bot", msg)
            return _resp(msg, language, "raise_complaint", state)

    state["stage"] = "collecting"

    # Robust invalid mobile check
    if any(k in text.lower() for k in ("mobile", "number", "phone")) and not collected["mobile"]:
        if not clean_mobile(text) and any(c.isdigit() for c in text):
            msg = "That mobile number doesn't look right. Please give a 10-digit Indian mobile starting with 6–9."
            db.save_state(session_id, state, language=language)
            db.log_turn(session_id, "bot", msg)
            return _resp(msg, language, "raise_complaint", state)

    collected = extract_fields(text, collected)

    if collected["mobile"]:
        m = clean_mobile(collected["mobile"])
        if not m:
            collected["mobile"] = None
            msg = "That mobile number doesn't look right. Please give a 10-digit Indian mobile starting with 6–9."
            state["collected"] = collected
            db.save_state(session_id, state, language=language)
            db.log_turn(session_id, "bot", msg)
            return _resp(msg, language, "raise_complaint", state)
        collected["mobile"] = m

    if collected["order_id"] and collected["mobile"]:
        ok, res = db.validate_order_owner(collected["order_id"], collected["mobile"])
        if not ok:
            collected["order_id"] = None
            msg = res
            state["collected"] = collected
            db.save_state(session_id, state, language=language)
            db.log_turn(session_id, "bot", msg)
            return _resp(msg, language, "raise_complaint", state)
        
        order = res        
    missing = _next_missing(collected)
    state["collected"] = collected

    if missing:
        msg = _ask_for(missing, language)
        db.save_state(session_id, state, language=language)
        db.log_turn(session_id, "bot", msg)
        return _resp(msg, language, "raise_complaint", state)

    state["category"] = categorise(collected["issue"])
    order = db.get_order(collected["order_id"])
    state["summary"] = summarise(collected["issue"], order)
    state["stage"] = "awaiting_confirmation"
    msg = read_back(collected)
    db.save_state(session_id, state, language=language)
    db.log_turn(session_id, "bot", msg)
    return _resp(msg, language, "raise_complaint", state)

def _next_missing(c):
    for f in ("name", "mobile", "order_id", "issue"):
        if not c[f]: return f
    return None

def _ask_for(field, lang):
    if lang == "hi":
        q = {"name": "कृपया अपना नाम बताइए।",
             "mobile": "कृपया अपना 10 अंकों का मोबाइल नंबर बताइए।",
             "order_id": "कृपया अपना ऑर्डर आईडी बताइए (QC-XXXXXX)।",
             "issue": "कृपया समस्या बताइए।"}
        return q[field]
    q = {"name": "Could you please share your name?",
         "mobile": "Could you share your 10-digit mobile number?",
         "order_id": "Could you share your order ID (QC-XXXXXX)?",
         "issue": "What's the issue with the order?"}
    return q[field]

def _finalize_ticket(session_id, state, language):
    c = state["collected"]
    ticket_id = db.create_ticket(
        session_id, c["name"], c["mobile"], c["order_id"],
        c["issue"], state["summary"], state["category"]
    )
    target = RESOLUTION_TARGETS.get(state["category"], "7 business days")
    state["stage"] = "done"
    state["pending_intent"] = None
    db.save_state(session_id, state, language=language)
    
    msg = (f"✅ Complaint registered. Your ticket is {ticket_id}. "
           f"Category: {state['category']}. "
           f"Resolution target: {target} (§8.2). "
           f"First response within 24 hours.")
    if state["category"] == "Delivery delay":
        msg += " You're also eligible for a ₹50 Wallet credit once the delay is confirmed (§1.3)."
        
    db.log_turn(session_id, "bot", msg)
    return _resp(msg, language, "raise_complaint", state, ticket_id=ticket_id)

def _handle_status(session_id, text, state, language, voice_mode):
    oid = clean_order_id(text) or state["collected"].get("order_id")
    
    if not oid:
        msg = "Which order ID would you like to check? (Format: QC-XXXXXX)"
        db.save_state(session_id, state, language=language)
        return _resp(msg, language, "check_order_status", state)
    
    order = db.get_order(oid)
    if not order:
        msg = f"I couldn't find that order ID in my data. Please check the ID and try again."
        state["pending_intent"] = None
        db.save_state(session_id, state, language=language)
        return _resp(msg, language, "check_order_status", state)

    if oid != state["collected"].get("order_id"):
        state["collected"]["mobile"] = None
    
    state["collected"]["order_id"] = oid
    mobile = clean_mobile(text) or state["collected"].get("mobile")
    
    if not mobile:
        state["pending_intent"] = "check_order_status"
        msg = "For security, please share the 10-digit mobile number on the order."
        db.save_state(session_id, state, language=language)
        return _resp(msg, language, "check_order_status", state)
    
    state["collected"]["mobile"] = mobile
    ok, res = db.validate_order_owner(oid, mobile)
    if not ok:
        msg = res + " Please check the number and try again, or provide a different order ID."
        db.save_state(session_id, state, language=language)
        return _resp(msg, language, "check_order_status", state)
        
    msg = f"Order {oid} status: {res['status']}. Item: {res['item']}. (§9.2 verified)"
    state["pending_intent"] = None
    state["stage"] = "idle"
    state["collected"] = {"name": None, "mobile": None, "order_id": None, "issue": None} # Reset completely
    db.save_state(session_id, state, language=language)
    db.log_turn(session_id, "bot", msg)
    return _resp(msg, language, "check_order_status", state)

def _handle_ticket_status(text, language):
    m = re.search(r"TKT-\d{6}", text.upper())
    if not m:
        return _resp("Please share the ticket ID (TKT-XXXXXX).", language, "check_ticket_status", DEFAULT_STATE)
    t = db.get_ticket(m.group(0))
    msg = f"Ticket {t['ticket_id']} is currently '{t['status']}'." if t else "Ticket not found."
    return _resp(msg, language, "check_ticket_status", DEFAULT_STATE)

def _resp(reply, language, intent, state, citations=None, ticket_id=None, escalated=False):
    return {
        "reply": reply,
        "language": language,
        "intent": intent,
        "state": state["stage"],
        "collected_fields": state["collected"],
        "citations": citations or [],
        "ticket_id": ticket_id,
        "escalated": escalated,
    }