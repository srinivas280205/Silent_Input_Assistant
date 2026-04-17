"""
Script 1 — Video (Lip) Data Collector
======================================
Records 40 lip video clips per word using your webcam.
Each clip = 2 seconds at 30 FPS = 60 frames.

VOCABULARY: yes | no | help | water | pain | stop

HOW TO RUN:
    python scripts/1_collect_video.py

CONTROLS:
    SPACE  = start recording a clip
    Q      = quit current word, move to next
    ESC    = exit completely
"""

import cv2
import os
import time

# ── Config ────────────────────────────────────────────────────────────────────
VOCABULARY   = ['yes', 'no', 'help', 'water', 'pain', 'stop']
SAMPLES_EACH = 40          # clips per word
CLIP_SECONDS = 2           # duration of each clip
FPS          = 30          # frames per second
FRAME_W      = 640
FRAME_H      = 480
OUTPUT_DIR   = os.path.join(os.path.dirname(__file__), '..', 'data', 'videos')

# ── Helpers ───────────────────────────────────────────────────────────────────
def count_existing(word):
    folder = os.path.join(OUTPUT_DIR, word)
    os.makedirs(folder, exist_ok=True)
    return len([f for f in os.listdir(folder) if f.endswith('.mp4')])

def draw_overlay(frame, word, recorded, total, state, countdown=None):
    overlay = frame.copy()
    # dark top bar
    cv2.rectangle(overlay, (0, 0), (FRAME_W, 90), (20, 20, 20), -1)
    cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)

    # word
    cv2.putText(frame, f'WORD: {word.upper()}', (15, 32),
                cv2.FONT_HERSHEY_DUPLEX, 0.9, (255, 255, 255), 2)
    # progress
    cv2.putText(frame, f'{recorded}/{total} recorded', (15, 65),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (180, 180, 180), 1)

    if state == 'idle':
        msg = 'SPACE = record  |  Q = next word  |  ESC = exit'
        cv2.putText(frame, msg, (15, FRAME_H - 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.48, (100, 220, 100), 1)

    elif state == 'countdown' and countdown is not None:
        txt = f'Get ready... {countdown}'
        cv2.putText(frame, txt, (FRAME_W//2 - 120, FRAME_H//2),
                    cv2.FONT_HERSHEY_DUPLEX, 1.2, (0, 220, 255), 3)

    elif state == 'recording':
        # red pulsing dot
        cv2.circle(frame, (FRAME_W - 30, 30), 12, (0, 0, 255), -1)
        cv2.putText(frame, 'REC', (FRAME_W - 75, 38),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        cv2.putText(frame, f'Say: {word.upper()}', (FRAME_W//2 - 80, FRAME_H//2),
                    cv2.FONT_HERSHEY_DUPLEX, 1.1, (0, 255, 120), 2)

    elif state == 'saved':
        cv2.putText(frame, 'SAVED!', (FRAME_W//2 - 60, FRAME_H//2),
                    cv2.FONT_HERSHEY_DUPLEX, 1.4, (0, 255, 0), 3)

    return frame

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  FRAME_W)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_H)
    cap.set(cv2.CAP_PROP_FPS, FPS)

    if not cap.isOpened():
        print("ERROR: Cannot open webcam. Check camera connection.")
        return

    print("\n" + "="*55)
    print("  Silent Input Assistant — Video Data Collector")
    print("="*55)
    print(f"  Words     : {', '.join(VOCABULARY)}")
    print(f"  Target    : {SAMPLES_EACH} clips per word")
    print(f"  Clip len  : {CLIP_SECONDS}s at {FPS} FPS")
    print("="*55 + "\n")

    for word in VOCABULARY:
        recorded = count_existing(word)
        print(f"\n[ {word.upper()} ] — {recorded}/{SAMPLES_EACH} already recorded")

        if recorded >= SAMPLES_EACH:
            print(f"  Already complete. Skipping.")
            continue

        print(f"  Press SPACE to start each clip. Q to skip word.")
        folder = os.path.join(OUTPUT_DIR, word)

        while recorded < SAMPLES_EACH:
            # ── Idle: wait for SPACE ──────────────────────────────────────
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                frame = draw_overlay(frame, word, recorded, SAMPLES_EACH, 'idle')
                cv2.imshow('Lip Data Collector', frame)
                key = cv2.waitKey(1) & 0xFF
                if key == ord(' '):
                    break
                if key == ord('q') or key == ord('Q'):
                    print(f"  Skipping word '{word}'")
                    goto_next = True
                    break
                if key == 27:  # ESC
                    print("\nExiting...")
                    cap.release()
                    cv2.destroyAllWindows()
                    return
            else:
                continue
            if 'goto_next' in dir() and goto_next:
                del goto_next
                break

            # ── 1-second countdown ────────────────────────────────────────
            for c in [3, 2, 1]:
                t_end = time.time() + 1.0
                while time.time() < t_end:
                    ret, frame = cap.read()
                    if not ret:
                        break
                    frame = draw_overlay(frame, word, recorded, SAMPLES_EACH, 'countdown', c)
                    cv2.imshow('Lip Data Collector', frame)
                    cv2.waitKey(1)

            # ── Record clip ───────────────────────────────────────────────
            filename = os.path.join(folder, f'{word}_{recorded+1:03d}.mp4')
            fourcc   = cv2.VideoWriter_fourcc(*'mp4v')
            writer   = cv2.VideoWriter(filename, fourcc, FPS, (FRAME_W, FRAME_H))

            total_frames = CLIP_SECONDS * FPS
            frame_count  = 0
            t_start      = time.time()

            while frame_count < total_frames:
                ret, frame = cap.read()
                if not ret:
                    break
                writer.write(frame)
                display = draw_overlay(frame.copy(), word, recorded, SAMPLES_EACH, 'recording')
                cv2.imshow('Lip Data Collector', display)
                cv2.waitKey(1)
                frame_count += 1

            writer.release()
            recorded += 1

            # ── Saved flash ───────────────────────────────────────────────
            t_end = time.time() + 0.5
            while time.time() < t_end:
                ret, frame = cap.read()
                if ret:
                    frame = draw_overlay(frame, word, recorded, SAMPLES_EACH, 'saved')
                    cv2.imshow('Lip Data Collector', frame)
                    cv2.waitKey(1)

            print(f"  [{recorded:02d}/{SAMPLES_EACH}] Saved: {filename}")

        print(f"  '{word.upper()}' complete!")

    cap.release()
    cv2.destroyAllWindows()
    print("\n" + "="*55)
    print("  All words collected! Run script 2 for audio next.")
    print("="*55 + "\n")

if __name__ == '__main__':
    main()
