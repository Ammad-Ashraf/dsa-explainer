"""Synthesize a calm, minimal music bed for the launch video (no samples, so no licensing questions).

Soft detuned pads, a plucked arpeggio, a warm sub and, from the second section, a gentle pulse.
Usage: python music.py <seconds> <out.wav>
"""
import sys
import wave

import numpy as np

SR = 48000
BPM = 96
BEAT = 60 / BPM
BAR = 4 * BEAT

# I - vi - IV - V in D major, with colour tones (maj7, 9)
CHORDS = [
    [50, 57, 61, 64, 66],  # Dmaj9-ish: D A C# E F#
    [47, 54, 57, 62, 66],  # Bm7: B F# A D F#
    [43, 50, 54, 57, 62],  # Gmaj7: G D F# A D
    [45, 52, 57, 61, 64],  # A6sus: A E A C# E
]


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def lowpass(x, cutoff):
    # one-pole, run twice for a softer slope
    a = np.exp(-2 * np.pi * cutoff / SR)
    for _ in range(2):
        y = np.empty_like(x)
        acc = 0.0
        for i in range(len(x)):  # chunks are short, this is fine
            acc = (1 - a) * x[i] + a * acc
            y[i] = acc
        x = y
    return x


def env(n, attack, release):
    e = np.ones(n)
    a = int(attack * SR)
    r = int(release * SR)
    if a:
        e[:a] = np.linspace(0, 1, a) ** 2
    if r:
        e[-r:] *= np.linspace(1, 0, r) ** 2
    return e


def pad(notes, seconds):
    n = int(seconds * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for m in notes:
        for det in (-0.07, 0.0, 0.07):
            f = hz(m) * 2 ** (det / 12)
            ph = np.random.rand() * 2 * np.pi
            # a soft "saw" from a few harmonics
            out += sum(np.sin(2 * np.pi * f * k * t + ph * k) / k ** 1.6 for k in range(1, 6))
    out /= len(notes) * 3
    return out * env(n, 1.2, 1.4)


def pluck(m, seconds=1.6):
    n = int(seconds * SR)
    t = np.arange(n) / SR
    f = hz(m)
    tone = (np.sin(2 * np.pi * f * t)
            + 0.35 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t * 6)
            + 0.12 * np.sin(2 * np.pi * 3 * f * t) * np.exp(-t * 9))
    return tone * np.exp(-t * 3.2) * env(n, 0.004, 0.05)


def kick():
    n = int(0.35 * SR)
    t = np.arange(n) / SR
    f = 48 + 70 * np.exp(-t * 28)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 11)


def tick():
    n = int(0.06 * SR)
    noise = np.random.randn(n)
    hp = noise - np.concatenate([[0], noise[:-1]])
    return hp * np.exp(-np.arange(n) / SR * 70) * 0.18


def main(total, path):
    rng = np.random.default_rng(7)
    np.random.seed(7)
    n = int(total * SR)
    L = np.zeros(n + SR * 3)
    R = np.zeros(n + SR * 3)

    def add(sig, at, gain=1.0, pan=0.0):
        i = int(at * SR)
        j = min(len(L), i + len(sig))
        sig = sig[: j - i] * gain
        L[i:j] += sig * np.sqrt(0.5 * (1 - pan))
        R[i:j] += sig * np.sqrt(0.5 * (1 + pan))

    bars = int(np.ceil(total / BAR)) + 1
    # one rendered pad per chord, reused (with a long overlap for smooth changes)
    pads = [lowpass(pad(c, BAR + 1.6), 1400) for c in CHORDS]
    for b in range(bars):
        chord = CHORDS[b % 4]
        at = b * BAR
        add(pads[b % 4], at, 0.34, pan=-0.15)
        # sub on beat 1
        sub_n = int(BAR * SR)
        ts = np.arange(sub_n) / SR
        add(np.sin(2 * np.pi * hz(chord[0] - 12) * ts) * env(sub_n, 0.08, 0.6), at, 0.22)
        # arpeggio from bar 2 on: eighth notes over the upper chord tones
        if b >= 1:
            pattern = [2, 3, 4, 3, 1, 3, 4, 2]
            for k, idx in enumerate(pattern):
                m = chord[idx] + 12
                vel = 0.13 if k % 2 == 0 else 0.09
                add(pluck(m), at + k * BEAT / 2 + rng.uniform(0, 0.008), vel, pan=0.35 if k % 2 else -0.25)
        # a gentle pulse from bar 5 to the last two bars
        if 4 <= b < bars - 3:
            for beat in range(4):
                if beat in (0, 2):
                    add(kick(), at + beat * BEAT, 0.32)
                add(tick(), at + beat * BEAT + BEAT / 2, 1.0, pan=0.3)

    mix = np.stack([L, R])[:, :n]
    # simple stereo "room": a couple of short delays
    for d, g in ((0.031, 0.18), (0.047, 0.14), (0.113, 0.08)):
        k = int(d * SR)
        mix[0, k:] += g * mix[1, :-k]
        mix[1, k:] += g * mix[0, :-k]
    fade_in, fade_out = int(1.5 * SR), int(4.0 * SR)
    mix[:, :fade_in] *= np.linspace(0, 1, fade_in)
    mix[:, -fade_out:] *= np.linspace(1, 0, fade_out) ** 1.5
    mix /= np.max(np.abs(mix)) * 1.12
    data = (mix.T * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())


if __name__ == "__main__":
    main(float(sys.argv[1]), sys.argv[2])
