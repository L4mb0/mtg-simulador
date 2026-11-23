"""Overlap, vigilance/defense, attack policy and diversification for the fast list."""
import sys
from multiprocessing import Pool
from harness import run, summary, paired
from decks import DECKS, swap_many
from scen import cfg
N = 3000
D = DECKS["Rápida B2"]
SC = ["Realista", "Combate fuerte", "Mesa agresiva", "Agresiva y nos apuntan"]
def causes(res):
    n = len(res)
    return (f"pierde x combate {100*sum(r['loss']=='combat' for r in res)/n:4.1f}%  x rival {100*sum(r['loss']=='rival' for r in res)/n:4.1f}%  "
            f"daño recibido {sum(r['taken'] for r in res)/n:4.1f}")
def row(pool, base, d, label, over=None):
    out = [f"{label:46s}"]
    for sc in SC:
        r = run(d, N, cfg=cfg(sc, **(over or {})), pool=pool)
        m, ci = paired(base[sc], r)
        out.append(f"{sc[:10]} {m:+5.1f}")
    print("  ".join(out), flush=True)
if __name__ == "__main__":
    step = sys.argv[1]
    with Pool() as pool:
        base = {sc: run(D, N, cfg=cfg(sc), pool=pool) for sc in SC}
        if step == "base":
            for sc in SC:
                s = summary(base[sc]); print(f"{sc:24s} win {s['win']:5.1f}  turno {s['mean_turn']:.2f}  {causes(base[sc])}")
        if step == "rancor":
            for c in ["Short Bow", "Long-Lost Lances", "Spider Umbra", "Shadowspear", "Snakeskin Veil", "Stony Strength",
                      "Gift of the Viper", "Tarrian's Soulcleaver", "Avarice Amulet", "Garruk's Uprising", "Blank"]:
                row(pool, base, swap_many(D, ["Rancor"], [c]), f"Rancor → {c}")
        if step == "vig":
            outs = ["Sixth Sense", "Thought Vessel", "Explore", "Mask of Memory"]
            for c in ["Short Bow", "Long-Lost Lances", "Tarrian's Soulcleaver", "Avarice Amulet", "Stony Strength",
                      "Gift of the Viper", "Seedborn Muse", "Silent Arbiter", "Spore Frog", "Fog", "Moment's Peace",
                      "Pariah's Shield", "Crawlspace", "Basilisk Collar"]:
                if c in D:
                    continue
                row(pool, base, swap_many(D, ["Sixth Sense"], [c]), f"Sixth Sense → {c}")
            row(pool, base, swap_many(D, outs, ["Short Bow", "Long-Lost Lances", "Avarice Amulet", "Tarrian's Soulcleaver"]),
                "4 de vigilancia (Bow, Lances, Amulet, Soulcleaver)")
        if step == "ataque":
            for pol in ["big:10", "big:15", "big:20", "safe"]:
                row(pool, base, D, f"política {pol}", dict(attack_policy=pol))
