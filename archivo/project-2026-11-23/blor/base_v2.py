"""Linea base de Blor 1.2 con la mesa v2 (15/11), por bracket."""
import sys, json
from multiprocessing import Pool
from collections import Counter
from harness import run, summary
from decks import DECKS, swap_many
from scen import cfg
D = swap_many(DECKS["Blor 1.1 (vigilancia)"], ["Forest"], ["Dryad Arbor"])
N = int(sys.argv[1]) if len(sys.argv) > 1 else 10000
if __name__ == "__main__":
    out = {}
    with Pool() as p:
        for sc in ["B1", "B2", "B3", "B3+B4", "B4", "B5"]:
            r = run(D, N, cfg=cfg(sc), pool=p, seed0=500000)
            s = summary(r)
            loss = Counter(x["loss"] for x in r if x["lost"])
            out[sc] = s
            print(f"{sc:6s} gana {s['win']:.1f}% ±{s['ci']:.1f}  turno medio de victoria {s['mean_turn']:.1f}  rivales muertos {s['kills']:.2f}  "
                  f"derrotas: " + ", ".join(f"{k} {100*v/N:.1f}%" for k, v in loss.most_common()), flush=True)
        g = run(D, N, mode="goldfish", pool=p, seed0=500000)
        s = summary(g); print(f"goldfish: turno medio {s['mean_turn']:.1f}, T8 o antes {s['k8']:.0f}%")
    json.dump(out, open("base_v2.json", "w"), indent=1)
