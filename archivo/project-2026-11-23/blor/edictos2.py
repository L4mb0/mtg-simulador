from multiprocessing import Pool
from harness import run, summary, paired, paired_turn
from decks import DECKS, swap_many
from scen import cfg
N = 4000
D = DECKS["Blor 1.1 (vigilancia)"]
SC = ["Edictos castiga", "Forge edictos", "Realista castiga", "Calibrada castiga", "Forge"]
def eb(res):
    return 100 * sum(1 for r in res if r["edict_blor"]) / len(res)
P6_OUT = ["Hunter's Insight", "Inquisitor's Flail", "Forest", "Rishkar's Expertise", "Return of the Wildspeaker", "Crystalline Armor"]
P6_IN = ["Tendershoot Dryad", "Esika's Chariot", "Dryad Arbor", "Sprout Swarm", "Assault Suit", "Scute Swarm"]
AUR = ["Ancestral Mask", "Hydra's Growth", "Level Up"]
EQ = ["Sword of Feast and Famine", "Umezawa's Jitte", "Loxodon Warhammer"]
V = {
    "Sprout Swarm (guardando 2 de maná)": swap_many(D, ["Hunter's Insight"], ["Sprout Swarm"]),
    "Paquete anti-edicto de 6": swap_many(D, P6_OUT, P6_IN),
    "Paquete anti-edicto de 3 (Tendershoot, Dryad Arbor, Sprout Swarm)": swap_many(D, P6_OUT[:3], ["Tendershoot Dryad", "Dryad Arbor", "Sprout Swarm"]),
    "3 auras → 3 equipos": swap_many(D, AUR, EQ),
}
if __name__ == "__main__":
    with Pool() as pool:
        b = {sc: run(D, N, cfg=cfg(sc), pool=pool) for sc in SC}
        g0 = run(D, N, mode="goldfish", pool=pool)
        for k, d in V.items():
            g = run(d, N, mode="goldfish", pool=pool)
            row = [f"{k:62s} gf {paired_turn(g0, g)[0]:+.2f}"]
            for sc in SC:
                r = run(d, N, cfg=cfg(sc), pool=pool)
                row.append(f"{sc[:12]} {paired(b[sc], r)[0]:+5.1f} ({eb(b[sc]):.0f}→{eb(r):.0f}%)")
            print("  ".join(row), flush=True)
