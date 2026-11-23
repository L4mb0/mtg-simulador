from collections import Counter
from multiprocessing import Pool
from harness import run, summary, paired, paired_turn
from decks import DECKS
from scen import cfg, SCEN
from engine import TableCfg
N = 4000
NAMES = ["Blor 1.0", "Rápida B2", "Rápida B3"]
def dist(res):
    n = len(res); w = [r["turn"] for r in res if r["win"]]
    return f"≤T7 {100*sum(t<=7 for t in w)/n:4.1f}%  ≤T8 {100*sum(t<=8 for t in w)/n:4.1f}%  ≤T9 {100*sum(t<=9 for t in w)/n:4.1f}%"
if __name__ == "__main__":
    with Pool() as pool:
        G = {n: run(DECKS[n], N, mode="goldfish", pool=pool) for n in NAMES}
        for n in NAMES:
            print(f"{n:12s} goldfish T{summary(G[n])['mean_turn']:.2f}  {dist(G[n])}  vs 1.0 {paired_turn(G[NAMES[0]], G[n])[0]:+.2f}")
        for pol in ("normal", "nunca guardar"):
            print("-- pilotaje:", pol)
            for sc in SCEN:
                over = dict(hold_from_turn=99) if pol != "normal" else {}
                R = {n: run(DECKS[n], N, cfg=cfg(sc, **over), pool=pool) for n in NAMES}
                base = run(DECKS[NAMES[0]], N, cfg=cfg(sc), pool=pool) if pol != "normal" else R[NAMES[0]]
                row = [f"{sc:26s}"]
                for n in NAMES:
                    s = summary(R[n]); m, _ = paired(base, R[n])
                    row.append(f"{n[-3:] if n!='Blor 1.0' else '1.0'}: {s['win']:5.1f} ({m:+.1f}) T{s['mean_turn']:.2f}")
                print("  ".join(row), flush=True)
                if sc != "Realista" and pol != "normal":
                    pass
            if pol == "nunca guardar":
                break
