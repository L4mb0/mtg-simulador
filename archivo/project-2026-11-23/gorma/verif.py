from multiprocessing import Pool
from harness import run, summary, paired
from scen import ACTUAL, CONS, B
from cards import swap
N = 4000
S2 = 1_900_000
def sw(d, pairs):
    for o, i in pairs: d = swap(d, o, i)
    return d
OWN = sw(CONS, [("Pest Rescuer", "Altar of Dementia"), ("Mazirek, Kraul Death Priest", "Archdruid's Charm")])
V = {
 "1.0": ACTUAL, "1.1": CONS,
 "1.1 + tuyas (Altar, Charm)": OWN,
 "+ Blasting Station": sw(OWN, [("Jadar, Ghoulcaller of Nephalia", "Blasting Station")]),
 "+ Chord": sw(OWN, [("Jadar, Ghoulcaller of Nephalia", "Blasting Station"), ("Greater Good", "Chord of Calling")]),
 "+ Fauna": sw(OWN, [("Jadar, Ghoulcaller of Nephalia", "Blasting Station"), ("Greater Good", "Chord of Calling"), ("Morbid Opportunist", "Fauna Shaman")]),
 "completa (Wishclaw, Finale, Warren+Gravecrawler)": sw(OWN, [("Jadar, Ghoulcaller of Nephalia", "Blasting Station"), ("Greater Good", "Chord of Calling"),
      ("Morbid Opportunist", "Wishclaw Talisman"), ("Find // Finality", "Finale of Devastation"), ("Pitiless Plunderer", "Warren Soultrader"), ("Pest Infestation", "Gravecrawler")]),
}
if __name__ == "__main__":
    with Pool() as P:
        base = {br: run(CONS, N, "table", cfg=B(br), seed0=S2, pool=P) for br in ("B2", "B3", "B4")}
        for nm, d in V.items():
            row = []
            for br in ("B2", "B3", "B4"):
                r = run(d, N, "table", cfg=B(br), seed0=S2, pool=P)
                row.append(f"{br} {summary(r)['win']:.1f}% ({paired(base[br], r)[0]:+.1f})")
            g = run(d, N, "goldfish", seed0=S2, pool=P)
            c6 = 100 * sum(1 for x in g if x[2] and x[1] <= 5) / N
            print(f"{nm:48s} " + "  ".join(row) + f"  | goldfish T{summary(g)['mean_turn']:.1f}, combo antes del T6 {c6:.0f}%")
