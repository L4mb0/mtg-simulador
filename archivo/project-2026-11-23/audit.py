"""Auditoria: identidad de color (incluye hibridos y costes en el texto) de todas las cartas del simulador."""
import json, re, os
from cards import C
_here = os.path.dirname(os.path.abspath(__file__))
_tx = os.path.join(_here, "texts.json")
TX = json.load(open(_tx if os.path.exists(_tx) else os.path.join(_here, "..", "sheet", "texts.json")))
INTERNAL = {"Blank", "Gandalf", "Flameshape", "Emeritus Bolt", "Molten Tide", "Lindblum Siege", "Harnfel, Horn of Bounty", "Embereth Blaze"}
# cartas sin texto en texts.json: identidad anotada a mano (no salio de Gatherer; verificar con Scryfall cuando haya navegador)
HAND_ID = {"Manamorphose": {"G"}}
HAND_ID.update({n: set() for n in ["Burst Lightning", "Crown of Flames", "Demon Bolt", "Doublecast", "Faithless Salvaging", "Fated Firepower",
    "Fiery Impulse", "Fire Diamond", "Fireblast", "Fork", "Frost Bite", "Grim Monolith", "Grinning Ignus", "Implement of Combustion",
    "Increasing Vengeance", "Lava Dart", "Lightning Strike", "Magma Spray", "Mana Vault", "Mine Collapse", "Mox Diamond", "Needle Drop",
    "Pirate's Pillage", "Play with Fire", "Renegade Map", "Searing Spear", "Shock", "Spikefield Hazard", "The Flame of Keld",
    "Thunderclap", "Tormenting Voice", "Unholy Heat"]})
def identity(name):
    v = TX.get(name)
    if not v: return HAND_ID.get(name)
    syms = re.findall(r"\{([^}]+)\}", v[1] + " " + v[3])
    cols = set()
    for sy in syms:
        for part in sy.split("/"):
            if part in "WUBG" and part: cols.add(part)
    return cols
if __name__ == "__main__":
    bad, missing = [], []
    for n in sorted(C):
        if n in INTERNAL or C[n]["t"] == "land" and n in ("Mountain",): continue
        idc = identity(n)
        if idc is None: missing.append(n)
        elif idc: bad.append((n, idc))
    print("FUERA DE IDENTIDAD:", bad)
    print("SIN TEXTO EN texts.json (verificar a mano):", missing)
