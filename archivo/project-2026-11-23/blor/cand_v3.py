"""15/11 (Juan): cartas pedidas sobre Blor 1.3, contra rol parecido. B2 (objetivo), B1, B3."""
import sys
from multiprocessing import Pool
from harness import run, paired, summary
from decks import DECKS, swap_many
from scen import cfg
D = DECKS["Blor 1.3"]
SC = ["B2", "B1", "B3"]; N = int(sys.argv[1]) if len(sys.argv) > 1 else 6000
ABL = ["Hunter's Insight", "Berserk", "Blanchwood Armor", "Basilisk Collar", "Archdruid's Charm", "Heroic Intervention",
       "Nature's Claim", "Beast Within", "Pariah's Shield", "Allosaurus Shepherd"]
SW = [(["Hunter's Insight"], ["Primal Bellow"]), (["Berserk"], ["Primal Bellow"]),
      (["Beast Within"], ["Spinning Wheel Kick"]), (["Hunter's Insight"], ["Spinning Wheel Kick"]),
      (["Allosaurus Shepherd"], ["Frenzied Baloth"]),
      (["Short Bow"], ["Tanuki Transplanter"]),
      (["Basilisk Collar"], ["Nightshade Peddler"]), (["Short Bow"], ["Nightshade Peddler"]),
      (["Basilisk Collar"], ["Ohran Frostfang"]), (["Short Bow"], ["Ohran Frostfang"]),
      (["Basilisk Collar"], ["Quietus Spike"]), (["Short Bow"], ["Quietus Spike"]), (["Basilisk Collar"], ["Gorgon's Head"]),
      (["Forest"], ["Talon Gates of Madara"]), (["Forest", "Rampant Growth"], ["Talon Gates of Madara", "Expedition Map"]),
      (["Hunter's Insight"], ["Krosan Grip"])]
B3ONLY = [(["Forest", "Hunter's Insight"], ["Talon Gates of Madara", "Crop Rotation"])]
if __name__ == "__main__":
    with Pool() as p:
        base = {sc: run(D, N, cfg=cfg(sc), pool=p, seed0=960000) for sc in SC}
        print("Blor 1.3: " + "  ".join(f"{sc} {summary(base[sc])['win']:.1f}%" for sc in SC), flush=True)
        b12 = [paired(run(DECKS["Blor 1.2"], N, cfg=cfg(sc), pool=p, seed0=960000), base[sc]) for sc in SC]
        print("1.3 contra 1.2: " + "  ".join(f"{sc} {d[0]:+.1f}±{d[1]:.1f}" for sc, d in zip(SC, b12)), flush=True)
        for c in ABL:
            ds = [paired(base[sc], run(swap_many(D, [c], ["Blank"]), N, cfg=cfg(sc), pool=p, seed0=960000)) for sc in SC]
            print(f"ABL {c:24s} " + "  ".join(f"{sc} {d[0]:+.1f}±{d[1]:.1f}" for sc, d in zip(SC, ds)), flush=True)
        for o, i in SW:
            ds = [paired(base[sc], run(swap_many(D, o, i), N, cfg=cfg(sc), pool=p, seed0=960000)) for sc in SC]
            print(f"{'+'.join(i):40s} por {'+'.join(o):28s} " + "  ".join(f"{sc} {d[0]:+.1f}±{d[1]:.1f}" for sc, d in zip(SC, ds)), flush=True)
        for o, i in B3ONLY:
            d = paired(base["B3"], run(swap_many(D, o, i), N, cfg=cfg("B3"), pool=p, seed0=960000))
            print(f"{'+'.join(i):40s} por {'+'.join(o):28s} B3 {d[0]:+.1f}±{d[1]:.1f}", flush=True)
        # sensibilidad: el triple de piezas que quitan antimaleficio
        for sc in ["B2", "B3"]:
            bh = run(D, N, cfg=cfg(sc, hate=0.18), pool=p, seed0=960000)
            for o, i in [(["Heroic Intervention"], ["Blank"]), (["Forest"], ["Talon Gates of Madara"]), (["Hunter's Insight"], ["Krosan Grip"])]:
                d = paired(bh, run(swap_many(D, o, i), N, cfg=cfg(sc, hate=0.18), pool=p, seed0=960000))
                print(f"HATE x3 {sc} {'+'.join(i)} por {'+'.join(o)}: {d[0]:+.1f}±{d[1]:.1f}", flush=True)
