"""Corridas en paralelo (2 núcleos) con semillas fijas: mismas semillas que simlib.winrate."""
import os, sys
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import simlib as S, table

def _chunk(args):
    deck, bracket, seed0, n, details = args
    return S.winrate(deck, n=n, seed0=seed0, bracket=bracket, details=details)

def winrate(deck, bracket, n=6000, seed0=900_000, details=False, procs=2):
    k = procs * 4
    sz = [n // k + (1 if i < n % k else 0) for i in range(k)]
    jobs, s0 = [], seed0
    for z in sz:
        jobs.append((deck, bracket, s0, z, details)); s0 += z
    with Pool(procs) as p:
        parts = p.map(_chunk, jobs)
    return [x for part in parts for x in part]

if __name__ == "__main__":
    d = S.load("gandalf_1.6.txt")
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 6000
    for b in sys.argv[2:] or ["B2", "B3", "B4"]:
        w = winrate(d, b, n)
        print(f"1.6 {b}: {S.pct(w):.1f}%  (n={n})", flush=True)
