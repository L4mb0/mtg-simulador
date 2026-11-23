"""Base de cartas del simulador de Blight Curse (Auntie Ool, Cursewretch).

Textos verificados con la API de Scryfall (01/11/2026). Costes: dígitos = genérico, letras = color,
"(BR)" = híbrido. t: C criatura, I instantáneo, S conjuro, A artefacto, E encantamiento, W planeswalker.
Etiquetas: fly, reach, wither, dt (deathtouch), menace, defender, black (para Midnight Banshee),
selfc (se pone contadores a sí misma), haste, legend, token1 (deja criaturas de 1 de resistencia).
"""
import re

COMMANDER = "Auntie Ool, Cursewretch"


def C(cost, t, p=0, tg=0):
    return dict(cost=cost, t=t, p=p, tg=tg)


CARDS = {
    # ---------------------------------------------------------------- precon (60 no-tierra + comandante)
    COMMANDER: C("1BRG", "C", 4, 4),
    "Archfiend of Ifnir": C("3BB", "C", 5, 4),
    "Carnifex Demon": C("4BB", "C", 6, 6),
    "Channeler Initiate": C("1G", "C", 3, 4),
    "Devoted Druid": C("1G", "C", 0, 2),
    "Dread Tiller": C("1BG", "C", 2, 4),
    "Dusk Urchins": C("2B", "C", 4, 3),
    "Evolution Sage": C("2G", "C", 3, 2),
    "Ferrafor, Young Yew": C("6G", "C", 4, 7),
    "Glissa Sunslayer": C("1BG", "C", 3, 3),
    "Grave Titan": C("4BB", "C", 6, 6),
    "Grim Poppet": C("7", "C", 4, 4),
    "Hapatra, Vizier of Poisons": C("BG", "C", 2, 2),
    "Ignoble Hierarch": C("G", "C", 0, 1),
    "Kulrath Knight": C("3(BR)(BR)", "C", 3, 3),
    "Massacre Girl, Known Killer": C("2BB", "C", 4, 4),
    "Midnight Banshee": C("3BBB", "C", 5, 5),
    "Necroskitter": C("1BB", "C", 1, 4),
    "Oft-Nabbed Goat": C("1B", "C", 0, 5),
    "Puppeteer Clique": C("3BB", "C", 3, 2),
    "Sinister Gnarlbark": C("2B", "C", 0, 4),
    "Skinrender": C("2BB", "C", 3, 3),
    "Soul Snuffers": C("2BB", "C", 3, 3),
    "The Reaper, King No More": C("BRG", "C", 3, 3),   # {2/B}{2/R}{2/G}: se paga con colores
    "The Scorpion God": C("3BR", "C", 6, 5),
    "Tree of Perdition": C("3B", "C", 0, 13),
    "Village Pillagers": C("3RR", "C", 5, 5),
    "Wickerbough Elder": C("3G", "C", 4, 4),
    "Assassin's Trophy": C("BG", "I"),
    "Cathartic Pyre": C("1R", "I"),
    "Fire Covenant": C("1BR", "I"),
    "Infernal Grasp": C("1B", "I"),
    "Putrefy": C("1BG", "I"),
    "Terminate": C("BR", "I"),
    "Aberrant Return": C("4BB", "S"),
    "Black Sun's Zenith": C("BB", "S"),
    "Burning Curiosity": C("2R", "S"),
    "Cathartic Reunion": C("1R", "S"),
    "Chain Reaction": C("2RR", "S"),
    "Eventide's Shadow": C("4B", "S"),
    "Harmonize": C("2GG", "S"),
    "Hoarder's Greed": C("3B", "S"),
    "Incremental Blight": C("3BB", "S"),
    "Night's Whisper": C("1B", "S"),
    "Painful Truths": C("2B", "S"),
    "Persist": C("1B", "S"),
    "Arcane Signet": C("2", "A"),
    "Chimil, the Inner Sun": C("6", "A", 0, 0),
    "Commander's Sphere": C("3", "A"),
    "Contagion Clasp": C("2", "A"),
    "Sol Ring": C("1", "A"),
    "Wickersmith's Tools": C("3", "A"),
    "Binding the Old Gods": C("2BG", "E"),
    "Blowfly Infestation": C("2B", "E"),
    "Everlasting Torment": C("2(BR)", "E"),
    "Flourishing Defenses": C("4G", "E"),
    "Grave Venerations": C("3B", "E"),
    "Lasting Tarfire": C("1R", "E"),
    "Puca's Covenant": C("2G", "E"),
    "Liliana, Death Wielder": C("5BB", "W"),
    "Vraska, Betrayal's Sting": C("4BB", "W"),
    # ---------------------------------------------------------------- candidatas (guías y EDHREC)
    "Generous Patron": C("2G", "C", 1, 4),
    "Dawnhand Dissident": C("B", "C", 1, 2),
    "Grim Affliction": C("2B", "I"),
    "Farseek": C("1G", "S"),
    "Rampant Growth": C("1G", "S"),
    "Nature's Lore": C("1G", "S"),
    "Obelisk Spider": C("1BG", "C", 1, 4),
    "Maha, Its Feathers Night": C("3BB", "C", 6, 5),
    "Persistent Constrictor": C("4B", "C", 5, 3),
    "Nest of Scarabs": C("2B", "E"),
    "Harbinger of Night": C("2BB", "C", 2, 3),
    "Scuzzback Scrounger": C("1R", "C", 3, 2),
    "Darkness Descends": C("2BB", "S"),
    "Heroic Intervention": C("1G", "I"),
    "Swiftfoot Boots": C("2", "A"),
    "Lightning Greaves": C("2", "A"),
    "Ammit Eternal": C("2B", "C", 5, 5),
    "Atomize": C("2BG", "I"),
    "Shadow Urchin": C("2(BR)", "C", 3, 4),
    "Banewhip Punisher": C("2B", "C", 2, 2),
    "Mahadi, Emporium Master": C("1BR", "C", 3, 3),
    "Whisper of the Dross": C("B", "I"),
    "Skullclamp": C("1", "A"),
    "Yawgmoth, Thran Physician": C("2BB", "C", 2, 4),
    "All Will Be One": C("3RR", "E"),
    "Contagion Engine": C("6", "A"),
    "Crumbling Ashes": C("1B", "E"),
    "Massacre Wurm": C("3BBB", "C", 6, 5),
    "Diabolic Tutor": C("2BB", "S"),
    "Grim Tutor": C("1BB", "S"),
    "Diabolic Intent": C("1B", "S"),
    "Pollenbright Druid": C("1G", "C", 1, 1),
    "Tezzeret's Gambit": C("3", "S"),          # {3}{U/P}: se paga la parte phyrexiana con 2 de vida
    "Archfiend of Sorrows": C("5BB", "C", 4, 5),
    "The Meathook Massacre": C("2BB", "E"),   # X fijo por el piloto (coste base BB + X)
    "Zulaport Cutthroat": C("1B", "C", 1, 1),
    "Blood Artist": C("1B", "C", 0, 1),
    "Bastion of Remembrance": C("2B", "E"),
    "Cauldron of Essence": C("1BG", "A"),
    "Soul Immolation": C("3RR", "S"),
    "Morselhoarder": C("4(RG)(RG)", "C", 6, 4),
    "High-Society Hunter": C("3BB", "C", 5, 3),
    "Agent Venom": C("2B", "C", 2, 3),
    "Grim Haruspex": C("2B", "C", 3, 2),
    "Demonic Tutor": C("1B", "S"),
    "Vampiric Tutor": C("B", "I"),
    "Worldly Tutor": C("G", "I"),
    "Blight Rot": C("2B", "I"),
    "Murder": C("1BB", "I"),
    "Blank": C("99", "S"),   # carta muerta para la ablación
}

# Fase 4: los efectos de cada carta (roles, palabras clave, respuestas, rocas...) viven en data/efectos.yaml;
# aquí quedan coste, tipo y P/T. core/mapeo.py los vuelve a poner con las claves de siempre.
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", ".."))
from core import mapeo as _MP
for _n in list(CARDS):
    CARDS[_n] = _MP.importar("blight", _n, CARDS[_n])

# ---------------------------------------------------------------- tierras
# col: colores que produce; mode: U (sin girar), T (girada), basics2, check:<tipos>, fetch, bounce
LANDS = {
    "Swamp": dict(col="B", mode="U", basic=True, types={"Swamp"}),
    "Mountain": dict(col="R", mode="U", basic=True, types={"Mountain"}),
    "Forest": dict(col="G", mode="U", basic=True, types={"Forest"}),
    "Canyon Slough": dict(col="BR", mode="T", cyc=2, types={"Swamp", "Mountain"}),
    "Cinder Glade": dict(col="RG", mode="basics2", types={"Mountain", "Forest"}),
    "Command Tower": dict(col="BRG", mode="U"),
    "Dragonskull Summit": dict(col="BR", mode="check:Swamp,Mountain"),
    "Evolving Wilds": dict(col="", mode="fetch"),
    "Terramorphic Expanse": dict(col="", mode="fetch"),
    "Riveteers Overlook": dict(col="", mode="fetch"),
    "Exotic Orchard": dict(col="BRG", mode="U"),
    "Festering Thicket": dict(col="BG", mode="T", cyc=2, types={"Swamp", "Forest"}),
    "Golgari Rot Farm": dict(col="BG", mode="bounce"),
    "Gruul Turf": dict(col="RG", mode="bounce"),
    "Rakdos Carnarium": dict(col="BR", mode="bounce"),
    "Ifnir Deadlands": dict(col="B", mode="U"),      # {C} o {B} pagando 1 vida: se modela como B
    "Nesting Grounds": dict(col="", mode="U"),
    "Path of Ancestry": dict(col="BRG", mode="T"),
    "Rootbound Crag": dict(col="RG", mode="check:Mountain,Forest"),
    "Savage Lands": dict(col="BRG", mode="T"),
    "Sheltered Thicket": dict(col="RG", mode="T", cyc=2, types={"Mountain", "Forest"}),
    "Smoldering Marsh": dict(col="BR", mode="basics2", types={"Swamp", "Mountain"}),
    "Vernal Fen": dict(col="BG", mode="basics2", types={"Swamp", "Forest"}),
    "Woodland Cemetery": dict(col="BG", mode="check:Swamp,Forest"),
    # candidatas
    "Ziatora's Proving Ground": dict(col="BRG", mode="T", cyc=3, types={"Swamp", "Mountain", "Forest"}),
    "Overgrown Tomb": dict(col="BG", mode="U", types={"Swamp", "Forest"}),
    "Blood Crypt": dict(col="BR", mode="U", types={"Swamp", "Mountain"}),
    "Stomping Ground": dict(col="RG", mode="U", types={"Mountain", "Forest"}),
}

PRECON = """1 Archfiend of Ifnir
1 Carnifex Demon
1 Channeler Initiate
1 Devoted Druid
1 Dread Tiller
1 Dusk Urchins
1 Evolution Sage
1 Ferrafor, Young Yew
1 Glissa Sunslayer
1 Grave Titan
1 Grim Poppet
1 Hapatra, Vizier of Poisons
1 Ignoble Hierarch
1 Kulrath Knight
1 Massacre Girl, Known Killer
1 Midnight Banshee
1 Necroskitter
1 Oft-Nabbed Goat
1 Puppeteer Clique
1 Sinister Gnarlbark
1 Skinrender
1 Soul Snuffers
1 The Reaper, King No More
1 The Scorpion God
1 Tree of Perdition
1 Village Pillagers
1 Wickerbough Elder
1 Assassin's Trophy
1 Cathartic Pyre
1 Fire Covenant
1 Infernal Grasp
1 Putrefy
1 Terminate
1 Aberrant Return
1 Black Sun's Zenith
1 Burning Curiosity
1 Cathartic Reunion
1 Chain Reaction
1 Eventide's Shadow
1 Harmonize
1 Hoarder's Greed
1 Incremental Blight
1 Night's Whisper
1 Painful Truths
1 Persist
1 Arcane Signet
1 Chimil, the Inner Sun
1 Commander's Sphere
1 Contagion Clasp
1 Sol Ring
1 Wickersmith's Tools
1 Binding the Old Gods
1 Blowfly Infestation
1 Everlasting Torment
1 Flourishing Defenses
1 Grave Venerations
1 Lasting Tarfire
1 Puca's Covenant
1 Liliana, Death Wielder
1 Vraska, Betrayal's Sting
1 Canyon Slough
1 Cinder Glade
1 Command Tower
1 Dragonskull Summit
1 Evolving Wilds
1 Exotic Orchard
1 Festering Thicket
1 Golgari Rot Farm
1 Gruul Turf
1 Ifnir Deadlands
1 Nesting Grounds
1 Path of Ancestry
1 Rakdos Carnarium
1 Riveteers Overlook
1 Rootbound Crag
1 Savage Lands
1 Sheltered Thicket
1 Smoldering Marsh
1 Terramorphic Expanse
1 Vernal Fen
1 Woodland Cemetery
8 Swamp
6 Forest
4 Mountain
"""


def load(text):
    deck = []
    for line in text.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        n, name = line.split(" ", 1)
        deck += [name] * int(n)
    return deck


def parse_cost(s):
    """'3(BR)(BR)' -> (generic, [pips]); cada pip es un string de colores aceptados."""
    pips = re.findall(r"\(([BRG]+)\)", s)
    s2 = re.sub(r"\([BRG]+\)", "", s)
    g = sum(int(x) for x in re.findall(r"\d+", s2))
    pips += [c for c in s2 if c in "BRG"]
    return g, pips


def mv(name):
    if name in LANDS:
        return 0
    g, pips = parse_cost(CARDS[name]["cost"])
    if name == "The Reaper, King No More":
        return 6
    return g + len(pips)


def swap(deck, out, inn):
    d = list(deck)
    d[d.index(out)] = inn
    return d


PRECON_DECK = load(PRECON)
assert len(PRECON_DECK) == 99, len(PRECON_DECK)
for _c in PRECON_DECK:
    assert _c in CARDS or _c in LANDS, _c

FASE1 = [("Hoarder's Greed", "Generous Patron"), ("Painful Truths", "Dawnhand Dissident"),
         ("Cathartic Reunion", "Grim Affliction"), ("Commander's Sphere", "Farseek"),
         ("Liliana, Death Wielder", "Obelisk Spider"), ("Grave Titan", "Maha, Its Feathers Night"),
         ("Archfiend of Ifnir", "Persistent Constrictor"), ("Chimil, the Inner Sun", "Nest of Scarabs"),
         ("Ferrafor, Young Yew", "Harbinger of Night")]


def apply(deck, pairs):
    d = list(deck)
    for o, i in pairs:
        d = swap(d, o, i)
    return d
