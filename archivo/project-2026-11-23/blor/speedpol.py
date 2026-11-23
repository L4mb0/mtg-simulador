import sys
from multiprocessing import Pool
from harness import run, summary, paired, paired_turn
from decks import DECKS, swap_many
from scen import cfg
from engine import TableCfg
N = 3000
D = DECKS["Blor 1.0"]
POL = {"trucos greedy": dict(pump="greedy"), "foco amenaza": dict(focus="threat"), "nunca guardar": dict(hold_from_turn=99)}
INTER = ["Archdruid's Charm", "Beast Within", "Krosan Grip", "Nature's Claim", "Ram Through", "Bridgeworks Battle",
         "Kenrith's Transformation", "Spore Frog", "Silent Arbiter", "Tajuru Preserver"]
FAST = ["Arbor Elf", "Colossus Hammer", "Rancor", "Sixth Sense", "Explore", "Mask of Memory", "Avarice Amulet",
        "Thought Vessel", "Emerald Medallion", "Curse of Predation"]
PACKS = {
    "Sin interacción (10 → aceleradores)": swap_many(D, INTER, FAST),
    "Sin interacción salvo 4 (6 → aceleradores)": swap_many(D, INTER[4:], FAST[:6]),
    "32 tierras (+Arbor Elf, Rancor)": swap_many(D, ["Forest", "Forest"], ["Arbor Elf", "Rancor"]),
    "30 tierras (+4 aceleradores)": swap_many(D, ["Forest"] * 4, ["Arbor Elf", "Rancor", "Explore", "Colossus Hammer"]),
    "Ramp de 3 → de 1 (Cultivate, Kodama's → Arbor Elf, Explore)": swap_many(D, ["Cultivate", "Kodama's Reach"], ["Arbor Elf", "Explore"]),
    "B3: One Ring + Ancient Tomb + Chrome Mox": swap_many(D, ["Spore Frog", "Forest", "Arcane Signet"], ["The One Ring", "Ancient Tomb", "Chrome Mox"]),
}
if __name__ == "__main__":
    with Pool() as pool:
        g0 = run(D, N, mode="goldfish", pool=pool)
        t0 = {sc: run(D, N, cfg=cfg(sc), pool=pool) for sc in ("Realista", "Calibrada")}
        for k, over in POL.items():
            g = run(D, N, mode="goldfish", cfg=TableCfg(**over), pool=pool)
            row = [f"{k:52s} goldfish {paired_turn(g0, g)[0]:+.2f}"]
            for sc in t0:
                r = run(D, N, cfg=cfg(sc, **over), pool=pool)
                row.append(f"{sc[:4]} {paired(t0[sc], r)[0]:+.1f} (turno {summary(r)['mean_turn']:.2f})")
            print("  ".join(row), flush=True)
        for k, d in PACKS.items():
            g = run(d, N, mode="goldfish", pool=pool)
            row = [f"{k:52s} goldfish {paired_turn(g0, g)[0]:+.2f}"]
            for sc in t0:
                r = run(d, N, cfg=cfg(sc), pool=pool)
                row.append(f"{sc[:4]} {paired(t0[sc], r)[0]:+.1f} (turno {summary(r)['mean_turn']:.2f})")
            print("  ".join(row), flush=True)
        print("base turnos:", {sc: round(summary(v)['mean_turn'], 2) for sc, v in t0.items()})
