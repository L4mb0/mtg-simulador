"""22/11: cartas nuevas de Juan (fotos) para Blor 1.6, orientado a B2."""
import sys
from multiprocessing import Pool
from harness import run, paired, summary, cast_rate
from decks import DECKS, swap_many
from scen import cfg
D = DECKS["Blor 1.6"]; N = 6000; S = 2200000
OUTS = ["Hunter's Insight", "Sylvan Library", "Snake Umbra", "Belt of Giant Strength", "Tarrian's Soulcleaver", "Short Bow"]
CANDS = ["Skullclamp", "Lotus Bloom", "Toski, Bearer of Secrets", "Shadowspear", "Sword of Truth and Justice",
         "Chromatic Lantern", "Hexhaven Invigorator", "Colossal Dreadmaw"]
if __name__ == "__main__":
    with Pool() as p:
        base = run(D, N, cfg=cfg("B2"), pool=p, seed0=S)
        print("1.6 B2", round(summary(base)['win'], 1), flush=True)
        for c in CANDS:
            out = []
            for o in OUTS:
                d = paired(base, run(swap_many(D, [o], [c]), N, cfg=cfg("B2"), pool=p, seed0=S))
                out.append(f"{o.split(',')[0].split(' ')[0]} {d[0]:+.1f}")
            print(c, "|", "  ".join(out), flush=True)
        for o in ("Forest",):
            d = paired(base, run(swap_many(D, [o], ["Roiling Canopy"]), N, cfg=cfg("B2"), pool=p, seed0=S))
            print("Roiling Canopy por Forest", f"{d[0]:+.1f} ±{d[1]:.1f}", flush=True)
