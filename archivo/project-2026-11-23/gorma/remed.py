"""Re-medicion con la mesa v2 (16/11): ablacion, 1.1, temporales, candidatas, Gorma. Uso: python3 remed.py <etapa>"""
import sys, json, dataclasses
from multiprocessing import Pool
from harness import run, summary, paired
from scen import SCEN, ACTUAL, CONS, SWAPS_11, B
from cards import swap, CARDS
from cards import physical_deck
N = 4000
S1, S2 = 500_000, 1_900_000
DEF = {"Foot Chopper", "The Gitrog, Ravenous Ride", "Jenova, Ancient Calamity", "Feral Ghoul", "Rampant Rejuvenator",
       "Culling Ritual", "Vicious Rivalry", "Traverse the Outlands", "Selvala, Heart of the Wilds", "Insidious Fungus",
       "Butcher of Malakir", "Jarad, Golgari Lich Lord", "Garruk's Uprising", "Moldervine Reclamation", "Priest of Forgotten Gods"}
def R(d, br="B3", seed=S1, P=None, **kw):
    cfg = B(br, **kw)
    return run(d, N, "table", cfg=cfg, seed0=seed, pool=P)
def fmt(x): return f"{x[0]:+.1f} ±{x[1]:.1f}"
def ablation(deck, P, br="B3"):
    b = R(deck, br, P=P); out = []
    for c in sorted(set(x for x in deck if x in CARDS)):
        out.append((paired(b, R(swap(deck, c, "Blank"), br, P=P)), c))
    return summary(b)["win"], sorted(out)
if __name__ == "__main__":
    st = sys.argv[1]
    res = {}
    with Pool() as P:
        if st == "abl":
            for nm, d in (("1.0", ACTUAL), ("1.1", CONS)):
                base, out = ablation(d, P)
                print(f"\\n== ablacion {nm} en B3 (base {base:.1f}%) ==")
                for (dd, ci), c in out:
                    print(f"{c:34s} {dd:+.1f} ±{ci:.1f}{'  (defendida)' if c in DEF else ''}")
                res[nm] = [(c, dd, ci) for (dd, ci), c in out]
        if st == "ruta":
            b = {br: R(ACTUAL, br, P=P) for br in ("B2", "B3", "B4")}
            print("== cambios de la 1.1 uno por uno sobre la 1.0 (B3 / B2 / B4) ==")
            for o, i in SWAPS_11:
                d = swap(ACTUAL, o, i)
                r = {br: paired(b[br], R(d, br, P=P)) for br in b}
                print(f"{o:28s} -> {i:24s} B3 {fmt(r['B3'])}  B2 {fmt(r['B2'])}  B4 {fmt(r['B4'])}")
            print("== 1.1 completa (semillas nuevas) ==")
            for br in ("B2", "B3", "B3+B4", "B4"):
                a = R(ACTUAL, br, seed=S2, P=P); t = R(CONS, br, seed=S2, P=P)
                print(f"{br:6s} 1.0 {summary(a)['win']:.1f}% -> 1.1 {summary(t)['win']:.1f}%  ({fmt(paired(a, t))})")
            # temporales (fisica provisional)
            print("== temporales (B3) ==")
            phys = swap(physical_deck(), "Woodfall Primus", "Woe Strider")
            a = R(ACTUAL, P=P)
            print("Twitching Doll en vez de Insidious Fungus:", fmt(paired(a, R(swap(ACTUAL, "Insidious Fungus", "Twitching Doll"), P=P))))
            print("Blade of the Bloodchief en vez de Rendclaw Trow:", fmt(paired(a, R(swap(ACTUAL, "Rendclaw Trow", "Blade of the Bloodchief"), P=P))))
            print("fisica de hoy (Doll, Blade, Woodfall) vs 1.0:", fmt(paired(a, R(physical_deck(), P=P))))
        if st == "gorma":
            for nm, d in (("1.0", ACTUAL), ("1.1", CONS)):
                for br in ("B3", "B2", "B4"):
                    a = R(d, br, P=P)
                    s = summary(a)["win"]
                    r1 = paired(a, R(d, br, P=P, gorma_policy="support")); r2 = paired(a, R(d, br, P=P, gorma_policy="combo"))
                    print(f"{nm} {br}: apenas puede {s:.1f}%  | con soporte {fmt(r1)} | solo en el combo {fmt(r2)}")
