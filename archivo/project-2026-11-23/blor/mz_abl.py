from multiprocessing import Pool
from harness import run, paired, summary
from decks import DECKS, swap_many
from scen import cfg
D = DECKS["Blor 1.6"]; N = 4000
if __name__ == "__main__":
    with Pool() as p:
        for sc in ("Mazmorra", "B3"):
            base = run(D, N, cfg=cfg(sc), pool=p, seed0=4200000)
            print(sc, "base", round(summary(base)['win'], 2), flush=True)
            for c in sorted(set(D)):
                if c == "Forest": continue
                d = paired(base, run(swap_many(D, [c], ["Blank"]), N, cfg=cfg(sc), pool=p, seed0=4200000))
                print(sc, c, f"{d[0]:+.2f}", flush=True)
