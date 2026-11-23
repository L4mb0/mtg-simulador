"""Regla 1: comportamiento de la remocion (mesa vieja vs regla 1 en B3)"""
import sys
from multiprocessing import Pool
from collections import Counter
import engine
from scen import SCEN, ACTUAL, CONS
K = ["rem_drawn", "rem_used", "rem_us", "rem_used_eng", "rem_us_eng", "rem_inst", "saved", "edict_us", "edict_each_us"]
def job(a):
    deck, sc, s = a
    g = engine.play(deck, 700000 + s, mode="table", cfg=SCEN[sc])
    d = {k: g.stats.get(k, 0) for k in K}
    d.update(won=g.won, lost=g.lost, T=g.turn, combo=1 if g.stats["combo_turn"] else 0, names=g.stats.get("rem_names", {}))
    return d
if __name__ == "__main__":
    N = 4000
    with Pool() as p:
        for dn, deck in [("1.0", ACTUAL), ("1.1", CONS)]:
            for sc in ["Realista (base)", "Realista + regla 1 (B3)"]:
                r = p.map(job, [(deck, sc, s) for s in range(N)], chunksize=100)
                m = {k: sum(x[k] for x in r) / N for k in K + ["won", "combo", "T"]}
                nm = Counter()
                for x in r: nm.update(x["names"])
                tot = sum(nm.values()) or 1
                top = ", ".join(f"{k} {100*v/tot:.0f}%" for k, v in nm.most_common(7))
                print(f"\n{dn} | {sc}")
                print(f"  remocion usada por la mesa {m['rem_used']:.2f}/partida (robada {m['rem_drawn']:.2f}); contra ti {m['rem_us']:.2f} ({100*m['rem_us']/max(1e-9,m['rem_used']):.0f}%)")
                print(f"  con un motor tuyo (peso>=0,5) en mesa: va contra ti {100*m['rem_us_eng']/max(1e-9,m['rem_used_eng']):.0f}%   al instante {m['rem_inst']:.2f}/partida   salvadas {m['saved']:.2f}   edictos que pagas {m['edict_us']+m['edict_each_us']:.2f}")
                print(f"  que te quitan: {top}")
                print(f"  ganas {100*m['won']:.1f}%  combo {100*m['combo']:.1f}%  fin T{m['T']:.1f}")
