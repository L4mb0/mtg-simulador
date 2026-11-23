"""Base de cartas del simulador de Blight Curse (Auntie Ool, Cursewretch).

Textos verificados con la API de Scryfall (01/11/2026). Costes: dígitos = genérico, letras = color,
"(BR)" = híbrido. t: C criatura, I instantáneo, S conjuro, A artefacto, E encantamiento, W planeswalker.
Etiquetas: fly, reach, wither, dt (deathtouch), menace, defender, black (para Midnight Banshee),
selfc (se pone contadores a sí misma), haste, legend, token1 (deja criaturas de 1 de resistencia).
"""
import re

COMMANDER = "Auntie Ool, Cursewretch"


FORGE = "FORGE"   # coste, tipo y P/T desde core/cards_db.json (Forge); ver core/stats.py

def C(cost, t, p=0, tg=0):
    return dict(cost=cost, t=t, p=p, tg=tg)


CARDS = {
    # ---------------------------------------------------------------- precon (60 no-tierra + comandante)
    COMMANDER: C("1BRG", "C", 4, 4),
    "Archfiend of Ifnir": FORGE,
    "Carnifex Demon": FORGE,
    "Channeler Initiate": FORGE,
    "Devoted Druid": FORGE,
    "Dread Tiller": FORGE,
    "Dusk Urchins": FORGE,
    "Evolution Sage": FORGE,
    "Ferrafor, Young Yew": FORGE,
    "Glissa Sunslayer": FORGE,
    "Grave Titan": FORGE,
    "Grim Poppet": FORGE,
    "Hapatra, Vizier of Poisons": FORGE,
    "Ignoble Hierarch": FORGE,
    "Kulrath Knight": FORGE,
    "Massacre Girl, Known Killer": FORGE,
    "Midnight Banshee": FORGE,
    "Necroskitter": FORGE,
    "Oft-Nabbed Goat": FORGE,
    "Puppeteer Clique": FORGE,
    "Sinister Gnarlbark": FORGE,
    "Skinrender": FORGE,
    "Soul Snuffers": FORGE,
    "The Reaper, King No More": C("BRG", "C", 3, 3),   # {2/B}{2/R}{2/G}: se paga con colores
    "The Scorpion God": FORGE,
    "Tree of Perdition": FORGE,
    "Village Pillagers": FORGE,
    "Wickerbough Elder": FORGE,
    "Assassin's Trophy": FORGE,
    "Cathartic Pyre": FORGE,
    "Fire Covenant": FORGE,
    "Infernal Grasp": FORGE,
    "Putrefy": FORGE,
    "Terminate": FORGE,
    "Aberrant Return": FORGE,
    "Black Sun's Zenith": FORGE,
    "Burning Curiosity": FORGE,
    "Cathartic Reunion": FORGE,
    "Chain Reaction": FORGE,
    "Eventide's Shadow": FORGE,
    "Harmonize": FORGE,
    "Hoarder's Greed": FORGE,
    "Incremental Blight": FORGE,
    "Night's Whisper": FORGE,
    "Painful Truths": FORGE,
    "Persist": FORGE,
    "Arcane Signet": FORGE,
    "Chimil, the Inner Sun": FORGE,
    "Commander's Sphere": FORGE,
    "Contagion Clasp": FORGE,
    "Sol Ring": FORGE,
    "Wickersmith's Tools": FORGE,
    "Binding the Old Gods": FORGE,
    "Blowfly Infestation": FORGE,
    "Everlasting Torment": FORGE,
    "Flourishing Defenses": FORGE,
    "Grave Venerations": FORGE,
    "Lasting Tarfire": FORGE,
    "Puca's Covenant": FORGE,
    "Liliana, Death Wielder": FORGE,
    "Vraska, Betrayal's Sting": FORGE,   # {B/P}: B o 2 de vida (23/11)
    # ---------------------------------------------------------------- candidatas (guías y EDHREC)
    "Generous Patron": FORGE,
    "Dawnhand Dissident": FORGE,
    "Grim Affliction": FORGE,
    "Farseek": FORGE,
    "Rampant Growth": FORGE,
    "Nature's Lore": FORGE,
    "Obelisk Spider": FORGE,
    "Maha, Its Feathers Night": FORGE,
    "Persistent Constrictor": FORGE,
    "Nest of Scarabs": FORGE,
    "Harbinger of Night": FORGE,
    "Scuzzback Scrounger": FORGE,
    "Darkness Descends": FORGE,
    "Heroic Intervention": FORGE,
    "Swiftfoot Boots": FORGE,
    "Lightning Greaves": FORGE,
    "Ammit Eternal": FORGE,
    "Atomize": FORGE,
    "Shadow Urchin": FORGE,
    "Banewhip Punisher": FORGE,
    "Mahadi, Emporium Master": FORGE,
    "Whisper of the Dross": FORGE,
    "Skullclamp": FORGE,
    "Yawgmoth, Thran Physician": FORGE,
    "All Will Be One": FORGE,
    "Contagion Engine": FORGE,
    "Crumbling Ashes": FORGE,
    "Massacre Wurm": FORGE,
    "Diabolic Tutor": FORGE,
    "Grim Tutor": FORGE,
    "Diabolic Intent": FORGE,
    "Pollenbright Druid": FORGE,
    "Tezzeret's Gambit": C("3", "S"),          # {3}{U/P}: se paga la parte phyrexiana con 2 de vida
    "Archfiend of Sorrows": FORGE,
    "The Meathook Massacre": C("2BB", "E"),   # X fijo por el piloto (coste base BB + X)
    "Zulaport Cutthroat": FORGE,
    "Blood Artist": FORGE,
    "Bastion of Remembrance": FORGE,
    "Cauldron of Essence": FORGE,
    "Soul Immolation": FORGE,
    "Morselhoarder": FORGE,
    "High-Society Hunter": FORGE,
    "Agent Venom": FORGE,
    "Grim Haruspex": FORGE,
    "Demonic Tutor": FORGE,
    "Vampiric Tutor": FORGE,
    "Worldly Tutor": FORGE,
    "Blight Rot": FORGE,
    "Murder": FORGE,
    "Blank": C("99", "S"),   # carta muerta para la ablación
}

# Fase 4: los efectos de cada carta (roles, palabras clave, respuestas, rocas...) viven en data/efectos.yaml;
# aquí quedan coste, tipo y P/T. core/mapeo.py los vuelve a poner con las claves de siempre.
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", ".."))
from core import mapeo as _MP, stats as _ST
for _n, _v in list(CARDS.items()):
    if _v is FORGE:
        CARDS[_n] = _ST.desde_forge("blight", _n)
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
    """'3(BR)(BR)' -> (generic, [pips]); cada pip es un string de colores aceptados.
    '(BP)' es maná phyrexiano: se paga con B o con 2 de vida (lo decide Game.cost)."""
    pips = re.findall(r"\(([BRGP]+)\)", s)
    s2 = re.sub(r"\([BRGP]+\)", "", s)
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
