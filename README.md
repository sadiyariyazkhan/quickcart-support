# QuickCart Voice + Chat Support Assistant

## 🔗 Video Demo
[[Paste your Video Link Here](https://drive.google.com/file/d/1ke2gtknTmAkDwwEl13lw6pybNDaYa1cp/view?usp=drive_link)]

## 🚀 Setup (≤ 5 commands)
1. `cd backend && pip install -r requirements.txt`
2. `cp .env.example .env` (Add your `GROQ_API_KEY`)
3. `uvicorn app.main:app --reload`
4. `cd ../frontend && npm install`
5. `npm run dev`

## 🏗️ Architecture
- **Backend:** FastAPI, SQLite for session persistence and ticket storage.
- **Frontend:** React + Vite. Features chat UI, manual push-to-talk mic, clickable citations modal, and tickets dashboard.
- **LLM:** Groq (`openai/gpt-oss-120b` or `llama-3.1-8b-instant`) used purely for NLP extraction and RAG generation.
- **STT:** `faster-whisper` (small model) for English and Hindi.
- **TTS:** `gTTS` (Google Text-to-Speech).
- **RAG:** Custom keyword matching and bilingual dictionary over the handbook.

## 💡 Assumptions
- The CSV is treated as a read-only database for validation.
- Conversation state is stored in SQLite to survive server restarts.
- Fraud and Safety messages are hardcoded to prevent LLM hallucinations (as required by the prompt).
- Custom Hindi/Hinglish typo dictionaries were added to handle voice transcription errors.

## 🤖 Models Used & Why
- **STT:** `faster-whisper` (small) - Optimal balance between Hindi accuracy and CPU inference speed. Uses `vad_filter=False` to prevent cutting off audio.
- **TTS:** `gTTS` - Free, handles Indian accents well. *(Limitation: Requires internet, single voice).*
- **LLM:** Groq - Free tier, extremely fast inference, excellent at JSON formatting.

## 🛠️ Where AI Tools Were Used
AI was used to scaffold the React boilerplate, generate the initial FastAPI routing structure, and assist with the regex for spoken digit normalization.

## 📅 What I'd Do With 2 More Weeks
- Upgrade TTS to a local model (Piper) for offline support and better emotion.
- Switch RAG from keyword matching to a Vector Database (FAISS) with multilingual embeddings.
- Implement WebSockets for real-time voice streaming and barge-in.
