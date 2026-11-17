"""A small numpy-only toolkit for the add-on's original, synthesised sound effects.

Everything works on mono float arrays at SR. Filters run in the frequency domain (zero phase), which is fine for the
noise textures and short events used here; time-varying filters use a windowed overlap-add.
"""
import hashlib

import numpy as np

SR = 32000

VOWELS = {  # adult male F1, F2, F3
    "a": (730, 1090, 2440), "o": (570, 840, 2410), "u": (300, 870, 2240), "e": (530, 1840, 2480),
    "i": (270, 2290, 3010), "ae": (660, 1720, 2410), "m": (250, 1000, 2200), "uh": (520, 1190, 2390),
}


def rng_for(key):
    return np.random.default_rng(int.from_bytes(hashlib.sha1(key.encode()).digest()[:4], "big"))


def N(dur):
    return int(round(dur * SR))


def tt(n):
    return np.arange(n) / SR


def env(n, *points, power=1.0):
    """Piecewise-linear envelope through (seconds, level) points."""
    e = np.interp(np.arange(n), [p[0] * SR for p in points], [p[1] for p in points])
    return e ** power if power != 1.0 else e


def expdec(n, tau, delay=0.0):
    t = tt(n) - delay
    return np.where(t < 0, 0.0, np.exp(-np.maximum(t, 0) / tau))


def noise(n, r, tilt=0.0):
    """White noise; tilt 1 = pink, 2 = brown."""
    x = r.standard_normal(n)
    if tilt:
        X = np.fft.rfft(x)
        f = np.maximum(np.fft.rfftfreq(n, 1 / SR), 20.0)
        x = np.fft.irfft(X * f ** (-tilt / 2), n)
    return x / (np.max(np.abs(x)) + 1e-9)


def filt(x, lo=None, hi=None, order=4):
    """Zero-phase high-pass at lo and/or low-pass at hi."""
    n = len(x)
    f = np.maximum(np.fft.rfftfreq(n, 1 / SR), 1e-3)
    g = np.ones_like(f)
    if lo:
        g /= np.sqrt(1 + (lo / f) ** (2 * order))
    if hi:
        g /= np.sqrt(1 + (f / hi) ** (2 * order))
    return np.fft.irfft(np.fft.rfft(x) * g, n)


def band(x, fc, width=0.5):
    """Band-pass: gaussian in log frequency, `width` in octaves (1 sigma)."""
    n = len(x)
    f = np.maximum(np.fft.rfftfreq(n, 1 / SR), 1.0)
    g = np.exp(-0.5 * (np.log2(f / fc) / width) ** 2)
    return np.fft.irfft(np.fft.rfft(x) * g, n)


def _frames(x, hop, fn):
    n = len(x)
    win = np.hanning(2 * hop + 1)[:-1]
    out = np.zeros(n + 2 * hop)
    f = np.fft.rfftfreq(2 * hop, 1 / SR)
    for i in range(0, n, hop):
        seg = x[i:i + 2 * hop]
        if len(seg) < 2 * hop:
            seg = np.pad(seg, (0, 2 * hop - len(seg)))
        out[i:i + 2 * hop] += np.fft.irfft(np.fft.rfft(seg * win) * fn(i / max(n - 1, 1), f), 2 * hop)
    return out[:n]


def sweep(x, f0, f1, width=0.6, hop=512):
    """Band-pass whose centre glides geometrically from f0 to f1 over the signal."""
    def fn(fr, f):
        fc = f0 * (f1 / f0) ** fr
        return np.exp(-0.5 * (np.log2(np.maximum(f, 1.0) / fc) / width) ** 2)
    return _frames(x, hop, fn)


def lp_sweep(x, f0, f1, hop=512, order=2):
    def fn(fr, f):
        fc = f0 * (f1 / f0) ** fr
        return 1 / np.sqrt(1 + (f / fc) ** (2 * order))
    return _frames(x, hop, fn)


def vowel_formants(spec, scale=1.0):
    """spec: a vowel name or (F1, F2, F3) -> list of (freq, bandwidth, gain)."""
    f = VOWELS[spec] if isinstance(spec, str) else spec
    return [(f[0] * scale, 90 + 0.05 * f[0], 1.0), (f[1] * scale, 110 + 0.06 * f[1], 0.55), (f[2] * scale, 160, 0.3)]


def vowel_filter(x, keys, scale=1.0, hop=256, floor=0.04):
    """Time-varying formant filter. keys: [(fraction_of_time, vowel)] interpolated linearly in between."""
    ks = sorted(keys, key=lambda k: k[0])
    fm = [np.array(vowel_formants(v, scale)) for _, v in ks]
    ts = [k[0] for k in ks]

    def fn(fr, f):
        j = max(0, min(len(ts) - 2, int(np.searchsorted(ts, fr) - 1))) if len(ts) > 1 else 0
        if len(ts) == 1:
            cur = fm[0]
        else:
            a = 0.0 if ts[j + 1] == ts[j] else min(1.0, max(0.0, (fr - ts[j]) / (ts[j + 1] - ts[j])))
            cur = fm[j] * (1 - a) + fm[j + 1] * a
        h = np.full_like(f, floor)
        for fc, bw, g in cur:
            h += g / (1 + ((f - fc) / (bw / 2)) ** 2)
        return h
    return _frames(x, hop, fn)


def curve(n, *points):
    """A control curve (Hz, level...) through (seconds, value) points, smoothed."""
    c = np.interp(np.arange(n), [p[0] * SR for p in points], [p[1] for p in points])
    k = max(3, int(0.012 * SR))
    return np.convolve(np.pad(c, (k, k), mode="edge"), np.ones(k) / k, mode="same")[k:-k]


def glottal(f0, r, tilt=1.25, jitter=0.004, vib=(5.5, 0.0), breath=0.04, maxf=5200, rough=0.0):
    """A voiced source with a falling harmonic spectrum. f0: Hz array (one per sample)."""
    n = len(f0)
    t = tt(n)
    wob = np.convolve(r.standard_normal(n), np.ones(int(0.03 * SR)) / (0.03 * SR), mode="same") * jitter * 6
    f = f0 * (1 + wob + vib[1] * np.sin(2 * np.pi * vib[0] * t))
    if rough:
        f = f * (1 + rough * np.sin(2 * np.pi * 37 * t + 1.3) * 0.5)
    ph = 2 * np.pi * np.cumsum(f) / SR
    nh = int(min(maxf, SR / 2.2) / max(float(np.min(f0)), 40.0))
    out = np.zeros(n)
    for h in range(1, nh + 1):
        amp = 1.0 / h ** tilt
        out += amp * np.sin(h * ph + r.uniform(0, 6.28))
    out /= np.max(np.abs(out)) + 1e-9
    if breath:
        out = out + breath * filt(noise(n, r), 300, 6000)
    return out


def thump(f0, f1, dur, decay, r, click=0.25, lp=260, tau_f=0.06, grit=0.0):
    """Low impact: a sine falling from f0 to f1 plus a low-passed noise burst."""
    n = N(dur)
    t = tt(n)
    f = f1 + (f0 - f1) * np.exp(-t / tau_f)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / decay)
    burst = filt(noise(n, r), hi=lp) * np.exp(-t / (decay * 0.55)) * click * 3
    out = body + burst
    if grit:
        out += grit * filt(noise(n, r), 900, 5000) * np.exp(-t / 0.02)
    return out


def modal(freqs, decays, amps, dur, r, tick=0.15, detune=0.0015):
    """Struck metal: decaying sinusoids (inharmonic) plus a short tick."""
    n = N(dur)
    t = tt(n)
    out = np.zeros(n)
    for fq, d, a in zip(freqs, decays, amps):
        out += a * np.sin(2 * np.pi * fq * (1 + r.uniform(-detune, detune)) * t + r.uniform(0, 6.28)) * np.exp(-t / d)
    out += tick * filt(noise(n, r), 1500, 9000) * np.exp(-t / 0.004)
    return out


def reverb(x, rt60=1.2, wet=0.25, r=None, damp=4500):
    r = r or np.random.default_rng(1)
    n = N(rt60 * 1.1)
    ir = noise(n, r) * np.exp(-6.9 * tt(n) / rt60)
    ir = filt(ir, hi=damp, order=2)
    ir[:int(0.012 * SR)] *= np.linspace(0, 1, int(0.012 * SR))
    m = len(x) + n
    y = np.fft.irfft(np.fft.rfft(x, m) * np.fft.rfft(ir, m), m)
    y = y / (np.max(np.abs(y)) + 1e-9) * np.max(np.abs(x))
    out = np.zeros(m)
    out[:len(x)] += (1 - wet) * x
    out += wet * y
    return out


def echo(x, delays, gains):
    out = np.zeros(len(x) + N(max(delays)))
    out[:len(x)] += x
    for d, g in zip(delays, gains):
        out[N(d):N(d) + len(x)] += g * x
    return out


def add(*xs):
    """Sum arrays of different lengths (shorter ones are padded with silence)."""
    out = np.zeros(max(len(x) for x in xs))
    for x in xs:
        out[:len(x)] += x
    return out


def mix(layers, total=None):
    """layers: [(offset_seconds, signal, gain)]"""
    end = max(N(o) + len(s) for o, s, _ in layers)
    out = np.zeros(max(end, N(total or 0)))
    for o, s, g in layers:
        out[N(o):N(o) + len(s)] += g * s
    return out


def finish(x, peak=0.9, fade_in=0.004, fade_out=0.03, trim=True):
    """Remove DC, fade the edges, normalise to `peak`, soft-clip the top."""
    x = np.asarray(x, float)
    x = x - np.mean(x)
    if trim:
        e = np.abs(x)
        idx = np.nonzero(e > 0.002 * (np.max(e) + 1e-9))[0]
        if len(idx):
            x = x[:idx[-1] + 1]
    fi, fo = min(N(fade_in), len(x) // 2), min(N(fade_out), len(x) // 2)
    if fi:
        x[:fi] *= np.linspace(0, 1, fi)
    if fo:
        x[-fo:] *= np.linspace(1, 0, fo) ** 1.5
    x = x / (np.max(np.abs(x)) + 1e-9)
    return np.tanh(x * 1.4) / np.tanh(1.4) * min(peak, 0.97)


def resample(x, ratio):
    """Pitch/speed change by linear interpolation (ratio > 1 = higher and shorter)."""
    idx = np.arange(0, len(x) - 1, ratio)
    return np.interp(idx, np.arange(len(x)), x)
