"""Que rol falta: sobre la fisica del 22/11, cambiar Merchant of Venom por una pieza de cada rol."""
from multiprocessing import Pool
from harness import run, paired, summary
from scen import SCEN
from verif import sw
from lineas import PHYS
N = 4000
V = {"+1 persist (Lesser Masticore)": "Lesser Masticore", "+1 persist (Wingrattle Scarecrow)": "Wingrattle Scarecrow",
     "+1 outlet (Spawning Pit)": "Spawning Pit", "+1 outlet-cierre (Ashnod's Altar)": "Ashnod's Altar",
     "+1 cierre (Bastion of Remembrance)": "Bastion of Remembrance", "+1 cierre (Walking Ballista)": "Walking Ballista",
     "+1 tutor (Dina's Guidance)": "Dina's Guidance"}
if __name__ == "__main__":
    with Pool() as P:
        for sc in ("B3", "Mazmorra"):
            for seed in (1_900_000, 3_300_000):
                b = run(PHYS, N, "table", cfg=SCEN[sc], seed0=seed, pool=P)
                print(f"== {sc} semillas {seed}: fisica {summary(b)['win']:.1f}% ==", flush=True)
                for nm, c in V.items():
                    d, ci = paired(b, run(sw(PHYS, [("Merchant of Venom", c)]), N, "table", cfg=SCEN[sc], seed0=seed, pool=P))
                    print(f"  {nm:38s} {d:+.1f} ±{ci:.1f}", flush=True)
