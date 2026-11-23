from multiprocessing import Pool
import engine
from harness import run, paired, summary
from decks import DECKS, swap_many
from scen import cfg
D = DECKS["Blor 1.5"]; N = 6000
OUTS = ["Sword of Truth and Justice", "Sylvan Library", "Short Bow", "Long-Lost Lances", "Tarrian's Soulcleaver"]
# cuanto da Primal Bellow cuando se lanza
_orig = engine.Game.apply_pumps
def ap(self, combo, budget):
    if "Primal Bellow" in combo:
        self.stats["bellow"] = self.stats.get("bellow", 0) + self.forests()
        self.stats["bellow_n"] = self.stats.get("bellow_n", 0) + 1
    return _orig(self, combo, budget)
engine.Game.apply_pumps = ap
def job(s):
    g = engine.play(D, 1400000 + s, cfg=cfg("B2")); return g.stats.get("bellow", 0), g.stats.get("bellow_n", 0)
if __name__ == "__main__":
    with Pool() as p:
        r = p.map(job, range(4000), chunksize=100)
        n = sum(x[1] for x in r)
        print(f"Primal Bellow: lanzado en {100*n/4000:.0f}% de partidas, +{sum(x[0] for x in r)/max(1,n):.1f}/+.. de media")
        print("1.5 vs 1.4:", [ (sc, paired(run(DECKS['Blor 1.4'], N, cfg=cfg(sc), pool=p, seed0=1500000), run(D, N, cfg=cfg(sc), pool=p, seed0=1500000))) for sc in ["B2"] ])
        for kw, scs in [({}, ["B2", "B1", "B3"]), (dict(p_big=0.3), ["B2"])]:
            base = {sc: run(D, N, cfg=cfg(sc, **kw), pool=p, seed0=1500000) for sc in scs}
            print("1.5:", {sc: round(summary(base[sc])['win'], 1) for sc in scs}, kw, flush=True)
            for o in OUTS:
                ds = [paired(base[sc], run(swap_many(D, [o], ["Ohran Frostfang"]), N, cfg=cfg(sc, **kw), pool=p, seed0=1500000)) for sc in scs]
                print(("BIG " if kw else "") + f"Ohran Frostfang por {o}: " + "  ".join(f"{sc} {d[0]:+.1f}±{d[1]:.1f}" for sc, d in zip(scs, ds)), flush=True)
