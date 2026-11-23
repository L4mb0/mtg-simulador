# Card database for the Gorma simulator.
# cost = (generic, colored_pips). Types: C creature, A artifact, E enchantment, S sorcery, I instant, L land.
# Tags drive the simulator's behaviour.

FORGE = "FORGE"   # coste, tipo y P/T desde core/cards_db.json (Forge); ver core/stats.py

CARDS = {
    # --- commander ---
    "Gorma, the Gullet": FORGE,
    # --- creatures ---
    "Blood Artist": FORGE,
    "Zulaport Cutthroat": FORGE,
    "Bloodghast": FORGE,
    "Butcher of Malakir": FORGE,
    "Defiling Daemogoth": FORGE,
    "Dina, Essence Brewer": FORGE,
    "Eccentric Pestfinder": FORGE,
    "Emeritus of Woe": FORGE,
    "Fanatic of Rhonas": FORGE,
    "Feral Ghoul": FORGE,
    "Gyre Sage": FORGE,
    "Haywire Mite": FORGE,
    "Jadar, Ghoulcaller of Nephalia": FORGE,
    "Jarad, Golgari Lich Lord": FORGE,
    "Jenova, Ancient Calamity": FORGE,
    "Mazirek, Kraul Death Priest": FORGE,
    "Merchant of Venom": FORGE,
    "Morbid Opportunist": FORGE,
    "Nether Traitor": FORGE,
    "Ophiomancer": FORGE,
    "Pawn of Ulamog": FORGE,
    "Pest Rescuer": FORGE,
    "Pitiless Plunderer": FORGE,
    "Priest of Forgotten Gods": FORGE,
    "Puppeteer Clique": FORGE,
    "Putrid Goblin": FORGE,
    "Rendclaw Trow": FORGE,
    "Woodfall Primus": FORGE,  # persist, but not usable as infinite loop in B3
    "Rampant Rejuvenator": FORGE,
    "Sakura-Tribe Elder": FORGE,
    "Selvala, Heart of the Wilds": FORGE,
    "Elvish Mystic": FORGE,
    "Twitching Doll": FORGE,
    "The Gitrog, Ravenous Ride": FORGE,
    "Umbral Collar Zealot": FORGE,
    "Veinwitch Coven": FORGE,
    "Viscera Seer": FORGE,
    "Wight of the Reliquary": FORGE,
    "Yahenni, Undying Partisan": FORGE,
    "Insidious Fungus": FORGE,
    "Woe Strider": FORGE,
    "Smothering Abomination": FORGE,
    "Thrashing Brontodon": FORGE,
    "Bloodflow Connoisseur": FORGE,
    "Carrion Feeder": FORGE,
    "Driver of the Dead": FORGE,
    # --- noncreature ---
    "Phyrexian Altar": FORGE,
    "Ashnod's Altar": FORGE,
    "Sol Ring": FORGE,
    "Arcane Signet": FORGE,
    "Blade of the Bloodchief": FORGE,
    "Blight Mound": FORGE,
    "Cauldron of Essence": FORGE,
    "Culling Ritual": FORGE,
    "Desperate Plea": FORGE,
    "Find // Finality": FORGE,
    "Foot Chopper": FORGE,
    "Garruk's Uprising": FORGE,
    "Greater Good": FORGE,
    "Immoral Bargain": FORGE,
    "Moldervine Reclamation": FORGE,
    "Mortality Spear": FORGE,
    "Pest Infestation": FORGE,
    "Profane Tutor": dict(cost=(1, 1), t="S"),
    "Diabolic Tutor": FORGE,
    "Toxic Deluge": FORGE,
    "Traverse the Outlands": FORGE,
    "Veil of Summer": FORGE,
    "Vicious Rivalry": FORGE,
    "Witherbloom Charm": FORGE,
    "Assassin's Trophy": FORGE,
    "Infernal Grasp": FORGE,
    "Tragic Slip": FORGE,
    "Fell": FORGE,
    "Heroic Intervention": FORGE,
    "Victimize": FORGE,
    "Skullclamp": FORGE,
    "Eldritch Evolution": FORGE,
    # --- purchase candidates (Nov 2026) ---
    "Dr. Joseph M'Benga": FORGE,
    "Vengeance Mission": FORGE,
    "Bastion of Remembrance": FORGE,
    "Poison-Tip Archer": FORGE,
    "Falkenrath Noble": FORGE,
    "Syr Konrad, the Grim": FORGE,
    "Vampire Aristocrat": FORGE,
    "Altar of Dementia": FORGE,
    "Blasting Station": FORGE,
    "Village Rites": FORGE,
    "Deadly Dispute": FORGE,
    "Khan, Vengeful Heart": FORGE,   # 5/3 (corregido 23/11)
    "Midnight Reaper": FORGE,
    "Grim Haruspex": FORGE,
    "Fecundity": FORGE,
    "Grand Nagus Zek": dict(cost=(2, 1), t="C", p=2),
    "Jadzia Dax": dict(cost=(1, 1), t="C", p=1),
    "Xenobotanist": FORGE,
    "Birds of Paradise": FORGE,
    "Golgari Charm": FORGE,
    "Tamiyo's Safekeeping": FORGE,
    "Snakeskin Veil": FORGE,
    "Diabolic Intent": FORGE,
    "Grim Tutor": FORGE,
    "Lesser Masticore": FORGE,   # 2/2 (corregido 23/11)
    "Go for the Throat": FORGE,
    "Eject the Warp Core": FORGE,
    "Feed the Swarm": FORGE,
    "Test of Courage": FORGE,
    "Tear Asunder": FORGE,
    "Wingrattle Scarecrow": FORGE,
    "Lingering Tormentor": FORGE,
    "Aerie Ouphes": FORGE,
    "Warren Soultrader": FORGE,
    "Vengeful Bloodwitch": FORGE,
    "Massacre Girl, Most Wanted": FORGE,
    "Marionette Apprentice": FORGE,
    "Dark Ritual": FORGE,
    "Culling the Weak": FORGE,
    "Persist": FORGE,
    "Dina's Guidance": FORGE,
    "Awakening Zone": FORGE,
    "Sifter of Skulls": FORGE,
    "Tendershoot Dryad": FORGE,
    "Creakwood Liege": FORGE,
    "Beast Within": FORGE,
    "Pernicious Deed": FORGE,
    "Melira, Sylvok Outcast": FORGE,
    "Thran Vigil": FORGE,
    "Mikaeus, the Unhallowed": FORGE,
    "Bloodthrone Vampire": FORGE,
    "Spawning Pit": FORGE,
    "Gravecrawler": FORGE,
    "Yawgmoth, Thran Physician": FORGE,
    "The Meathook Massacre": FORGE,
    "Sephiroth, Fabled SOLDIER": FORGE,
    "Braids, Arisen Nightmare": FORGE,
    "Mirkwood Bats": FORGE,
    "Basking Broodscale": FORGE,
    "Scurry Oak": FORGE,
    "Teacher's Pest": FORGE,
    "Reassembling Skeleton": FORGE,
    "Tenacious Dead": FORGE,
    "Grave Pact": FORGE,
    "Dictate of Erebos": FORGE,
    "Tireless Provisioner": FORGE,
    "Support Mission": FORGE,
    "Renata, Called to the Hunt": dict(cost=(2, 2), t="C", p=2),
    "Tribute to the World Tree": FORGE,
    "Beifong's Bounty Hunters": FORGE,
    "Chatterfang, Squirrel General": FORGE,
    "Cankerbloom": FORGE,
    "Demonic Tutor": FORGE,
    "Vampiric Tutor": FORGE,
    "Imperial Seal": FORGE,
    "Worldly Tutor": FORGE,
    "Chord of Calling": FORGE,   # X + GGG con convoke (engine.x_tutor_cost)
    "Finale of Devastation": FORGE,   # X X G G (engine.x_tutor_cost)
    "Fauna Shaman": FORGE,
    "Sidisi, Undead Vizier": FORGE,
    "Wishclaw Talisman": FORGE,
    "Beseech the Mirror": FORGE,
    # --- cartas de Juan agregadas el 16/11 (compras para Blor, The List, MB2) ---
    "Archdruid's Charm": FORGE,
    "Collected Company": FORGE,
    "Ravenous Chupacabra": FORGE,
    "Cast Down": FORGE,
    "Power Word Kill": FORGE,
    "Llanowar Elves": FORGE,
    "Three Visits": FORGE,
    "Cultivate": FORGE,
    "Thought Vessel": FORGE,
    "Coalition Relic": FORGE,
    # --- lista de venta (17/11) ---
    "Dread Return": FORGE,
    "Blasphemous Edict": FORGE,
    "Damnation": FORGE,
    "Ygra, Eater of All": FORGE,
    "Sylvan Library": FORGE,
    # --- mazos del arquetipo (cEDH y budget de Gorma en EDHREC, playgroup.gg; 17/11) ---
    "Walking Ballista": FORGE,
    "Witherbloom Apprentice": FORGE,
    "Chain of Smog": FORGE,
    "Carpet of Flowers": FORGE,
    "Mox Amber": FORGE,
    "Lotus Petal": FORGE,
    "Cabal Ritual": FORGE,
    "Elves of Deep Shadow": FORGE,
    "Fyndhorn Elves": FORGE,
    "Arbor Elf": FORGE,
    "Deathrite Shaman": FORGE,
    "Talisman of Resilience": FORGE,
    "Green Sun's Zenith": dict(cost=(1, 1), t="S"),
    "Allosaurus Shepherd": FORGE,
    "Defense Grid": FORGE,
    "Night's Whisper": FORGE,
    "Blank": dict(cost=(4, 0), t="S"),
}

# Fase 4: los efectos de cada carta (roles, palabras clave, respuestas, rocas...) viven en data/efectos.yaml;
# aquí quedan coste, tipo y P/T. core/mapeo.py los vuelve a poner con las claves de siempre.
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", ".."))
from core import mapeo as _MP, stats as _ST
for _n, _v in list(CARDS.items()):
    if _v is FORGE:
        CARDS[_n] = _ST.desde_forge("gorma", _n)
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
