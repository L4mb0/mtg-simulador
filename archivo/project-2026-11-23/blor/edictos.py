"""Edicts against Blor: what keeps him alive when a rival forces a sacrifice?"""
from multiprocessing import Pool
from harness import run, summary, paired, paired_turn
from decks import DECKS, swap_many
from scen import cfg
N = 4000
D = DECKS["Blor 1.1 (vigilancia)"]
SC = ["Edictos castiga", "Forge edictos", "Realista castiga", "Forge"]
OUT = "Hunter's Insight"
SINGLE = ["Assault Suit", "Tendershoot Dryad", "Esika's Chariot", "Scute Swarm", "Sprout Swarm", "Wood Elves",
          "Kodama of the West Tree", "Saproling Migration", "Garruk, Primal Hunter", "Spore Frog", "Toski, Bearer of Secrets"]
def eb(res):
    n = len(res)
    return 100 * sum(1 for r in res if r["edict_blor"]) / n
if __name__ == "__main__":
    with Pool() as pool:
        b = {sc: run(D, N, cfg=cfg(sc), pool=pool) for sc in SC}
        print("1.1: " + "  ".join(f"{sc} {summary(b[sc])['win']:.1f} (edicto se lleva a Blor en {eb(b[sc]):.1f}% de las partidas)" for sc in SC))
        V = {f"+ {c}": swap_many(D, [OUT], [c]) for c in SINGLE}
        V["Sin Tajuru Preserver"] = swap_many(D, ["Tajuru Preserver"], ["Sixth Sense"])
        V["+ Dryad Arbor (por Forest)"] = swap_many(D, ["Forest"], ["Dryad Arbor"])
        V["Paquete: Tendershoot + Esika + Dryad Arbor + Assault Suit"] = swap_many(
            D, [OUT, "Inquisitor's Flail", "Forest", "Rishkar's Expertise"],
            ["Tendershoot Dryad", "Esika's Chariot", "Dryad Arbor", "Assault Suit"])
        V["Paquete barato: Tendershoot + Dryad Arbor + Sprout Swarm"] = swap_many(
            D, [OUT, "Forest", "Inquisitor's Flail"], ["Tendershoot Dryad", "Dryad Arbor", "Sprout Swarm"])
        for k, d in V.items():
            row = [f"{k:58s}"]
            for sc in SC:
                r = run(d, N, cfg=cfg(sc), pool=pool)
                row.append(f"{sc[:12]} {paired(b[sc], r)[0]:+5.1f} ({eb(r):.1f}%)")
            print("  ".join(row), flush=True)
