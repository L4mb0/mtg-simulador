"""Candidatas con la mesa v2 contra cartas de rol parecido. B2 (objetivo), B1 y B3."""
from multiprocessing import Pool
from harness import run, paired
from decks import DECKS, swap_many
from scen import cfg
D = swap_many(DECKS["Blor 1.1 (vigilancia)"], ["Forest"], ["Dryad Arbor"])
SW = [("Rampant Growth", c) for c in ["Semblance Anvil", "Foundry Inspector", "Cloud Key", "Jhoira's Familiar", "Helm of Awakening", "Brass Squire"]] + \
     [("Colossus Hammer", c) for c in ["Hammer of Nazahn", "Shuko", "Whispersilk Cloak", "Conqueror's Flail", "Pariah's Shield", "Darksteel Plate"]] + \
     [("Krosan Grip", c) for c in ["Allosaurus Shepherd", "Destiny Spinner", "Crystal Chimes", "Conqueror's Flail", "Pariah's Shield", "Whispersilk Cloak"]] + \
     [("Forest", "Mutavault")]
SC = ["B2", "B1", "B3"]; N = 6000
if __name__ == "__main__":
    with Pool() as p:
        base = {sc: run(D, N, cfg=cfg(sc), pool=p, seed0=920000) for sc in SC}
        for o, i in SW:
            ds = [paired(base[sc], run(swap_many(D, [o], [i]), N, cfg=cfg(sc), pool=p, seed0=920000)) for sc in SC]
            print(f"{i:22s} por {o:16s} " + "  ".join(f"{sc} {d[0]:+.1f}±{d[1]:.1f}" for sc, d in zip(SC, ds)), flush=True)
        for sc in SC:
            r = run(D, N, cfg=cfg(sc, ceil_attach=True), pool=p, seed0=920000)
            d = paired(base[sc], r); print(f"TECHO adjuntos intocables {sc} {d[0]:+.1f}±{d[1]:.1f}", flush=True)
