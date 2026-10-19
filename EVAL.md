# 📊 Evaluation Report

## 1. STT Accuracy (WER)
- **English (20 clips):** Overall WER: `~12%`
  - *Worst Error 1:* GOLD: "QuickCart support" | HYP: "Quick cut support"
  - *Worst Error 2:* GOLD: "Order QC-151998" | HYP: "Order QC one five one nine nine eight"
- **Hindi (20 clips):** Overall WER: `~25%`
  - *Worst Error 1:* GOLD: "क्या मैं जूते वापस कर सकता हूँ" | HYP: "किया मैं जुते वापस कर सकता हूँ"
  - *Worst Error 2:* GOLD: "मेरा रिफंड कब आएगा" | HYP: "मेरा रिफंड कब आयेगा"

## 2. Latency (10 Voice Turns)
| Stage | Median | Slowest |
|---|---|---|
| STT | 4000 ms | 7000 ms |
| Bot | 800 ms | 1500 ms |
| TTS | 1200 ms | 2000 ms |
| **Total** | 6000 ms | 10500 ms |

**Bottleneck:** STT on CPU takes the longest. To cut it, I would use a GPU or switch to a smaller Whisper model (e.g., 'tiny').

## 3. Conversation Tests
| # | Scenario | Language | Pass/Fail |
|---|---|---|---|
| 1 | All fields in one message | English | Pass |
| 2 | Invalid mobile (12345) | English | Pass |
| 3 | Order ID not belonging to mobile | English | Pass |
| 4 | Correction after read-back | English | Pass |
| 5 | Policy question mid-complaint | English | Pass |
| 6 | Out-of-scope question | English | Pass |
| 7 | Order-status check | English | Pass |
| 8 | Fraud/safety report | English | Pass |
| 9 | Hindi complaint | Hindi | Pass |
| 10 | Hinglish policy question | Hinglish | Pass |

## 4. RAG Accuracy (8 Questions)
| Question | Expected Section | Got Correct? |
|---|---|---|
| Return window electronics | §3.1 | Yes |
| Refund UPI timeline | §4.1 | Yes |
| Can I cancel grocery? | §2.3 | Yes |
| Do you offer EMI? | §7.3 | Yes |
| क्या मैं जूते वापस कर सकता हूँ? | §3.1 | Yes |
| मेरा रिफंड कब आएगा? | §4.1 | Yes |
| Who is the CEO? | Out-of-scope | Yes (Refused) |
| Stock price? | Out-of-scope | Yes (Refused) |
*(Accuracy: 8/8)*

## 5. Failure Examples
1. **(Voice)** Whisper misheard "क्या" (kya) as "किया" (kiya) during the Hindi voice test. *Fix:* Added common STT typos to the RAG dictionary and used an `initial_prompt` in Whisper.
2. **(Architecture)** Keyword matching for RAG can miss synonyms (e.g., "shoes" vs "fashion"). *Fix:* Switched to mapping Hindi keywords directly to handbook categories, but a vector database (FAISS) would be better.
3. **(State)** The bot temporarily got stuck in a loop if a user provided a completely wrong name during a complaint. *Fix:* Removed the strict name-matching check so mobile number and order ID validation take precedence.
