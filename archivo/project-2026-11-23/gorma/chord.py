"""Chord of Calling vs Worldly Tutor vs Diabolic Intent en el cupo de la ruta (por Morbid Opportunist)."""
from multiprocessing import Pool
from harness import run, paired, summary
from scen import SCEN
from verif import OWN, sw
N = 4000
BASE3 = [("Jadar, Ghoulcaller of Nephalia", "Walking Ballista"), ("Greater Good", "Carpet of Flowers"), ("Find // Finality", "Blasting Station")]
OPTS = {"Morbid (sin tutor)": [], "Chord of Calling": [("Morbid Opportunist", "Chord of Calling")],
        "Worldly Tutor": [("Morbid Opportunist", "Worldly Tutor")], "Diabolic Intent": [("Morbid Opportunist", "Diabolic Intent")], "Finale of Devastation": [("Morbid Opportunist", "Finale of Devastation")], "Grim Tutor": [("Morbid Opportunist", "Grim Tutor")],
        "Worldly + Intent (por Morbid y Pest Infestation)": [("Morbid Opportunist", "Worldly Tutor"), ("Pest Infestation", "Diabolic Intent")],
        "Chord + Worldly (por Morbid y Pest Infestation)": [("Morbid Opportunist", "Chord of Calling"), ("Pest Infestation", "Worldly Tutor")]}
if __name__ == "__main__":
    with Pool() as P:
        for seed in (1_900_000, 3_300_000):
            print(f"\n#### semillas {seed}")
            for sc in ("B3", "Mazmorra"):
                ref = sw(OWN, BASE3 + OPTS["Chord of Calling"])
                b = run(ref, N, "table", cfg=SCEN[sc], seed0=seed, pool=P)
                print(f"== {sc}: ruta con Chord {summary(b)['win']:.1f}% ==")
                for nm, extra in OPTS.items():
                    if nm == "Chord of Calling": continue
                    d, ci = paired(b, run(sw(OWN, BASE3 + extra), N, "table", cfg=SCEN[sc], seed0=seed, pool=P))
                    print(f"  {nm:48s} {d:+.1f} ±{ci:.1f} vs Chord", flush=True)
        for nm, extra in OPTS.items():
            g = summary(run(sw(OWN, BASE3 + extra), N, "goldfish", seed0=1_900_000, pool=P))
            print(f"goldfish {nm:48s} {g}")
