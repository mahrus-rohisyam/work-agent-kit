#!/usr/bin/env python3
"""Voice-over by local TTS (Kokoro, Apache-2.0, CPU, no cost), with an optional ASMR / whisper treatment.

  tools/.venv-tts/bin/python tools/make_voice.py OUT.wav "First phrase." "Second phrase." \
      [--voice af_nicole] [--speed 0.85] [--gap 0.35] [--asmr 0.65]

Each text argument is one phrase; phrases are joined with --gap seconds of silence.
--asmr is the share of whispered sound (0 = plain voice, 1 = pure whisper). The whisper is made by LPC:
the voice's spectral envelope driven by noise instead of the vocal cords, blended with the soft original
so words stay clear. Then close-mic warmth, de-ess, short room.

The voice is synthetic. Do not present it as a real person, and label it where a platform asks
for AI-generated content.
"""
import argparse
import os
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
MODELS = os.path.join(HERE, "tts-models")


def lpc(frame, order):
    r = np.correlate(frame, frame, "full")[len(frame) - 1: len(frame) + order]
    if r[0] <= 1e-9:
        return np.zeros(order + 1), 0.0
    a = np.zeros(order + 1); a[0] = 1.0; e = r[0]
    for i in range(1, order + 1):
        k = -(r[i] + np.dot(a[1:i], r[i - 1:0:-1])) / e
        a[1:i + 1] = a[1:i + 1] + k * np.concatenate([a[i - 1:0:-1], [1.0]])
        e *= 1 - k * k
    return a, e


def whisper(x, sr, order=18, seed=0):
    rnd = np.random.default_rng(seed)
    win, hop = int(0.025 * sr), int(0.0125 * sr)
    w = np.hanning(win)
    out = np.zeros(len(x) + win)
    pre = np.append(x[0], x[1:] - 0.94 * x[:-1])          # pre-emphasis
    for start in range(0, len(x) - win, hop):
        fr = pre[start:start + win] * w
        a, e = lpc(fr, order)
        if e <= 0:
            continue
        g = np.sqrt(e / win)
        exc = rnd.standard_normal(win) * g
        y = np.zeros(win)                                  # all-pole synthesis 1/A(z)
        for n in range(win):
            acc = exc[n]
            for k in range(1, min(order, n) + 1):
                acc -= a[k] * y[n - k]
            y[n] = acc
        out[start:start + win] += y * w
    out = out[: len(x)]
    for i in range(1, len(out)):                           # de-emphasis
        out[i] += 0.94 * out[i - 1]
    return out / (np.max(np.abs(out)) + 1e-9) * np.max(np.abs(x))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("phrases", nargs="+")
    ap.add_argument("--voice", default="af_nicole")
    ap.add_argument("--speed", type=float, default=0.85)
    ap.add_argument("--gap", type=float, default=0.35)
    ap.add_argument("--asmr", type=float, default=0.65)
    a = ap.parse_args()

    from kokoro_onnx import Kokoro
    import soundfile as sf
    tts = Kokoro(os.path.join(MODELS, "kokoro-v1.0.onnx"), os.path.join(MODELS, "voices-v1.0.bin"))
    parts, sr = [], 24000
    for i, p in enumerate(a.phrases):
        y, sr = tts.create(p, voice=a.voice, speed=a.speed, lang="en-us")
        nz = np.nonzero(np.abs(y) > 0.01)[0]                  # trim TTS silence
        y = y[max(0, nz[0] - int(0.03 * sr)): nz[-1] + int(0.12 * sr)] if len(nz) else y
        parts.append(y)
        if i < len(a.phrases) - 1:
            parts.append(np.zeros(int(a.gap * sr)))
    x = np.concatenate(parts).astype(np.float64)

    if a.asmr > 0:
        wh = whisper(x, sr)
        x = (1 - a.asmr) * x * 0.8 + a.asmr * wh
    tmp = a.out + ".dry.wav"
    sf.write(tmp, x / (np.max(np.abs(x)) + 1e-9) * 0.8, sr)
    # close-mic warmth, gentle de-ess, soft compression, short room; mono to stereo
    af = ("highpass=f=70,lowshelf=g=3:f=180,equalizer=f=6500:t=q:w=2:g=-5,highshelf=g=-2:f=11000,"
          "acompressor=threshold=-22dB:ratio=3:attack=5:release=120,"
          "aecho=0.9:0.5:28|52:0.18|0.10,loudnorm=I=-18:TP=-2,aformat=channel_layouts=stereo")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-af", af, "-ar", "44100", a.out], check=True)
    os.remove(tmp)
    print(a.out, f"{len(x) / sr:.2f}s")


if __name__ == "__main__":
    sys.exit(main())
