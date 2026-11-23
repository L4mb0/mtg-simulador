"""22/11 (Juan: 'prueba lo que tengas que probar'): Lotus Bloom con mas partidas y Skullclamp agresivo."""
from multiprocessing import Pool
import engine
from harness import run, paired, summary
from decks import DECKS, swap_many
from scen import cfg
D = DECKS["Blor 1.6"]; S = 7700000

def aggro(flag):
    engine.CLAMP_AGGRO = flag

if __name__ == "__main__":
    with Pool() as p:
        for br, N in (("B2", 20000), ("B1", 10000), ("B3", 10000), ("Mazmorra", 10000)):
            base = run(D, N, cfg=cfg(br), pool=p, seed0=S)
            for o in ("Snake Umbra", "Hunter's Insight"):
                d = paired(base, run(swap_many(D, [o], ["Lotus Bloom"]), N, cfg=cfg(br), pool=p, seed0=S))
                print(f"{br} base {summary(base)['win']:.1f}  Lotus Bloom por {o}: {d[0]:+.2f} ±{d[1]:.2f}", flush=True)
            if br == "B2":
                d = paired(base, run(swap_many(D, ["Snake Umbra", "Hunter's Insight"], ["Lotus Bloom", "Skullclamp"]), N, cfg=cfg(br), pool=p, seed0=S))
                print(f"B2 Lotus Bloom + Skullclamp por Snake + Hunter's: {d[0]:+.2f} ±{d[1]:.2f}", flush=True)
                p.map(aggro, [True] * 64)
                r = run(swap_many(D, ["Snake Umbra"], ["Skullclamp"]), N, cfg=cfg(br), pool=p, seed0=S)
                p.map(aggro, [False] * 64)
                n = sum(x['cast'].get('(act) Skullclamp', 0) for x in r) / N
                print(f"B2 Skullclamp AGRESIVO por Snake Umbra: {paired(base, r)[0]:+.2f}  activaciones {n:.2f}", flush=True)
