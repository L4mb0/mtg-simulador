"""22/11b: dobles rol que REEMPLAZAN una pieza (outlet que da maná o robo) y más maná, en el plan."""
from multiprocessing import Pool
from scen import SCEN
from turnos import PLAN, HOY
from verif import sw
from harness import run, paired, summary
import statistics
V = [("Feeder→Ashnod", [("Carrion Feeder", "Ashnod's Altar")]),
     ("Feeder→Yawgmoth", [("Carrion Feeder", "Yawgmoth, Thran Physician")]),
     ("Seer→Ashnod", [("Viscera Seer", "Ashnod's Altar")]),
     ("Bloodthrone→Ashnod", [("Bloodthrone Vampire", "Ashnod's Altar")]),
     ("Bloodthrone→Yawgmoth", [("Bloodthrone Vampire", "Yawgmoth, Thran Physician")]),
     ("Bloodthrone→Talisman", [("Bloodthrone Vampire", "Talisman of Resilience")]),
     ("DiabolicTutor→Intent", [("Diabolic Tutor", "Diabolic Intent")]),
     ("Bloodthrone→Ashnod + Feeder→Yawgmoth", [("Bloodthrone Vampire", "Ashnod's Altar"), ("Carrion Feeder", "Yawgmoth, Thran Physician")])]
def tw(r):
    w = [x[1] for x in r if x[0]]; return statistics.mean(w)
if __name__ == "__main__":
    N = 4000
    with Pool() as P:
        for dn, deck in (("PLAN", PLAN), ("HOY", HOY)):
            vs = V if dn == "PLAN" else [("Merchant→Ashnod", [("Merchant of Venom", "Ashnod's Altar")]), ("Merchant→Yawgmoth", [("Merchant of Venom", "Yawgmoth, Thran Physician")]),
                                         ("DiabolicTutor→Intent", [("Diabolic Tutor", "Diabolic Intent")]), ("Merchant→Talisman", [("Merchant of Venom", "Talisman of Resilience")])]
            for sc in ("B3", "Mazmorra"):
                for s0 in (1_900_000, 3_300_000):
                    b = run(deck, N, "table", cfg=SCEN[sc], seed0=s0, pool=P)
                    print(f"\n{dn} {sc} s{s0//100000}: base {summary(b)['win']:.1f}% (turno medio de victoria {tw(b):.2f})", flush=True)
                    for n, pairs in vs:
                        r = run(sw(deck, pairs), N, "table", cfg=SCEN[sc], seed0=s0, pool=P)
                        d, ci = paired(b, r)
                        print(f"  {n:40s} {d:+.1f} ±{ci:.1f}  T̄ {tw(r)-tw(b):+.2f}", flush=True)
