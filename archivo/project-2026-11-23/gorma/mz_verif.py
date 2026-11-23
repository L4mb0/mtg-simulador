from multiprocessing import Pool
from harness import run, summary, paired
from mz_runs import cfg, sw, f, N, S2
from verif import V
from scen import CONS
from cards import swap
if __name__ == "__main__":
    with Pool() as P:
        print("== rutas en la Mazmorra (semillas nuevas): Mazmorra / optimista / pesimista ==")
        base = {sc: run(CONS, N, "table", cfg=cfg(sc), seed0=S2, pool=P) for sc in ("Mazmorra", "Mazmorra optimista", "Mazmorra pesimista")}
        for nm, d in V.items():
            row = []
            for sc in base:
                r = run(d, N, "table", cfg=cfg(sc), seed0=S2, pool=P)
                row.append(f"{summary(r)['win']:.1f}%")
            print(f"{nm:48s} " + " / ".join(row))
        print("\n== verificacion con semillas nuevas (por Pest Rescuer, sobre la 1.1) ==")
        for c in ("Sylvan Library", "Grim Tutor", "Finale of Devastation", "Dark Ritual"):
            row = []
            for sc in ("B3", "Mazmorra", "B2", "B4"):
                b = run(CONS, N, "table", cfg=cfg(sc), seed0=S2, pool=P)
                row.append(f"{sc} {f(paired(b, run(swap(CONS, 'Pest Rescuer', c), N, 'table', cfg=cfg(sc), seed0=S2, pool=P)))}")
            print(f"{c:24s} " + "  ".join(row))
