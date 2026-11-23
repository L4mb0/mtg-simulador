"""Corridas del análisis de Blight Curse. Uso: python3 runs.py <fase>"""
import sys, json, time
from multiprocessing import Pool
from harness import run, summary, paired, paired_turn
from scen import SCEN, ACTUAL, C
from cards import CARDS, LANDS, swap, apply, FASE1
NT, NG = 4000, 2000
OUT = "/home/claude/blight_sim/results"
import os; os.makedirs(OUT, exist_ok=True)

def save(name, obj):
    json.dump(obj, open(f"{OUT}/{name}.json", "w"), ensure_ascii=False, indent=1)

def base(P):
    out = {}
    for s, cfg in SCEN.items():
        sm = summary(run(ACTUAL, NT, "table", cfg=cfg, pool=P))
        out[s] = sm; print(s, round(sm["win"], 1), sm["how"], flush=True)
    g = summary(run(ACTUAL, NG, "goldfish", pool=P)); out["goldfish"] = g
    print("goldfish", round(g["mean_turn"], 2), round(g["k8"], 1), round(g["k10"], 1), g["how"])
    save("base", out)

def motor(P):
    out = {}
    for s in ["Realista (base)", "Rivales lentos (10-14)", "Optimista"]:
        b = run(ACTUAL, NT, "table", cfg=SCEN[s], pool=P)
        t = run(ACTUAL, NT, "table", cfg=SCEN[s], policy={"no_auntie": True}, pool=P)
        h = run(ACTUAL, NT, "table", cfg=C(**{**SCEN[s].__dict__, "hold_from_turn": 99}), pool=P)
        out[s] = dict(base=summary(b)["win"], no_auntie=summary(t)["win"], d_no=paired(b, t), no_hold=summary(h)["win"], d_hold=paired(b, h))
        print(s, out[s], flush=True)
    b = run(ACTUAL, NG, "goldfish", pool=P); t = run(ACTUAL, NG, "goldfish", policy={"no_auntie": True}, pool=P)
    out["goldfish"] = dict(base=summary(b)["mean_turn"], no_auntie=summary(t)["mean_turn"], d=paired_turn(b, t),
                           win20=summary(b)["win"], win20_no=summary(t)["win"])
    print(out["goldfish"]); save("motor", out)


ABL_T = ["Realista (base)", "Rivales lentos (10-14)", "Optimista"]

def ablacion(P):
    bases = {s: run(ACTUAL, NT, "table", cfg=SCEN[s], pool=P) for s in ABL_T}
    bg = run(ACTUAL, NG, "goldfish", pool=P)
    out = {}
    for c in dict.fromkeys(ACTUAL):
        if c in LANDS:
            continue
        d = swap(ACTUAL, c, "Blank")
        row = {s: paired(bases[s], run(d, NT, "table", cfg=SCEN[s], pool=P)) for s in ABL_T}
        row["goldfish_turn"] = paired_turn(bg, run(d, NG, "goldfish", pool=P))
        row["avg"] = sum(row[s][0] for s in ABL_T) / 3
        out[c] = row
        print(f"{c:34s} {row['avg']:+.2f}  " + "  ".join(f"{row[s][0]:+.1f}" for s in ABL_T) + f"  gf {row['goldfish_turn'][0]:+.2f}", flush=True)
    save("ablacion", out)

PRICES = {"Generous Patron": 0.79, "Dawnhand Dissident": 0.49, "Grim Affliction": 0.49, "Farseek": 1.49,
          "Obelisk Spider": 4.49, "Maha, Its Feathers Night": 23.99, "Persistent Constrictor": 18.99,
          "Nest of Scarabs": 5.99, "Harbinger of Night": 19.99, "Rampant Growth": 0.79, "Nature's Lore": 3.49,
          "Scuzzback Scrounger": 1.29, "Darkness Descends": 0.35, "Heroic Intervention": 14.99,
          "Swiftfoot Boots": 0.0, "Lightning Greaves": 5.99, "Ammit Eternal": 0.69, "Atomize": 10.99,
          "Shadow Urchin": 0.49, "Banewhip Punisher": 0.35, "Mahadi, Emporium Master": 1.99,
          "Whisper of the Dross": 0.79, "Skullclamp": 7.49, "Yawgmoth, Thran Physician": 32.99,
          "All Will Be One": 14.99, "Contagion Engine": 16.99, "Crumbling Ashes": 20.99,
          "Zulaport Cutthroat": 2.79, "Blood Artist": None, "Bastion of Remembrance": 0.79,
          "Cauldron of Essence": 4.49, "Soul Immolation": 4.49, "Morselhoarder": 0.35,
          "High-Society Hunter": 0.69, "Agent Venom": 0.59, "Grim Haruspex": 2.79, "Demonic Tutor": 84.99,
          "Vampiric Tutor": 64.99, "Worldly Tutor": 32.99, "Blight Rot": None, "Murder": 0.0}
LAND_C = {"Ziatora's Proving Ground": 11.99, "Overgrown Tomb": 7.99, "Blood Crypt": 7.99, "Stomping Ground": 5.99}

def candidatas(P, out_card=None, land_out="Gruul Turf"):
    abl = json.load(open(f"{OUT}/ablacion.json"))
    out_card = out_card or min(abl, key=lambda c: abs(abl[c]["avg"]) + (5 if c in ("Black Sun's Zenith",) else 0))
    tables = ABL_T
    bases = {s: run(ACTUAL, NT, "table", cfg=SCEN[s], pool=P) for s in tables}
    bg = run(ACTUAL, NG, "goldfish", pool=P)
    res = {"_out": out_card, "_land_out": land_out}
    for c, price in list(PRICES.items()) + list(LAND_C.items()):
        o = land_out if c in LAND_C else out_card
        d = swap(ACTUAL, o, c)
        row = {s: paired(bases[s], run(d, NT, "table", cfg=SCEN[s], pool=P)) for s in tables}
        row["goldfish_turn"] = paired_turn(bg, run(d, NG, "goldfish", pool=P))
        row["avg"] = sum(row[s][0] for s in tables) / 3
        row["price"] = price
        res[c] = row
        print(f"{c:30s} por {o:22s} {row['avg']:+.2f}  " + "  ".join(f"{row[s][0]:+.1f}±{row[s][1]:.1f}" for s in tables) + f"  gf {row['goldfish_turn'][0]:+.2f}", flush=True)
    save("candidatas", res)

def pilotaje(P):
    out = {}
    tabs = ABL_T + ["Pesimista"]
    for s in tabs:
        b = run(ACTUAL, NT, "table", cfg=SCEN[s], pool=P)
        row = {"base": summary(b)["win"]}
        for pol in ("wait_blue", "protected", "late"):
            t = run(ACTUAL, NT, "table", cfg=SCEN[s], policy={"auntie": pol}, pool=P)
            row[pol] = paired(b, t)
        t = run(ACTUAL, NT, "table", cfg=C(**{**SCEN[s].__dict__, "hold_from_turn": 99}), pool=P)
        row["no_hold"] = paired(b, t)
        out[s] = row
        print(s, row, flush=True)
    save("pilotaje", out)

def _avg(deck, tables, P, bases, n=NT, policy=None):
    r = {s: run(deck, n, "table", cfg=SCEN[s], pool=P, policy=policy) for s in tables}
    d = {s: paired(bases[s], r[s]) for s in tables}
    return sum(d[s][0] for s in tables) / len(tables), d, {s: summary(r[s])["win"] for s in tables}

def ruta(P, ins, outs, name, tables=None):
    """Aplica cambios uno a uno (greedy): para cada entrada, prueba las 3 salidas más débiles que queden y se queda
    con la mejor si suma > 0. Devuelve el historial."""
    tables = tables or ABL_T
    abl = json.load(open(f"{OUT}/ablacion.json"))
    deck = list(ACTUAL)
    base0 = {s: run(ACTUAL, NT, "table", cfg=SCEN[s], pool=P) for s in tables}
    cur = dict(base0)
    hist = []
    outs = [o for o in sorted(outs, key=lambda c: -abl[c]["avg"])]  # más débil primero (avg alto = quitarla no duele)
    for inn in ins:
        best = None
        for o in [x for x in outs if x in deck][:3]:
            d = swap(deck, o, inn)
            m, det, wins = _avg(d, tables, P, cur)
            if best is None or m > best[0]:
                best = (m, o, d, det, wins)
        if best and best[0] > 0.3:
            m, o, d, det, wins = best
            deck = d
            cur = {s: run(deck, NT, "table", cfg=SCEN[s], pool=P) for s in tables}
            tot = {s: paired(base0[s], cur[s]) for s in tables}
            hist.append(dict(out=o, inn=inn, step=m, det={s: det[s] for s in tables}, wins=wins,
                             cum={s: tot[s][0] for s in tables}))
            print(f"[{name}] {o} -> {inn}: {m:+.2f}  " + "  ".join(f"{s[:8]} {wins[s]:.1f}%" for s in tables), flush=True)
        else:
            print(f"[{name}] {inn}: no entra ({best[0] if best else None:+.2f})", flush=True)
    g0 = run(ACTUAL, NG, "goldfish", pool=P); g1 = run(deck, NG, "goldfish", pool=P)
    allt = {s: (summary(run(ACTUAL, NT, "table", cfg=SCEN[s], pool=P))["win"], summary(run(deck, NT, "table", cfg=SCEN[s], pool=P))["win"]) for s in SCEN}
    res = dict(hist=hist, deck=deck, goldfish=(summary(g0)["mean_turn"], summary(g1)["mean_turn"]), all=allt)
    save("ruta_" + name, res)
    return res

def fase1(P):
    deck = apply(ACTUAL, FASE1)
    out = {}
    for s in SCEN:
        b = run(ACTUAL, NT, "table", cfg=SCEN[s], pool=P); t = run(deck, NT, "table", cfg=SCEN[s], pool=P)
        out[s] = (summary(b)["win"], summary(t)["win"], paired(b, t))
        print(s, out[s], flush=True)
    g0 = run(ACTUAL, NG, "goldfish", pool=P); g1 = run(deck, NG, "goldfish", pool=P)
    out["goldfish"] = (summary(g0)["mean_turn"], summary(g1)["mean_turn"], paired_turn(g0, g1))
    # cada cambio de la Fase 1 por separado sobre el precon
    single = {}
    for o, i in FASE1:
        single[f"{o} -> {i}"] = _avg(swap(ACTUAL, o, i), ABL_T, P, {s: run(ACTUAL, NT, "table", cfg=SCEN[s], pool=P) for s in ABL_T})[0]
        print(o, i, round(single[f"{o} -> {i}"], 2), flush=True)
    out["single"] = single
    save("fase1", out)


if __name__ == "__main__":
    t = time.time()
    with Pool(2) as P:
        globals()[sys.argv[1]](P, *sys.argv[2:])
    print("tiempo", round(time.time() - t), "s")
