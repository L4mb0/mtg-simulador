"""Regla 2: comportamiento de los counters (mesa vieja / regla 1 / reglas 1-2, B3)"""
from multiprocessing import Pool
from collections import Counter
import engine
from scen import SCEN, ACTUAL, CONS
K = ["cnt_drawn", "cnt_used", "cnt_dev", "cnt_combo", "combo_tries", "veil_saves", "rem_us"]
def job(a):
    deck, sc, s = a
    g = engine.play(deck, 700000 + s, mode="table", cfg=SCEN[sc])
    d = {k: g.stats.get(k, 0) for k in K}
    d.update(won=g.won, T=g.turn, combo=1 if g.stats["combo_turn"] else 0, names=g.stats.get("cnt_names", {}),
             gorma_cast=1 if g.gorma_turn else 0)
    return d
if __name__ == "__main__":
    N = 4000
    with Pool() as p:
        for dn, deck in [("1.0", ACTUAL), ("1.1", CONS)]:
            for sc in ["Realista (base)", "Realista + regla 1 (B3)", "Realista + reglas 1-2 (B3)"]:
                r = p.map(job, [(deck, sc, s) for s in range(N)], chunksize=100)
                m = {k: sum(x[k] for x in r) / N for k in K + ["won", "combo", "T"]}
                nm = Counter()
                for x in r: nm.update(x["names"])
                tot = sum(nm.values()) or 1
                top = ", ".join(f"{k} {100*v/tot:.0f}%" for k, v in nm.most_common(6))
                print(f"{dn} | {sc:28s} counters usados {m['cnt_used']:.2f} (robados {m['cnt_drawn']:.2f}; en desarrollo {m['cnt_dev']:.2f}, en el turno del combo {m['cnt_combo']:.2f} de {m['combo_tries']:.2f} intentos)  Veil {m['veil_saves']:.2f}  ganas {100*m['won']:.1f}%  combo {100*m['combo']:.1f}%")
                if top.strip(): print("     a que:", top)
