"""Traducción entre el formato de cada cards.py y el vocabulario común de data/efectos.yaml (fase 4).

`exportar(mazo, datos)` saca de un dict de cards.py los efectos (todo lo que no es coste, tipo ni P/T);
`importar(mazo, nombre, stats)` los vuelve a poner con las claves de siempre, así los motores no cambian.
tests: importar(exportar(x)) == x para cada carta de cada mazo.
"""
from core import efectos as EF

# claves de estadísticas que siguen en cards.py (no son efectos)
STATS = {"gandalf": {"t", "g", "r", "red"}, "gorma": {"cost", "t", "p"}, "giada": {"cost", "t", "p", "x"},
         "blight": {"cost", "t", "p", "tg"}, "blor": {"cost", "t", "p", "x"}}

# palabras clave y tipos con nombre propio en cada mazo -> nombre común
KW = {
    "giada": {"first": "first_strike", "flash": "flash", "flying": "flying", "lifelink": "lifelink", "vigilance": "vigilance"},
    "blight": {"fly": "flying", "dt": "deathtouch", "defender": "defender", "menace": "menace", "persist": "persist",
               "reach": "reach", "wither": "wither", "black": "black", "legend": "legendary", "selfc": "selfc"},
}
# banderas (True) que pasan a etiqueta común
FLAG = {
    "gandalf": {"wiz": "wizard", "shaman": "shaman", "mdfc": "mdfc"},
    "giada": {"artifact": "artifact", "cleric": "cleric", "prot": "prot_spot", "wipe": "wipe", "etb_tapped": "etb_tapped",
              "mdfc": "mdfc", "myriad": "myriad"},
    "blor": {"artifact": "artifact", "ench": "enchantment", "colorless": "colorless", "gc": "game_changer",
             "prot": "prot_spot", "fog": "fog"},
}
# valores que pasan a un campo común
VALUE = {"giada": {"rock": "rock", "draw": "draw"}, "blor": {"rock": "rock", "draw": "draw", "eq": "equip"}}
COMMANDER_COLOR = {"giada": "W", "blor": "G"}   # rock: COM = maná del color del comandante (Arcane Signet)
ANS = {"giada": ("ans", "sans"), "blor": ("ans", "sans")}   # respuestas instantáneas / de conjuro
# Gorma lee sus etiquetas tal cual: solo las de su vocabulario (otro mazo puede marcar más cosas en la misma carta)
GORMA_TAGS = {"ramp", "tutor", "closer", "outlet", "drainer", "dork", "flying", "enabler", "persist", "wipe", "menace",
              "artifact", "zombie", "ritual", "recursive", "pact", "trample", "haste", "inf_mana_outlet", "tutor_hand",
              "prot_spot", "drain_each", "cantblock", "rites", "mazirek_combo", "shadow", "wipe_small", "vigilance",
              "answer_cre_inst", "answer_cre_sorc", "answer_any_inst", "answer_any_sorc", "answer_ae_inst",
              "answer_ae_sorc", "answer_ae_hand"}


def exportar(mazo, d):
    """dict de cards.py -> (entrada parcial del YAML). Lo que no tiene nombre común va al bloque del mazo."""
    tags, e, ns = set(), {}, {}
    for k, v in d.items():
        if k in STATS[mazo]:
            continue
        if mazo == "gorma" and k == "tags":
            tags |= set(v)
        elif k == "kw" and mazo == "giada" or k == "tags" and mazo == "blight":
            tags |= {KW[mazo][x] for x in v}
        elif mazo == "giada" and k == "angel":
            if v:
                tags.add("angel")
        elif k in FLAG.get(mazo, {}) and v is True:
            tags.add(FLAG[mazo][k])
        elif k in VALUE.get(mazo, {}):
            e[VALUE[mazo][k]] = v
        elif k in ANS.get(mazo, ()):
            lst = sorted(v) if isinstance(v, (set, frozenset)) else v.split()
            e["answer" if k == ANS[mazo][0] else "answer_sorc"] = lst
        else:
            ns[k] = list(v) if isinstance(v, tuple) else v
    if tags:
        e["tags"] = sorted(tags)
    if ns:
        e[mazo] = ns
    return e


def importar(mazo, nombre, stats):
    """Rehace el dict de cards.py de `nombre` a partir de sus estadísticas y de data/efectos.yaml."""
    e = EF.card(nombre)
    no = set(e.get(mazo, {}).get("no", ()))   # lo que este mazo todavía no modela de la carta (a revisar)
    e = {k: v for k, v in e.items() if k not in no}
    d = dict(stats)
    tags = set(e.get("tags", ())) - no
    if mazo == "gorma":
        d["tags"] = tags & GORMA_TAGS
        return d
    if mazo == "blight":
        inv = {v: k for k, v in KW["blight"].items()}
        d["tags"] = {inv[t] for t in tags if t in inv}
    if mazo == "giada":
        if "p" in d:
            inv = {v: k for k, v in KW["giada"].items()}
            d["kw"] = {inv[t] for t in tags if t in inv}
        d["angel"] = "angel" in tags
    for k, t in FLAG.get(mazo, {}).items():
        if t in tags:
            d[k] = True
    for k, f in VALUE.get(mazo, {}).items():
        if f in e:
            d[k] = COMMANDER_COLOR[mazo] if e[f] == "COM" else e[f]
    if mazo in ANS:
        for k, f in zip(ANS[mazo], ("answer", "answer_sorc")):
            if f in e:
                d[k] = set(e[f]) if mazo == "giada" else " ".join(e[f])
    for k, v in e.get(mazo, {}).items():
        if k not in ("no", "motor"):
            d[k] = tuple(v) if isinstance(v, list) else v
    return d
