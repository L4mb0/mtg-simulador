from multiprocessing import Pool
from harness import run, paired, summary
from decks import DECKS, swap_many
from scen import cfg
D = DECKS["Blor 1.6"]; N = 10000; S = 9100000
V = [("Lotus Bloom", "Snake Umbra"), ("Lotus Bloom", "Short Bow"), ("Lotus Bloom", "Hunter's Insight"), ("Roiling Canopy", "Forest")]
if __name__ == "__main__":
    with Pool() as p:
        for br in ("B2", "B1", "B3"):
            base = run(D, N, cfg=cfg(br), pool=p, seed0=S)
            print(br, "1.6", round(summary(base)['win'], 1), flush=True)
            for c, o in V:
                r = run(swap_many(D, [o], [c]), N, cfg=cfg(br), pool=p, seed0=S)
                d = paired(base, r)
                extra = ""
                if c == "Lotus Bloom":
                    extra = f" (llega en {100*sum(1 for x in r if x['cast'].get('(act) Lotus Bloom'))/N:.0f}%)"
                print(f"  {c} por {o}: {d[0]:+.1f} ±{d[1]:.1f}{extra}", flush=True)
            if br == "B2":
                r = run(swap_many(D, ["Snake Umbra"], ["Skullclamp"]), N, cfg=cfg(br), pool=p, seed0=S)
                n = sum(x['cast'].get('(act) Skullclamp', 0) for x in r) / N
                print(f"  Skullclamp por Snake Umbra: {paired(base, r)[0]:+.1f}; activaciones por partida {n:.2f}", flush=True)
