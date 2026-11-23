"""22/11b: cartas que convierten cada muerte del loop en robo o maná (doble rol), medidas en un cupo flojo."""
import sys
from multiprocessing import Pool
from scen import SCEN
from turnos import HOY, PLAN
from verif import sw
from harness import run, paired, summary
import statistics
C = ["Grim Haruspex", "Midnight Reaper", "Fecundity", "Smothering Abomination", "Skullclamp", "Yawgmoth, Thran Physician",
     "Ashnod's Altar", "Sifter of Skulls", "Sylvan Library"]
def med(r):
    return 100 * sum(1 for x in r if x[2] and x[1] <= 6) / len(r)
if __name__ == "__main__":
    N = 4000
    with Pool() as P:
        for dn, deck, slot in (("HOY", HOY, "Merchant of Venom"), ("PLAN", PLAN, "Bloodthrone Vampire")):
            for sc in ("goldfish", "B3", "Mazmorra"):
                for s0 in (1_900_000, 3_300_000):
                    kw = dict(mode="goldfish") if sc == "goldfish" else dict(mode="table", cfg=SCEN[sc])
                    b = run(deck, N, kw.pop("mode"), seed0=s0, pool=P, **kw)
                    line = f"{dn} {sc:8s} s{s0//100000}: base {summary(b)['combo' if sc=='goldfish' else 'win']:.1f}% ≤T6 {med(b):.1f}% |"
                    for c in C:
                        kw = dict(mode="goldfish") if sc == "goldfish" else dict(mode="table", cfg=SCEN[sc])
                        r = run(sw(deck, [(slot, c)]), N, kw.pop("mode"), seed0=s0, pool=P, **kw)
                        d, ci = paired(b, r, idx=2 if sc == 'goldfish' else 0)
                        line += f" {c.split(',')[0][:14]} {d:+.1f}" + (f"/≤T6 {med(r)-med(b):+.1f}" if sc == "goldfish" else "")
                    print(line, flush=True)
