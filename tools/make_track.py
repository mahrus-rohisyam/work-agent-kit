#!/usr/bin/env python3
"""Upbeat marketing track, made by code (numpy + ffmpeg, no samples, no models, no cost).

Groove pop/house: four-on-the-floor kick, claps on 2 and 4, off-beat open hats, 16th shakers,
off-beat plucked bass, syncopated detuned-saw chord stabs, a pumping pad (sidechain to the kick),
a pluck lead hook, risers, snare rolls and crashes. The arrangement is a list of sections in bars, so
drops can be placed on scene changes of a video.

  make_track.py OUT.m4a [--bpm 120] [--key F] [--seed 1] [--plan tour]

Plans live in PLANS below; "tour" is a 78 s arrangement at 120 BPM. Add one per video length.
"""
import argparse
import os
import subprocess
import tempfile
import wave

import numpy as np

SR = 44100
NOTE = {"C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11}

# vi IV I V in the key (pop, lifts without sounding sad). Degrees as semitones from the tonic.
PROG = [(9, "m"), (5, ""), (0, ""), (7, "")]

# Sections: (bars, name). Elements per section are chosen in render().
PLANS = {
    # 78 s tour: opener 0-4 s, groove to 36 s, build, drop at 40 s, chill 50-64 s, build, drop at 66 s, outro
    "tour": [(2, "intro"), (8, "groove"), (8, "groove_lead"), (2, "build"), (5, "drop"),
             (7, "chill"), (1, "build_short"), (5, "drop"), (1, "outro_hit"), (1, "tail")],
}


def hz(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)


def chord_notes(root_midi, quality):
    third = 3 if quality == "m" else 4
    return [root_midi, root_midi + third, root_midi + 7]


def saw(freq, t, bright):
    """Band-limited saw by additive harmonics; `bright` (array or scalar, 0..1) closes the 'filter'."""
    out = np.zeros_like(t)
    nmax = int(min(40, (SR / 2) / freq))
    for k in range(1, nmax + 1):
        w = (1.0 / k) * np.exp(-(k - 1) * (1.0 - bright) * 0.9)
        out += w * np.sin(2 * np.pi * freq * k * t)
    return out * 0.6


def env_adsr(n, a, d, s, r, hold):
    """n samples; a/d/r in seconds; hold = note length in seconds before release."""
    t = np.arange(n) / SR
    e = np.where(t < a, t / max(a, 1e-4), 0.0)
    dec = (t >= a) & (t < a + d)
    e = np.where(dec, 1 - (1 - s) * (t - a) / max(d, 1e-4), e)
    e = np.where((t >= a + d) & (t < hold), s, e)
    rel = t >= hold
    e = np.where(rel, s * np.exp(-(t - hold) / max(r, 1e-4)), e)
    return e


class Mix:
    def __init__(self, seconds):
        self.n = int(seconds * SR) + SR * 2
        self.bus = {k: np.zeros((2, self.n)) for k in ("drums", "bass", "music", "fx")}

    def add(self, bus, start_s, sig, pan=0.0, gain=1.0):
        i0 = int(start_s * SR)
        if i0 >= self.n:
            return
        sig = sig[: self.n - i0]
        l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
        self.bus[bus][0, i0:i0 + len(sig)] += sig * gain * l * 1.41
        self.bus[bus][1, i0:i0 + len(sig)] += sig * gain * r * 1.41


def fft_filter(x, lo, hi):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    X[(f < lo) | (f > hi)] = 0
    return np.fft.irfft(X, len(x))


def reverb(x, seconds=1.6, mix=0.25, rnd=None):
    """Convolution with decaying stereo noise (cheap plate)."""
    rnd = rnd or np.random.default_rng(0)
    n = int(seconds * SR)
    t = np.arange(n) / SR
    out = np.copy(x)
    for ch in range(2):
        ir = rnd.standard_normal(n) * np.exp(-t * 4.5 / seconds)
        ir = fft_filter(ir, 200, 7000)
        ir /= np.sqrt(np.sum(ir ** 2))
        m = len(x[ch]) + n - 1
        size = 1 << (m - 1).bit_length()
        wet = np.fft.irfft(np.fft.rfft(x[ch], size) * np.fft.rfft(ir, size), size)[: len(x[ch])]
        out[ch] = x[ch] * (1 - mix) + wet * mix
    return out


def render(bpm, key, seed, plan):
    rnd = np.random.default_rng(seed)
    beat = 60.0 / bpm
    bar = beat * 4
    s16 = beat / 4
    sections = PLANS[plan]
    total_bars = sum(b for b, _ in sections)
    seconds = total_bars * bar + 2.5
    mx = Mix(seconds)
    tonic = 48 + NOTE[key] - (12 if NOTE[key] > 6 else 0)  # around C3..F#3

    # ── instruments ───────────────────────────────────────────────────────────
    def kick(t0, g=1.0):
        n = int(0.4 * SR); t = np.arange(n) / SR
        f = 45 + 110 * np.exp(-t * 38)
        ph = 2 * np.pi * np.cumsum(f) / SR
        body = np.sin(ph) * np.exp(-t * 11)
        click = rnd.standard_normal(n) * np.exp(-t * 400) * 0.25
        mx.add("drums", t0, np.tanh((body + click * 1.6) * 1.6) * 0.62, gain=g)

    def clap(t0, g=1.0):
        n = int(0.35 * SR); t = np.arange(n) / SR
        e = np.zeros(n)
        for d in (0.0, 0.011, 0.022):
            e += np.where(t >= d, np.exp(-(t - d) * 60), 0)
        e += np.exp(-t * 14) * 0.5
        sig = fft_filter(rnd.standard_normal(n), 900, 6000) * e
        mx.add("drums", t0, sig * 0.5, pan=0.05, gain=g)

    def hat(t0, open_=False, g=1.0, pan=0.25):
        n = int((0.25 if open_ else 0.06) * SR); t = np.arange(n) / SR
        sig = fft_filter(rnd.standard_normal(n), 7000, 16000) * np.exp(-t * (14 if open_ else 90))
        mx.add("drums", t0, sig * (0.35 if open_ else 0.22), pan=pan, gain=g)

    def snare(t0, g=1.0):
        n = int(0.2 * SR); t = np.arange(n) / SR
        sig = fft_filter(rnd.standard_normal(n), 1500, 9000) * np.exp(-t * 28) + np.sin(2 * np.pi * 190 * t) * np.exp(-t * 30) * 0.5
        mx.add("drums", t0, sig * 0.45, gain=g)

    def crash(t0, g=1.0):
        n = int(2.2 * SR); t = np.arange(n) / SR
        sig = fft_filter(rnd.standard_normal(n), 4000, 15000) * np.exp(-t * 2.2)
        mx.add("fx", t0, sig * 0.22, pan=-0.2, gain=g)
        mx.add("fx", t0, fft_filter(rnd.standard_normal(n), 4000, 15000) * np.exp(-t * 2.2) * 0.22, pan=0.2, gain=g)

    def riser(t0, dur, g=1.0):
        n = int(dur * SR); t = np.arange(n) / SR
        noise = rnd.standard_normal(n)
        # rising band: split into chunks with increasing low cut
        out = np.zeros(n); chunk = SR // 20
        for i in range(0, n, chunk):
            p = i / n
            seg = noise[i:i + chunk]
            out[i:i + chunk] = fft_filter(seg, 300 + 6000 * p, 2000 + 12000 * p) if len(seg) > 64 else 0
        sig = out * (t / dur) ** 2 * 0.5
        mx.add("fx", t0, sig, pan=-0.3, gain=g); mx.add("fx", t0, sig, pan=0.3, gain=g * 0.8)

    def bass(t0, midi, length, g=1.0):
        n = int((length + 0.05) * SR); t = np.arange(n) / SR
        e = env_adsr(n, 0.004, 0.12, 0.55, 0.03, length)
        bright = 0.25 + 0.5 * np.exp(-t * 18)
        sig = saw(hz(midi), t, bright) * 0.9 + np.sin(2 * np.pi * hz(midi - 12) * t) * 0.2
        mx.add("bass", t0, np.tanh(sig * e * 1.4) * 0.4, gain=g)

    def stab(t0, notes, length, g=1.0, bright_top=0.85):
        n = int((length + 0.25) * SR); t = np.arange(n) / SR
        e = env_adsr(n, 0.003, 0.18, 0.35, 0.12, length)
        bright = 0.2 + (bright_top - 0.2) * np.exp(-t * 14)
        for i, m in enumerate(notes):
            for det, pan in ((-0.12, -0.6), (0.0, 0.0), (0.12, 0.6)):
                sig = saw(hz(m + det), t + rnd.random() * 0.01, bright) * e
                mx.add("music", t0, sig * 0.11, pan=pan, gain=g)

    def pad(t0, notes, length, g=1.0, bright=0.35):
        n = int((length + 0.6) * SR); t = np.arange(n) / SR
        e = env_adsr(n, 0.25, 0.3, 0.8, 0.4, length)
        for m in notes:
            for det, pan in ((-0.08, -0.7), (0.08, 0.7)):
                mx.add("music", t0, saw(hz(m + det), t, bright) * e * 0.06, pan=pan, gain=g)

    def pluck(t0, midi, g=1.0):
        n = int(0.5 * SR); t = np.arange(n) / SR
        e = np.exp(-t * 7) * np.minimum(1, t / 0.003)
        bright = 0.3 + 0.65 * np.exp(-t * 20)
        sig = saw(hz(midi), t, bright) * 0.7 + np.sin(2 * np.pi * hz(midi + 12) * t) * 0.15
        mx.add("music", t0, sig * e * 0.5, pan=0.15, gain=g)
        mx.add("fx", t0 + beat * 0.75, sig * e * 0.12, pan=-0.4, gain=g)  # dotted-8th echo

    def conga(t0, high=True, slap=False, g=1.0):
        n = int(0.3 * SR); t = np.arange(n) / SR
        f0 = (330 if high else 220) * (1 + 0.25 * np.exp(-t * 60))
        ph = 2 * np.pi * np.cumsum(f0) / SR
        body = np.sin(ph) * np.exp(-t * (16 if not slap else 30))
        skin = fft_filter(rnd.standard_normal(n), 1500, 6000) * np.exp(-t * (90 if not slap else 45)) * (0.3 if not slap else 0.7)
        mx.add("drums", t0, (body + skin) * 0.32, pan=0.35 if high else 0.2, gain=g)

    def shaker(t0, g=1.0):
        n = int(0.09 * SR); t = np.arange(n) / SR
        e = np.minimum(1, t / 0.012) * np.exp(-t * 45)        # soft attack: shaken, not hit
        mx.add("drums", t0, fft_filter(rnd.standard_normal(n), 5000, 12000) * e * 0.2, pan=-0.45, gain=g)

    def tambourine(t0, g=1.0):
        n = int(0.18 * SR); t = np.arange(n) / SR
        jingle = fft_filter(rnd.standard_normal(n), 6000, 14000) * (0.6 + 0.4 * np.sin(2 * np.pi * 38 * t))
        mx.add("drums", t0, jingle * np.exp(-t * 22) * 0.22, pan=-0.3, gain=g)

    def clave(t0, g=1.0):
        n = int(0.12 * SR); t = np.arange(n) / SR
        sig = (np.sin(2 * np.pi * 2500 * t) + 0.4 * np.sin(2 * np.pi * 3700 * t)) * np.exp(-t * 55)
        mx.add("drums", t0, sig * 0.12, pan=0.5, gain=g)

    conga_pat = [(3, True, False), (6, False, False), (7, True, True), (10, True, False), (11, True, False), (14, False, False), (15, True, True)]
    clave_pat = ([0, 6, 12], [4, 8])                # 3-2 son clave over two bars, in 16ths

    # Hook: two bars of 16th steps (index, scale degree offset from chord root, or None).
    hook = [(0, 12), (3, 10), (6, 7), (8, 12), (10, 14), (14, 12),
            (16, 7), (19, 9), (22, 12), (24, 14), (27, 16), (30, 14)]
    stab_rhythm = [0, 3, 6, 10, 12, 14]          # 3-3-4-2-2 syncopation per bar, in 16ths
    sc_times = []                                # kick times for sidechain

    # ── arrangement ───────────────────────────────────────────────────────────
    b0 = 0
    for nbars, name in sections:
        for bi in range(nbars):
            gb = b0 + bi
            t_bar = gb * bar
            root, q = PROG[gb % 4]
            croot = tonic + root
            notes = chord_notes(croot + 12, q)
            last_of_section = bi == nbars - 1
            full = name in ("groove", "groove_lead", "drop")
            if name == "intro":
                pad(t_bar, notes, bar, g=0.9, bright=0.2 + 0.1 * bi)
                for s in stab_rhythm:
                    stab(t_bar + s * s16, notes, s16 * 1.5, g=0.5, bright_top=0.35 + 0.15 * bi)
                for i in range(8):
                    hat(t_bar + i * beat / 2 + beat / 2 * (i % 2), g=0.5)
                if bi == nbars - 1:
                    for i in range(16):
                        shaker(t_bar + i * s16, g=0.35 if i % 2 else 0.2)
                    riser(t_bar, bar)
                    for i in range(4):
                        kick(t_bar + i * beat, g=0.6); sc_times.append(t_bar + i * beat)
            elif full or name in ("chill",):
                for i in range(4):
                    if name == "chill" and i % 2:   # half-time feel under the chat demo
                        continue
                    kick(t_bar + i * beat, g=1.0 if full else 0.8); sc_times.append(t_bar + i * beat)
                if full:
                    clap(t_bar + beat); clap(t_bar + 3 * beat)
                else:
                    clap(t_bar + 2 * beat, g=0.7)
                for i in range(16):
                    v = (0.55 if i % 4 == 2 else 0.3) if full else 0.22
                    hat(t_bar + i * s16, g=v, pan=0.3 if i % 2 else 0.15)
                if full:
                    for i in range(4):
                        hat(t_bar + i * beat + beat / 2, open_=True, g=0.6, pan=-0.2)
                # percussion layer: shaker always, congas and clave from the hook sections on, tambourine in drops
                for i in range(16):
                    shaker(t_bar + i * s16, g=(0.9 if i % 2 else 0.5) * (1.0 if full else 0.7))
                if name in ("groove_lead", "drop", "chill"):
                    for st, hi, sl in conga_pat:
                        conga(t_bar + st * s16, high=hi, slap=sl, g=1.0 if full else 0.8)
                    for st in clave_pat[gb % 2]:
                        clave(t_bar + st * s16, g=0.9)
                if name == "drop":
                    for i in range(4):
                        tambourine(t_bar + i * beat + beat / 2)
                # bass: off-beat 8ths, octave pop on the last one
                for i in range(4):
                    m = croot - 12 + (12 if (i == 3 and full) else 0)
                    bass(t_bar + i * beat + beat / 2, m, beat / 2 * 0.85, g=1.0 if full else 0.75)
                pad(t_bar, notes, bar, g=0.7 if full else 1.0, bright=0.3 if full else 0.4)
                if full or name == "chill":
                    for s in stab_rhythm:
                        stab(t_bar + s * s16, notes, s16 * 1.4, g=0.9 if full else 0.45, bright_top=0.9 if full else 0.5)
                if name in ("groove_lead", "drop"):
                    off = (gb % 2) * 16
                    for st, deg in hook:
                        if off <= st < off + 16:
                            pluck(t_bar + (st - off) * s16, croot + deg if name == "drop" else croot + deg - 12 + 12)
                if bi == 0 and name in ("groove", "drop"):
                    crash(t_bar)
                if name == "groove" and last_of_section:
                    for i in range(4):
                        snare(t_bar + 3 * beat + i * s16, g=0.4 + 0.15 * i)
            elif name in ("build", "build_short"):
                n16 = 16
                for i in range(n16):
                    dens = 1 if (name == "build_short" or bi == nbars - 1) else (2 if i % 2 == 0 else 0)
                    if dens:
                        snare(t_bar + i * s16, g=0.25 + 0.6 * (bi * 16 + i) / (nbars * 16))
                for i in range(4):
                    kick(t_bar + i * beat, g=0.7); sc_times.append(t_bar + i * beat)
                pad(t_bar, notes, bar, g=0.9, bright=0.3 + 0.3 * (bi + 1) / nbars)
                for s in stab_rhythm:
                    stab(t_bar + s * s16, notes, s16 * 1.3, g=0.6, bright_top=0.4 + 0.4 * (bi + 1) / nbars)
                if bi == 0:
                    riser(t_bar, bar * nbars)
            elif name == "outro_hit":
                crash(t_bar)
                kick(t_bar); sc_times.append(t_bar)
                stab(t_bar, notes, beat * 1.5, g=1.0)
                bass(t_bar, croot - 12, beat * 1.5)
                pad(t_bar, chord_notes(tonic + 12, ""), bar * 2, g=1.0, bright=0.4)
                pluck(t_bar + beat * 2, tonic + 24, g=0.8)
            elif name == "tail":
                pass
        b0 += nbars

    # ── mix ───────────────────────────────────────────────────────────────────
    n = mx.n
    t = np.arange(n) / SR
    duck = np.ones(n)
    for k in sc_times:
        i0 = int(k * SR); i1 = min(n, i0 + int(beat * SR))
        tt = t[i0:i1] - k
        duck[i0:i1] = np.minimum(duck[i0:i1], 1 - 0.65 * np.exp(-tt * 9))
    music = reverb(mx.bus["music"] * duck, 1.8, 0.28, rnd)
    bassb = mx.bus["bass"] * (0.35 + 0.65 * duck)
    fx = reverb(mx.bus["fx"], 2.2, 0.35, rnd)
    out = mx.bus["drums"] * 0.95 + bassb * 0.9 + music * 2.0 + fx * 1.0
    for ch in range(2):
        X = np.fft.rfft(out[ch]); f = np.fft.rfftfreq(out.shape[1], 1 / SR)
        g = np.where(f < 35, (f / 35) ** 2, 1.0) * (1 + 0.6 / (1 + np.exp(-(f - 3000) / 600)))
        out[ch] = np.fft.irfft(X * g, out.shape[1])
    out = np.tanh(out * 1.2) / np.tanh(1.2)          # gentle glue / saturation
    out = out[:, : int(seconds * SR)]
    fade = int(0.02 * SR)
    out[:, :fade] *= np.linspace(0, 1, fade)
    tail = int(2.0 * SR)
    out[:, -tail:] *= np.linspace(1, 0, tail) ** 2
    return out / (np.max(np.abs(out)) + 1e-9) * 0.9


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--bpm", type=float, default=120)
    ap.add_argument("--key", default="F", choices=NOTE)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--plan", default="tour", choices=PLANS)
    a = ap.parse_args()
    x = render(a.bpm, a.key, a.seed, a.plan)
    with tempfile.TemporaryDirectory() as d:
        raw = os.path.join(d, "mix.wav")
        with wave.open(raw, "wb") as w:
            w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
            w.writeframes((x.T * 32767).astype("<i2").tobytes())
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-af", "loudnorm=I=-14:TP=-1.5:LRA=9",
                        "-ar", "44100", "-c:a", "aac", "-b:a", "192k", a.out], check=True)
    print(a.out)


if __name__ == "__main__":
    main()
