from multiprocessing import Pool
from harness import run, paired, summary
from decks import DECKS, swap_many
from scen import cfg
D12 = swap_many(DECKS["Blor 1.1 (vigilancia)"], ["Forest"], ["Dryad Arbor"])
V = ["Blor 1.0", "Blor 1.0 económica", "Blor 1.1 (vigilancia)", "Blor 1.1 económica", "Rápida B2", "Rápida B3", "Rápida económica", "Rápida defensiva"]
SC = ["B1", "B2", "B3", "B4"]
N = 6000
if __name__ == "__main__":
    with Pool() as p:
        base = {sc: run(D12, N, cfg=cfg(sc), pool=p, seed0=910000) for sc in SC}
        print("Blor 1.2 ".ljust(24) + "  ".join(f"{sc} {summary(base[sc])['win']:.1f}%" for sc in SC), flush=True)
        for v in V:
            out = []
            for sc in SC:
                r = run(DECKS[v], N, cfg=cfg(sc), pool=p, seed0=910000)
                d = paired(base[sc], r)
                out.append(f"{sc} {summary(r)['win']:.1f}% ({d[0]:+.1f}±{d[1]:.1f})")
            print(f"{v:24s}" + "  ".join(out), flush=True)
