#!/usr/bin/env python3
"""Generate a royalty-free background track from code (no samples, no AI, no cost).

A soft chord pad plus a plucked arpeggio, then ffmpeg adds reverb and loudness
normalization. Every track is our own, so it is safe on any channel.

Usage:
  make_music.py OUT.m4a [--seconds 40] [--bpm 96] [--key C] [--mood calm|bright|focus] [--seed 1]

Standard library + ffmpeg only.
"""

import argparse
import math
import os
import random
import struct
import subprocess
import tempfile
import wave

RATE = 32000
NOTE = {"C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11}

# Chords as semitone offsets from the key root; progressions per mood.
MOODS = {
    "calm":   [[0, 4, 7, 11], [9, 12, 16, 19], [5, 9, 12, 16], [7, 11, 14, 17]],   # Imaj7 vi7 IVmaj7 V
    "bright": [[0, 4, 7, 14], [7, 11, 14, 19], [9, 12, 16, 21], [5, 9, 12, 19]],   # I V vi IV (add9)
    "focus":  [[9, 12, 16, 19], [5, 9, 12, 16], [0, 4, 7, 11], [7, 11, 14, 17]],   # vi IV I V
    # bright chords plus a pulse: eighth-note bass, soft kick on 1 and 3, light off-beat hats.
    # Energetic but smooth (no drops, no heavy four-on-the-floor).
    "upbeat": [[0, 4, 7, 14], [7, 11, 14, 19], [9, 12, 16, 21], [5, 9, 12, 19]],
}


def freq(semi_from_a4):
    return 440.0 * 2 ** (semi_from_a4 / 12)


def render(seconds, bpm, key, mood, seed):
    rnd = random.Random(seed)
    n = int(seconds * RATE)
    out = [0.0] * n
    beat = 60.0 / bpm
    bar = beat * 4
    prog = MOODS[mood]
    root = NOTE[key] - 9 - 12  # semitones from A4 to the key root in octave 3

    # Pad: each chord lasts one bar, crossfaded; sines with slight detune.
    bars = int(math.ceil(seconds / bar))
    for b in range(bars):
        chord = prog[b % len(prog)]
        start, end = b * bar, (b + 1) * bar + 0.6
        i0, i1 = int(start * RATE), min(n, int(end * RATE))
        for semi in chord:
            for det in (-0.07, 0.07):
                w = 2 * math.pi * freq(root + semi + det)
                ph = rnd.random() * 6.28
                for i in range(i0, i1):
                    t = i / RATE - start
                    env = min(1.0, t / 0.6) * min(1.0, (end - start - t) / 0.6)
                    out[i] += 0.035 * env * math.sin(w * t + ph)

    # Arpeggio: eighth notes walking up the chord (one node after another).
    step = beat / 2
    steps = int(seconds / step)
    for s in range(steps):
        chord = prog[int(s * step / bar) % len(prog)]
        semi = chord[s % len(chord)] + 12
        if rnd.random() < 0.15:
            continue  # leave space so it breathes
        w = 2 * math.pi * freq(root + semi)
        i0 = int(s * step * RATE)
        length = int(0.9 * RATE)
        for k in range(length):
            i = i0 + k
            if i >= n:
                break
            t = k / RATE
            env = math.exp(-t * 6) * min(1.0, t / 0.004)
            out[i] += 0.09 * env * (math.sin(w * t) + 0.25 * math.sin(2 * w * t))

    if mood == "upbeat":
        # Bass: chord root, two octaves down, eighth notes, accent on the beat.
        for s8 in range(int(seconds / step)):
            chord = prog[int(s8 * step / bar) % len(prog)]
            w = 2 * math.pi * freq(root + chord[0] - 12)
            i0 = int(s8 * step * RATE)
            amp = 0.11 if s8 % 2 == 0 else 0.07
            for k in range(int(step * 0.9 * RATE)):
                i = i0 + k
                if i >= n:
                    break
                t = k / RATE
                env = min(1.0, t / 0.005) * math.exp(-t * 5)
                out[i] += amp * env * (math.sin(w * t) + 0.3 * math.sin(2 * w * t))
        # Kick on beats 1 and 3 (skip the first bar so the track eases in).
        for bt in range(4, int(seconds / beat)):
            if bt % 2:
                continue
            i0 = int(bt * beat * RATE)
            ph = 0.0
            for k in range(int(0.22 * RATE)):
                i = i0 + k
                if i >= n:
                    break
                t = k / RATE
                f = 50 + 70 * math.exp(-t * 30)
                ph += 2 * math.pi * f / RATE
                out[i] += 0.30 * math.exp(-t * 14) * math.sin(ph)
        # Hats on the off-beat eighths: short high-passed noise.
        for s8 in range(8, int(seconds / step)):
            if s8 % 2 == 0:
                continue
            i0 = int(s8 * step * RATE)
            prev = 0.0
            for k in range(int(0.05 * RATE)):
                i = i0 + k
                if i >= n:
                    break
                x = rnd.uniform(-1, 1)
                out[i] += 0.035 * math.exp(-k / RATE * 70) * (x - prev)
                prev = x

    # Fade in/out so loops and cuts never click.
    fade = int(1.0 * RATE)
    for i in range(fade):
        g = i / fade
        out[i] *= g
        out[n - 1 - i] *= g
    peak = max(abs(x) for x in out) or 1.0
    return [x / peak * 0.8 for x in out]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--seconds", type=float, default=40)
    ap.add_argument("--bpm", type=float, default=96)
    ap.add_argument("--key", default="C", choices=NOTE)
    ap.add_argument("--mood", default="calm", choices=MOODS)
    ap.add_argument("--seed", type=int, default=1)
    a = ap.parse_args()
    samples = render(a.seconds, a.bpm, a.key, a.mood, a.seed)
    with tempfile.TemporaryDirectory() as d:
        raw = os.path.join(d, "dry.wav")
        with wave.open(raw, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(RATE)
            w.writeframes(b"".join(struct.pack("<h", int(x * 32767)) for x in samples))
        subprocess.run([
            "ffmpeg", "-v", "error", "-y", "-i", raw,
            "-af", "aecho=0.8:0.7:60|140|260:0.35|0.25|0.15,lowpass=f=7000,"
                   "aformat=channel_layouts=stereo,loudnorm=I=-18:TP=-2",
            "-ar", "44100", "-c:a", "aac", "-b:a", "160k", a.out,
        ], check=True)
    print(a.out)


if __name__ == "__main__":
    main()
