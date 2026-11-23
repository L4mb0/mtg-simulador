"""Token makers against edicts (Juan, 13/11): enchantments, auras, living-weapon equipment and creature lands."""
from multiprocessing import Pool
from harness import run, summary, paired, paired_turn, cast_rate
from decks import DECKS, swap_many
from scen import cfg
N = 4000
D = DECKS["Blor 1.1 (vigilancia)"]
SC = ["Edictos castiga", "Forge edictos", "Realista castiga", "Calibrada castiga", "Forge"]
def eb(res):
    return 100 * sum(1 for r in res if r["edict_blor"]) / len(res)
OUT = "Hunter's Insight"
V = {f"+ {c}": swap_many(D, [OUT], [c]) for c in
     ["Verdant Embrace", "Awakening Zone", "From Beyond", "Nettlecyst", "Batterskull", "Flayer Husk"]}
for l in ["Lair of the Hydra", "Treetop Village", "Mutavault", "Dryad Arbor"]:
    V[f"+ {l} (por Forest)"] = swap_many(D, ["Forest"], [l])
V["Combo: Verdant Embrace + Awakening Zone + Lair + Dryad Arbor"] = swap_many(
    D, [OUT, "Inquisitor's Flail", "Forest", "Forest"], ["Verdant Embrace", "Awakening Zone", "Lair of the Hydra", "Dryad Arbor"])
if __name__ == "__main__":
    with Pool() as pool:
        b = {sc: run(D, N, cfg=cfg(sc), pool=pool) for sc in SC}
        g0 = run(D, N, mode="goldfish", pool=pool)
        print("1.1 edicto se lleva a Blor: " + "  ".join(f"{sc[:12]} {eb(b[sc]):.0f}%" for sc in SC))
        for k, d in V.items():
            g = run(d, N, mode="goldfish", pool=pool)
            row = [f"{k:62s} gf {paired_turn(g0, g)[0]:+.2f}"]
            for sc in SC:
                r = run(d, N, cfg=cfg(sc), pool=pool)
                row.append(f"{sc[:12]} {paired(b[sc], r)[0]:+5.1f} ({eb(r):.0f}%)")
            name = k[2:].split(" (")[0]
            if not k.startswith("Combo"):
                row.append(f"lanzada {cast_rate(r, name):.0f}%")
            print("  ".join(row), flush=True)
