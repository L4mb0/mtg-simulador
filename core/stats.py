"""Coste, tipo y P/T de cada carta desde core/cards_db.json (Forge), con el formato de cada cards.py.

    desde_forge(mazo, nombre) -> dict con las claves de estadísticas de ese mazo (o None si Forge no la tiene)

Los cards.py solo escriben a mano lo que el simulador modela distinto de la carta (ajustes revisados con Juan);
todo lo demás sale de aquí. `python3 core/stats.py` muestra, por mazo, qué cartas no coinciden.
"""
import os, json, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DB = None
COLOR = {"gandalf": "R", "giada": "W", "blor": "G"}   # mazos que cuentan solo los pips de su color
ALIAS = {"Gandalf": "Gandalf, Goblins' Bane", "Jadzia Dax": "Jadzia Dax, Living Legacy"}


def db():
    global _DB
    if _DB is None:
        _DB = json.load(open(os.path.join(ROOT, "core", "cards_db.json"), encoding="utf-8"))
        idx = dict(_DB)
        for c in list(_DB.values()):
            if "full_name" in c:
                idx.setdefault(c["full_name"], c)
        _DB = idx
    return _DB


def carta(nombre):
    return db().get(ALIAS.get(nombre, nombre))


def _int(x):
    return int(x) if isinstance(x, str) and x.lstrip("-").isdigit() else 0


def _tipo(mazo, c):
    t = set(c["types"])
    if mazo == "gandalf":
        for k in ("Land", "Creature", "Instant", "Sorcery", "Artifact", "Enchantment"):
            if k in t:
                return k.lower()
    if mazo in ("gorma", "giada", "blight"):
        for k, v in (("Creature", "C"), ("Instant", "I"), ("Sorcery", "S"), ("Planeswalker", "W"), ("Artifact", "A"),
                     ("Enchantment", "E")):
            if k in t:
                return v
    if mazo == "blor":
        sub = set(c["subtypes"])
        if "Land" in t: return "land"
        if "Equipment" in sub: return "equip"            # también las criaturas-equipo (Tanuki Transplanter)
        if "Creature" in t: return "cre"
        if "Aura" in sub:                                 # aura de criatura; las de tierra o jugador son "ench"
            return "ench" if re.search(r"^Enchant (land|player|Forest)", c["oracle"], re.M) else "aura"
        for k, v in (("Instant", "inst"), ("Sorcery", "sorc"), ("Planeswalker", "pw"), ("Artifact", "art"),
                     ("Enchantment", "ench")):
            if k in t:
                return v
    return None


def _blight_cost(c):
    out = str(c["generic"]) if c["generic"] else ""
    for k in sorted(c["pips"], key=lambda k: ("/" in k, ["WUBRG".find(x) for x in k.split("/")])):
        n = c["pips"][k]
        out += ("(" + k.replace("/", "") + ")") * n if "/" in k else k * n
    return out


def desde_forge(mazo, nombre):
    c = carta(nombre)
    if c is None:
        return None
    t = _tipo(mazo, c)
    gen = c["generic"]
    colored = sum(n for k, n in c["pips"].items() if k not in ("C", "S"))
    cre = "Creature" in c["types"]
    if mazo == "gandalf":
        col = sum(n for k, n in c["pips"].items() if "R" in k.split("/"))
        red = "R" in "".join(c["pips"]) or any("R" in "".join(f["pips"]) for f in c.get("faces", []))
        if t == "land":
            return dict(t=t, g=0, r=0, red=True)       # convención de Gandalf: las tierras van como "rojas"
        return dict(t=t, g=gen + sum(n for k, n in c["pips"].items() if k == "C"), r=col, red=red)
    if mazo == "gorma":
        d = dict(cost=(gen, colored), t=t)
        if cre:
            d["p"] = _int(c.get("power"))
        return d
    if mazo == "giada":
        d = dict(cost=(gen, colored), t=t)
        if cre:
            d.update(p=_int(c.get("power")), x=_int(c.get("toughness")))
        return d
    if mazo == "blight":
        return dict(cost=_blight_cost(c), t=t, p=_int(c.get("power")), tg=_int(c.get("toughness")))
    if mazo == "blor":
        d = dict(t=t, cost=(gen if t != "land" else 0, colored if t != "land" else 0))
        if cre and t == "cre":
            d.update(p=_int(c.get("power")), x=_int(c.get("toughness")))
        return d


if __name__ == "__main__":
    import sys, subprocess
    for mazo in ("gandalf", "gorma", "giada", "blight", "blor"):
        code = f"""
import sys, json; sys.path.insert(0, {ROOT!r})
import cards as m
from core import stats as S, mapeo as MP
D = m.C if isinstance(getattr(m, "C", None), dict) else m.CARDS
bad = {{}}
for n, v in D.items():
    st = {{k: x for k, x in v.items() if k in MP.STATS["{mazo}"]}}
    f = S.desde_forge("{mazo}", n)
    if f != st:
        bad[n] = [st, f]
print(json.dumps(dict(n=len(D), bad=bad), default=str))
"""
        r = subprocess.run([sys.executable, "-c", code], cwd=os.path.join(ROOT, "decks", mazo), capture_output=True,
                           text=True, env=dict(os.environ, PYTHONHASHSEED="0"))
        out = json.loads(r.stdout.strip().splitlines()[-1])
        print(f"{mazo}: {out['n'] - len(out['bad'])}/{out['n']} coinciden con Forge")
        for n, (a, b) in list(out["bad"].items())[: int(sys.argv[1]) if len(sys.argv) > 1 else 8]:
            print(f"   {n}: simulador {a} | Forge {b}")
