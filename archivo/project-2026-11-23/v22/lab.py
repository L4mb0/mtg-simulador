import os, sys, math, statistics
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import table, engine, ai
from cards import C, OFF_COLOR

def load(path):
    d = []
    for line in open(path):
        line = line.strip()
        if not line: continue
        n, name = line.split(" ", 1)
        d += [name] * int(n)
    return d

def swap(deck, pairs):
    d = deck[:]
    for a, b in pairs:
        assert b in C and b not in OFF_COLOR, b
        d[d.index(a)] = b
    return d

def _one(args):
    deck, mesa, seed0, n = args
    tb, ix = table.BRACKETS[mesa]
    engine.DEV_TUTOR[:] = ["Ojer Axonil, Deepest Might", "Harmonic Prodigy", "Ruby Medallion", "Past in Flames"]
    return [int(table.play_table(deck, "E", seed0 + i, tb, ix=ix)[2] == "win") for i in range(n)]

def run(deck, n, seed0, mesa, procs=None):
    procs = procs or os.cpu_count()
    k = procs * 4
    sz = [n // k + (1 if i < n % k else 0) for i in range(k)]
    jobs, s0 = [], seed0
    for z in sz:
        jobs.append((deck, mesa, s0, z)); s0 += z
    with Pool(procs) as p:
        return [x for part in p.map(_one, jobs) for x in part]

def gf(deck, n=2000):
    ts = [ai.play_game(deck, "C", 700000 + i)[0] for i in range(n)]
    return statistics.median(ts), 100 * sum(t <= 6 for t in ts) / n

w = lambda R: 100 * statistics.mean(R)
def diff(A, B):
    d = [b - a for a, b in zip(A, B)]
    return 100 * statistics.mean(d), 196 * statistics.pstdev(d) / math.sqrt(len(d))
