from multiprocessing import Pool
from harness import run, paired
from decks import DECKS, swap_many
from scen import cfg
D = swap_many(DECKS["Blor 1.1 (vigilancia)"], ["Forest"], ["Dryad Arbor"])
SC = ["B2", "B1", "B3"]; N = 8000
TESTS = [(["Krosan Grip"], ["Pariah's Shield"], {}), (["Colossus Hammer"], ["Pariah's Shield"], {}),
         (["Krosan Grip"], ["Allosaurus Shepherd"], {}), (["Krosan Grip"], ["Destiny Spinner"], {}),
         (["Krosan Grip", "Colossus Hammer"], ["Pariah's Shield", "Allosaurus Shepherd"], {}),
         (["Krosan Grip"], ["Pariah's Shield"], dict(w_plan=0.25)),
         (["Krosan Grip"], ["Crystal Chimes"], dict(aem=0.6)), (["Colossus Hammer"], ["Darksteel Plate"], dict(aem=0.6))]
if __name__ == "__main__":
    with Pool() as p:
        bases = {}
        for o, i, kw in TESTS:
            out = []
            for sc in SC:
                key = (sc, tuple(sorted(kw.items())))
                if key not in bases:
                    bases[key] = run(D, N, cfg=cfg(sc, **kw), pool=p, seed0=950000)
                d = paired(bases[key], run(swap_many(D, o, i), N, cfg=cfg(sc, **kw), pool=p, seed0=950000))
                out.append(f"{sc} {d[0]:+.1f}±{d[1]:.1f}")
            print(f"{'+'.join(i)} por {'+'.join(o)} {kw}: " + "  ".join(out), flush=True)
