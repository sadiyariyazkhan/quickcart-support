import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Paths (Pointing to the data folder at the root level)
BASE_DIR = Path(__file__).resolve().parent.parent.parent  # -> quickcart-support/
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "quickcart.db"
ORDERS_CSV = DATA_DIR / "quickcart_mock_orders.csv"
HANDBOOK_MD = DATA_DIR / "quickcart_policy_handbook.md"
VOICES_DIR = BASE_DIR / "voices"

# LLM Config
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

# STT / TTS Config
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")
WHISPER_COMPUTE = os.getenv("WHISPER_COMPUTE", "int8")
TTS_ENGINE = os.getenv("TTS_ENGINE", "gtts")
PIPER_EN_VOICE = str(VOICES_DIR / "en_US-lessac-medium.onnx")
PIPER_HI_VOICE = str(VOICES_DIR / "hi_IN-rohan-medium.onnx")

# Handbook §8.2 Resolution Targets
RESOLUTION_TARGETS = {
    "Delivery delay": "3 business days",
    "Damaged item": "5 business days",
    "Wrong item": "5 business days",
    "Missing item": "5 business days",
    "Refund": "7 business days",
    "Payment": "5 business days",
    "Other": "7 business days",
}