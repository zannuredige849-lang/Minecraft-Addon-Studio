"""Original, synthesised sound effects for every creature, move and place in the add-on.

The film's own audio is copyrighted and is not used. These sounds are made from scratch (noise, resonators, formant
voices and struck-metal models) to fit what the film shows: giant breath and footfalls, bronze armour, wet bites, a
siren choir, a storm. Each recipe is a name "entity.short" that animations, controllers and the script refer to as
the sound id odyssey.<entity>.<short>.

    python3 -m tools.odyssey.sfx            # write RP/sounds/odyssey/*.ogg and RP/sounds/sound_definitions.json
"""
import hashlib
import json
import os
import subprocess
import sys

import numpy as np

from . import sfx_dsp as D
from .sfx_dsp import (N, SR, add, band, curve, echo, env, expdec, filt, finish, glottal, lp_sweep, mix, modal, noise,
                      reverb, sweep, thump, tt, vowel_filter)

RECIPES = {}


def recipe(key, cat="neutral", dist=(8, 48), variants=1, vol=1.0):
    def deco(fn):
        RECIPES[key] = dict(fn=fn, cat=cat, dist=dist, variants=variants, vol=vol)
        return fn
    return deco


# ------------------------------------------------------------------ building blocks
def voice(r, dur, pitch, vowels, scale=1.0, tilt=1.25, breath=0.05, rough=0.0, vib=(5.5, 0.0), shape=None, maxf=5200,
          drive=0):
    n = N(dur)
    f0 = curve(n, *pitch)
    x = glottal(f0, r, tilt=tilt, breath=breath, vib=vib, rough=rough, maxf=maxf)
    x = vowel_filter(x, vowels, scale)
    x = x * env(n, *(shape or [(0, 0), (0.06, 1), (dur * 0.7, 0.85), (dur, 0)]))
    if drive:
        x = np.tanh(x / (np.max(np.abs(x)) + 1e-9) * (1 + drive)) * 0.9
    return x


def whisper(r, dur, vowels, scale=1.0, syl=0.0, shape=None):
    n = N(dur)
    x = vowel_filter(noise(n, r), vowels, scale, floor=0.01)
    if syl:
        x = x * (0.55 + 0.45 * np.sin(2 * np.pi * syl * tt(n) + r.uniform(0, 6)) ** 2)
    return x * env(n, *(shape or [(0, 0), (0.15, 1), (dur - 0.2, 0.8), (dur, 0)]))


def whoosh(r, dur, f0, f1, width=0.7, tilt=0.0, peak=0.45, power=1.4):
    n = N(dur)
    return sweep(noise(n, r, tilt), f0, f1, width) * env(n, (0, 0), (dur * peak, 1), (dur, 0), power=power)


def grains(r, dur, count, flo, fhi, decay=0.5, start=0.0, size=0.012):
    """Falling stones, splinters or bone: short band-passed noise ticks that thin out over time."""
    n = N(dur)
    out = np.zeros(n)
    for _ in range(count):
        at = start + r.exponential(decay * 0.45)
        i = N(at)
        m = N(size * r.uniform(0.5, 1.6))
        if i + m >= n:
            continue
        g = band(noise(m, r), float(np.exp(r.uniform(np.log(flo), np.log(fhi)))), 0.45) * np.hanning(m)
        out[i:i + m] += g * np.exp(-at / decay) * r.uniform(0.35, 1.0) * 6
    return out


def pulse_train(r, dur, rate, jitter=0.3, width=0.5):
    n = N(dur)
    t = tt(n)
    ph = np.cumsum(rate * (1 + jitter * np.convolve(r.standard_normal(n), np.ones(900) / 900, mode="same") * 6)) / SR
    return (np.mod(ph, 1.0) < width).astype(float)


def splash(r, dur=1.2, hi=7000, lo=600):
    n = N(dur)
    body = lp_sweep(noise(n, r), hi, lo) * env(n, (0, 0), (0.03, 1), (dur * 0.5, 0.35), (dur, 0), power=1.3)
    drops = grains(r, dur, 36, 1800, 6000, decay=dur * 0.4, size=0.006) * 0.35
    return body + drops


def bubbles(r, dur, count, flo=300, fhi=1100):
    n = N(dur)
    out = np.zeros(n)
    for _ in range(count):
        at = r.uniform(0, dur * 0.9)
        m = N(r.uniform(0.03, 0.09))
        i = N(at)
        if i + m >= n:
            continue
        t = tt(m)
        f = r.uniform(flo, fhi) * (1 + 1.6 * t / (t[-1] + 1e-9))
        out[i:i + m] += np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.025) * r.uniform(0.3, 1)
    return out


def bronze(freqs=(1, 2.01, 2.76, 5.4, 8.93), base=440, decay=1.4, dur=2.4, r=None, amp=0.7):
    return modal([base * k for k in freqs], [decay / (1 + 0.55 * i) for i in range(len(freqs))],
                 [amp / (1 + 0.6 * i) for i in range(len(freqs))], dur, r, tick=0.1)


# ================================================================== Polyphemus (an 11-block giant: very low and slow)
@recipe("cyclops.step", "hostile", (14, 110), variants=3)
def _(r):
    a = thump(64, 26, 0.9, 0.28, r, click=0.35, lp=180, grit=0.15)
    rum = filt(noise(N(1.1), r, 1.5), hi=140) * expdec(N(1.1), 0.35)
    deb = grains(r, 0.9, 22, 600, 3000, decay=0.4, start=0.05) * 0.25
    return finish(reverb(mix([(0, a, 1), (0, rum, 1.3), (0.05, deb, 1)]), 0.7, 0.18, r, 2500), 0.95)


@recipe("cyclops.breath", "hostile", (10, 70), vol=0.7)
def _(r):
    n = N(2.6)
    inh = band(noise(n, r, 0.8), 380, 0.9) * env(n, (0, 0), (0.9, 1), (1.2, 0.25), (1.3, 0))
    exh = band(noise(n, r, 0.8), 260, 0.8) * env(n, (1.25, 0), (1.35, 0.2), (1.8, 0.9), (2.5, 0))
    low = glottal(curve(n, (0, 52), (2.6, 46)), r, tilt=1.6, breath=0, maxf=1500) * env(n, (1.2, 0), (1.8, 0.5), (2.5, 0))
    return finish(reverb(inh * 0.8 + exh + low * 0.3, 0.9, 0.2, r), 0.6)


@recipe("cyclops.snore", "hostile", (12, 80), vol=0.8)
def _(r):
    n = N(3.2)
    t = tt(n)
    flut = 0.55 + 0.45 * np.sin(2 * np.pi * 26 * t) ** 2
    inh = band(noise(n, r, 0.6), 300, 0.9) * flut * env(n, (0, 0), (0.5, 0.6), (1.2, 1), (1.4, 0))
    ex = vowel_filter(glottal(curve(n, (1.4, 52), (3.0, 40)), r, tilt=1.0, breath=0.3, rough=0.5, maxf=1800), [(0, "uh")], 0.7)
    ex = ex * (0.6 + 0.4 * np.sin(2 * np.pi * 19 * t)) * env(n, (1.4, 0), (1.7, 0.9), (2.6, 0.8), (3.1, 0))
    return finish(reverb(inh * 0.9 + ex * 1.2, 0.8, 0.15, r), 0.7)


@recipe("cyclops.hurt", "hostile", (16, 90))
def _(r):
    v = voice(r, 0.8, [(0, 95), (0.8, 62)], [(0, "a"), (1, "o")], 0.78, 1.1, 0.25, 0.4, maxf=2500, drive=0.83)
    return finish(reverb(v, 0.6, 0.15, r), 0.9)


@recipe("cyclops.death", "hostile", (16, 100))
def _(r):
    g = voice(r, 2.6, [(0, 90), (0.6, 78), (2.6, 34)], [(0, "a"), (0.5, "o"), (1, "u")], 0.78, 1.0, 0.3, 0.5,
              shape=[(0, 0), (0.1, 1), (1.6, 0.8), (2.6, 0)], maxf=2200, drive=0.55)
    fall = thump(52, 22, 1.4, 0.5, r, click=0.5, lp=150, grit=0.2)
    deb = grains(r, 1.4, 40, 500, 3000, decay=0.5) * 0.3
    return finish(reverb(mix([(0, g, 0.9), (2.3, fall, 1.2), (2.35, deb, 1)]), 1.3, 0.25, r, 3000), 0.95)


@recipe("cyclops.devour_grab", "hostile", (12, 80))
def _(r):
    w = whoosh(r, 0.6, 140, 650, 0.8, peak=0.55)
    g = voice(r, 0.35, [(0, 105), (0.35, 80)], [(0, "uh")], 0.78, 1.0, 0.3, 0.4, maxf=2200)
    return finish(mix([(0, w, 0.8), (0.3, g, 0.8)]), 0.85)


@recipe("cyclops.bite", "hostile", (10, 70), variants=2)
def _(r):
    crack = grains(r, 0.5, 14, 700, 3500, decay=0.12, size=0.01) * 0.8
    thud = thump(90, 45, 0.5, 0.14, r, click=0.3, lp=300)
    wet = band(noise(N(0.5), r), 500, 1.0) * expdec(N(0.5), 0.12) * 0.35
    return finish(reverb(crack + thud + wet, 0.5, 0.12, r), 0.9)


@recipe("cyclops.gulp", "hostile", (10, 60))
def _(r):
    a = thump(110, 60, 0.6, 0.18, r, click=0.1, lp=400)
    b = thump(95, 55, 0.5, 0.14, r, click=0.1, lp=350)
    wet = band(noise(N(0.9), r), 500, 1.0) * env(N(0.9), (0, 0), (0.1, 0.5), (0.5, 0.35), (0.9, 0)) * 0.3
    return finish(mix([(0, a, 1), (0.42, b, 0.8), (0, wet + bubbles(r, 0.9, 6, 120, 400) * 0.15, 1)]), 0.85)


@recipe("cyclops.kick_whoosh", "hostile", (12, 80))
def _(r):
    return finish(whoosh(r, 0.55, 140, 700, 0.8, peak=0.6), 0.85)


@recipe("cyclops.kick_hit", "hostile", (14, 90))
def _(r):
    h = thump(85, 38, 0.7, 0.2, r, click=0.5, lp=400, grit=0.5)
    c = grains(r, 0.4, 4, 1500, 4500, decay=0.08) * 0.6
    g = voice(r, 0.3, [(0, 120), (0.3, 80)], [(0, "uh")], 0.8, 1.0, 0.4, 0.3, maxf=2200)
    return finish(reverb(mix([(0, h, 1), (0, c, 0.7), (0.05, g, 0.5)]), 0.5, 0.12, r), 0.95)


@recipe("cyclops.stomp_boom", "hostile", (20, 128))
def _(r):
    b = thump(48, 20, 1.6, 0.55, r, click=0.5, lp=140, tau_f=0.1, grit=0.2)
    rum = filt(noise(N(2.0), r, 1.8), hi=110) * env(N(2.0), (0, 0), (0.05, 1), (1.0, 0.5), (2.0, 0))
    deb = grains(r, 1.5, 40, 500, 3200, decay=0.5, start=0.05) * 0.3
    return finish(reverb(mix([(0, b, 1), (0, rum, 1.4), (0.05, deb, 1)]), 1.4, 0.3, r, 2500), 1.0)


@recipe("cyclops.debris", "hostile", (10, 70))
def _(r):
    d = grains(r, 1.6, 70, 500, 3500, decay=0.5, size=0.014)
    low = filt(noise(N(1.6), r), hi=200) * expdec(N(1.6), 0.4) * 0.5
    return finish(d + low, 0.7)


@recipe("cyclops.rock_lift", "hostile", (12, 80))
def _(r):
    v = voice(r, 1.0, [(0, 68), (0.7, 92), (1.0, 88)], [(0, "uh"), (1, "a")], 0.78, 1.0, 0.35, 0.5, maxf=2200,
              shape=[(0, 0), (0.2, 0.8), (0.8, 1), (1.0, 0)])
    sc = sweep(noise(N(0.9), r), 250, 900, 0.9) * (0.4 + 0.6 * pulse_train(r, 0.9, 11, 0.5, 0.6))
    return finish(mix([(0, v, 0.9), (0.05, sc, 0.45)]), 0.85)


@recipe("cyclops.throw_grunt", "hostile", (14, 90))
def _(r):
    v = voice(r, 0.55, [(0, 150), (0.55, 105)], [(0, "a")], 0.8, 1.0, 0.3, 0.6, maxf=2400, drive=0.66)
    w = whoosh(r, 0.5, 300, 1500, 0.8, peak=0.5)
    return finish(reverb(mix([(0, v, 1), (0.1, w, 0.5)]), 0.5, 0.12, r), 0.9)


@recipe("cyclops.cry_voice", "hostile", (20, 110))
def _(r):
    n = 4.6
    v = voice(r, n, [(0, 110), (0.5, 170), (1.2, 235), (2.4, 190), (3.5, 150), (4.6, 100)],
              [(0, "a"), (0.25, "o"), (0.5, "a"), (0.8, "u")], 0.82, 1.15, 0.12, 0.25, vib=(5.2, 0.035), maxf=3000,
              shape=[(0, 0), (0.3, 0.7), (1.2, 1), (3.6, 0.8), (n, 0)])
    return finish(echo(reverb(v, 1.8, 0.35, r, 3500), [0.45], [0.25]), 0.95)


@recipe("cyclops.sob", "hostile", (10, 70))
def _(r):
    layers = []
    for i, g in enumerate((1.0, 0.8, 0.55)):
        p = voice(r, 0.5, [(0, 125 - i * 5), (0.5, 92)], [(0, "ae"), (1, "uh")], 0.8, 1.0, 0.3, 0.3, maxf=2400,
                  shape=[(0, 0), (0.05, 1), (0.25, 0.7), (0.5, 0)])
        layers.append((i * 0.55, p, g))
    return finish(reverb(mix(layers), 0.9, 0.2, r), 0.8)


@recipe("cyclops.hum", "neutral", (10, 70), vol=0.8)
def _(r):
    n = 2.6
    v = voice(r, n, [(0, 98), (0.75, 98), (0.85, 110), (1.45, 110), (1.55, 87), (2.6, 87)],
              [(0, "m"), (0.5, "u"), (1, "m")], 0.8, 1.4, 0.05, 0.1, vib=(4.8, 0.015), maxf=1800,
              shape=[(0, 0), (0.2, 0.8), (2.2, 0.8), (n, 0)])
    return finish(reverb(v, 0.8, 0.15, r), 0.6)


@recipe("cyclops.sniff", "hostile", (8, 50), vol=0.8)
def _(r):
    n = N(0.9)
    s = band(noise(n, r), 1800, 1.0) * (env(n, (0.04, 0), (0.12, 1), (0.28, 0)) + 0.8 * env(n, (0.42, 0), (0.52, 1), (0.74, 0)))
    low = filt(noise(n, r), hi=350) * env(n, (0.3, 0), (0.5, 0.3), (0.85, 0))
    return finish(s * 0.7 + low * 0.8, 0.6)


@recipe("cyclops.wake_groan", "hostile", (14, 90))
def _(r):
    v = voice(r, 2.4, [(0, 62), (0.8, 88), (1.6, 70), (2.4, 55)], [(0, "uh"), (0.4, "a"), (1, "o")], 0.8, 1.1, 0.3, 0.5,
              maxf=2200, shape=[(0, 0), (0.4, 0.8), (1.5, 1), (2.4, 0)])
    st = sweep(noise(N(1.4), r), 200, 700, 0.9) * env(N(1.4), (0, 0), (0.5, 0.5), (1.4, 0)) * 0.3
    return finish(reverb(mix([(0, v, 1), (0.3, st, 0.6)]), 1.0, 0.2, r), 0.85)


@recipe("cyclops.pain_roar", "hostile", (24, 128))
def _(r):
    v = voice(r, 2.8, [(0, 100), (0.3, 150), (1.2, 125), (2.8, 70)], [(0, "a"), (0.5, "o"), (1, "a")], 0.8, 0.9, 0.3, 0.9,
              maxf=2600, drive=1.65, shape=[(0, 0), (0.05, 1), (1.8, 0.9), (2.8, 0)])
    return finish(echo(reverb(v, 1.8, 0.35, r, 3500), [0.4], [0.3]), 1.0)


@recipe("cyclops.stake_pierce", "hostile", (10, 70))
def _(r):
    st = thump(120, 60, 0.4, 0.1, r, click=0.4, lp=600)
    sq = lp_sweep(noise(N(0.7), r), 2200, 300) * env(N(0.7), (0, 0), (0.03, 1), (0.7, 0)) * 0.6
    siz = filt(noise(N(1.4), r), 3500) * env(N(1.4), (0, 0), (0.1, 0.6), (1.4, 0)) * 0.3
    return finish(mix([(0, st, 1), (0, sq, 0.8), (0.05, siz, 0.7), (0, bubbles(r, 0.8, 6, 200, 700), 0.15)]), 0.9)


# ================================================================== Laestrygonians (armoured giants)
@recipe("laestrygonian.step", "hostile", (10, 64), variants=3)
def _(r):
    th = thump(95, 45, 0.5, 0.14, r, click=0.4, lp=500)
    mt = modal([680, 1530, 2480, 3900], [0.1, 0.07, 0.05, 0.035], [0.5, 0.35, 0.25, 0.15], 0.4, r)
    ch = grains(r, 0.3, 14, 3500, 9000, decay=0.12, size=0.004) * 0.25
    return finish(reverb(mix([(0, th, 1), (0.01, mt, 0.5), (0.02, ch, 1)]), 0.5, 0.1, r), 0.9)


@recipe("laestrygonian.breath", "hostile", (6, 40), vol=0.6)
def _(r):
    n = N(1.8)
    inh = band(noise(n, r, 0.5), 700, 0.7) * env(n, (0, 0), (0.55, 1), (0.8, 0))
    exh = band(noise(n, r, 0.5), 520, 0.7) * env(n, (0.85, 0), (0.95, 0.4), (1.25, 0.9), (1.75, 0))
    return finish(reverb(inh * 0.8 + exh, 0.35, 0.3, r, 3000), 0.5)


@recipe("laestrygonian.hurt", "hostile", (10, 60))
def _(r):
    v = voice(r, 0.6, [(0, 130), (0.6, 92)], [(0, "ae"), (1, "o")], 1.0, 1.1, 0.2, 0.4, drive=0.83)
    mt = modal([700, 1500, 2600], [0.12, 0.08, 0.05], [0.4, 0.3, 0.2], 0.4, r)
    return finish(mix([(0, v, 1), (0.0, mt, 0.35)]), 0.9)


@recipe("laestrygonian.death", "hostile", (12, 70))
def _(r):
    v = voice(r, 2.0, [(0, 120), (0.5, 95), (1.4, 55)], [(0, "a"), (1, "o")], 1.0, 1.0, 0.25, 0.5,
              shape=[(0, 0), (0.1, 1), (1.2, 0.7), (2.0, 0)], drive=0.55)
    layers = [(0, v, 1)]
    for i in range(6):
        at = 1.5 + r.uniform(0, 0.6)
        layers.append((at, modal(r.uniform(500, 900) * np.array([1, 2.1, 3.6, 6.2]), [0.18, 0.12, 0.08, 0.05],
                                 [0.5, 0.35, 0.25, 0.15], 0.5, r), r.uniform(0.3, 0.7)))
    layers.append((1.6, thump(80, 35, 0.8, 0.25, r, lp=400, grit=0.4), 1.0))
    return finish(reverb(mix(layers), 0.7, 0.15, r), 0.95)


@recipe("laestrygonian.slash_whoosh", "hostile", (8, 56))
def _(r):
    w = whoosh(r, 0.5, 500, 2600, 0.7, peak=0.5)
    return finish(mix([(0, w, 1), (0.25, modal([2600, 4700], [0.18, 0.1], [0.2, 0.1], 0.5, r, tick=0), 0.25)]), 0.85)


@recipe("laestrygonian.cleave_whoosh", "hostile", (8, 56))
def _(r):
    return finish(whoosh(r, 0.75, 250, 1900, 0.8, peak=0.5), 0.9)


@recipe("laestrygonian.blade_ring", "hostile", (8, 56))
def _(r):
    return finish(modal([1480, 2410, 3960, 5800], [0.9, 0.6, 0.35, 0.2], [0.6, 0.4, 0.3, 0.2], 1.7, r, tick=0.3), 0.8)


@recipe("laestrygonian.stab", "hostile", (8, 56))
def _(r):
    th = thump(120, 60, 0.3, 0.09, r, click=0.4, lp=600)
    wet = lp_sweep(noise(N(0.4), r), 1800, 300) * env(N(0.4), (0, 0), (0.02, 1), (0.4, 0)) * 0.5
    sh = modal([700, 1600], [0.15, 0.1], [0.4, 0.2], 0.4, r, tick=0)
    return finish(mix([(0, th, 1), (0, wet, 0.8), (0.03, sh, 0.35)]), 0.85)


@recipe("laestrygonian.thrust", "hostile", (8, 56))
def _(r):
    w = whoosh(r, 0.4, 400, 1500, 0.8, peak=0.7)
    g = voice(r, 0.25, [(0, 140), (0.25, 110)], [(0, "uh")], 1.0, 1.0, 0.3, 0.3)
    return finish(mix([(0, w, 0.9), (0.02, g, 0.7)]), 0.85)


@recipe("laestrygonian.fling", "hostile", (10, 64))
def _(r):
    v = voice(r, 0.9, [(0, 100), (0.7, 170), (0.9, 150)], [(0, "a"), (1, "o")], 1.0, 1.0, 0.3, 0.5, drive=0.66,
              shape=[(0, 0), (0.15, 1), (0.7, 1), (0.9, 0)])
    w = whoosh(r, 0.7, 200, 1400, 0.8, peak=0.55)
    return finish(mix([(0, v, 1), (0.25, w, 0.7)]), 0.9)


@recipe("laestrygonian.mace_slam", "hostile", (14, 96))
def _(r):
    th = thump(70, 30, 1.0, 0.3, r, click=0.5, lp=300, grit=0.5)
    mt = modal([320, 760, 1900, 3300], [0.4, 0.3, 0.2, 0.1], [0.5, 0.4, 0.3, 0.2], 0.8, r)
    deb = grains(r, 0.9, 30, 600, 3500, decay=0.35, start=0.04) * 0.3
    return finish(reverb(mix([(0, th, 1), (0, mt, 0.6), (0.04, deb, 1)]), 0.8, 0.2, r), 1.0)


@recipe("laestrygonian.boat_smash", "hostile", (16, 100))
def _(r):
    n = N(1.9)
    spl = grains(r, 1.9, 70, 300, 2500, decay=0.8, size=0.016)
    th = thump(95, 40, 0.8, 0.25, r, click=0.5, lp=400, grit=0.4)
    cr = filt(noise(n, r), 1000, 6000) * expdec(n, 0.07) * 0.8
    sp = splash(r, 1.4, 6000, 500)
    return finish(reverb(mix([(0, th, 1), (0, cr, 0.7), (0, spl, 0.9), (0.15, sp, 0.7)]), 0.8, 0.18, r), 1.0)


@recipe("laestrygonian.debris", "hostile", (8, 56))
def _(r):
    return finish(add(grains(r, 1.1, 45, 600, 3200, decay=0.4), thump(70, 40, 0.5, 0.15, r, lp=300) * 0.3), 0.7)


@recipe("laestrygonian.war_cry", "hostile", (24, 110))
def _(r):
    v = voice(r, 1.4, [(0, 120), (0.3, 190), (1.0, 150), (1.4, 100)], [(0, "a"), (0.6, "o")], 1.0, 1.0, 0.3, 0.6,
              drive=1.38, shape=[(0, 0), (0.05, 1), (1.0, 0.9), (1.4, 0)])
    return finish(echo(reverb(v, 1.0, 0.3, r), [0.35], [0.3]), 1.0)


# ------------------------------------------------------------------ the child
@recipe("laestrygonian_child.laugh", "neutral", (8, 40))
def _(r):
    layers = []
    for i in range(4):
        p = voice(r, 0.2, [(0, 400 - i * 25), (0.2, 340 - i * 25)], [(0, "a")], 1.15, 1.2, 0.2, 0.1,
                  shape=[(0, 0), (0.02, 1), (0.1, 0.7), (0.2, 0)])
        layers.append((i * 0.27, p, 1 - i * 0.12))
    return finish(reverb(mix(layers), 0.5, 0.15, r), 0.85)


@recipe("laestrygonian_child.scream", "neutral", (10, 56))
def _(r):
    v = voice(r, 1.4, [(0, 600), (0.2, 920), (0.9, 800), (1.4, 480)], [(0, "a"), (1, "e")], 1.2, 0.9, 0.25, 0.7, drive=1.1,
              shape=[(0, 0), (0.04, 1), (1.0, 0.9), (1.4, 0)])
    return finish(reverb(v, 0.6, 0.15, r), 0.9)


@recipe("laestrygonian_child.step", "neutral", (6, 32), variants=2)
def _(r):
    return finish(add(thump(140, 80, 0.18, 0.05, r, click=0.5, lp=700), grains(r, 0.2, 8, 3000, 8000, decay=0.06) * 0.15), 0.7)


# ================================================================== Circe
@recipe("circe.ladle", "neutral", (6, 32))
def _(r):
    layers = [(0.0, 0.5), (0.4, 0.4), (0.8, 0.45)]
    out = [(o, modal([620, 1180, 1740], [0.05, 0.035, 0.02], [0.6, 0.4, 0.3], 0.2, r), g) for o, g in layers]
    n = N(1.3)
    sw = band(noise(n, r), 700, 0.8) * env(n, (0, 0), (0.2, 0.5), (1.1, 0.4), (1.3, 0)) * 0.25
    return finish(mix(out + [(0, sw + bubbles(r, 1.3, 7, 300, 900) * 0.15, 1)]), 0.6)


@recipe("circe.murmur", "neutral", (8, 40))
def _(r):
    w = whisper(r, 2.2, [(0, "o"), (0.25, "e"), (0.5, "a"), (0.75, "u"), (1, "o")], 1.15, 5.5)
    return finish(reverb(w, 1.4, 0.35, r), 0.6)


@recipe("circe.scream", "neutral", (10, 56))
def _(r):
    v = voice(r, 1.5, [(0, 420), (0.25, 780), (1.1, 700), (1.5, 420)], [(0, "a"), (1, "i")], 1.18, 0.9, 0.2, 0.6, drive=1.1,
              shape=[(0, 0), (0.04, 1), (1.1, 0.9), (1.5, 0)])
    return finish(reverb(v, 0.7, 0.2, r), 0.9)


@recipe("circe.squelch", "neutral", (8, 40))
def _(r):
    n = N(1.2)
    sq = lp_sweep(noise(n, r), 900, 250) * (0.5 + 0.5 * np.sin(2 * np.pi * 9 * tt(n)) ** 2) * env(n, (0, 0), (0.1, 1), (1.2, 0))
    bl = thump(150, 70, 0.4, 0.1, r, click=0.1, lp=400)
    return finish(mix([(0, sq, 0.7), (0, bubbles(r, 1.2, 14, 200, 800), 0.4), (0.1, bl, 0.7)]), 0.7)


@recipe("circe.step", "neutral", (5, 24), variants=2, vol=0.7)
def _(r):
    return finish(add(thump(120, 70, 0.14, 0.04, r, click=0.6, lp=500), grains(r, 0.2, 6, 3000, 8000, decay=0.05) * 0.12), 0.5)


@recipe("circe_sister.chirp", "neutral", (6, 32), vol=0.8)
def _(r):
    out = []
    for i, o in enumerate((0.0, 0.18)):
        n = N(0.12)
        f = np.linspace(3200 + i * 300, 4900 + i * 200, n) * (1 + 0.04 * np.sin(2 * np.pi * 40 * tt(n)))
        out.append((o, np.sin(2 * np.pi * np.cumsum(f) / SR) * np.hanning(n), 1.0))
    return finish(mix(out), 0.6)


@recipe("circe_sister.screech", "neutral", (8, 40))
def _(r):
    n = N(0.9)
    f = curve(n, (0, 1800), (0.4, 2700), (0.9, 1900)) * (1 + 0.15 * np.sin(2 * np.pi * 60 * tt(n)))
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.5 * np.sign(np.sin(2 * np.pi * np.cumsum(f * 0.5) / SR))
    s = filt(s, 900, 7000) + 0.4 * band(noise(n, r), 2800, 0.6)
    return finish(s * env(n, (0, 0), (0.03, 1), (0.6, 0.8), (0.9, 0)), 0.8)


# ================================================================== Sirens
def _song(r, muffled=False):
    notes = [(330, 0.0, 1.5), (349, 1.4, 1.1), (440, 2.4, 1.9), (392, 4.2, 1.3), (349, 5.4, 1.1), (330, 6.4, 2.0)]
    total = 8.6
    n = N(total)
    out = np.zeros(n)
    for k, (mult, gain, vow) in enumerate(((1.0, 1.0, "a"), (1.2, 0.7, "o"), (0.5, 0.55, "o"), (1.5, 0.45, "a"))):
        pts = []
        for fq, st, du in notes:
            pts += [(max(0, st - 0.001), None), (st + 0.07, fq * mult), (st + du, fq * mult)]
        pts = [(t, v) for t, v in pts if v is not None]
        f = curve(n, *pts)
        g = glottal(f, r, tilt=1.1, breath=0.1, vib=(5.6 + k * 0.3, 0.014), maxf=4500)
        g = vowel_filter(g, [(0, vow), (0.4, "o"), (0.7, "a"), (1, "u")], 1.18)
        amp = np.zeros(n)
        for fq, st, du in notes:
            amp += env(n, (0, 0), (st, 0), (st + 0.18, 1), (st + du - 0.15, 0.85), (st + du + 0.25, 0), (total, 0))
        out += g * np.minimum(amp, 1.0) * gain * (0.9 + 0.1 * np.sin(2 * np.pi * (0.4 + 0.1 * k) * tt(n)))
    drone = glottal(curve(n, (0, 220), (total, 218)), r, tilt=1.5, breath=0.2, vib=(4.5, 0.01), maxf=2500)
    drone = vowel_filter(drone, [(0, "o")], 1.1) * env(n, (0, 0), (1, 0.5), (7, 0.5), (total, 0))
    out += 0.4 * drone
    out = reverb(out, 2.4, 0.5, r, 4000)
    if muffled:
        out = filt(out, hi=420, order=3) * 0.8
    return finish(out, 0.9 if not muffled else 0.55, fade_in=0.4, fade_out=0.8)


@recipe("siren.song", "ambient", (30, 72), vol=1.0)
def _(r):
    return _song(r)


@recipe("siren.song_muffled", "ambient", (6, 40), vol=1.0)
def _(r):
    return _song(r, True)


@recipe("siren.beckon_breath", "hostile", (6, 36), vol=0.9)
def _(r):
    w = whisper(r, 1.4, [(0, "u"), (0.35, "uh"), (0.7, "o"), (1, "m")], 1.15, 3.0, shape=[(0, 0), (0.2, 0.7), (1.1, 0.6), (1.4, 0)])
    h = voice(r, 1.3, [(0, 330), (1.3, 311)], [(0, "u"), (1, "o")], 1.18, 1.6, 0.3, 0.0, vib=(5.5, 0.02),
              shape=[(0, 0), (0.5, 0.25), (1.3, 0)])
    return finish(reverb(mix([(0, w, 0.9), (0.1, h, 0.4)]), 1.2, 0.35, r), 0.6)


@recipe("siren.drag_hiss", "hostile", (8, 44))
def _(r):
    n = N(1.7)
    hs = filt(noise(n, r), 3500) * (0.6 + 0.4 * np.sin(2 * np.pi * 7 * tt(n)) ** 2) * env(n, (0, 0), (0.2, 1), (1.4, 0.7), (1.7, 0))
    gr = voice(r, 1.4, [(0, 95), (1.4, 80)], [(0, "uh")], 1.0, 1.0, 0.3, 0.7, shape=[(0, 0), (0.3, 0.7), (1.0, 0.7), (1.4, 0)])
    gu = bubbles(r, 1.7, 10, 200, 700) * 0.25
    return finish(mix([(0, hs, 0.55), (0.1, gr, 0.5), (0, gu, 1)]), 0.75)


@recipe("siren.splash", "neutral", (8, 56))
def _(r):
    return finish(mix([(0, splash(r, 1.2, 7000, 600), 1), (0, thump(160, 70, 0.3, 0.08, r, click=0.1, lp=500), 0.5)]), 0.85)


# ================================================================== Scylla
@recipe("scylla.bite", "hostile", (12, 90))
def _(r):
    cr = grains(r, 0.6, 16, 600, 3500, decay=0.15, size=0.012)
    th = thump(110, 50, 0.5, 0.14, r, click=0.3, lp=350)
    wt = band(noise(N(0.6), r), 450, 1.0) * expdec(N(0.6), 0.14) * 0.5
    return finish(reverb(add(cr, th, wt), 0.6, 0.15, r), 0.95)


@recipe("scylla.chew", "hostile", (10, 70))
def _(r):
    out = []
    for o in (0.0, 0.22, 0.46, 0.68):
        out.append((o, grains(r, 0.25, 8, 500, 3000, decay=0.08) + band(noise(N(0.25), r), 700, 1.0) * expdec(N(0.25), 0.07) * 0.5, 1.0))
    return finish(mix(out), 0.8)


@recipe("scylla.hiss", "hostile", (12, 80), vol=0.8)
def _(r):
    n = N(2.4)
    t = tt(n)
    h = filt(noise(n, r), 2500, 11000) * (0.65 + 0.35 * np.sin(2 * np.pi * 11 * t + 1) ** 2) * env(n, (0, 0), (0.5, 1), (1.8, 0.8), (2.4, 0))
    g = glottal(curve(n, (0, 80), (2.4, 66)), r, tilt=1.2, breath=0, rough=0.9, maxf=1500) * env(n, (0, 0), (0.8, 0.5), (2.4, 0))
    return finish(reverb(h * 0.8 + g * 0.35, 0.8, 0.2, r), 0.7)


@recipe("scylla.rend", "hostile", (14, 100))
def _(r):
    n = N(1.9)
    tr = grains(r, 1.9, 90, 300, 3000, decay=0.7, size=0.018)
    sc = band(noise(n, r), 800, 1.0) * (0.4 + 0.6 * pulse_train(r, 1.9, 13, 0.6, 0.5)) * env(n, (0, 0), (0.1, 1), (1.2, 0.7), (1.9, 0)) * 0.5
    th = thump(90, 40, 0.8, 0.25, r, click=0.5, lp=350, grit=0.5)
    return finish(reverb(mix([(0, th, 1), (0, tr, 0.9), (0, sc, 0.8)]), 0.7, 0.15, r), 0.95)


@recipe("scylla.roar", "hostile", (20, 110))
def _(r):
    layers = []
    for k, m in enumerate((1.0, 1.06, 0.93)):
        layers.append((k * 0.04, voice(r, 2.4, [(0, 70 * m), (0.4, 105 * m), (1.6, 90 * m), (2.4, 55 * m)], [(0, "a"), (0.6, "o"), (1, "a")],
                                       0.85, 0.9, 0.3, 0.9, maxf=2600, drive=1.65,
                                       shape=[(0, 0), (0.06, 1), (1.6, 0.9), (2.4, 0)]), 0.8))
    return finish(echo(reverb(mix(layers), 1.4, 0.3, r, 3500), [0.3], [0.25]), 1.0)


@recipe("scylla.snatch_scream", "neutral", (16, 90))
def _(r):
    v = voice(r, 1.2, [(0, 300), (0.2, 520), (0.9, 450), (1.2, 260)], [(0, "a"), (1, "e")], 1.0, 0.9, 0.3, 0.7, drive=1.1,
              shape=[(0, 0), (0.04, 1), (0.9, 0.9), (1.2, 0)])
    return finish(reverb(v, 1.0, 0.3, r), 0.8)


# ================================================================== Charybdis
@recipe("charybdis.gulp", "hostile", (16, 100))
def _(r):
    n = N(1.8)
    th = thump(70, 30, 1.2, 0.35, r, click=0.2, lp=200)
    sw = lp_sweep(noise(n, r), 1500, 120) * env(n, (0, 0), (0.1, 1), (1.7, 0)) * 0.5
    return finish(reverb(mix([(0, th, 1), (0, sw, 0.8), (0, bubbles(r, 1.8, 18, 100, 500), 0.4)]), 1.0, 0.2, r), 0.95)


@recipe("charybdis.roar", "hostile", (20, 110), vol=0.9)
def _(r):
    n = N(4.2)
    t = tt(n)
    sw = band(noise(n, r, 1.0), 150, 1.2) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.7 * t)) * (0.75 + 0.25 * np.sin(2 * np.pi * 3.1 * t + 1))
    hi = band(noise(n, r), 900, 1.0) * 0.25 * (0.5 + 0.5 * np.sin(2 * np.pi * 1.3 * t) ** 2)
    return finish((sw + hi) * env(n, (0, 0), (0.8, 1), (3.3, 1), (4.2, 0)), 0.85, fade_in=0.5, fade_out=0.8)


@recipe("charybdis.surge", "hostile", (24, 128))
def _(r):
    n = N(6.0)
    s = lp_sweep(noise(n, r, 0.5), 250, 3200) * env(n, (0, 0), (2.8, 1), (4.0, 0.9), (6.0, 0)) * 1.0
    rum = filt(noise(n, r, 1.8), hi=130) * env(n, (0, 0), (2.5, 1), (6, 0))
    return finish(reverb(mix([(0, s, 0.9), (0, rum, 1.3), (0, bubbles(r, 6.0, 30, 100, 500), 0.2)]), 1.5, 0.25, r), 0.95, fade_in=0.2, fade_out=0.8)


# ================================================================== the dead
def _ghost(r, dur, pitch, vowels, breath=0.7, vib=0.04, wet=0.45):
    v = voice(r, dur, pitch, vowels, 1.1, 1.4, breath, 0.2, vib=(5.0, vib), shape=[(0, 0), (dur * 0.2, 1), (dur * 0.6, 0.8), (dur, 0)], maxf=3500)
    return reverb(v, 1.6, wet, r, 3500)


@recipe("shade.death", "neutral", (8, 44))
def _(r):
    return finish(_ghost(r, 1.6, [(0, 300), (1.6, 170)], [(0, "o"), (1, "u")]), 0.7)


@recipe("shade.grasp_moan", "hostile", (6, 36))
def _(r):
    return finish(_ghost(r, 1.5, [(0, 160), (0.6, 192), (1.5, 120)], [(0, "o"), (1, "uh")], 0.5, 0.03), 0.75)


@recipe("shade.hurt", "neutral", (6, 36))
def _(r):
    return finish(_ghost(r, 0.7, [(0, 200), (0.7, 150)], [(0, "a"), (1, "o")], 0.8, 0.02, 0.3), 0.65)


@recipe("shade.moan", "neutral", (6, 40), vol=0.7)
def _(r):
    return finish(_ghost(r, 3.4, [(0, 150), (1.5, 176), (3.4, 135)], [(0, "u"), (0.5, "o"), (1, "u")], 0.8, 0.03), 0.5)


def _rise(r, up=True):
    n = N(1.9)
    s = sweep(noise(n, r, 1.0), 120, 900, 0.9) if up else sweep(noise(n, r, 1.0), 900, 120, 0.9)
    sh = env(n, (0, 0), (1.2, 1), (1.9, 0)) if up else env(n, (0, 0), (0.05, 1), (1.9, 0))
    low = glottal(curve(n, (0, 60), (1.9, 70) if up else (1.9, 52)), r, tilt=1.5, breath=0, maxf=800) * sh * 0.35
    return s * sh + low


@recipe("shade.rise", "neutral", (8, 48))
def _(r):
    return finish(reverb(_rise(r), 1.2, 0.3, r), 0.7)


@recipe("shade.sink", "neutral", (8, 48))
def _(r):
    return finish(reverb(_rise(r, False), 1.2, 0.3, r), 0.7)


@recipe("shade.voice", "neutral", (8, 44), vol=0.9)
def _(r):
    v = voice(r, 2.8, [(0, 120), (1.0, 128), (1.8, 112), (2.8, 100)], [(0, "a"), (0.2, "e"), (0.4, "o"), (0.6, "i"), (0.8, "a"), (1, "o")],
              1.0, 1.3, 0.3, 0.3, vib=(4.0, 0.01), maxf=3000,
              shape=[(0, 0), (0.15, 0.9), (2.3, 0.8), (2.8, 0)])
    v = v * (0.55 + 0.45 * np.sin(2 * np.pi * 4.0 * tt(len(v)) + 0.5) ** 2)
    return finish(reverb(v, 1.4, 0.4, r), 0.6)


@recipe("shade.whispers", "ambient", (8, 40), vol=0.8)
def _(r):
    layers = []
    for k in range(5):
        layers.append((r.uniform(0, 3.0), whisper(r, r.uniform(1.8, 3.2), [(0, "o"), (0.3, "e"), (0.6, "u"), (1, "a")], 1.1 + 0.05 * k, r.uniform(3, 5.5)), 0.5))
    return finish(reverb(mix(layers, 6.0), 2.0, 0.5, r), 0.55, fade_in=0.5, fade_out=0.8)


@recipe("tiresias.rise", "neutral", (8, 48))
def _(r):
    return finish(reverb(_rise(r), 1.2, 0.3, r), 0.6)


@recipe("tiresias.sink", "neutral", (8, 48))
def _(r):
    return finish(reverb(_rise(r, False), 1.2, 0.3, r), 0.6)


@recipe("tiresias.voice", "neutral", (8, 44), vol=0.9)
def _(r):
    v = voice(r, 3.4, [(0, 100), (1.2, 108), (2.4, 92), (3.4, 84)], [(0, "o"), (0.2, "a"), (0.4, "e"), (0.6, "o"), (0.8, "uh"), (1, "a")],
              0.95, 1.0, 0.4, 0.5, vib=(3.5, 0.015), maxf=3000, shape=[(0, 0), (0.2, 0.9), (2.9, 0.8), (3.4, 0)])
    v = v * (0.5 + 0.5 * np.sin(2 * np.pi * 3.5 * tt(len(v))) ** 2)
    return finish(reverb(v, 1.2, 0.3, r), 0.6)


# ================================================================== the cattle of Apollo
@recipe("sun_cattle.chew", "neutral", (5, 28), vol=0.8)
def _(r):
    out = [(o, add(grains(r, 0.25, 7, 1500, 5000, decay=0.07) * 0.6, thump(110, 70, 0.2, 0.05, r, lp=400) * 0.5), 1) for o in (0, 0.28, 0.58)]
    return finish(mix(out), 0.5)


@recipe("sun_cattle.low", "neutral", (14, 80))
def _(r):
    v = voice(r, 1.8, [(0, 100), (0.4, 132), (1.0, 122), (1.8, 85)], [(0, "o"), (0.4, "u"), (0.8, "o")], 0.9, 1.5, 0.1, 0.2,
              vib=(5.0, 0.02), shape=[(0, 0), (0.15, 1), (1.3, 0.9), (1.8, 0)], maxf=2500)
    return finish(reverb(v, 0.7, 0.15, r), 0.85)


@recipe("sun_cattle.step", "neutral", (5, 32), variants=3, vol=0.8)
def _(r):
    h = modal([900, 1700], [0.03, 0.02], [0.5, 0.3], 0.15, r, tick=0.3)
    return finish(mix([(0, thump(100, 60, 0.12, 0.04, r, lp=300), 1), (0, h, 0.7)]), 0.6)


# ================================================================== Calypso and Athena
@recipe("calypso.lotus_chime", "neutral", (6, 36))
def _(r):
    out = []
    for i, f in enumerate((523, 784, 1047, 1568)):
        out.append((i * 0.12, modal([f, f * 2.01], [1.2, 0.6], [0.5, 0.15], 1.8, r, tick=0), 1.0 - i * 0.1))
    sh = band(noise(N(1.8), r), 5200, 0.4) * env(N(1.8), (0, 0), (0.4, 0.4), (1.8, 0)) * 0.06
    return finish(reverb(mix(out + [(0, sh, 1)]), 1.2, 0.4, r), 0.65)


@recipe("calypso.sigh", "neutral", (5, 28), vol=0.8)
def _(r):
    n = N(1.4)
    b = band(noise(n, r, 0.5), 900, 0.9) * env(n, (0, 0), (0.25, 1), (1.4, 0))
    v = voice(r, 1.3, [(0, 200), (1.3, 168)], [(0, "a"), (1, "uh")], 1.15, 1.6, 0.8, 0.0, shape=[(0, 0), (0.25, 0.4), (1.3, 0)])
    return finish(reverb(mix([(0, b, 1), (0, v, 0.3)]), 0.7, 0.25, r), 0.5)


@recipe("calypso.step", "neutral", (4, 20), variants=2, vol=0.6)
def _(r):
    return finish(add(thump(110, 60, 0.14, 0.04, r, click=0.6, lp=400), grains(r, 0.2, 10, 3000, 8000, decay=0.06) * 0.1), 0.45)


@recipe("athena.chime", "neutral", (8, 44))
def _(r):
    a = bronze((1, 1.5, 2, 3, 4), 880, 1.4, 2.6, r, 0.5)
    b = bronze((1, 1.5, 2, 3, 4), 1320, 1.2, 2.2, r, 0.5)
    return finish(reverb(mix([(0, a, 1), (0.35, b, 0.8)]), 1.4, 0.35, r), 0.7)


@recipe("athena.shimmer", "neutral", (8, 44), vol=0.9)
def _(r):
    n = N(2.8)
    t = tt(n)
    sh = np.zeros(n)
    for k in range(14):
        f0, f1 = r.uniform(1800, 3000), r.uniform(4500, 7000)
        f = f0 + (f1 - f0) * (t / t[-1]) ** 1.5
        sh += np.sin(2 * np.pi * np.cumsum(f) / SR + r.uniform(0, 6)) * (0.5 + 0.5 * np.sin(2 * np.pi * r.uniform(3, 8) * t + r.uniform(0, 6))) / 14
    ch = np.zeros(n)
    for f in (440, 554, 659):
        ch += vowel_filter(glottal(np.full(n, float(f)), r, tilt=1.3, breath=0.1, vib=(5.2, 0.012), maxf=4000), [(0, "a")], 1.15)
    e = env(n, (0, 0), (0.8, 1), (2.0, 0.8), (2.8, 0))
    return finish(reverb(sh * e * 0.7 + ch * e * 0.25, 1.4, 0.45, r), 0.65, fade_in=0.2)


@recipe("athena.step", "neutral", (4, 20), variants=2, vol=0.6)
def _(r):
    return finish(add(thump(150, 90, 0.12, 0.035, r, click=0.6, lp=900), grains(r, 0.15, 6, 3500, 9000, decay=0.04) * 0.1), 0.4)


# ================================================================== the Trojan Horse
@recipe("trojan_horse.creak", "neutral", (10, 60), vol=0.9)
def _(r):
    n = N(2.8)
    s = band(noise(n, r), 380, 0.25) * (0.3 + 0.7 * pulse_train(r, 2.8, 11, 0.6, 0.45)) * env(n, (0, 0), (0.5, 1), (2.2, 0.8), (2.8, 0))
    g = glottal(curve(n, (0, 58), (2.8, 64)), r, tilt=1.4, breath=0, rough=0.8, maxf=700) * env(n, (0, 0), (1.0, 0.5), (2.8, 0)) * 0.2
    return finish(reverb(s * 0.8 + g, 0.7, 0.2, r), 0.7)


@recipe("trojan_horse.hatch_open", "neutral", (10, 56))
def _(r):
    n = N(1.0)
    f = curve(n, (0, 700), (0.5, 940), (1.0, 780)) * (1 + 0.04 * np.sin(2 * np.pi * 50 * tt(n)))
    sq = (np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * 0.4 + np.sin(2 * np.pi * np.cumsum(f * 2) / SR) * 0.2)
    sq = filt(sq, 500, 4000) * (0.4 + 0.6 * pulse_train(r, 1.0, 14, 0.4, 0.55)) * env(n, (0, 0), (0.1, 1), (0.9, 0.7), (1.0, 0))
    cl = thump(160, 80, 0.4, 0.12, r, click=0.5, lp=500, grit=0.3)
    return finish(reverb(mix([(0, sq, 0.6), (0.85, cl, 1.0)]), 0.6, 0.15, r), 0.85)


@recipe("trojan_horse.shudder", "neutral", (12, 70))
def _(r):
    n = N(2.8)
    t = tt(n)
    rum = band(noise(n, r, 1.0), 180, 0.9) * (0.5 + 0.5 * np.sin(2 * np.pi * 14 * t) ** 2) * env(n, (0, 0), (0.3, 1), (2.2, 0.8), (2.8, 0))
    rat = grains(r, 2.8, 50, 300, 2500, decay=1.2, size=0.01) * 0.3
    return finish(reverb(rum + rat, 0.8, 0.2, r), 0.8)


# ================================================================== stones thrown, and the world
@recipe("boulder.whoosh", "hostile", (16, 100))
def _(r):
    n = N(1.5)
    return finish(sweep(noise(n, r, 0.5), 250, 1100, 1.0) * env(n, (0, 0), (0.7, 1), (1.5, 0), power=1.6), 0.7, fade_in=0.15)


@recipe("boulder.impact", "hostile", (20, 128))
def _(r):
    th = thump(58, 24, 1.4, 0.45, r, click=0.5, lp=220, grit=0.5)
    gr = grains(r, 1.8, 90, 500, 4500, decay=0.7, start=0.03) * 0.5
    sp = splash(r, 1.6, 6500, 500)
    return finish(reverb(mix([(0, th, 1), (0, gr, 0.9), (0.06, sp, 0.6)]), 1.0, 0.22, r), 1.0)


@recipe("world.storm", "weather", (30, 128), vol=1.0)
def _(r):
    n = N(7.0)
    t = tt(n)
    base = filt(noise(n, r, 1.5), hi=600) * (0.55 + 0.45 * np.sin(2 * np.pi * 0.35 * t + 1)) * env(n, (0, 0), (0.4, 1), (5.5, 0.7), (7.0, 0))
    cr = grains(r, 7.0, 6, 900, 3500, decay=2.2, size=0.05) * 0.5
    th = thump(60, 28, 1.8, 0.6, r, click=0.4, lp=220, grit=0.2)
    return finish(reverb(mix([(0, base, 1), (0.2, cr, 0.6), (0.5, th, 0.9), (3.1, th, 0.6)]), 2.2, 0.5, r, 3000), 0.95, fade_in=0.1, fade_out=1.0)


@recipe("world.arrive", "ambient", (16, 64), vol=1.0)
def _(r):
    n = N(5.0)
    dr = glottal(curve(n, (0, 55), (5.0, 55)), r, tilt=0.9, breath=0.05, vib=(0.3, 0.004), maxf=1200) * env(n, (0, 0), (1.5, 0.8), (3.5, 0.9), (5, 0))
    ch = np.zeros(n)
    for f in (165, 220, 247):
        g = vowel_filter(glottal(np.full(n, float(f)), r, tilt=1.2, breath=0.15, vib=(4.8, 0.012), maxf=3500), [(0, "o"), (1, "a")], 1.1)
        ch += g
    ch *= env(n, (0, 0), (2.0, 1), (3.6, 0.9), (5.0, 0))
    bl = bronze((1, 1.5, 2.01, 3.0), 110, 3.0, 5.0, r, 0.4)
    return finish(reverb(mix([(0, dr, 0.7), (0, ch, 0.28), (0.2, bl, 0.6)]), 2.2, 0.5, r, 3500), 0.85, fade_in=0.3, fade_out=1.0)


# ================================================================== writing the files
CATEGORY_DIR = "RP/sounds/odyssey"


def _encode(x, path):
    pcm = (np.clip(x, -1, 1) * 32767).astype("<i2").tobytes()
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "s16le", "-ar", str(SR), "-ac", "1", "-i", "pipe:0",
                    "-c:a", "libvorbis", "-q:a", "3", path], input=pcm, check=True)


def definitions():
    defs = {}
    for key, rec in sorted(RECIPES.items()):
        ent, short = key.split(".", 1)
        names = [f"sounds/odyssey/{ent}/{short}" + (f"_{i}" if rec["variants"] > 1 else "") for i in range(rec["variants"])]
        defs[f"odyssey.{key}"] = {
            "category": rec["cat"], "min_distance": float(rec["dist"][0]), "max_distance": float(rec["dist"][1]),
            "sounds": [{"name": nm, "volume": rec["vol"], "load_on_low_memory": True} for nm in names]}
    return {"format_version": "1.20.20", "sound_definitions": defs}


def write_all(root, force=False):
    base = os.path.join(root, CATEGORY_DIR)
    os.makedirs(base, exist_ok=True)
    src = open(__file__).read() + open(D.__file__).read()
    digest = hashlib.sha1(src.encode()).hexdigest()
    stamp = os.path.join(base, ".stamp")
    want = [(key, i) for key, rec in sorted(RECIPES.items()) for i in range(rec["variants"])]
    files = {}
    for key, i in want:
        ent, short = key.split(".", 1)
        suffix = f"_{i}" if RECIPES[key]["variants"] > 1 else ""
        files[(key, i)] = os.path.join(base, ent, f"{short}{suffix}.ogg")
    fresh = (not force and os.path.exists(stamp) and open(stamp).read() == digest and all(os.path.exists(p) for p in files.values()))
    if not fresh:
        for dirpath, _, names in os.walk(base):                  # drop stale files, never a directory tree
            for nm in names:
                if nm.endswith(".ogg"):
                    os.remove(os.path.join(dirpath, nm))
        for (key, i), path in files.items():
            os.makedirs(os.path.dirname(path), exist_ok=True)
            x = RECIPES[key]["fn"](D.rng_for(f"{key}#{i}"))
            assert np.all(np.isfinite(x)) and len(x) > 0, key
            _encode(x, path)
        with open(stamp, "w") as f:
            f.write(digest)
    out = os.path.join(root, "RP/sounds/sound_definitions.json")
    with open(out, "w") as f:
        json.dump(definitions(), f, indent=1)
        f.write("\n")
    return not fresh


if __name__ == "__main__":
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    did = write_all(root, force="--force" in sys.argv)
    total = sum(os.path.getsize(os.path.join(d, n)) for d, _, ns in os.walk(os.path.join(root, CATEGORY_DIR)) for n in ns if n.endswith(".ogg"))
    print(f"{len(RECIPES)} sound events, {'written' if did else 'up to date'}, {total // 1024} KB of audio")
