import sys
from multiprocessing import Pool
from harness import run, paired, summary
from decks import DECKS, swap_many
from scen import cfg
D = DECKS["Blor 1.6"]; N = 6000; S = 4300000
WEAK = ["Staff of Titania", "Commander's Plate", "Allosaurus Shepherd", "Sword of Fire and Ice", "Ohran Frostfang", "Hunter's Insight"]
FRENO = ["Krosan Grip", "Ram Through", "Return to Nature", "Slice in Twain", "Kenrith's Transformation", "Bridgeworks Battle"]
PROT = ["Tamiyo's Safekeeping", "Veil of Summer", "Spellskite"]
V = {"2 para frenar": (WEAK[:2], FRENO[:2]), "4 para frenar": (WEAK[:4], FRENO[:4]), "6 para frenar": (WEAK, FRENO),
     "2 para proteger": (WEAK[:2], PROT[:2]), "3 para proteger": (WEAK[:3], PROT),
     "3 frenar + 3 proteger": (WEAK, FRENO[:3] + PROT)}
CAND = ["Conqueror's Flail", "Garruk's Uprising", "Sylvan Safekeeper", "Glorious Sunrise", "Finale of Devastation", "Mithril Coat",
        "Akroma's Memorial", "Shadowspear", "Spellskite", "Tamiyo's Safekeeping", "Hardened Scales", "Thran Dynamo", "Lotus Cobra",
        "Bloom Tender", "Azusa, Lost but Seeking"]
SLOTS = ["Hunter's Insight", "Staff of Titania"]
if __name__ == "__main__":
    st = sys.argv[1]
    with Pool() as p:
        base = {sc: run(D, N, cfg=cfg(sc), pool=p, seed0=S) for sc in ("Mazmorra", "B3")}
        print("base", {k: round(summary(v)['win'], 2) for k, v in base.items()}, flush=True)
        if st == "resp":
            for k, (o, i) in V.items():
                print(k, "  ".join(f"{sc} {paired(base[sc], run(swap_many(D, o, i), N, cfg=cfg(sc), pool=p, seed0=S))[0]:+.1f}" for sc in base), flush=True)
        if st == "cand":
            for c in CAND:
                out = []
                for sl in SLOTS:
                    for sc in base:
                        d = paired(base[sc], run(swap_many(D, [sl], [c]), N, cfg=cfg(sc), pool=p, seed0=S))
                        out.append(f"{sl[:8]}/{sc[:3]} {d[0]:+.1f}")
                print(c, " | ".join(out), flush=True)
            for c, sl in (("Ancient Tomb", "Forest"), ("Cavern of Souls", "Forest"), ("The One Ring", "Arcane Signet")):
                print(c, "  ".join(f"{sc} {paired(base[sc], run(swap_many(D, [sl], [c]), N, cfg=cfg(sc), pool=p, seed0=S))[0]:+.1f}" for sc in base), flush=True)
