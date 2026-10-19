import requests
import time
import statistics
import os
import glob
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
API_URL = "http://127.0.0.1:8000/voice"

def evaluate_latency():
    print("--- Evaluating Voice Latency (10 turns) ---")
    
    # Get a sample audio file
    sample_dir = BASE_DIR / "fleurus_clips" / "data" / "en_us" / "test"
    audio_files = list(sample_dir.glob("*.wav"))[:1]
    if not audio_files:
        print("No audio files found. Run download_fleurs.py first.")
        return
    
    audio_path = audio_files[0]
    print(f"Using sample audio: {audio_path.name}")
    
    stt_times, bot_times, tts_times, total_times = [], [], [], []

    for i in range(10):
        print(f"Turn {i+1}...", end=" ", flush=True)
        
        with open(audio_path, "rb") as f:
            files = {"audio": (audio_path.name, f, "audio/wav")}
            data = {"session_id": f"latency-test-{i}"}
            
            t0 = time.time()
            res = requests.post(API_URL, files=files, data=data)
            wall_time = (time.time() - t0) * 1000
            
            if res.status_code != 200:
                print(f"FAILED: {res.text}")
                continue
                
            timings = res.json()["timings_ms"]
            stt_times.append(timings["stt"])
            bot_times.append(timings["bot"])
            tts_times.append(timings["tts"])
            total_times.append(timings["total"])
            print("OK")

    if not total_times:
        return

    def print_stats(name, arr):
        med = statistics.median(arr)
        mx = max(arr)
        print(f"{name:6} | Median: {med:7.0f} ms | Slowest: {mx:7.0f} ms")

    print("\n--- Results ---")
    print_stats("STT", stt_times)
    print_stats("Bot", bot_times)
    print_stats("TTS", tts_times)
    print_stats("TOTAL", total_times)
    print("\nBottleneck: Usually STT on CPU. To cut it: use GPU, or switch to WHISPER_MODEL='tiny'.")

if __name__ == "__main__":
    evaluate_latency()