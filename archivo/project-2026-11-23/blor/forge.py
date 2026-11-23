"""Forge-like table: rivals pile onto us when Blor is tapped. Which defensive package works best?"""
from multiprocessing import Pool
from harness import run, summary, paired, paired_turn
from decks import DECKS, swap_many
from scen import cfg
N = 4000
R = DECKS["Rápida B2"]
SC = ["Forge", "Forge dura", "Realista", "Mesa agresiva"]
V = {
    "Rápida B2": R,
    "1.0 (con Silent Arbiter y Spore Frog)": DECKS["Blor 1.0"],
    "+ Silent Arbiter (por Explore)": swap_many(R, ["Explore"], ["Silent Arbiter"]),
    "Defensiva (Shadowspear, Lances, Moment's Peace)": DECKS["Rápida defensiva"],
    "Defensiva + Silent Arbiter": swap_many(DECKS["Rápida defensiva"], ["Explore"], ["Silent Arbiter"]),
    "Defensiva + Silent Arbiter + Spore Frog": swap_many(DECKS["Rápida defensiva"], ["Explore", "Mask of Memory"], ["Silent Arbiter", "Spore Frog"]),
    "Defensiva + Silent Arbiter + Short Bow": swap_many(DECKS["Rápida defensiva"], ["Explore", "Mask of Memory"], ["Silent Arbiter", "Short Bow"]),
    "Defensiva + Silent Arbiter + Crawlspace": swap_many(DECKS["Rápida defensiva"], ["Explore", "Mask of Memory"], ["Silent Arbiter", "Crawlspace"]),
    "4 vigilancias + Silent Arbiter": swap_many(R, ["Sixth Sense", "Thought Vessel", "Explore", "Mask of Memory", "Arbor Elf"],
                                                ["Short Bow", "Long-Lost Lances", "Avarice Amulet", "Tarrian's Soulcleaver", "Silent Arbiter"]),
}
def causes(res):
    n = len(res)
    return f"x combate {100*sum(r['loss']=='combat' for r in res)/n:4.1f}%"
if __name__ == "__main__":
    with Pool() as pool:
        base = {sc: run(R, N, cfg=cfg(sc), pool=pool) for sc in SC}
        g0 = run(R, N, mode="goldfish", pool=pool)
        for sc in SC:
            s = summary(base[sc]); print(f"Rápida B2 en {sc:14s}: win {s['win']:5.1f}  turno {s['mean_turn']:.2f}  {causes(base[sc])}")
        for k, d in V.items():
            if k == "Rápida B2":
                continue
            row = [f"{k:48s}"]
            for sc in SC:
                r = run(d, N, cfg=cfg(sc), pool=pool)
                row.append(f"{sc[:10]} {summary(r)['win']:5.1f} ({paired(base[sc], r)[0]:+.1f}) {causes(r)}")
            g = run(d, N, mode="goldfish", pool=pool)
            row.append(f"gf {paired_turn(g0, g)[0]:+.2f}")
            print("  ".join(row), flush=True)
