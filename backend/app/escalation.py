FRAUD_KEYWORDS = {"otp", "fraud", "unauthorised", "unauthorized", "scam",
                  "cvv", "pin", "card pin", "upi pin", "someone asked",
                  "ओटीपी", "धोखा", "पैसे कट"}
SAFETY_KEYWORDS = {"overheat", "smoke", "fire", "shock", "electric shock",
                   "burning", "exploded", "blast", "आग", "धुआं", "झटका", "गरम"}

FRAUD_MESSAGE = (
    "⚠️ I've escalated this to a human agent immediately. "
    "QuickCart staff will NEVER ask for your OTP, card PIN, CVV, or UPI PIN. "
    "If you are in immediate danger, please contact local emergency services first. "
    "(Reference: §7.4 and §8.4)"
)

SAFETY_MESSAGE = (
    "⚠️ This is a product safety issue and I've escalated it to a human agent immediately. "
    "Please stop using the product and keep it away from flammable items. "
    "If there is fire, smoke, or risk of injury, contact local emergency services first. "
    "(Reference: §8.4)"
)

def check_escalation(text: str):
    t = text.lower()
    if any(k in t for k in FRAUD_KEYWORDS):
        return "fraud", FRAUD_MESSAGE
    if any(k in t for k in SAFETY_KEYWORDS):
        return "safety", SAFETY_MESSAGE
    return None, None