# Card database for the Gandalf goldfish simulator.
# t: land / creature / artifact / enchantment / instant / sorcery
# g: generic cost, r: red pips, red: is the spell red (Ruby Medallion etc.)
C = {}
FORGE = "FORGE"   # coste, tipo y P/T desde core/cards_db.json (Forge); ver core/stats.py
def card(name, t=None, g=0, r=0, red=True):
    """card(nombre): coste y tipo desde Forge (core/stats.py); con más argumentos, un ajuste a mano."""
    C[name] = FORGE if t is None else dict(t=t, g=g, r=r, red=red)

# lands
card("Mountain")
card("War Room")
card("Rogue's Passage")
# MDFC / land-adventure
card("Lindblum, Industrial Regency")
card("Shatterskull Smashing")
card("Sundering Eruption")
card("Valakut Awakening")
card("Pinnacle Monk")
# rocks / mana permanents
card("Sol Ring")
card("Arcane Signet")
card("Mind Stone")
card("Tablet of Discovery")
card("The Fire Crystal")
card("Ruby Medallion")
card("Primal Amulet")
card("The One Ring")
card("Lightning Greaves")
card("Swiftfoot Boots")
card("Simian Spirit Guide")
card("Mishra's Bauble")
# creatures
card("Harmonic Prodigy")
card("Coruscation Mage")
card("Erebor Flamesmith")
card("Guttersnipe")
card("Kessig Flamebreather")
card("Thunderdrum Soloist")
card("Emeritus of Conflict")
card("Krark, the Thumbless")
card("Tomik, Izzet Sparkmage")
card("Party Thrasher")
card("Burning Prophet")
card("Mysidian Elder")
card("Electro, Assaulting Battery")
card("Pyre Rhymer")
card("Ashling, Flame Dancer")
card("Longshot, Rebel Bowman")
card("Ojer Axonil, Deepest Might")
card("Storm-Kiln Artist")
card("Urabrask")
card("Wiccan, Young Avenger")
# enchantments
card("Artist's Talent")
card("Count on Luck")
card("Fiery Inscription")
card("Burn, Burn, Tree and Fern")
card("Virtue of Courage")
# instants / sorceries
card("Faithless Looting")
card("Gamble")
card("Gut Shot", "instant", 0, 0)            # Phyrexian: paid with life
card("Lightning Bolt")
card("Redirect Lightning")
card("Vandalblast")
card("Commune with Lava")
card("Demand Answers")
card("Desperate Ritual")
card("Pyretic Ritual")
card("Seething Song")
card("Grapeshot")
card("Reckless Impulse")
card("Wrenn's Resolve")
card("Tormenting Voice")
card("Return the Favor", "instant", 1, 2)   # copy mode: {R}{R} + {1}
card("Reverberate")
card("Doublecast")
card("Untimely Malfunction")
card("Chaos Warp")
card("Delayed Blast Fireball")
card("Jeska's Will")
card("Light Up the Stage")
card("Wheel of Misfortune")
card("Seize the Spoils")
card("Big Score")
card("Fiery Confluence")
card("Mizzix's Mastery")
card("Past in Flames")
card("Will of the Jeskai")
card("Mana Geyser")
card("Blasphemous Act")
card("Thunderclap")

RITUAL_NET = {"Desperate Ritual": 3, "Pyretic Ritual": 3, "Seething Song": 5}

# value used to decide what to discard / bottom (higher = keep)
VALUE = {
    "Blasphemous Act": 0, "Redirect Lightning": 1, "Rogue's Passage": 2, "War Room": 2,
    "Vandalblast": 3, "Chaos Warp": 3, "Untimely Malfunction": 3, "Lightning Greaves": 3, "Swiftfoot Boots": 3,
    "Burn, Burn, Tree and Fern": 3, "Shatterskull Smashing": 4, "Sundering Eruption": 4,
}

card("Blank", "sorcery", 99, 0)
VALUE["Blank"] = -1
# --- candidates for 1.4 tests ---
card("Lotus Petal")
card("Mox Amber")
card("Fireblast")
card("Lava Dart")
card("Spikefield Hazard")
card("Rite of Flame")
card("Burst Lightning")
card("Strike It Rich")
card("Torbran, Thane of Red Fell")
card("Birgi, God of Storytelling")
card("Electrostatic Field")
card("Thermo-Alchemist")
card("Firebrand Archer")
VALUE.update({"Simian Spirit Guide": 6})
card("Solphim, Mayhem Dominus")
card("Fiery Emancipation")
card("Fire Diamond")
card("Thrill of Possibility")
card("Mine Collapse")
card("Shock")
card("Magma Spray")
card("Lightning Strike")
card("Demon Bolt")
card("Abrade")
card("Fiery Impulse")
card("Searing Spear")
card("Play with Fire")
card("Unholy Heat")
card("Unexpected Windfall")
card("Pirate's Pillage")
card("Runaway Steam-Kin")
card("Neheb, the Eternal")
card("Faithless Salvaging")
card("Frost Bite")
card("Implement of Combustion")   # {1}, incolora (corregido 23/11)
card("Renegade Map")
card("The Flame of Keld")
card("Skullcrack")

card("Underworld Breach")
card("Ancient Tomb")
card("Mana Vault")
card("Grim Monolith")
card("Chrome Mox")
card("Mox Diamond")
card("Reiterate")
card("Flashback")
card("Overmaster")
card("Manamorphose")
card("Crash Through")
card("Needle Drop")
card("Bonus Round")
card("Fork")
card("Increasing Vengeance")
card("Grinning Ignus")
card("Fated Firepower", "enchantment", 1, 3)
card("Aetherflux Reservoir")
card("Crown of Flames")
card("Helm of Awakening")

# --- 13/11: caras dobles y aventuras ---
card("Harnfel, Horn of Bounty", "artifact", 4, 1)       # dorso de Birgi: descarta una carta -> exilia 2, juegalas este turno
card("Embereth Blaze", "instant", 1, 1)                  # aventura de Virtue of Courage: 2 de dano
# maná neto de cartas que se pueden usar para habilitar una jugada en desarrollo (coste -> maná que dejan)
FAST_NET = {"Lotus Petal": 1, "Rite of Flame": 1, "Desperate Ritual": 1, "Pyretic Ritual": 1, "Seething Song": 2}
# identidad de color: cartas que NO son mono-rojas (se rechazan al cargar una lista)
OFF_COLOR = {"Manamorphose", "Kitchen Finks", "Studious First-Year // Rampant Growth"}

# --- 17/11 y 22/11 (rehechas el 22/11): candidatas de listas online y de la coleccion nueva ---
card("Boltwave")
card("Magmatic Insight")        # coste adicional: descartar una tierra
card("Cathartic Reunion")       # coste adicional: descartar dos cartas
card("Price of Progress")       # 2 de dano por cada tierra no basica de cada jugador
card("Lotus Bloom") # suspend 3: entra al 4to turno desde que se suspende; se sacrifica por 3 de un color
card("Chromatic Lantern")
card("Skullclamp")

# Comandante y mitades de cartas especiales (antes se agregaban en engine.py)
card("Gandalf")
card("Flameshape", "sorcery", g=1, r=1)
card("Emeritus Bolt", "instant", g=0, r=1)
card("Molten Tide", "instant", g=0, r=1)
card("Lindblum Siege", "instant", g=2, r=1)

# Fase 4: los efectos de cada carta (roles, palabras clave, respuestas, rocas...) viven en data/efectos.yaml;
# aquí quedan coste, tipo y P/T. core/mapeo.py los vuelve a poner con las claves de siempre.
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", ".."))
from core import mapeo as _MP, stats as _ST
for _n, _v in list(C.items()):
    if _v is FORGE:
        C[_n] = _ST.desde_forge("gandalf", _n)
for _n in list(C):
    C[_n] = _MP.importar("gandalf", _n, C[_n])
# (después de cargar los efectos; antes de la fase 4b se calculaba sin ellos)
WIZ_OR_SHAMAN = {n for n, d in C.items() if d.get("wiz") or d.get("shaman")} | {"Gandalf"}
