"""Genera core/cards_db.json desde los guiones de cartas de MTG Forge.

    git clone --depth 1 --filter=blob:none --sparse https://github.com/Card-Forge/forge.git /tmp/forge
    git -C /tmp/forge sparse-checkout set forge-gui/res/cardsfolder
    python3 core/build_cards_db.py /tmp/forge/forge-gui/res/cardsfolder [--todas]

Por defecto guarda solo las cartas que usa algún simulador (más las que se pasen en core/extra.txt);
con --todas guarda las ~34.000 (archivo grande, no va al repo).

Cada carta: name, layout, mana_cost ("{1}{B}{G}"), mv, generic, pips ({"B": 1, "G": 1}; híbridos como "B/R"),
types / supertypes / subtypes, power, toughness, loyalty, keywords, color_identity, oracle y faces
(las otras caras con sus propios datos). Las cartas de dos caras se encuentran por la cara frontal
y por "Frente // Dorso".
"""
import os, re, sys, json, glob

HERE = os.path.dirname(os.path.abspath(__file__))
SUPER = {"Legendary", "Basic", "Snow", "World", "Ongoing", "Host"}
CARD_TYPES = {"Artifact", "Battle", "Creature", "Enchantment", "Instant", "Kindred", "Land", "Planeswalker",
              "Sorcery", "Tribal", "Conspiracy", "Dungeon", "Phenomenon", "Plane", "Scheme", "Vanguard"}
# K: de Forge que son mecánica interna, no palabras clave impresas
K_INTERNAL = {"ETBReplacement", "etbCounter", "Chapter", "CARDNAME enters tapped.", "Class", "MayEffectFromOpeningHand",
              "Hidden agenda", "TypeCycling"}
COLORS = "WUBRG"


def parse_cost(raw):
    raw = (raw or "").strip()
    if not raw or raw == "no cost":
        return None, 0, 0, {}
    generic, pips, syms = 0, {}, []
    for tok in raw.split():
        syms.append("{" + ("/".join(tok) if len(tok) == 2 and not tok.isdigit() else tok) + "}")
        if tok.isdigit():
            generic += int(tok)
        elif tok in ("X", "Y", "Z"):
            pass
        elif tok == "C":
            pips["C"] = pips.get("C", 0) + 1
        elif tok == "S":
            pips["S"] = pips.get("S", 0) + 1
        else:  # Forge: W, BR (híbrido), 2W (dos o W), RP (phyrexiano) -> W, B/R, 2/W, R/P
            key = "/".join(tok) if len(tok) == 2 else tok
            pips[key] = pips.get(key, 0) + 1
    mv = generic
    for k, n in pips.items():
        mv += (2 if k.startswith("2/") else 1) * n
    return "".join(syms), mv, generic, pips


def colors_in(text):
    return {c for c in COLORS if re.search(r"\{[^}]*" + c + r"[^}]*\}", text or "")}


def parse_face(lines):
    f = {"keywords": [], "svars": {}}
    for ln in lines:
        if ":" not in ln:
            continue
        k, v = ln.split(":", 1)
        if k == "Name": f["name"] = v.strip()
        elif k == "ManaCost": f["mana_raw"] = v.strip()
        elif k == "Types": f["types_raw"] = v.strip()
        elif k == "PT": f["pt"] = v.strip()
        elif k == "Loyalty": f["loyalty"] = v.strip()
        elif k == "Colors": f["color_ind"] = v.strip()
        elif k == "Oracle": f["oracle"] = v.replace("\\n", "\n").strip()
        elif k == "AlternateMode": f["alt"] = v.strip()
        elif k == "K":
            kw = v.split(":", 1)[0].strip()
            if kw and kw not in K_INTERNAL and not kw.startswith("ETB") and "CARDNAME" not in kw:
                f["keywords"].append(kw)
    mana, mv, generic, pips = parse_cost(f.get("mana_raw"))
    t = (f.get("types_raw") or "").split()
    sup = [x for x in t if x in SUPER]
    if "-" in t:   # por si algún guion trae el separador
        t = [x for x in t if x != "-"]
    types = [x for x in t if x in CARD_TYPES]
    sub = [x for x in t if x not in SUPER and x not in CARD_TYPES]
    out = {"name": f.get("name"), "mana_cost": mana, "mv": mv, "generic": generic, "pips": pips,
           "supertypes": sup, "types": types, "subtypes": sub,
           "keywords": sorted(set(f["keywords"])), "oracle": f.get("oracle", "")}
    if "pt" in f:
        p, _, x = f["pt"].partition("/")
        out["power"], out["toughness"] = p, x
    if "loyalty" in f:
        out["loyalty"] = f["loyalty"]
    ci = set()
    for k in pips:
        ci |= {c for c in COLORS if c in k}
    for c, name in zip(COLORS, ("white", "blue", "black", "red", "green")):
        if name in (f.get("color_ind") or "").lower():
            ci.add(c)
    # símbolos de maná en el texto (sin el texto recordatorio entre paréntesis)
    ci |= colors_in(re.sub(r"\([^)]*\)", "", out["oracle"]))
    return out, ci, f.get("alt")


def parse_file(path):
    txt = open(path, encoding="utf-8").read()
    blocks = re.split(r"^ALTERNATE\s*$", txt, flags=re.M)
    faces, ci, layout = [], set(), "normal"
    for b in blocks:
        face, c, alt = parse_face(b.splitlines())
        if alt:
            layout = {"DoubleFaced": "transform", "Modal": "modal_dfc", "Split": "split", "Adventure": "adventure",
                      "Flip": "flip", "Omen": "omen", "Specialize": "specialize"}.get(alt, alt.lower())
        if face["name"]:
            faces.append(face); ci |= c
    if not faces or not faces[0]["name"]:
        return None
    card = dict(faces[0])
    card["layout"] = layout
    card["color_identity"] = "".join(c for c in COLORS if c in ci)
    if len(faces) > 1 and layout != "normal":
        card["faces"] = faces[1:]
        card["full_name"] = " // ".join(f["name"] for f in faces)
    return card


def build(folder):
    db = {}
    for path in glob.glob(os.path.join(folder, "**", "*.txt"), recursive=True):
        c = parse_file(path)
        if not c:
            continue
        # reimpresiones y variantes (A-, playtest): gana la que no tiene prefijo
        if c["name"] in db and c["name"].startswith("A-"):
            continue
        db[c["name"]] = c
    return db


def wanted_names():
    sys.path.insert(0, HERE)
    import deck_cards
    names = set()
    for deck in deck_cards.DECKS:
        names |= set(deck_cards.load(deck))
    extra = os.path.join(HERE, "extra.txt")
    if os.path.exists(extra):
        names |= {l.strip() for l in open(extra, encoding="utf-8") if l.strip() and not l.startswith("#")}
    return names


def main():
    folder = sys.argv[1]
    allc = "--todas" in sys.argv
    db = build(folder)
    index = dict(db)
    for c in db.values():
        if "full_name" in c:
            index.setdefault(c["full_name"], c)
            for f in c.get("faces", []):
                index.setdefault(f["name"], c)
    if allc:
        out, path = db, os.path.join(HERE, "cards_db_todas.json")
    else:
        names = wanted_names()
        out, missing = {}, []
        for n in sorted(names):
            c = index.get(n)
            (out.__setitem__(c["name"], c) if c else missing.append(n))
        path = os.path.join(HERE, "cards_db.json")
        if missing:
            print(f"{len(missing)} nombres sin carta en Forge (alias internos del simulador):", missing)
    json.dump(out, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=0, sort_keys=True)
    print(f"{len(out)} cartas -> {path} ({os.path.getsize(path) // 1024} KB)")


if __name__ == "__main__":
    main()
