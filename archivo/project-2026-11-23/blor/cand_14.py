"""Candidatas contra los 6 cupos mas debiles de la 1.4 (B2)."""
import json
from multiprocessing import Pool
from harness import run, paired
from decks import DECKS, swap_many
from scen import cfg
D = DECKS["Blor 1.4"]; N = 4000
OUTS = ["Long-Lost Lances", "Tarrian's Soulcleaver", "Sylvan Library", "Sword of Truth and Justice", "Short Bow", "Tajuru Preserver"]
INS = ["Tanuki Transplanter", "Primal Bellow", "Spinning Wheel Kick", "Frenzied Baloth", "Ohran Frostfang", "Nightshade Peddler",
       "Quietus Spike", "Gorgon's Head", "Hunter's Blowgun", "Lure", "Destiny Spinner", "Conqueror's Flail"]
if __name__ == "__main__":
    res = {}
    with Pool() as p:
        base = run(D, N, cfg=cfg("B2"), pool=p, seed0=1200000)
        for i in INS:
            row = []
            for o in OUTS:
                d = paired(base, run(swap_many(D, [o], [i]), N, cfg=cfg("B2"), pool=p, seed0=1200000))
                row.append(d[0])
            res[i] = row
            print(f"{i:22s} " + "  ".join(f"{x:+.1f}" for x in row) + f"   mejor {max(row):+.1f} ({OUTS[row.index(max(row))]})", flush=True)
        for pair in [("Lure", "Hunter's Blowgun")]:
            d = paired(base, run(swap_many(D, ["Long-Lost Lances", "Tarrian's Soulcleaver"], list(pair)), N, cfg=cfg("B2"), pool=p, seed0=1200000))
            print(f"{'+'.join(pair)} por Lances+Soulcleaver {d[0]:+.1f}±{d[1]:.1f}", flush=True)
    json.dump(res, open("cand_14.json", "w"))
