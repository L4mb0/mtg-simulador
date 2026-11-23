"""22/11: cartas que juntan roles (o cierran sin maná ni robo) sobre la física con Fungus y Rendclaw, por Merchant of Venom."""
from multiprocessing import Pool
from harness import run, paired, summary
from scen import SCEN
from verif import sw
from lineas import PHYS_LLEGAN as D
N = 4000
V = {"Walking Ballista (cierre a 0 de maná)": "Walking Ballista", "Ashnod's Altar (outlet + maná)": "Ashnod's Altar",
     "Diabolic Intent (tutor; sacrifica)": "Diabolic Intent", "Lesser Masticore (persist, referencia)": "Lesser Masticore",
     "Dina's Guidance (tutor de criatura)": "Dina's Guidance", "Sylvan Library (robo)": "Sylvan Library"}
if __name__ == "__main__":
    with Pool() as P:
        for sc in ("B3", "Mazmorra"):
            for seed in (1_900_000, 3_300_000):
                b = run(D, N, "table", cfg=SCEN[sc], seed0=seed, pool=P)
                print(f"== {sc} semillas {seed}: base {summary(b)['win']:.1f}% ==", flush=True)
                for nm, c in V.items():
                    d, ci = paired(b, run(sw(D, [("Merchant of Venom", c)]), N, "table", cfg=SCEN[sc], seed0=seed, pool=P))
                    print(f"  {nm:40s} {d:+.1f} ±{ci:.1f}", flush=True)
