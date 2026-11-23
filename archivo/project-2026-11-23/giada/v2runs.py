"""Mesa v2 (16/11): línea base por bracket, ablación, candidatas contra rol parecido y cupos débiles, verificación."""
import json, sys, time
from multiprocessing import Pool
from cards import ACTUAL, PRECON, LANDS, CARDS, swap
from harness import run, summary, paired
from scen import cfg

N = 4000
SEED_NEW = 900000
PEND = [("Reya Dawnbringer", "Flawless Maneuver"), ("Search the Premises", "Resplendent Angel"),
        ("Swiftfoot Boots", "Herald of the Host"), ("Invoke the Divine", "Starnheim Unleashed"),
        ("Cleansing Nova", "Sigarda's Vanguard"), ("Seraph of the Sword", "Felidar Sovereign")]
OPT = [("Emeria Shepherd", "Urza's Incubator"), ("Angel of the Ruins", "Pearl Medallion"),
       ("Commander's Sphere", "Restoration Angel")]
PACK20 = [("Invoke the Divine", "Flawless Maneuver"), ("Swiftfoot Boots", "Felidar Sovereign"),
          ("Fateful Absence", "Lyra, Archangel of Dawn"), ("Search the Premises", "Sigarda's Vanguard"),
          ("Cleansing Nova", "Ob Nixilis, the Ascended")]
FASE1 = [("Exorcise", "Path to Exile"), ("Invoke the Divine", "Generous Gift"), ("Sunblast Angel", "Valkyrie Harbinger"),
         ("Linvala, the Preserver", "Resplendent Angel"), ("Reya Dawnbringer", "Lyra, Archangel of Dawn"),
         ("Commander's Sphere", "Pearl Medallion"), ("Plains", "Emeria's Call"), ("Seraph of the Sword", "Guide of Souls"),
         ("Metallic Mimic", "Soul Warden"), ("Search the Premises", "Folk Hero"), ("Radiant Fountain", "Minas Tirith")]


def apply(d, pairs):
    d = list(d)
    for o, i in pairs:
        if i in d and i != "Plains":
            continue          # ya está (Lyra, Archangel of Dawn entró el 12/11)
        d = swap(d, o, i)
    return d


PRE12 = swap(ACTUAL, "Lyra, Archangel of Dawn", "Cryptic Gateway")   # lista del 07/11 (base de las rutas viejas)
DECKS = {
    "Precon": PRECON,
    "Actual (12/11)": ACTUAL,
    "Paquete $20 (sobre la del 07/11)": apply(PRE12, PACK20),
    "Fase 1 (sobre la del 07/11)": apply(PRE12, FASE1),
    "Núcleo pendiente (6)": apply(ACTUAL, PEND),
    "Núcleo + opcionales": apply(ACTUAL, PEND + OPT),
}
BRS = ["B1", "B2", "B3", "B4", "B5", "B3+B4"]
INTERACTION = {c for c, v in CARDS.items() if v.get("ans") or v.get("sans") or v.get("wipe") or v.get("prot")}


def base(pool):
    out = {}
    for name, d in DECKS.items():
        row = {}
        for br in BRS:
            row[br] = summary(run(d, N, cfg=cfg(br), pool=pool))["win"]
        row["gf"] = summary(run(d, N, mode="goldfish", pool=pool))["mean_turn"]
        out[name] = row
        print("BASE", name, {k: round(v, 1) for k, v in row.items()}, flush=True)
    return out


def ablation(pool, br):
    ref = run(ACTUAL, N, cfg=cfg(br), pool=pool)
    out = {}
    for c in sorted(set(x for x in ACTUAL if x not in LANDS)):
        d, ci = paired(ref, run(swap(ACTUAL, c, "Blank"), N, cfg=cfg(br), pool=pool))
        out[c] = (d, ci)
        print(f"ABL {br} {c:28s} {d:+5.2f} ±{ci:.2f}", flush=True)
    return out


CANDS = {  # candidata: salida del plan (o None)
    "Flawless Maneuver": "Reya Dawnbringer", "Resplendent Angel": "Search the Premises", "Herald of the Host": "Swiftfoot Boots",
    "Starnheim Unleashed": "Invoke the Divine", "Sigarda's Vanguard": "Cleansing Nova", "Felidar Sovereign": "Seraph of the Sword",
    "Urza's Incubator": "Emeria Shepherd", "Pearl Medallion": "Angel of the Ruins", "Restoration Angel": "Commander's Sphere",
    # banca y sueltas de Juan
    "Cryptic Gateway": None, "Speaker of the Heavens": None, "Endless Atlas": None, "Leader's Talent": None,
    "Lingering Souls": None, "Disenchant": "Invoke the Divine", "Millikin": "Commander's Sphere",
    # descartadas antes
    "Valkyrie Harbinger": None, "Ob Nixilis, the Ascended": "Sunblast Angel", "Folk Hero": None, "Path to Exile": "Exorcise",
    "Generous Gift": "Invoke the Divine", "Archangel of Thune": None, "Avacyn, Angel of Hope": None, "Guide of Souls": None,
    "Soul Warden": None, "Karmic Guide": "Defy Death", "Akroma's Will": None, "Blinding Angel": None,
    "Kindred Judgment": "Cleansing Nova", "Lightning Greaves": "Swiftfoot Boots", "Emeria's Call": "Plains",
}


def candidates(pool, abl, br="B2"):
    weak = [c for c, _ in sorted(abl.items(), key=lambda kv: -kv[1][0]) if c not in INTERACTION][:3]   # Δ más alto = aporta menos
    print("cupos débiles:", weak, flush=True)
    ref = run(ACTUAL, N, cfg=cfg(br), pool=pool)
    out = {}
    for c, plan in CANDS.items():
        outs = ([plan] if plan else []) + [w for w in weak if w != plan]
        res = {}
        for o in outs:
            if c in ACTUAL or o not in ACTUAL:
                continue
            res[o] = paired(ref, run(swap(ACTUAL, o, c), N, cfg=cfg(br), pool=pool))
        out[c] = res
        print("CAND", c, {o: (round(v[0], 2), round(v[1], 2)) for o, v in res.items()}, flush=True)
    return out, weak


def verify(pool, picks):
    """cada cambio elegido, con semillas nuevas en B1, B2, B3"""
    out = {}
    for lab, d in picks.items():
        row = {}
        for br in ("B1", "B2", "B3"):
            a = run(ACTUAL, N, cfg=cfg(br), pool=pool, seed0=SEED_NEW)
            b = run(d, N, cfg=cfg(br), pool=pool, seed0=SEED_NEW)
            row[br] = paired(a, b)
        out[lab] = row
        print("VER", lab, {k: (round(v[0], 2), round(v[1], 2)) for k, v in row.items()}, flush=True)
    return out


if __name__ == "__main__":
    t0 = time.time()
    R = {}
    with Pool(2) as pool:
        R["base"] = base(pool)
        R["abl_B2"] = ablation(pool, "B2")
        R["abl_B1"] = ablation(pool, "B1")
        R["cands"], R["weak"] = candidates(pool, R["abl_B2"])
        json.dump(R, open("v2runs.json", "w"), indent=1, ensure_ascii=False)
        # verificación con semillas nuevas: cada candidata en su mejor cupo, y las listas
        picks = {}
        for c, res in R["cands"].items():
            if res:
                o = max(res, key=lambda k: res[k][0])
                picks[f"{c} por {o}"] = swap(ACTUAL, o, c)
        picks.update({"Núcleo pendiente (6)": DECKS["Núcleo pendiente (6)"], "Núcleo + opcionales": DECKS["Núcleo + opcionales"],
                      "Paquete $20": apply(ACTUAL, PACK20), "Fase 1": apply(ACTUAL, FASE1)})
        R["verify"] = verify(pool, picks)
    json.dump(R, open("v2runs.json", "w"), indent=1, ensure_ascii=False)
    print("time", time.time() - t0)
