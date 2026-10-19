import os
import glob
import json
import sys
from jiwer import wer
import pandas as pd
from pathlib import Path

# Add backend to path so we can import stt
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))
from app.stt import transcribe # type: ignore

BASE_DIR = Path(__file__).resolve().parent.parent
CLIPS_DIR = BASE_DIR / "fleurus_clips" / "data"

def evaluate_language(lang_code):
    print(f"\n--- Evaluating {lang_code} ---")
    lang_dir = CLIPS_DIR / lang_code / "test"
    
    # FLEURS uses a TSV file for transcripts
    tsv_path = lang_dir / "test.tsv"
    if not tsv_path.exists():
        print(f"Missing {tsv_path}. Please run download_fleurs.py first.")
        return

    df = pd.read_csv(tsv_path, sep="\t")
    
    results = []
    errors = []
    
    # Test on first 20 clips as per TASK.md
    for idx, row in df.head(20).iterrows():
        audio_path = lang_dir / row["filename"]
        if not audio_path.exists():
            continue
            
        gold = row["transcription"]
        res = transcribe(str(audio_path))
        hyp = res["text"]
        
        error_rate = wer(gold, hyp)
        results.append(error_rate)
        errors.append((error_rate, gold, hyp))

    if not results:
        print("No audio files found.")
        return

    avg_wer = sum(results) / len(results)
    print(f"Average WER for {lang_code}: {avg_wer:.2%}")
    
    # Show 2 worst errors (EVAL.md §1)
    errors.sort(key=lambda x: x[0], reverse=True)
    print(f"Worst Errors for {lang_code}:")
    for i in range(min(2, len(errors))):
        print(f"  {i+1}. WER: {errors[i][0]:.2%}")
        print(f"     GOLD: {errors[i][1]}")
        print(f"     HYP:  {errors[i][2]}")

if __name__ == "__main__":
    evaluate_language("en_us")
    evaluate_language("hi_in")