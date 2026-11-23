"""Compara los datos escritos a mano en cada decks/<mazo>/cards.py con core/cards_db.json (Forge).

    python3 core/compare.py            # escribe core/diferencias.md y resume por consola
    python3 core/compare.py --test     # sale con error si aparece una diferencia que no está en core/revisadas.txt

Qué compara: valor de maná, genérico, pips de color, tipo principal, poder/resistencia (si el simulador los
anota) e identidad de color contra la del comandante. Las diferencias revisadas con Juan y aceptadas (el
simulador modela la carta a propósito de otra forma) se anotan en core/revisadas.txt como
"mazo|carta|campo" para que la prueba no las vuelva a marcar.
"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import deck_cards as DC

HERE = os.path.dirname(os.path.abspath(__file__))
COMMANDER_CI = {"gandalf": "R", "gorma": "BG", "giada": "W", "blight": "BRG", "blor": "G"}
SKIP = {"Blank"}  # relleno del simulador, no es una carta


def color_count(pips, color):
    return sum(n for k, n in pips.items() if color in k.split("/") or k == color)


def compare(deck, db):
    rows, missing = [], []
    sim = DC.load(deck)
    cur = DC.current_list(deck)
    for name, s in sorted(sim.items()):
        if name in SKIP:
            continue
        c = db.get(name) or next((v for v in db.values() if v.get("full_name") == name or
                                  any(f["name"] == name for f in v.get("faces", []))), None)
        if not c:
            missing.append(name); continue
        face = c if c["name"] == name or c.get("full_name") == name else next(f for f in c["faces"] if f["name"] == name)
        all_types = set(c["types"]) | {t for f in c.get("faces", []) for t in f["types"]}

        def diff(field, mine, real):
            rows.append((name, field, mine, real, "sí" if name in cur else ""))

        if s["type"] and s["type"] not in all_types:
            diff("tipo", s["type"], " ".join(c["supertypes"] + c["types"]))
        if s["type"] != "Land" and "Land" not in face["types"]:
            has_x = "{X}" in (face["mana_cost"] or "")
            if has_x:
                pass  # el simulador anota el X que elige
            elif s["mv"] != face["mv"]:
                diff("valor de maná", s["mv"], f'{face["mv"]} {face["mana_cost"] or ""}')
            elif s["generic"] != face["generic"] and "*" not in s["pips"]:
                diff("genérico", s["generic"], f'{face["generic"]} {face["mana_cost"]}')
            pips = s["pips"]
            if "*" in pips:  # Gorma: solo anota cuántos pips de color
                real = sum(n for k, n in face["pips"].items() if k not in ("C", "S") and not k.startswith("2/"))
                if pips["*"] != real:
                    diff("pips de color", pips["*"], face["mana_cost"])
            elif deck == "blight":
                if dict(sorted(pips.items())) != dict(sorted((k, n) for k, n in face["pips"].items())):
                    diff("pips de color", pips, face["mana_cost"])
            else:
                col = DC.MAIN_COLOR[deck]
                if pips.get(col, 0) != color_count(face["pips"], col):
                    diff(f"pips {col}", pips.get(col, 0), face["mana_cost"])
        if s["power"] is not None and face.get("power", "").isdigit() and int(face["power"]) != s["power"]:
            diff("poder", s["power"], face["power"])
        if s["toughness"] is not None and face.get("toughness", "").isdigit() and int(face["toughness"]) != s["toughness"]:
            diff("resistencia", s["toughness"], face["toughness"])
        out_ci = set(c["color_identity"]) - set(COMMANDER_CI[deck])
        if out_ci:
            diff("identidad de color", COMMANDER_CI[deck], c["color_identity"])
    return rows, missing


def main():
    db = json.load(open(os.path.join(HERE, "cards_db.json"), encoding="utf-8"))
    rev_path = os.path.join(HERE, "revisadas.txt")
    reviewed = set()
    if os.path.exists(rev_path):
        reviewed = {l.strip() for l in open(rev_path, encoding="utf-8") if l.strip() and not l.startswith("#")}
    md = ["# Diferencias entre los cards.py y Forge", "",
          "Generado con `python3 core/compare.py`. «Simulador» es lo que dice `cards.py`; «Forge» es la carta real.",
          "Las marcadas ✔ ya se revisaron con Juan (`core/revisadas.txt`).", ""]
    new_total = 0
    for deck in DC.DECKS:
        rows, missing = compare(deck, db)
        new = [r for r in rows if f"{deck}|{r[0]}|{r[1]}" not in reviewed]
        new_total += len(new)
        print(f"{deck:8} {len(rows):3} diferencias ({len(new)} sin revisar), {len(missing)} sin carta en Forge")
        md += [f"## {deck} ({len(rows)})", ""]
        if missing:
            md += ["Sin carta en Forge: " + ", ".join(missing), ""]
        if rows:
            md += ["| Carta | Campo | Simulador | Forge | En la lista vigente | |", "|---|---|---|---|---|---|"]
            for n, f, a, b, cur in sorted(rows, key=lambda r: (r[4] != "sí", r[0])):
                md.append(f"| {n} | {f} | {a} | {b} | {cur} | {'✔' if f'{deck}|{n}|{f}' in reviewed else ''} |")
            md.append("")
    open(os.path.join(HERE, "diferencias.md"), "w", encoding="utf-8").write("\n".join(md))
    if "--test" in sys.argv and new_total:
        sys.exit(f"{new_total} diferencias sin revisar (ver core/diferencias.md)")


if __name__ == "__main__":
    main()
