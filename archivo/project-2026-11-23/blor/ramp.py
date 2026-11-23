"""How much does ramp matter in Blor 1.1? Remove or add ramp pieces and measure speed and win rate."""
from multiprocessing import Pool
from harness import run, summary, paired, paired_turn
from decks import DECKS, swap_many
from scen import cfg
N = 4000
D = DECKS["Blor 1.1 (vigilancia)"]
SC = ["Realista castiga", "Calibrada castiga", "Forge", "Forge dura"]
R4 = ["Cultivate", "Kodama's Reach", "Bugenhagen, Wise Elder", "Overgrowth"]
R8 = R4 + ["Three Visits", "Rampant Growth", "Fyndhorn Elves", "Wild Growth"]
S8 = ["Sixth Sense", "Mask of Memory", "Colossal Majesty", "Spider Umbra", "Garruk's Uprising", "Become Immense",
      "Shadowspear", "Curse of Predation"]
ADD = ["Arbor Elf", "Explore", "Wood Elves", "Kodama of the West Tree"]
ADD8 = ADD + ["Paradise Druid", "Sylvan Caryatid", "Skyshroud Claim", "Wolfwillow Haven"]
V = {
    "−8 de ramp (19 → 11), por hechizos": swap_many(D, R8, S8),
    "−4 de ramp (19 → 15), por hechizos": swap_many(D, R4, S8[:4]),
    "−4 de ramp (19 → 15), por Forest": swap_many(D, R4, ["Forest"] * 4),
    "+4 de ramp (→ 23), por robo": swap_many(D, ["Hunter's Insight", "Inquisitor's Flail", "Rishkar's Expertise", "Return of the Wildspeaker"], ADD),
    "+4 de ramp (→ 23), por amenazas": swap_many(D, ["Rancor", "Indomitable Might", "Commander's Plate", "Crystalline Armor"], ADD),
    "+8 de ramp (→ 27)": swap_many(D, ["Hunter's Insight", "Inquisitor's Flail", "Rishkar's Expertise", "Return of the Wildspeaker",
                                     "Rancor", "Indomitable Might", "Commander's Plate", "Crystalline Armor"], ADD8),
    "+4 de ramp por 4 Forest (34 → 30 tierras)": swap_many(D, ["Forest"] * 4, ADD),
}
if __name__ == "__main__":
    with Pool() as pool:
        g0 = run(D, N, mode="goldfish", pool=pool)
        b = {sc: run(D, N, cfg=cfg(sc), pool=pool) for sc in SC}
        s0 = summary(g0)
        print(f"1.1 (19 de ramp): goldfish T{s0['mean_turn']:.2f}  Blor T{s0['blor_t']:.2f}  " +
              "  ".join(f"{sc} {summary(b[sc])['win']:.1f}" for sc in SC))
        for k, d in V.items():
            g = run(d, N, mode="goldfish", pool=pool)
            sg = summary(g)
            row = [f"{k:44s} goldfish {paired_turn(g0, g)[0]:+.2f}  Blor T{sg['blor_t']:.2f}"]
            for sc in SC:
                r = run(d, N, cfg=cfg(sc), pool=pool)
                row.append(f"{sc[:10]} {paired(b[sc], r)[0]:+5.1f}")
            print("  ".join(row), flush=True)
