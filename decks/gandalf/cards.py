# Card database for the Gandalf goldfish simulator.
# t: land / creature / artifact / enchantment / instant / sorcery
# g: generic cost, r: red pips, red: is the spell red (Ruby Medallion etc.)
C = {}
def card(name, t, g=0, r=0, red=True):
    C[name] = dict(t=t, g=g, r=r, red=red)

# lands
card("Mountain", "land")
card("War Room", "land")
card("Rogue's Passage", "land")
# MDFC / land-adventure
card("Lindblum, Industrial Regency", "land")
card("Shatterskull Smashing", "sorcery", 0, 2)
card("Sundering Eruption", "sorcery", 2, 1)
card("Valakut Awakening", "instant", 2, 1)
card("Pinnacle Monk", "creature", 3, 2)
# rocks / mana permanents
card("Sol Ring", "artifact", 1, 0, red=False)
card("Arcane Signet", "artifact", 2, 0, red=False)
card("Mind Stone", "artifact", 2, 0, red=False)
card("Tablet of Discovery", "artifact", 2, 1)
card("The Fire Crystal", "artifact", 2, 2)
card("Ruby Medallion", "artifact", 2, 0, red=False)
card("Primal Amulet", "artifact", 4, 0, red=False)
card("The One Ring", "artifact", 4, 0, red=False)
card("Lightning Greaves", "artifact", 2, 0, red=False)
card("Swiftfoot Boots", "artifact", 2, 0, red=False)
card("Simian Spirit Guide", "creature", 2, 1)
card("Mishra's Bauble", "artifact", 0, 0, red=False)
# creatures
card("Harmonic Prodigy", "creature", 1, 1)
card("Coruscation Mage", "creature", 1, 1)
card("Erebor Flamesmith", "creature", 1, 1)
card("Guttersnipe", "creature", 2, 1)
card("Kessig Flamebreather", "creature", 1, 1)
card("Thunderdrum Soloist", "creature", 1, 1)
card("Emeritus of Conflict", "creature", 1, 1)
card("Krark, the Thumbless", "creature", 1, 1)
card("Tomik, Izzet Sparkmage", "creature", 1, 1)
card("Party Thrasher", "creature", 1, 1)
card("Burning Prophet", "creature", 1, 1)
card("Mysidian Elder", "creature", 2, 1)
card("Electro, Assaulting Battery", "creature", 1, 2)
card("Pyre Rhymer", "creature", 1, 2)
card("Ashling, Flame Dancer", "creature", 2, 2)
card("Longshot, Rebel Bowman", "creature", 3, 1)
card("Ojer Axonil, Deepest Might", "creature", 2, 2)
card("Storm-Kiln Artist", "creature", 3, 1)
card("Urabrask", "creature", 2, 2)
card("Wiccan, Young Avenger", "creature", 3, 1)
# enchantments
card("Artist's Talent", "enchantment", 1, 1)
card("Count on Luck", "enchantment", 0, 3)
card("Fiery Inscription", "enchantment", 2, 1)
card("Burn, Burn, Tree and Fern", "enchantment", 3, 1)
card("Virtue of Courage", "enchantment", 3, 2)
# instants / sorceries
card("Faithless Looting", "sorcery", 0, 1)
card("Gamble", "sorcery", 0, 1)
card("Gut Shot", "instant", 0, 0)            # Phyrexian: paid with life
card("Lightning Bolt", "instant", 0, 1)
card("Redirect Lightning", "instant", 0, 1)
card("Vandalblast", "sorcery", 0, 1)
card("Commune with Lava", "instant", 0, 2)
card("Demand Answers", "instant", 1, 1)
card("Desperate Ritual", "instant", 1, 1)
card("Pyretic Ritual", "instant", 1, 1)
card("Seething Song", "instant", 2, 1)
card("Grapeshot", "sorcery", 1, 1)
card("Reckless Impulse", "sorcery", 1, 1)
card("Wrenn's Resolve", "sorcery", 1, 1)
card("Tormenting Voice", "sorcery", 1, 1)
card("Return the Favor", "instant", 1, 2)   # copy mode: {R}{R} + {1}
card("Reverberate", "instant", 0, 2)
card("Doublecast", "sorcery", 0, 2)
card("Untimely Malfunction", "instant", 1, 1)
card("Chaos Warp", "instant", 2, 1)
card("Delayed Blast Fireball", "instant", 1, 2)
card("Jeska's Will", "sorcery", 2, 1)
card("Light Up the Stage", "sorcery", 2, 1)
card("Wheel of Misfortune", "sorcery", 2, 1)
card("Seize the Spoils", "sorcery", 2, 1)
card("Big Score", "instant", 3, 1)
card("Fiery Confluence", "sorcery", 2, 2)
card("Mizzix's Mastery", "sorcery", 3, 1)
card("Past in Flames", "sorcery", 3, 1)
card("Will of the Jeskai", "sorcery", 3, 1)
card("Mana Geyser", "sorcery", 3, 2)
card("Blasphemous Act", "sorcery", 8, 1)
card("Thunderclap", "instant", 2, 1)

RITUAL_NET = {"Desperate Ritual": 3, "Pyretic Ritual": 3, "Seething Song": 5}
WIZ_OR_SHAMAN = {n for n, d in C.items() if d.get("wiz") or d.get("shaman")} | {"Gandalf"}

# value used to decide what to discard / bottom (higher = keep)
VALUE = {
    "Blasphemous Act": 0, "Redirect Lightning": 1, "Rogue's Passage": 2, "War Room": 2,
    "Vandalblast": 3, "Chaos Warp": 3, "Untimely Malfunction": 3, "Lightning Greaves": 3, "Swiftfoot Boots": 3,
    "Burn, Burn, Tree and Fern": 3, "Shatterskull Smashing": 4, "Sundering Eruption": 4,
}

card("Blank", "sorcery", 99, 0)
VALUE["Blank"] = -1
# --- candidates for 1.4 tests ---
card("Lotus Petal", "artifact", 0, 0, red=False)
card("Mox Amber", "artifact", 0, 0, red=False)
card("Fireblast", "instant", 4, 2)
card("Lava Dart", "instant", 0, 1)
card("Spikefield Hazard", "instant", 0, 1)
card("Rite of Flame", "sorcery", 0, 1)
card("Burst Lightning", "instant", 0, 1)
card("Strike It Rich", "sorcery", 0, 1)
card("Torbran, Thane of Red Fell", "creature", 1, 3)
card("Birgi, God of Storytelling", "creature", 2, 1)
card("Electrostatic Field", "creature", 1, 1)
card("Thermo-Alchemist", "creature", 1, 1)
card("Firebrand Archer", "creature", 1, 1)
VALUE.update({"Simian Spirit Guide": 6})
card("Solphim, Mayhem Dominus", "creature", 2, 2)
card("Fiery Emancipation", "enchantment", 3, 3)
card("Fire Diamond", "artifact", 2, 0, red=False)
card("Thrill of Possibility", "instant", 1, 1)
card("Mine Collapse", "instant", 3, 1)
card("Shock", "instant", 0, 1)
card("Magma Spray", "instant", 0, 1)
card("Lightning Strike", "instant", 1, 1)
card("Demon Bolt", "instant", 2, 1)
card("Abrade", "instant", 1, 1)
card("Fiery Impulse", "instant", 0, 1)
card("Searing Spear", "instant", 1, 1)
card("Play with Fire", "instant", 0, 1)
card("Unholy Heat", "instant", 0, 1)
card("Unexpected Windfall", "instant", 2, 2)
card("Pirate's Pillage", "sorcery", 3, 1)
card("Runaway Steam-Kin", "creature", 1, 1)
card("Neheb, the Eternal", "creature", 3, 2)
card("Faithless Salvaging", "instant", 1, 1)
card("Frost Bite", "instant", 0, 1)
card("Implement of Combustion", "artifact", 0, 1)
card("Renegade Map", "artifact", 1, 0, red=False)
card("The Flame of Keld", "enchantment", 1, 1)
card("Skullcrack", "instant", 1, 1)

card("Underworld Breach", "enchantment", 1, 1)
card("Ancient Tomb", "land")
card("Mana Vault", "artifact", 1, 0, red=False)
card("Grim Monolith", "artifact", 2, 0, red=False)
card("Chrome Mox", "artifact", 0, 0, red=False)
card("Mox Diamond", "artifact", 0, 0, red=False)
card("Reiterate", "instant", 1, 2)
card("Flashback", "instant", 0, 1)
card("Overmaster", "sorcery", 0, 1)
card("Manamorphose", "instant", 1, 1)
card("Crash Through", "sorcery", 0, 1)
card("Needle Drop", "instant", 0, 1)
card("Bonus Round", "sorcery", 1, 2)
card("Fork", "instant", 0, 2)
card("Increasing Vengeance", "instant", 0, 2)
card("Grinning Ignus", "creature", 2, 1)
card("Fated Firepower", "enchantment", 1, 3)
card("Aetherflux Reservoir", "artifact", 4, 0, red=False)
card("Crown of Flames", "enchantment", 0, 1)
card("Helm of Awakening", "artifact", 2, 0, red=False)

# --- 13/11: caras dobles y aventuras ---
card("Harnfel, Horn of Bounty", "artifact", 4, 1)       # dorso de Birgi: descarta una carta -> exilia 2, juegalas este turno
card("Embereth Blaze", "instant", 1, 1)                  # aventura de Virtue of Courage: 2 de dano
# maná neto de cartas que se pueden usar para habilitar una jugada en desarrollo (coste -> maná que dejan)
FAST_NET = {"Lotus Petal": 1, "Rite of Flame": 1, "Desperate Ritual": 1, "Pyretic Ritual": 1, "Seething Song": 2}
# identidad de color: cartas que NO son mono-rojas (se rechazan al cargar una lista)
OFF_COLOR = {"Manamorphose", "Kitchen Finks", "Studious First-Year // Rampant Growth"}

# --- 17/11 y 22/11 (rehechas el 22/11): candidatas de listas online y de la coleccion nueva ---
card("Boltwave", "sorcery", 0, 1)
card("Magmatic Insight", "sorcery", 0, 1)        # coste adicional: descartar una tierra
card("Cathartic Reunion", "sorcery", 1, 1)       # coste adicional: descartar dos cartas
card("Price of Progress", "instant", 1, 1)       # 2 de dano por cada tierra no basica de cada jugador
card("Lotus Bloom", "artifact", 0, 0, red=False) # suspend 3: entra al 4to turno desde que se suspende; se sacrifica por 3 de un color
card("Chromatic Lantern", "artifact", 3, 0, red=False)
card("Skullclamp", "artifact", 1, 0, red=False)

# Fase 4: los efectos de cada carta (roles, palabras clave, respuestas, rocas...) viven en data/efectos.yaml;
# aquí quedan coste, tipo y P/T. core/mapeo.py los vuelve a poner con las claves de siempre.
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", ".."))
from core import mapeo as _MP
for _n in list(C):
    C[_n] = _MP.importar("gandalf", _n, C[_n])
