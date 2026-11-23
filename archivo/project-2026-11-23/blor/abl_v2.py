"""Ablacion de Blor 1.2 con la mesa v2: cada no-tierra por un Blank, pareado, B2 (objetivo) y vecinos B1, B3."""
import sys, json
from multiprocessing import Pool
from harness import run, paired
from decks import DECKS, swap_many
from scen import cfg
from cards import is_land
D = swap_many(DECKS["Blor 1.1 (vigilancia)"], ["Forest"], ["Dryad Arbor"])
N = int(sys.argv[1]) if len(sys.argv) > 1 else 4000
SC = ["B2", "B1", "B3"]
def swap(deck, out, inn):
    d = list(deck); d[d.index(out)] = inn; return d
if __name__ == "__main__":
    with Pool() as pool:
        base = {sc: run(D, N, cfg=cfg(sc), pool=pool, seed0=700000) for sc in SC}
        res = {}
        for c in sorted(set(x for x in D if not is_land(x) and x != "Blank")):
            ds = [paired(base[sc], run(swap(D, c, "Blank"), N, cfg=cfg(sc), pool=pool, seed0=700000)) for sc in SC]
            res[c] = [(d[0], d[1]) for d in ds]
            print(f"{c:30s} " + "  ".join(f"{sc} {d[0]:+5.1f}±{d[1]:.1f}" for sc, d in zip(SC, ds)), flush=True)
    json.dump(res, open("abl_v2.json", "w"), indent=1)
