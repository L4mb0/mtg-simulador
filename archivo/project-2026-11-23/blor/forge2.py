from multiprocessing import Pool
from harness import run, summary, paired, paired_turn
from decks import DECKS, swap_many
from scen import cfg
N = 4000
R = DECKS["Rápida B2"]
SC = ["Forge", "Forge dura", "Realista", "Mesa agresiva"]
VIG = swap_many(R, ["Sixth Sense", "Thought Vessel", "Explore", "Mask of Memory", "Arbor Elf"],
                ["Short Bow", "Long-Lost Lances", "Avarice Amulet", "Tarrian's Soulcleaver", "Silent Arbiter"])
V = {
    "4 vig + Arbiter": VIG,
    "4 vig + Arbiter + Pariah's Shield (por Rancor)": swap_many(VIG, ["Rancor"], ["Pariah's Shield"]),
    "4 vig + Arbiter + Shadowspear (por Rancor)": swap_many(VIG, ["Rancor"], ["Shadowspear"]),
    "4 vig + Arbiter + Shadowspear + Pariah + Moment's Peace": swap_many(VIG, ["Rancor", "Colossus Hammer", "Hunter's Insight"], ["Shadowspear", "Pariah's Shield", "Moment's Peace"]),
    "Rápida + Pariah's Shield (por Explore)": swap_many(R, ["Explore"], ["Pariah's Shield"]),
}
if __name__ == "__main__":
    with Pool() as pool:
        base = {sc: run(R, N, cfg=cfg(sc), pool=pool) for sc in SC}
        g0 = run(R, N, mode="goldfish", pool=pool)
        for k, d in V.items():
            row = [f"{k:56s}"]
            for sc in SC:
                r = run(d, N, cfg=cfg(sc), pool=pool)
                row.append(f"{sc[:10]} {summary(r)['win']:5.1f} ({paired(base[sc], r)[0]:+.1f})")
            g = run(d, N, mode="goldfish", pool=pool)
            row.append(f"gf {paired_turn(g0, g)[0]:+.2f}")
            print("  ".join(row), flush=True)
        for pol in ("safe", "big:10"):
            for name, d in (("Rápida", R), ("4 vig + Arbiter", VIG)):
                row = [f"{name} con política {pol:8s}"]
                for sc in SC[:2]:
                    r = run(d, N, cfg=cfg(sc, attack_policy=pol), pool=pool)
                    row.append(f"{sc} {summary(r)['win']:5.1f} ({paired(base[sc], r)[0]:+.1f} vs rápida)")
                print("  ".join(row), flush=True)
