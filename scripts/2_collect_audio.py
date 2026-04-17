"""
Script 2 — Whisper Audio Data Collector
=========================================
Records 40 whisper audio clips per word using your microphone.
Each clip = 2 seconds at 22050 Hz (mono).

VOCABULARY: yes | no | help | water | pain | stop

HOW TO RUN:
    python scripts/2_collect_audio.py

CONTROLS:
    ENTER  = start recording a clip
    S      = skip current word
    CTRL+C = exit
"""

import sounddevice as sd
import soundfile as sf
import numpy as np
import os
import time

# ── Config ────────────────────────────────────────────────────────────────────
VOCABULARY   = ['yes', 'no', 'help', 'water', 'pain', 'stop']
SAMPLES_EACH = 40
CLIP_SECONDS = 2
SAMPLE_RATE  = 22050     # Hz — standard for librosa/MFCC
CHANNELS     = 1         # mono
OUTPUT_DIR   = os.path.join(os.path.dirname(__file__), '..', 'data', 'audio')

# ── Helpers ───────────────────────────────────────────────────────────────────
def count_existing(word):
    folder = os.path.join(OUTPUT_DIR, word)
    os.makedirs(folder, exist_ok=True)
    return len([f for f in os.listdir(folder) if f.endswith('.wav')])

def record_clip():
    """Record CLIP_SECONDS of audio and return numpy array."""
    frames = int(SAMPLE_RATE * CLIP_SECONDS)
    audio  = sd.rec(frames, samplerate=SAMPLE_RATE,
                    channels=CHANNELS, dtype='float32')
    sd.wait()   # block until done
    return audio.flatten()

def show_level(audio):
    """Print a simple RMS level bar."""
    rms = np.sqrt(np.mean(audio**2))
    level = int(rms * 400)
    bar   = '█' * min(level, 40)
    color = 'LOW' if level < 5 else 'OK'
    print(f"  Level: [{bar:<40}] {color}")

def print_header(word, recorded, total):
    print(f"\n{'─'*50}")
    print(f"  WORD: {word.upper():<10}  Progress: {recorded}/{total}")
    print(f"{'─'*50}")

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print("\n" + "="*55)
    print("  Silent Input Assistant — Audio Data Collector")
    print("="*55)
    print(f"  Words     : {', '.join(VOCABULARY)}")
    print(f"  Target    : {SAMPLES_EACH} clips per word")
    print(f"  Duration  : {CLIP_SECONDS}s per clip")
    print(f"  Mode      : WHISPER (speak quietly!)")
    print("="*55)
    print("\n  TIP: Whisper each word clearly into the mic.")
    print("  Keep your face close to the mic for best results.\n")

    for word in VOCABULARY:
        recorded = count_existing(word)
        print(f"\n[ {word.upper()} ] — {recorded}/{SAMPLES_EACH} already recorded")

        if recorded >= SAMPLES_EACH:
            print("  Already complete. Skipping.")
            continue

        folder = os.path.join(OUTPUT_DIR, word)
        print_header(word, recorded, SAMPLES_EACH)

        while recorded < SAMPLES_EACH:
            remaining = SAMPLES_EACH - recorded
            print(f"\n  [{recorded+1:02d}/{SAMPLES_EACH}] Get ready to whisper: '{word.upper()}'")
            print(f"  Press ENTER to record  |  Type 's' + ENTER to skip word")

            try:
                user_input = input("  > ").strip().lower()
            except KeyboardInterrupt:
                print("\n\nExiting...")
                return

            if user_input == 's':
                print(f"  Skipping '{word}'.")
                break

            # Countdown
            for c in [3, 2, 1]:
                print(f"  {c}...", end=' ', flush=True)
                time.sleep(0.7)
            print("WHISPER NOW!")

            # Record
            audio = record_clip()
            show_level(audio)

            # Check if too quiet
            rms = np.sqrt(np.mean(audio**2))
            if rms < 0.001:
                print("  ⚠ Too quiet! No sound detected. Try again.")
                continue

            # Save
            filename = os.path.join(folder, f'{word}_{recorded+1:03d}.wav')
            sf.write(filename, audio, SAMPLE_RATE)
            recorded += 1
            print(f"  ✓ Saved ({recorded}/{SAMPLES_EACH})")

        print(f"\n  '{word.upper()}' complete!")

    print("\n" + "="*55)
    print("  All audio collected! Run script 3 to train models.")
    print("="*55 + "\n")

if __name__ == '__main__':
    main()
