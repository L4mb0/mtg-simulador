"""Mazmorra (sin limite de tiempo) para Gorma: base, ablacion, mas respuestas, candidatas. python3 mz_runs.py <etapa>"""
import sys, json
from multiprocessing import Pool
import engine
from harness import run, summary, paired
from scen import SCEN, ACTUAL, CONS, B
from cards import swap, CARDS
N = 4000; S1 = 500_000; S2 = 1_900_000
MZ = dict(time_limit=False)
DEF = {"Foot Chopper", "The Gitrog, Ravenous Ride", "Jenova, Ancient Calamity", "Feral Ghoul", "Rampant Rejuvenator",
       "Culling Ritual", "Vicious Rivalry", "Traverse the Outlands", "Selvala, Heart of the Wilds", "Insidious Fungus",
       "Butcher of Malakir", "Jarad, Golgari Lich Lord", "Garruk's Uprising", "Moldervine Reclamation", "Priest of Forgotten Gods"}
INTER = {"Mortality Spear", "Immoral Bargain", "Desperate Plea", "Toxic Deluge", "Witherbloom Charm", "Haywire Mite",
         "Veil of Summer", "Pest Infestation", "Find // Finality", "Insidious Fungus", "Culling Ritual", "Vicious Rivalry"}
def cfg(sc, **kw):
    if sc.startswith("Mazmorra"):
        d = dict(MZ); d.update(kw)
        if sc == "Mazmorra optimista": d["mz_mus"] = (4, 5, 7)
        if sc == "Mazmorra pesimista": d["mz_mus"] = (3, 5, 6)
        return B("Mazmorra", **d)
    return B(sc, **kw)
def R(d, sc="Mazmorra", seed=S1, P=None, **kw):
    return run(d, N, "table", cfg=cfg(sc, **kw), seed0=seed, pool=P)
def f(x): return f"{x[0]:+.1f} ±{x[1]:.1f}"
def sw(d, pairs):
    for o, i in pairs: d = swap(d, o, i)
    return d
def job(a):
    deck, sc, s, kw = a
    g = engine.play(deck, S1 + s, mode="table", cfg=cfg(sc, **kw))
    st = g.stats
    cause = "gana" if g.won else ("golpe parcial" if st.get("mz_partial_us") else ("combate" if g.life <= 0 else ("intento rival" if g.lost else "sin terminar")))
    return cause, g.turn, st.get("we_stop", 0), st.get("others_stop", 0)
if __name__ == "__main__":
    st = sys.argv[1]
    with Pool() as P:
        if st == "base":
            for nm, d in (("1.0", ACTUAL), ("1.1", CONS)):
                print(f"\n== Gorma {nm} ==")
                for sc in ("B3", "Mazmorra", "Mazmorra optimista", "Mazmorra pesimista"):
                    r = P.map(job, [(d, sc, s, {}) for s in range(N)], chunksize=100)
                    from collections import Counter
                    c = Counter(x[0] for x in r)
                    wt = sorted(x[1] for x in r if x[0] == "gana")
                    lt = sorted(x[1] for x in r if x[0] != "gana")
                    med = lambda L: L[len(L)//2] if L else "-"
                    print(f"{sc:20s} gana {100*c['gana']/N:.1f}% (mediana T{med(wt)})  pierde: intento rival {100*c['intento rival']/N:.1f}%, golpe parcial {100*c['golpe parcial']/N:.1f}%, combate {100*c['combate']/N:.1f}%, sin terminar {100*c['sin terminar']/N:.1f}% (mediana T{med(lt)})  frenas {sum(x[2] for x in r)/N:.2f}, otros frenan {sum(x[3] for x in r)/N:.2f}")
        if st == "abl":
            b = R(CONS, P=P); out = []
            for c in sorted(set(x for x in CONS if x in CARDS)):
                out.append((paired(b, R(swap(CONS, c, "Blank"), P=P)), c))
            print(f"ablacion 1.1 en la Mazmorra (base {summary(b)['win']:.1f}%)")
            for (dd, ci), c in sorted(out):
                tag = " (defendida)" if c in DEF else (" (interaccion)" if c in INTER else "")
                print(f"{c:34s} {dd:+.1f} ±{ci:.1f}{tag}")
            json.dump([(c, dd) for (dd, ci), c in sorted(out)], open("abl_mz.json", "w"))
        if st == "resp":
            abl = json.load(open("abl_mz.json"))
            weak = [c for c, dd in reversed(abl) if c not in DEF and c not in INTER][:6]
            ans = ["Cast Down", "Power Word Kill", "Infernal Grasp", "Go for the Throat", "Assassin's Trophy", "Beast Within"]
            print("salen (las que menos aportan en la Mazmorra):", ", ".join(weak))
            for sc in ("Mazmorra", "B3"):
                for hold in (6, 4):
                    b = R(CONS, sc, P=P, hold_from_turn=hold)
                    base_stop = sum(x[2] for x in P.map(job, [(CONS, sc, s, dict(hold_from_turn=hold)) for s in range(N)], chunksize=100)) / N
                    row = [f"base {summary(b)['win']:.1f}% (frenas {base_stop:.2f})"]
                    for n in (2, 4, 6):
                        d = sw(CONS, list(zip(weak[:n], ans[:n])))
                        r = R(d, sc, P=P, hold_from_turn=hold)
                        stp = sum(x[2] for x in P.map(job, [(d, sc, s, dict(hold_from_turn=hold)) for s in range(N)], chunksize=100)) / N
                        row.append(f"+{n}: {f(paired(b, r))} (frenas {stp:.2f})")
                    print(f"{sc:9s} guardar maná desde T{hold}: " + " | ".join(row))
                pr = sw(CONS, list(zip(weak[:2], ["Heroic Intervention", "Snakeskin Veil"])))
                print(f"{sc:9s} proteger lo propio (Heroic + Snakeskin Veil): {f(paired(R(CONS, sc, P=P), R(pr, sc, P=P)))}")
        if st == "cand":
            abl = json.load(open("abl_mz.json"))
            weak = [c for c, dd in reversed(abl) if c not in DEF and c not in INTER][:3]
            print("salen:", ", ".join(weak))
            groups = [(["Grim Tutor", "Finale of Devastation", "Dread Return", "Dark Ritual", "Ygra, Eater of All", "Sylvan Library",
                        "Altar of Dementia", "Archdruid's Charm"], weak),
                      (["Damnation", "Blasphemous Edict"], ["Toxic Deluge", "Immoral Bargain"])]
            for sc in ("Mazmorra", "B3"):
                b = R(CONS, sc, P=P)
                print(f"\n== {sc} (1.1 {summary(b)['win']:.1f}%) ==")
                for ins, outs in groups:
                    for c in ins:
                        print(f"{c:24s} " + "  ".join(f"por {o.split(',')[0]} {f(paired(b, R(swap(CONS, o, c), sc, P=P)))}" for o in outs))
                print("Carrion Feeder: sacarla de la 1.1 (Blank)", f(paired(b, R(swap(CONS, "Carrion Feeder", "Blank"), sc, P=P))),
                      "| en la 1.0 por Nether Traitor", f(paired(R(ACTUAL, sc, P=P), R(swap(ACTUAL, "Nether Traitor", "Carrion Feeder"), sc, P=P))))
