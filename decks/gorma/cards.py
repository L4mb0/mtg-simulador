# Card database for the Gorma simulator.
# cost = (generic, colored_pips). Types: C creature, A artifact, E enchantment, S sorcery, I instant, L land.
# Tags drive the simulator's behaviour.

CARDS = {
    # --- commander ---
    "Gorma, the Gullet": dict(cost=(1, 2), t="C", p=1),
    # --- creatures ---
    "Blood Artist": dict(cost=(1, 1), t="C", p=0),
    "Zulaport Cutthroat": dict(cost=(1, 1), t="C", p=1),
    "Bloodghast": dict(cost=(0, 2), t="C", p=2),
    "Butcher of Malakir": dict(cost=(5, 2), t="C", p=5),
    "Defiling Daemogoth": dict(cost=(3, 2), t="C", p=5),
    "Dina, Essence Brewer": dict(cost=(1, 2), t="C", p=2),
    "Eccentric Pestfinder": dict(cost=(2, 2), t="C", p=5),
    "Emeritus of Woe": dict(cost=(3, 1), t="C", p=5),
    "Fanatic of Rhonas": dict(cost=(1, 1), t="C", p=1),
    "Feral Ghoul": dict(cost=(2, 1), t="C", p=2),
    "Gyre Sage": dict(cost=(1, 1), t="C", p=1),
    "Haywire Mite": dict(cost=(1, 0), t="C", p=1),
    "Jadar, Ghoulcaller of Nephalia": dict(cost=(1, 1), t="C", p=1),
    "Jarad, Golgari Lich Lord": dict(cost=(0, 4), t="C", p=2),
    "Jenova, Ancient Calamity": dict(cost=(2, 2), t="C", p=1),
    "Mazirek, Kraul Death Priest": dict(cost=(3, 2), t="C", p=2),
    "Merchant of Venom": dict(cost=(3, 1), t="C", p=1),
    "Morbid Opportunist": dict(cost=(2, 1), t="C", p=1),
    "Nether Traitor": dict(cost=(0, 2), t="C", p=1),
    "Ophiomancer": dict(cost=(2, 1), t="C", p=2),
    "Pawn of Ulamog": dict(cost=(1, 2), t="C", p=2),
    "Pest Rescuer": dict(cost=(2, 1), t="C", p=2),
    "Pitiless Plunderer": dict(cost=(3, 1), t="C", p=1),
    "Priest of Forgotten Gods": dict(cost=(1, 1), t="C", p=1),
    "Puppeteer Clique": dict(cost=(3, 2), t="C", p=3),
    "Putrid Goblin": dict(cost=(1, 1), t="C", p=2),
    "Rendclaw Trow": dict(cost=(2, 1), t="C", p=2),
    "Woodfall Primus": dict(cost=(5, 3), t="C", p=6),  # persist, but not usable as infinite loop in B3
    "Rampant Rejuvenator": dict(cost=(3, 1), t="C", p=0),
    "Sakura-Tribe Elder": dict(cost=(1, 1), t="C", p=1),
    "Selvala, Heart of the Wilds": dict(cost=(1, 2), t="C", p=2),
    "Elvish Mystic": dict(cost=(0, 1), t="C", p=1),
    "Twitching Doll": dict(cost=(1, 1), t="C", p=2),
    "The Gitrog, Ravenous Ride": dict(cost=(3, 2), t="C", p=6),
    "Umbral Collar Zealot": dict(cost=(1, 1), t="C", p=3),
    "Veinwitch Coven": dict(cost=(2, 1), t="C", p=3),
    "Viscera Seer": dict(cost=(0, 1), t="C", p=1),
    "Wight of the Reliquary": dict(cost=(0, 2), t="C", p=2),
    "Yahenni, Undying Partisan": dict(cost=(2, 1), t="C", p=2),
    "Insidious Fungus": dict(cost=(0, 1), t="C", p=1),
    "Woe Strider": dict(cost=(2, 1), t="C", p=3),
    "Smothering Abomination": dict(cost=(2, 2), t="C", p=4),
    "Thrashing Brontodon": dict(cost=(1, 2), t="C", p=3),
    "Bloodflow Connoisseur": dict(cost=(2, 1), t="C", p=1),
    "Carrion Feeder": dict(cost=(0, 1), t="C", p=1),
    "Driver of the Dead": dict(cost=(3, 1), t="C", p=3),
    # --- noncreature ---
    "Phyrexian Altar": dict(cost=(3, 0), t="A"),
    "Ashnod's Altar": dict(cost=(3, 0), t="A"),
    "Sol Ring": dict(cost=(1, 0), t="A"),
    "Arcane Signet": dict(cost=(2, 0), t="A"),
    "Blade of the Bloodchief": dict(cost=(1, 0), t="A"),
    "Blight Mound": dict(cost=(2, 1), t="E"),
    "Cauldron of Essence": dict(cost=(1, 2), t="A"),
    "Culling Ritual": dict(cost=(2, 2), t="S"),
    "Desperate Plea": dict(cost=(1, 1), t="S"),
    "Find // Finality": dict(cost=(0, 2), t="S"),
    "Foot Chopper": dict(cost=(1, 1), t="A"),
    "Garruk's Uprising": dict(cost=(2, 1), t="E"),
    "Greater Good": dict(cost=(2, 2), t="E"),
    "Immoral Bargain": dict(cost=(1, 2), t="S"),
    "Moldervine Reclamation": dict(cost=(3, 2), t="E"),
    "Mortality Spear": dict(cost=(2, 2), t="I"),
    "Pest Infestation": dict(cost=(0, 1), t="S"),
    "Profane Tutor": dict(cost=(1, 1), t="S"),
    "Diabolic Tutor": dict(cost=(2, 2), t="S"),
    "Toxic Deluge": dict(cost=(2, 1), t="S"),
    "Traverse the Outlands": dict(cost=(4, 1), t="S"),
    "Veil of Summer": dict(cost=(0, 1), t="I"),
    "Vicious Rivalry": dict(cost=(2, 2), t="S"),
    "Witherbloom Charm": dict(cost=(0, 2), t="I"),
    "Assassin's Trophy": dict(cost=(0, 2), t="I"),
    "Infernal Grasp": dict(cost=(1, 1), t="I"),
    "Tragic Slip": dict(cost=(0, 1), t="I"),
    "Fell": dict(cost=(1, 1), t="S"),
    "Heroic Intervention": dict(cost=(1, 1), t="I"),
    "Victimize": dict(cost=(2, 1), t="S"),
    "Skullclamp": dict(cost=(1, 0), t="A"),
    "Eldritch Evolution": dict(cost=(1, 2), t="S"),
    # --- purchase candidates (Nov 2026) ---
    "Dr. Joseph M'Benga": dict(cost=(2, 2), t="C", p=3),
    "Vengeance Mission": dict(cost=(2, 1), t="E"),
    "Bastion of Remembrance": dict(cost=(2, 1), t="E"),
    "Poison-Tip Archer": dict(cost=(2, 2), t="C", p=2),
    "Falkenrath Noble": dict(cost=(3, 1), t="C", p=2),
    "Syr Konrad, the Grim": dict(cost=(3, 2), t="C", p=5),
    "Vampire Aristocrat": dict(cost=(2, 1), t="C", p=2),
    "Altar of Dementia": dict(cost=(2, 0), t="A"),
    "Blasting Station": dict(cost=(3, 0), t="A"),
    "Village Rites": dict(cost=(0, 1), t="I"),
    "Deadly Dispute": dict(cost=(1, 1), t="I"),
    "Khan, Vengeful Heart": dict(cost=(2, 2), t="C", p=5),   # 5/3 (corregido 23/11)
    "Midnight Reaper": dict(cost=(2, 1), t="C", p=3),
    "Grim Haruspex": dict(cost=(2, 1), t="C", p=3),
    "Fecundity": dict(cost=(2, 1), t="E"),
    "Grand Nagus Zek": dict(cost=(2, 1), t="C", p=2),
    "Jadzia Dax": dict(cost=(1, 1), t="C", p=1),
    "Xenobotanist": dict(cost=(1, 1), t="C", p=1),
    "Birds of Paradise": dict(cost=(0, 1), t="C", p=0),
    "Golgari Charm": dict(cost=(0, 2), t="I"),
    "Tamiyo's Safekeeping": dict(cost=(0, 1), t="I"),
    "Snakeskin Veil": dict(cost=(0, 1), t="I"),
    "Diabolic Intent": dict(cost=(1, 1), t="S"),
    "Grim Tutor": dict(cost=(1, 2), t="S"),
    "Lesser Masticore": dict(cost=(2, 0), t="C", p=2),   # 2/2 (corregido 23/11)
    "Go for the Throat": dict(cost=(1, 1), t="I"),
    "Eject the Warp Core": dict(cost=(1, 1), t="I"),
    "Feed the Swarm": dict(cost=(1, 1), t="S"),
    "Test of Courage": dict(cost=(0, 1), t="I"),
    "Tear Asunder": dict(cost=(1, 1), t="I"),
    "Wingrattle Scarecrow": dict(cost=(3, 0), t="C", p=2),
    "Lingering Tormentor": dict(cost=(3, 1), t="C", p=2),
    "Aerie Ouphes": dict(cost=(4, 1), t="C", p=3),
    "Warren Soultrader": dict(cost=(2, 1), t="C", p=3),
    "Vengeful Bloodwitch": dict(cost=(1, 1), t="C", p=1),
    "Massacre Girl, Most Wanted": dict(cost=(4, 1), t="C", p=4),
    "Marionette Apprentice": dict(cost=(1, 1), t="C", p=1),
    "Dark Ritual": dict(cost=(0, 1), t="I"),
    "Culling the Weak": dict(cost=(0, 1), t="I"),
    "Persist": dict(cost=(1, 1), t="S"),
    "Dina's Guidance": dict(cost=(1, 2), t="I"),
    "Awakening Zone": dict(cost=(2, 1), t="E"),
    "Sifter of Skulls": dict(cost=(3, 1), t="C", p=4),
    "Tendershoot Dryad": dict(cost=(4, 1), t="C", p=2),
    "Creakwood Liege": dict(cost=(1, 3), t="C", p=2),
    "Beast Within": dict(cost=(2, 1), t="I"),
    "Pernicious Deed": dict(cost=(1, 2), t="E"),
    "Melira, Sylvok Outcast": dict(cost=(1, 1), t="C", p=2),
    "Thran Vigil": dict(cost=(1, 1), t="E"),
    "Mikaeus, the Unhallowed": dict(cost=(3, 3), t="C", p=5),
    "Bloodthrone Vampire": dict(cost=(1, 1), t="C", p=1),
    "Spawning Pit": dict(cost=(2, 0), t="A"),
    "Gravecrawler": dict(cost=(0, 1), t="C", p=2),
    "Yawgmoth, Thran Physician": dict(cost=(2, 2), t="C", p=2),
    "The Meathook Massacre": dict(cost=(0, 2), t="E"),
    "Sephiroth, Fabled SOLDIER": dict(cost=(2, 1), t="C", p=3),
    "Braids, Arisen Nightmare": dict(cost=(1, 2), t="C", p=3),
    "Mirkwood Bats": dict(cost=(3, 1), t="C", p=2),
    "Basking Broodscale": dict(cost=(1, 1), t="C", p=2),
    "Scurry Oak": dict(cost=(2, 1), t="C", p=1),
    "Teacher's Pest": dict(cost=(0, 2), t="C", p=1),
    "Reassembling Skeleton": dict(cost=(1, 1), t="C", p=1),
    "Tenacious Dead": dict(cost=(0, 1), t="C", p=1),
    "Grave Pact": dict(cost=(1, 3), t="E"),
    "Dictate of Erebos": dict(cost=(3, 2), t="E"),
    "Tireless Provisioner": dict(cost=(2, 1), t="C", p=3),
    "Support Mission": dict(cost=(2, 1), t="E"),
    "Renata, Called to the Hunt": dict(cost=(2, 2), t="C", p=2),
    "Tribute to the World Tree": dict(cost=(0, 3), t="E"),
    "Beifong's Bounty Hunters": dict(cost=(2, 2), t="C", p=4),
    "Chatterfang, Squirrel General": dict(cost=(2, 1), t="C", p=3),
    "Cankerbloom": dict(cost=(1, 1), t="C", p=3),
    "Demonic Tutor": dict(cost=(1, 1), t="S"),
    "Vampiric Tutor": dict(cost=(0, 1), t="I"),
    "Imperial Seal": dict(cost=(0, 1), t="S"),
    "Worldly Tutor": dict(cost=(0, 1), t="I"),
    "Chord of Calling": dict(cost=(0, 3), t="I"),   # X + GGG con convoke (engine.x_tutor_cost)
    "Finale of Devastation": dict(cost=(0, 2), t="S"),   # X X G G (engine.x_tutor_cost)
    "Fauna Shaman": dict(cost=(1, 1), t="C", p=2),
    "Sidisi, Undead Vizier": dict(cost=(3, 2), t="C", p=4),
    "Wishclaw Talisman": dict(cost=(1, 1), t="A"),
    "Beseech the Mirror": dict(cost=(1, 3), t="S"),
    # --- cartas de Juan agregadas el 16/11 (compras para Blor, The List, MB2) ---
    "Archdruid's Charm": dict(cost=(0, 3), t="I"),
    "Collected Company": dict(cost=(3, 1), t="I"),
    "Ravenous Chupacabra": dict(cost=(2, 2), t="C", p=2),
    "Cast Down": dict(cost=(1, 1), t="I"),
    "Power Word Kill": dict(cost=(1, 1), t="I"),
    "Llanowar Elves": dict(cost=(0, 1), t="C", p=1),
    "Three Visits": dict(cost=(1, 1), t="S"),
    "Cultivate": dict(cost=(2, 1), t="S"),
    "Thought Vessel": dict(cost=(2, 0), t="A"),
    "Coalition Relic": dict(cost=(3, 0), t="A"),
    # --- lista de venta (17/11) ---
    "Dread Return": dict(cost=(2, 2), t="S"),
    "Blasphemous Edict": dict(cost=(3, 2), t="S"),
    "Damnation": dict(cost=(2, 2), t="S"),
    "Ygra, Eater of All": dict(cost=(3, 2), t="C", p=6),
    "Sylvan Library": dict(cost=(1, 1), t="E"),
    # --- mazos del arquetipo (cEDH y budget de Gorma en EDHREC, playgroup.gg; 17/11) ---
    "Walking Ballista": dict(cost=(0, 0), t="C", p=0),
    "Witherbloom Apprentice": dict(cost=(0, 2), t="C", p=2),
    "Chain of Smog": dict(cost=(1, 1), t="S"),
    "Carpet of Flowers": dict(cost=(0, 1), t="E"),
    "Mox Amber": dict(cost=(0, 0), t="A"),
    "Lotus Petal": dict(cost=(0, 0), t="A"),
    "Cabal Ritual": dict(cost=(1, 1), t="I"),
    "Elves of Deep Shadow": dict(cost=(0, 1), t="C", p=1),
    "Fyndhorn Elves": dict(cost=(0, 1), t="C", p=1),
    "Arbor Elf": dict(cost=(0, 1), t="C", p=1),
    "Deathrite Shaman": dict(cost=(0, 1), t="C", p=1),
    "Talisman of Resilience": dict(cost=(2, 0), t="A"),
    "Green Sun's Zenith": dict(cost=(1, 1), t="S"),
    "Allosaurus Shepherd": dict(cost=(0, 1), t="C", p=1),
    "Defense Grid": dict(cost=(2, 0), t="A"),
    "Night's Whisper": dict(cost=(1, 1), t="S"),
    "Blank": dict(cost=(4, 0), t="S"),
}

# Fase 4: los efectos de cada carta (roles, palabras clave, respuestas, rocas...) viven en data/efectos.yaml;
# aquí quedan coste, tipo y P/T. core/mapeo.py los vuelve a poner con las claves de siempre.
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", ".."))
from core import mapeo as _MP
for _n in list(CARDS):
    CARDS[_n] = _MP.importar("gorma", _n, CARDS[_n])

# Lands: name -> (tapped_mode, colored, special)
LANDS = {
    "Forest": dict(mode="U", col=True, basic=True, types={"Forest"}),
    "Swamp": dict(mode="U", col=True, basic=True, types={"Swamp"}),
    "Bojuka Bog": dict(mode="T", col=True),
    "Command Tower": dict(mode="U", col=True),
    "Exotic Orchard": dict(mode="U", col=True),
    "Fabled Passage": dict(mode="fabled", col=True),
    "Terramorphic Expanse": dict(mode="fetch", col=True),
    "Festering Thicket": dict(mode="T", col=True, types={"Swamp", "Forest"}),
    "Haunted Mire": dict(mode="T", col=True, types={"Swamp", "Forest"}),
    "High Market": dict(mode="U", col=False),
    "Llanowar Wastes": dict(mode="U", col=True),
    "Necroblossom Snarl": dict(mode="snarl", col=True),
    "Temple of Malady": dict(mode="T", col=True),
    "Turbulent Fen": dict(mode="oppl8", col=True, types={"Swamp", "Forest"}),
    "Twilight Mire": dict(mode="U", col=True),
    "Vernal Fen": dict(mode="basics2", col=True, types={"Swamp", "Forest"}),
    "Viridescent Bog": dict(mode="U", col=True),
    "Woodland Cemetery": dict(mode="typed", col=True),
    "Deathcap Glade": dict(mode="deathcap", col=True),
    "Overgrown Tomb": dict(mode="U", col=True, types={"Swamp", "Forest"}),
    "Phyrexian Tower": dict(mode="U", col=True),
}

COMMANDER = "Gorma, the Gullet"

# Target list (when Insidious Fungus and Rendclaw Trow arrive)
NONLANDS_TARGET = [
    "Blood Artist", "Bloodghast", "Butcher of Malakir", "Defiling Daemogoth", "Dina, Essence Brewer",
    "Eccentric Pestfinder", "Elvish Mystic", "Emeritus of Woe", "Fanatic of Rhonas", "Feral Ghoul", "Gyre Sage",
    "Haywire Mite", "Insidious Fungus", "Jadar, Ghoulcaller of Nephalia", "Jarad, Golgari Lich Lord",
    "Jenova, Ancient Calamity", "Mazirek, Kraul Death Priest", "Merchant of Venom", "Morbid Opportunist",
    "Nether Traitor", "Ophiomancer", "Pawn of Ulamog", "Pest Rescuer", "Pitiless Plunderer",
    "Priest of Forgotten Gods", "Puppeteer Clique", "Putrid Goblin", "Rampant Rejuvenator", "Rendclaw Trow",
    "Sakura-Tribe Elder", "Selvala, Heart of the Wilds", "The Gitrog, Ravenous Ride", "Umbral Collar Zealot",
    "Veinwitch Coven", "Viscera Seer", "Wight of the Reliquary", "Woodfall Primus", "Yahenni, Undying Partisan",
    "Zulaport Cutthroat",
    "Arcane Signet", "Blight Mound", "Cauldron of Essence", "Culling Ritual", "Desperate Plea", "Diabolic Tutor",
    "Find // Finality", "Foot Chopper", "Garruk's Uprising", "Greater Good", "Immoral Bargain",
    "Moldervine Reclamation", "Mortality Spear", "Pest Infestation", "Phyrexian Altar", "Profane Tutor",
    "Sol Ring", "Toxic Deluge", "Traverse the Outlands", "Veil of Summer", "Vicious Rivalry", "Witherbloom Charm",
]
LANDS_LIST = (["Forest"] * 11 + ["Swamp"] * 11 + [
    "Bojuka Bog", "Command Tower", "Exotic Orchard", "Fabled Passage", "Festering Thicket", "Haunted Mire",
    "High Market", "Llanowar Wastes", "Necroblossom Snarl", "Temple of Malady", "Terramorphic Expanse",
    "Turbulent Fen", "Twilight Mire", "Vernal Fen", "Viridescent Bog", "Woodland Cemetery"])

assert len(NONLANDS_TARGET) == 61, len(NONLANDS_TARGET)
assert len(LANDS_LIST) == 38


def target_deck():
    return NONLANDS_TARGET + LANDS_LIST


def physical_deck():
    d = list(NONLANDS_TARGET)
    d[d.index("Insidious Fungus")] = "Twitching Doll"
    d[d.index("Rendclaw Trow")] = "Blade of the Bloodchief"
    return d + LANDS_LIST


def swap(deck, out, inn):
    d = list(deck)
    d[d.index(out)] = inn
    return d

# criaturas y hechizos verdes (para Green Sun's Zenith y Allosaurus Shepherd)
GREEN = {"Gorma, the Gullet", "Fecundity", "Aerie Ouphes", "Fauna Shaman", "Insidious Fungus", "Fanatic of Rhonas", "Sakura-Tribe Elder",
         "Elvish Mystic", "Gyre Sage", "Selvala, Heart of the Wilds", "Rampant Rejuvenator", "Witherbloom Apprentice",
         "Allosaurus Shepherd", "Llanowar Elves", "Fyndhorn Elves", "Arbor Elf", "Elves of Deep Shadow", "Deathrite Shaman",
         "Birds of Paradise", "Jadar, Ghoulcaller of Nephalia", "Dina, Essence Brewer", "Pest Rescuer", "Morbid Opportunist",
         "Jarad, Golgari Lich Lord", "The Gitrog, Ravenous Ride", "Mazirek, Kraul Death Priest", "Defiling Daemogoth",
         "Veinwitch Coven", "Eccentric Pestfinder", "Yahenni, Undying Partisan", "Ygra, Eater of All",
         "Archdruid's Charm", "Chord of Calling", "Finale of Devastation", "Green Sun's Zenith", "Collected Company",
         "Sylvan Library", "Carpet of Flowers", "Moldervine Reclamation", "Garruk's Uprising", "Greater Good",
         "Witherbloom Charm", "Assassin's Trophy", "Veil of Summer", "Three Visits", "Cultivate", "Traverse the Outlands",
         "Find // Finality", "Pest Infestation", "Blight Mound"}
LEGENDS = {"Gorma, the Gullet", "Jarad, Golgari Lich Lord", "Mazirek, Kraul Death Priest", "Yahenni, Undying Partisan",
           "Dina, Essence Brewer", "Selvala, Heart of the Wilds", "The Gitrog, Ravenous Ride", "Jenova, Ancient Calamity",
           "Jadar, Ghoulcaller of Nephalia", "Ygra, Eater of All", "Yawgmoth, Thran Physician"}
