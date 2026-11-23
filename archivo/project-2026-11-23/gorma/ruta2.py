from multiprocessing import Pool
from harness import run, summary, paired
from mz_runs import cfg, sw, N, S2
from scen import CONS
from verif import OWN
V = {
 "1.1": CONS,
 "1.1 + tuyas (Altar, Charm)": OWN,
 "ruta 16/11: + Blasting, Chord, Fauna": sw(OWN, [("Jadar, Ghoulcaller of Nephalia", "Blasting Station"), ("Greater Good", "Chord of Calling"), ("Morbid Opportunist", "Fauna Shaman")]),
 "+ Walking Ballista": sw(OWN, [("Jadar, Ghoulcaller of Nephalia", "Walking Ballista")]),
 "+ Ballista, Sylvan Library": sw(OWN, [("Jadar, Ghoulcaller of Nephalia", "Walking Ballista"), ("Greater Good", "Sylvan Library")]),
 "+ Ballista, Sylvan, Carpet": sw(OWN, [("Jadar, Ghoulcaller of Nephalia", "Walking Ballista"), ("Greater Good", "Sylvan Library"), ("Morbid Opportunist", "Carpet of Flowers")]),
 "+ Ballista, Sylvan, Carpet, Chord": sw(OWN, [("Jadar, Ghoulcaller of Nephalia", "Walking Ballista"), ("Greater Good", "Sylvan Library"), ("Morbid Opportunist", "Carpet of Flowers"), ("Find // Finality", "Chord of Calling")]),
 "+ Ballista, Sylvan, Carpet, Chord, Blasting": sw(OWN, [("Jadar, Ghoulcaller of Nephalia", "Walking Ballista"), ("Greater Good", "Sylvan Library"), ("Morbid Opportunist", "Carpet of Flowers"), ("Find // Finality", "Chord of Calling"), ("Pitiless Plunderer", "Blasting Station")]),
}
SC = ("B3", "B2", "B4", "Mazmorra", "Mazmorra optimista", "Mazmorra pesimista")
if __name__ == "__main__":
    with Pool() as P:
        print(f"{'':46s} " + "  ".join(f"{s[:13]:>13s}" for s in SC) + "   goldfish / combo<T6")
        for nm, d in V.items():
            row = [f"{summary(run(d, N, 'table', cfg=cfg(s), seed0=S2, pool=P))['win']:13.1f}" for s in SC]
            g = run(d, N, "goldfish", seed0=S2, pool=P)
            c6 = 100 * sum(1 for x in g if x[2] and x[1] <= 5) / N
            print(f"{nm:46s} " + "  ".join(row) + f"   T{summary(g)['mean_turn']:.1f} / {c6:.0f}%")
