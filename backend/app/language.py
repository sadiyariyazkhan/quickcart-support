import re

HI_DEVANAGARI = re.compile(r"[\u0900-\u097F]")
HINGLISH_WORDS = {"kya", "mujhe", "hai", "mera", "nahi", "karo", "chahiye", "batao", "kitna"}

def detect_language(text: str) -> str:
    if HI_DEVANAGARI.search(text):
        return "hi"
    tokens = set(re.findall(r"\b\w+\b", text.lower()))
    if tokens & HINGLISH_WORDS:
        return "hi"
    return "en"

# Spoken digits
EN_DIGITS = {"zero":"0","one":"1","two":"2","three":"3","four":"4","five":"5",
             "six":"6","seven":"7","eight":"8","nine":"9","oh":"0","o":"0"}
HI_DIGITS = {"शून्य":"0","एक":"1","दो":"2","तीन":"3","चार":"4","पांच":"5","पाँच":"5",
             "छह":"6","छे":"6","सात":"7","आठ":"8","नौ":"9"}

def normalise_spoken_digits(text: str) -> str:
    tokens = re.split(r"(\s+)", text.lower())
    out = []
    for tok in tokens:
        if tok.strip() in EN_DIGITS: out.append(EN_DIGITS[tok.strip()])
        elif tok.strip() in HI_DIGITS: out.append(HI_DIGITS[tok.strip()])
        else: out.append(tok)
    text = "".join(out)
    text = re.sub(r"\b(\d)\s+(?=\d)", r"\1", text)
    return text

def clean_mobile(text: str):
    text = normalise_spoken_digits(text)
    
    # 1. Remove country code formats like +91 or + 91
    text = text.replace("+91", " ").replace("+ 91", " ")
    
    # 2. Find a sequence of 10 digits starting with 6-9, allowing spaces or dashes between them.
    # (?!\d) and (?<!\d) ensure we don't grab a part of a longer number.
    match = re.search(r"(?<!\d)([6-9](?:[\s-]?\d){9})(?!\d)", text)
    
    if match:
        # 3. Strip out any dashes or spaces from the matched number
        digits = re.sub(r"\D", "", match.group(1))
        return digits
        
    # 4. Fallback: Check if the number starts with 91 (without the +)
    match2 = re.search(r"(?<!\d)91([6-9](?:[\s-]?\d){9})(?!\d)", text)
    if match2:
        return re.sub(r"\D", "", match2.group(1))
        
    return None

def clean_order_id(text: str):
    text = normalise_spoken_digits(text)
    cleaned = re.sub(r"[^A-Za-z0-9]", "", text.upper())
    # Accepts QC followed by 1 to 6 digits (so QC46572 is caught)
    m = re.search(r"QC(\d{1,6})", cleaned)
    return f"QC-{m.group(1).zfill(6)}" if m else None

def mask_mobile(m: str) -> str:
    if not m or len(m) < 4: return m
    return m[:2] + "X" * (len(m) - 4) + m[-2:]