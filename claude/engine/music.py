"""Muzică sintetizată (fără drepturi de autor). Utilizare: music.py out.wav DURATA '[start_p1, start_p2, ...]'"""
import json, sys
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt

OUT, DUR, STARTS = sys.argv[1], float(sys.argv[2]), json.loads(sys.argv[3])
SR = 48000; N = int(SR * DUR); t = np.arange(N) / SR
L = np.zeros(N); R = np.zeros(N)
BEAT = 0.7; DROP = STARTS[0] if STARTS else 3.5
rng = np.random.default_rng(3)

def nf(name):
    names = {'C':0,'C#':1,'D':2,'D#':3,'E':4,'F':5,'F#':6,'G':7,'G#':8,'A':9,'A#':10,'B':11}
    return 440.0 * 2 ** ((names[name[:-1]] + 12 * (int(name[-1]) + 1) - 69) / 12)

def add(sig, start, gain=1.0, pan=0.0):
    i = int(start * SR)
    if i >= N or i < 0: return
    seg = sig[:N - i]
    L[i:i+len(seg)] += seg * gain * np.sqrt((1-pan)/2) * 1.414
    R[i:i+len(seg)] += seg * gain * np.sqrt((1+pan)/2) * 1.414

PROG = [(['C3','E3','G3','B3','D4'],'C2',['C5','E5','G5','B5']),
        (['A2','C3','E3','G3','B3'],'A2',['A4','C5','E5','G5']),
        (['F3','A3','C4','E4'],'F2',['F4','A4','C5','E5']),
        (['G3','B3','D4','A3'],'G2',['G4','B4','D5','A5'])]
CH = []; x = 0.0; k = 0
while x < DUR:
    CH.append((x,) + PROG[k % 4]); x += 2.8; k += 1

pump = np.ones(N)
for b in np.arange(DROP, DUR, BEAT):
    i = int(b * SR); pump[i:] = np.minimum(pump[i:], 1 - 0.45 * np.exp(-(t[i:] - b) * 9))
for k, (st, notes, bass, arp) in enumerate(CH):
    end = CH[k+1][0] if k + 1 < len(CH) else DUR
    d = end - st + 0.6; tt = np.arange(int(d * SR)) / SR
    env = np.minimum(1, tt / 0.35) * np.clip((d - tt) / 0.6, 0, 1)
    for n in notes:
        for det, pan in ((0.9985, -0.6), (1.0015, 0.6)):
            ff = nf(n) * det
            add((np.sin(2*np.pi*ff*tt) + .28*np.sin(4*np.pi*ff*tt) + .1*np.sin(6*np.pi*ff*tt)) * env, st, 0.03, pan)
L *= 0.55 + 0.45 * pump; R *= 0.55 + 0.45 * pump
for k, (st, notes, bass, arp) in enumerate(CH):
    end = CH[k+1][0] if k + 1 < len(CH) else DUR - 0.8
    for b in np.arange(max(st, DROP), end - 1e-6, BEAT):
        f = nf(bass); tt = np.arange(int(.65*SR)) / SR
        add((np.sin(2*np.pi*f*tt) + .35*np.sin(4*np.pi*f*tt)) * np.minimum(1, tt/.01) * np.exp(-tt*4.5), b + .02, .16)
    x = max(st, .45); i = 0
    end = CH[k+1][0] if k + 1 < len(CH) else DUR - 1.2
    while x < end - 1e-6:
        f = nf(arp[i % 4]); tt = np.arange(int(.5*SR)) / SR
        s = (np.sin(2*np.pi*f*tt) + .22*np.sin(6*np.pi*f*tt)*np.exp(-tt*20)) * np.minimum(1, tt/.004) * np.exp(-tt*9)
        add(s, x, .055 if x >= DROP else .065, -.35 if i % 2 else .35)
        x += BEAT/2 if x < DROP else BEAT/4; i += 1
for b in np.arange(DROP, DUR - 0.9, BEAT):
    tt = np.arange(int(.4*SR)) / SR; fr = 48 + 110*np.exp(-tt*30)
    add(np.sin(2*np.pi*np.cumsum(fr)/SR) * np.exp(-tt*9), b, .42)
    hn = sosfilt(butter(4, 7000, 'hp', fs=SR, output='sos'), rng.standard_normal(int(.06*SR)))
    hn *= np.exp(-np.arange(len(hn))/SR*70)
    add(hn, b + BEAT/2, .05, .3); add(hn*.6, b + BEAT*.75, .04, -.3)

def whoosh(c, length=.6, gain=.11):
    n = int(length*SR); x = sosfilt(butter(2, [500, 6000], 'bp', fs=SR, output='sos'), rng.standard_normal(n))
    env = np.sin(np.pi*np.clip(np.arange(n)/SR/length, 0, 1))**2
    add(x*env, c - length/2, gain, -.4); add(x[::-1]*env, c - length/2, gain*.8, .4)
def ding(at):
    for k, f in enumerate((nf('E6'), nf('A6'))):
        tt = np.arange(int(.7*SR))/SR
        add((np.sin(2*np.pi*f*tt) + .3*np.sin(2*np.pi*2.01*f*tt))*np.exp(-tt*6), at + k*.07, .09)
def pop(at):
    tt = np.arange(int(.12*SR))/SR; fr = 220 + 700*np.exp(-tt*40)
    add(np.sin(2*np.pi*np.cumsum(fr)/SR)*np.exp(-tt*30), at, .16)

whoosh(DROP - .25)
for s0 in STARTS:
    ding(s0 + 1.52); pop(s0 + 1.78)
for s0 in STARTS[:-1]:
    whoosh(s0 + 4.2 - .25)
if STARTS:
    whoosh(STARTS[-1] + 4.2 - .3, .8, .13)
    n = int(2.5*SR); x = sosfilt(butter(2, 5000, 'hp', fs=SR, output='sos'), rng.standard_normal(n)) * np.exp(-np.arange(n)/SR*2.2)
    add(x, STARTS[-1] + 4.3, .035)

mix = np.stack([L, R], 1) * np.clip((DUR - t)/1.3, 0, 1)[:, None] * np.clip(t/.05, 0, 1)[:, None]
mix /= np.max(np.abs(mix)) + 1e-9
mix = np.tanh(mix*1.6)/np.tanh(1.6)*.89
wavfile.write(OUT, SR, (mix*32767).astype(np.int16))
