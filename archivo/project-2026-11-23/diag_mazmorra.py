"""Diagnóstico de la mesa Mazmorra (16/11/2026): ¿la mesa simulada se parece a lo que pasó en el torneo B3 del 15/11?

Lo observado (8 partidas: 4 de Juan con Gandalf, 4 de Juma):
  - Turno en que terminó la partida: 5, 5, 5, ~5-6, 6, 6, 7, 7  -> ~45% en T5 o antes, ~75% en T6 o antes, todas en T7 o antes
  - Primer intento serio de ganar: T3-T4 en 3 de las 4 mesas de Juan (Tifa mata a Ureni en T3, Vivi en T4, Mikey pega en T5)
  - Juan ganó 1 de 4 (en T6, porque el azul frenó dos veces al Mikey); Juma ganó 1 de 4 (en T7)
  - Edictos en 2 de 4 mesas (Gandalf sacrificado 2 veces en una), Strip Mine en bucle en 1 de 4

Uso: python3 diag_mazmorra.py [partidas] [mesa ...]
"""
import os, sys, statistics
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import simlib as S, table, engine

def _one(args):
    deck, name, seed0, n = args
    tb, ix = table.MZ_VARIANTS.get(name) or table.BRACKETS[name]
    engine.DEV_TUTOR[:] = ["Ojer Axonil, Deepest Might", "Harmonic Prodigy", "Ruby Medallion", "Past in Flames"]
    out = []
    for i in range(n):
        t, s, r = table.play_table(deck, "E", seed0 + i, tb, ix=ix)
        out.append(dict(win=int(r == "win"), t=t, first=s.first_att, n_att=s.n_att, stops=getattr(s, "others_stop", 0),
                        partial=s.partial_kills, by_partial=getattr(s, "killed_by_partial", False),
                        edicts=getattr(s, "edicts_hit", 0), g_ed=getattr(s, "gandalf_edicted", 0),
                        lands=getattr(s, "lands_lost", 0), slowed=getattr(s, "slow_used", 0), by_time=s.by_time, cause=getattr(s, "cause", None)))
    return out

def run(deck, name, n=4000, seed0=900_000, procs=2):
    k = procs * 4
    sz = [n // k + (1 if i < n % k else 0) for i in range(k)]
    jobs, s0 = [], seed0
    for z in sz:
        jobs.append((deck, name, s0, z)); s0 += z
    with Pool(procs) as p:
        return [x for part in p.map(_one, jobs) for x in part]

def report(name, R):
    n = len(R)
    ts = [r["t"] for r in R if r["t"] < 99]
    le = lambda k: 100 * sum(t <= k for t in ts) / n
    fa = [r["first"] for r in R if r["first"]]
    w = 100 * sum(r["win"] for r in R) / n
    print(f"{name:28s} gana {w:5.1f}% | fin ≤T5 {le(5):4.0f}% ≤T6 {le(6):4.0f}% ≤T7 {le(7):4.0f}% med T{statistics.median(ts):.0f}"
          f" | 1er intento ≤T4 {100*sum(f<=4 for f in fa)/n:3.0f}% | frenos/partida {statistics.mean(r['stops'] + r['slowed'] for r in R):.1f}"
          f" | parciales {100*sum(r['partial']>0 for r in R)/n:3.0f}%"
          f" | por tiempo {100*sum(r['by_time'] is not None for r in R)/n:3.0f}% (ganas {100*sum(r['by_time'] is True for r in R)/n:.1f})", flush=True)
    return w

if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 4000
    names = sys.argv[2:] or list(table.MZ_VARIANTS) + ["B3", "B3+B4", "B4"]
    d = S.load(os.path.join(os.path.dirname(os.path.abspath(__file__)), "gandalf_1.6.txt"))
    print("OBSERVADO (8 partidas)        gana ~25%  | fin ≤T5  ~45% ≤T6  ~75% ≤T7 ~100% med T6 | 1er intento ≤T4 ~75%")
    for nm in names:
        report(nm, run(d, nm, n))
