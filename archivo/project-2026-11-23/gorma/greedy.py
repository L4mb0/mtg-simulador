from multiprocessing import Pool
from harness import run, summary, paired
from scen import CONS, B
from cards import swap
N = 4000
def R(d, br="B3", seed=500_000, P=None):
    return run(d, N, "table", cfg=B(br), seed0=seed, pool=P)
def f(x): return f"{x[0]:+.1f} ±{x[1]:.1f}"
PRICE = {"Blasting Station": 13.99, "Chord of Calling": 9.49, "Fauna Shaman": 3.99, "Wishclaw Talisman": 3.99,
         "Grim Tutor": 27.99, "Finale of Devastation": None, "Ashnod's Altar": 18.99, "Warren Soultrader": 29.99,
         "Beseech the Mirror": None, "The Meathook Massacre": None, "Vengeance Mission": 0.35}
OUTS = ["Jadar, Ghoulcaller of Nephalia", "Greater Good", "Morbid Opportunist", "Find // Finality", "Pitiless Plunderer", "Pest Infestation"]
if __name__ == "__main__":
    with Pool() as P:
        b0 = R(CONS, P=P)
        own = swap(swap(CONS, "Pest Rescuer", "Altar of Dementia"), "Mazirek, Kraul Death Priest", "Archdruid's Charm")
        bo = R(own, P=P)
        print(f"1.1 {summary(b0)['win']:.1f}% -> + Altar of Dementia + Archdruid's Charm (ya tuyas) {summary(bo)['win']:.1f}% ({f(paired(b0, bo))})")
        ow = swap(own, "Jadar, Ghoulcaller of Nephalia", "Worldly Tutor")
        print(f"   + Worldly Tutor (Game Changer, ya tuya; por Jadar): {f(paired(bo, R(ow, P=P)))}")
        cur, bc = own, bo
        pool = list(PRICE)
        outs = list(OUTS)
        for step in range(6):
            o = outs[0]; best = None
            for c in pool:
                if c == "Warren Soultrader":
                    if len(outs) < 2: continue
                    d = swap(swap(cur, o, c), outs[1], "Gravecrawler")
                else:
                    d = swap(cur, o, c)
                r = R(d, P=P); g = paired(bc, r)
                if best is None or g[0] > best[1][0]:
                    best = (c, g, d, r)
            c, g, d, r = best
            if g[0] < 0.5:
                print(f"paso {step+1}: nada suma 0,5 o más (mejor {c} {f(g)}); fin"); break
            used = 2 if c == "Warren Soultrader" else 1
            print(f"paso {step+1}: {c}{' + Gravecrawler' if used == 2 else ''} por {', '.join(outs[:used])}: {f(g)} -> {summary(r)['win']:.1f}%")
            cur, bc = d, r; pool.remove(c); outs = outs[used:]
        import json; json.dump(cur, open("ruta12.json", "w"))
