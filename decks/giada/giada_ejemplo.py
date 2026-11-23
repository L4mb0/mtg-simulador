"""Ejemplos de uso del simulador de Giada.

PYTHONHASHSEED=0 python3 giada_ejemplo.py base
PYTHONHASHSEED=0 python3 giada_ejemplo.py candidata "Path to Exile" "Exorcise"
PYTHONHASHSEED=0 python3 giada_ejemplo.py ablacion
PYTHONHASHSEED=0 python3 giada_ejemplo.py ruta "Exorcise,Invoke the Divine" "Path to Exile,Generous Gift"
PYTHONHASHSEED=0 python3 giada_ejemplo.py log 7          # una partida con registro, semilla 7
"""
import sys
from multiprocessing import Pool
from cards import ACTUAL, LANDS, swap
from harness import run, summary, paired, fmt
from scen import cfg
from engine import play

N = 4000
MESAS = ("Realista", "Optimista", "Rivales lentos", "Pesimista")

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "base"
    if cmd == "log":
        g = play(ACTUAL, int(sys.argv[2]), mode="table", cfg=cfg("Realista"), log=True)
        print("ganó" if g.won else f"perdió ({g.loss})", g.win_turn)
        sys.exit()
    with Pool(2) as pool:
        if cmd == "base":
            print("Goldfish ", fmt(summary(run(ACTUAL, N, mode="goldfish", pool=pool))))
            for m in MESAS:
                print(f"{m:10s}", fmt(summary(run(ACTUAL, N, cfg=cfg(m), pool=pool))))
        elif cmd in ("candidata", "ruta"):
            ins = sys.argv[2].split(",") if cmd == "candidata" else sys.argv[3].split(",")
            outs = sys.argv[3].split(",") if cmd == "candidata" else sys.argv[2].split(",")
            d = list(ACTUAL)
            for o, i in zip(outs, ins):
                d = swap(d, o, i)
            for m in MESAS:
                a = run(ACTUAL, N, cfg=cfg(m), pool=pool); b = run(d, N, cfg=cfg(m), pool=pool)
                dm, ci = paired(a, b)
                print(f"{m:10s} {dm:+5.2f} ± {ci:.2f} pts")
        elif cmd == "ablacion":
            base = {m: run(ACTUAL, N, cfg=cfg(m), pool=pool) for m in MESAS[:2]}
            for c in sorted(set(x for x in ACTUAL if x not in LANDS)):
                d = swap(ACTUAL, c, "Blank")
                vals = [paired(run(d, N, cfg=cfg(m), pool=pool), base[m]) for m in MESAS[:2]]
                print(f"{c:28s}", "  ".join(f"{m[:4]} {v[0]:+5.2f}±{v[1]:.2f}" for m, v in zip(MESAS, vals)))
