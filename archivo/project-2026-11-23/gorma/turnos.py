"""22/11: lineas de combo por turno (goldfish y B3) en la fisica de hoy y en el plan aprobado; y re-medicion de los cambios pendientes."""
import random, sys, collections, statistics
from multiprocessing import Pool
from engine import Game
from scen import SCEN, SWAPS_11
from cards import target_deck
from verif import sw
from harness import run, paired, summary
A, Bc = ("Pest Rescuer", "Altar of Dementia"), ("Mazirek, Kraul Death Priest", "Archdruid's Charm")
HOY = sw(target_deck(), [("Bloodghast", "Blasting Station"), ("Nether Traitor", "Carrion Feeder"), A])   # con Fungus y Rendclaw recogidas
PLAN = sw(target_deck(), SWAPS_11 + [A, Bc])                                                           # 1.1 aprobada + A + B (Woodfall se queda)
NAME = {"drainer": "Drenador en mesa", "mill": "Altar of Dementia (mill)", "station": "Blasting Station", "gg-dig": "Greater Good cava",
        "hand": "Cierre en la mano", "feral": "Feral Ghoul", "jarad": "Jarad en mesa (sacrifica a Gorma)", "tutor": "Tutor busca el cierre",
        "dig": "Moldervine cava", "uprising-dig": "Garruk's Uprising cava", "plea": "Zealot + Desperate Plea", "find": "Zealot + Find",
        "zealot-draw": "Zealot + Morbid/Dina", "zealot-veinwitch": "Zealot + Veinwitch", "zealot-jarad": "Zealot → Jarad del cementerio",
        "jaradgy": "Jarad desde el cementerio", "daemogoth": "Daemogoth", "ballista": "Walking Ballista"}
def nm(c):
    c = str(c)
    if c.startswith("inf+"): return "Maná infinito + " + {"hand": "cierre en mano", "tutor": "tutor", "dig": "cavar", "jaradgy": "Jarad del cementerio",
                                                         "zealot": "Zealot→Jarad", "daemogoth": "Daemogoth"}.get(c[4:], c[4:])
    if "+" in c and (c.startswith("recur") or c.startswith("maz") or c.startswith("chatter") or c.startswith("hunters")): return "Línea sin Gorma: " + c
    return NAME.get(c, c)
def one(a):
    deck, mode, seed = a
    g = Game(deck, random.Random(seed), mode=mode, cfg=None if mode == "goldfish" else SCEN["B3"])
    g.run()
    return (g.won, g.stats.get("closer"), g.win_turn)
if __name__ == "__main__":
    N = 4000
    with Pool() as P:
        if "lineas" in sys.argv:
            for dn, deck in (("HOY (con Fungus y Rendclaw)", HOY), ("PLAN 1.1 + A + B", PLAN)):
                for mode in ("goldfish", "table"):
                    res = P.map(one, [(deck, mode, 1_900_000 + i) for i in range(N)], chunksize=100)
                    w = [r for r in res if r[0] and r[1]]
                    allw = [r[2] for r in res if r[0]]
                    print(f"\n### {dn} / {'goldfish' if mode=='goldfish' else 'B3'}: gana {100*len(allw)/N:.1f}% (combo {100*len(w)/N:.1f}%), turno medio {statistics.mean([r[2] for r in w]):.1f}, mediana {statistics.median([r[2] for r in w])}")
                    by = collections.defaultdict(list)
                    for r in w: by[nm(r[1])].append(r[2])
                    for k, ts in sorted(by.items(), key=lambda kv: -len(kv[1])):
                        ts.sort()
                        print(f"  {k:42s} {100*len(ts)/N:5.1f}% de las partidas | primero T{ts[0]} | mediana T{statistics.median(ts):.0f} | ≤T6 {100*sum(t<=6 for t in ts)/N:.1f}% ≤T8 {100*sum(t<=8 for t in ts)/N:.1f}%")
        if "cambios" in sys.argv:
            pend = SWAPS_11 + [A, Bc]
            for sc in ("B3", "Mazmorra"):
                b = run(PLAN, N, "table", cfg=SCEN[sc], seed0=3_300_000, pool=P)
                print(f"\n== {sc}: plan {summary(b)['win']:.1f}% ==", flush=True)
                for o, i in pend:
                    d, ci = paired(b, run(sw(PLAN, [(i, o)]), N, "table", cfg=SCEN[sc], seed0=3_300_000, pool=P))
                    print(f"  {o:30s} -> {i:24s} aporta {-d:+.1f} ±{ci:.1f}", flush=True)
                d, ci = paired(b, run(sw(PLAN, [("Find // Finality", "Blasting Station")]), N, "table", cfg=SCEN[sc], seed0=3_300_000, pool=P))
                print(f"  {'Find // Finality':30s} -> {'Blasting Station':24s} suma   {d:+.1f} ±{ci:.1f}")
                d, ci = paired(b, run(sw(PLAN, [("Woodfall Primus", "Woe Strider")]), N, "table", cfg=SCEN[sc], seed0=3_300_000, pool=P))
                print(f"  {'Woodfall Primus':30s} -> {'Woe Strider':24s} suma   {d:+.1f} ±{ci:.1f}")
