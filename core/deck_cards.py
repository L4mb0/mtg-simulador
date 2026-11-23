"""Lee el cards.py de cada simulador y lo deja en un formato común para compararlo con cards_db.json.

Formato común por carta: {"generic", "pips" (dict color -> cantidad), "mv", "type", "power", "toughness"};
None en lo que el simulador no anota.
"""
import os, re, sys, importlib.util

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DECKS = ["gandalf", "gorma", "giada", "blight", "blor"]

# nombres internos del simulador -> nombre real de la carta
ALIAS = {
    "gandalf": {"Gandalf": "Gandalf, Goblins' Bane"},
    "gorma": {"Jadzia Dax": "Jadzia Dax, Living Legacy"},
}

TYPE = {  # códigos de tipo de cada simulador -> tipo principal
    "gandalf": {"instant": "Instant", "creature": "Creature", "sorcery": "Sorcery", "artifact": "Artifact",
                "enchantment": "Enchantment", "land": "Land"},
    "gorma": {"C": "Creature", "S": "Sorcery", "I": "Instant", "A": "Artifact", "E": "Enchantment"},
    "giada": {"C": "Creature", "S": "Sorcery", "I": "Instant", "A": "Artifact", "E": "Enchantment"},
    "blight": {"C": "Creature", "S": "Sorcery", "I": "Instant", "A": "Artifact", "E": "Enchantment", "W": "Planeswalker"},
    "blor": {"cre": "Creature", "equip": "Artifact", "inst": "Instant", "art": "Artifact", "land": "Land",
             "ench": "Enchantment", "sorc": "Sorcery", "aura": "Enchantment", "pw": "Planeswalker"},
}
MAIN_COLOR = {"gandalf": "R", "gorma": None, "giada": "W", "blight": None, "blor": "G"}


def _module(deck):
    d = os.path.join(ROOT, "decks", deck)
    spec = importlib.util.spec_from_file_location(f"cards_{deck}", os.path.join(d, "cards.py"))
    m = importlib.util.module_from_spec(spec)
    sys.path.insert(0, d)
    try:
        spec.loader.exec_module(m)
    finally:
        sys.path.remove(d)
    return m


def _blight_cost(s):
    pips = {}
    for h in re.findall(r"\(([BRG]+)\)", s):
        k = "/".join(h); pips[k] = pips.get(k, 0) + 1
    s2 = re.sub(r"\([BRG]+\)", "", s)
    g = sum(int(x) for x in re.findall(r"\d+", s2))
    for c in s2:
        if c in "WUBRG":
            pips[c] = pips.get(c, 0) + 1
    return g, pips


def load(deck):
    m = _module(deck)
    raw = m.C if isinstance(getattr(m, "C", None), dict) else m.CARDS
    alias = ALIAS.get(deck, {})
    out = {}
    for name, d in raw.items():
        e = {"type": TYPE[deck].get(d.get("t"), d.get("t")), "power": d.get("p"), "toughness": None,
             "generic": None, "pips": None, "sim_name": name}
        if deck == "gandalf":
            e["generic"], e["pips"] = d.get("g", 0), ({"R": d["r"]} if d.get("r") else {})
            if d.get("t") == "land":
                e["generic"], e["pips"] = 0, {}
        elif deck == "blight":
            e["generic"], e["pips"] = _blight_cost(d["cost"])
            e["toughness"] = d.get("tg")
        else:  # (genérico, coloreado)
            g, c = d.get("cost", (0, 0))
            col = MAIN_COLOR[deck]
            e["generic"], e["pips"] = g, ({col: c} if c else {}) if col else {"*": c} if c else {}
            e["toughness"] = d.get("x")
        if e["type"] != "Creature" and deck != "gandalf":
            e["power"] = e["toughness"] = None
        if deck == "gandalf":
            e["power"] = None  # Gandalf no anota P/T
        e["mv"] = e["generic"] + sum(e["pips"].values())
        out[alias.get(name, name)] = e
    for name, d in getattr(m, "LANDS", {}).items():
        out[alias.get(name, name)] = {"type": "Land", "generic": 0, "pips": {}, "mv": 0, "power": None,
                                      "toughness": None, "sim_name": name, "land_col": d.get("col")}
    return out


def current_list(deck):
    """Nombres de la lista vigente de cada mazo (la misma que usa linea_base.py)."""
    d = os.path.join(ROOT, "decks", deck)
    sys.path.insert(0, d)
    try:
        if deck == "gandalf":
            names = [l.strip().split(" ", 1)[1] for l in open(os.path.join(d, "gandalf_1.6.txt")) if l.strip()]
        elif deck in ("gorma", "blight"):
            import scen; names = scen.ACTUAL
        elif deck == "giada":
            names = _module("giada").ACTUAL
        else:
            import decks; names = decks.DECKS["Blor 1.6"]
    finally:
        sys.path.remove(d)
        for m in ("scen", "decks", "cards", "engine", "mesa", "mesa2", "harness"):
            sys.modules.pop(m, None)
    return {ALIAS.get(deck, {}).get(n, n) for n in names}


if __name__ == "__main__":
    for dk in DECKS:
        print(dk, len(load(dk)))
