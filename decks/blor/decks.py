"""Deck lists: EDHREC average deck (13/11/2026) and one fixed package per playstyle on a shared core."""
from cards import C

LANDS = ["Forest"] * 27 + ["Boseiju, Who Endures", "Nykthos, Shrine to Nyx", "Reliquary Tower", "Rogue's Passage",
                           "War Room", "Witch's Clinic", "Yavimaya, Cradle of Growth"]

EDHREC = LANDS + [
    "Birds of Paradise", "Bugenhagen, Wise Elder", "Delighted Halfling", "Elvish Mystic", "Eternal Witness",
    "Fanatic of Rhonas", "Forgotten Ancient", "Frenzied Baloth", "Fyndhorn Elves", "Llanowar Elves",
    "Sakura-Tribe Elder", "Silent Arbiter", "Spore Frog", "Tajuru Preserver", "Toski, Bearer of Secrets",
    "Archdruid's Charm", "Beast Within", "Berserk", "Fog", "Gift of the Viper", "Hunter's Insight", "Krosan Grip",
    "Nature's Claim", "Ram Through", "Return of the Wildspeaker",
    "Bridgeworks Battle", "Cultivate", "Epic Fight", "Harmonize", "Kodama's Reach", "Nature's Lore",
    "Rampant Growth", "Rishkar's Expertise", "Three Visits",
    "Arcane Signet", "Basilisk Collar", "Blackblade Reforged", "Buster Sword", "Commander's Plate",
    "Emerald Medallion", "Fireshrieker", "Genji Glove", "Inquisitor's Flail", "Necklace of Girion",
    "Pariah's Shield", "Power Fist", "Shadowspear", "Sol Ring", "Staff of Titania", "The Earth Crystal",
    "Ancestral Mask", "Bear Umbra", "Blanchwood Armor", "Colossification", "Hydra's Growth", "Keen Sense",
    "Kenrith's Transformation", "Level Up", "Lion Umbra", "Snake Umbra", "Strong Back",
    "Blank",          # Super State: not found in Gatherer, left as an empty slot
    "Unnatural Growth", "Utopia Sprawl", "Wild Growth",
]

CORE = LANDS + [
    # ramp (16)
    "Birds of Paradise", "Delighted Halfling", "Elvish Mystic", "Fanatic of Rhonas", "Fyndhorn Elves",
    "Llanowar Elves", "Sakura-Tribe Elder", "Sol Ring", "Arcane Signet", "Wild Growth", "Utopia Sprawl",
    "Nature's Lore", "Three Visits", "Rampant Growth", "Cultivate", "Kodama's Reach",
    # interaction (8)
    "Archdruid's Charm", "Beast Within", "Krosan Grip", "Nature's Claim", "Ram Through", "Heroic Intervention",
    "Bridgeworks Battle", "Kenrith's Transformation",
    # cards (4)
    "Rishkar's Expertise", "Return of the Wildspeaker", "Harmonize", "Hunter's Insight",
    # defense (3)
    "Silent Arbiter", "Tajuru Preserver", "Spore Frog",
]

STYLES = {
    "Auras + enchantress": [
        "Blanchwood Armor", "Strong Back", "Level Up", "Ancestral Mask", "Bear Umbra", "Lion Umbra", "Snake Umbra",
        "Spider Umbra", "Rancor", "Hydra's Growth", "Colossification", "Indomitable Might", "Keen Sense",
        "Sixth Sense", "Crystalline Armor", "Curse of Predation", "Unnatural Growth", "Hardened Scales",
        "Eidolon of Blossoms", "Setessan Champion", "Verduran Enchantress", "Argothian Enchantress",
        "Enchantress's Presence", "Sanctum Weaver", "Pia, Aether Ascetic", "Season of Growth", "Garruk's Uprising",
        "Colossal Majesty", "Berserk", "Gift of the Viper", "Eternal Witness", "Fog", "Moment's Peace",
        "Toski, Bearer of Secrets"],
    "Equipos": [
        "Blackblade Reforged", "Staff of Titania", "Commander's Plate", "Shadowspear", "Basilisk Collar",
        "Fireshrieker", "Leyline Axe", "Genji Glove", "Inquisitor's Flail", "Power Fist", "Buster Sword",
        "Bone Sabres", "Colossus Hammer", "Sword of Feast and Famine", "Sword of Fire and Ice",
        "Sword of Truth and Justice", "Sword of Hearth and Home", "Sword of the Animist", "Pariah's Shield",
        "Mask of Memory", "Umezawa's Jitte", "Loxodon Warhammer", "Thran Power Suit", "Swiftfoot Boots",
        "Lightning Greaves", "Assault Suit", "Belt of Giant Strength", "Strong Back", "Colossal Majesty",
        "Toski, Bearer of Secrets", "Ohran Frostfang", "Berserk", "Fog", "Eternal Witness"],
    "Mixto (auras + equipos)": [
        "Blanchwood Armor", "Strong Back", "Level Up", "Ancestral Mask", "Bear Umbra", "Lion Umbra", "Snake Umbra",
        "Hydra's Growth", "Colossification", "Keen Sense", "Unnatural Growth", "Blackblade Reforged",
        "Staff of Titania", "Commander's Plate", "Shadowspear", "Basilisk Collar", "Fireshrieker", "Genji Glove",
        "Inquisitor's Flail", "Power Fist", "Buster Sword", "Pariah's Shield", "Necklace of Girion",
        "Emerald Medallion", "The Earth Crystal", "Berserk", "Gift of the Viper", "Epic Fight",
        "Toski, Bearer of Secrets", "Forgotten Ancient", "Frenzied Baloth", "Bugenhagen, Wise Elder", "Fog",
        "Eternal Witness"],
    "Contadores +1/+1": [
        "Hydra's Growth", "Level Up", "Hardened Scales", "Branching Evolution", "The Earth Crystal",
        "Kami of Whispered Hopes", "Forgotten Ancient", "Necklace of Girion", "Power Fist", "Bone Sabres",
        "Sword of Truth and Justice", "Curse of Predation", "Gift of the Viper", "Snakeskin Veil", "Stony Strength",
        "Inscription of Abundance", "Tarrian's Soulcleaver", "Evolution Sage", "Blanchwood Armor", "Strong Back",
        "Lion Umbra", "Bear Umbra", "Snake Umbra", "Blackblade Reforged", "Shadowspear", "Fireshrieker",
        "Colossal Majesty", "Toski, Bearer of Secrets", "Berserk", "Unnatural Growth", "Fog", "Eternal Witness",
        "Keen Sense", "Inquisitor's Flail"],
    "Trucos (pump instantáneo)": [
        "Berserk", "Become Immense", "Primal Bellow", "Giant Growth", "Invigorate", "Might of Old Krosa",
        "Tyvar's Stand", "Overprotect", "Vines of Vastwood", "Blossoming Defense", "Snakeskin Veil", "Epic Fight",
        "Primal Might", "Inscription of Abundance", "Gift of the Viper", "Stony Strength", "Season of Growth",
        "Toski, Bearer of Secrets", "Ohran Frostfang", "Keen Sense", "Snake Umbra", "Sixth Sense", "Shadowspear",
        "Fireshrieker", "Inquisitor's Flail", "Rancor", "Blanchwood Armor", "Colossal Majesty", "Fog",
        "Moment's Peace", "Eternal Witness", "Garruk's Uprising", "Leyline Axe", "Unnatural Growth"],
    "Veneno (infect)": [
        "Grafted Exoskeleton", "Triumph of the Hordes", "Fynn, the Fangbearer", "Basilisk Collar",
        "Gift of the Viper", "Ohran Frostfang", "Sword of Truth and Justice", "Evolution Sage", "Fireshrieker",
        "Leyline Axe", "Genji Glove", "Inquisitor's Flail", "Blanchwood Armor", "Strong Back", "Bear Umbra",
        "Lion Umbra", "Snake Umbra", "Hydra's Growth", "Level Up", "Blackblade Reforged", "Staff of Titania",
        "Berserk", "Keen Sense", "Toski, Bearer of Secrets", "Colossal Majesty", "Unnatural Growth", "Fog",
        "Eternal Witness", "Power Fist", "Commander's Plate", "Swiftfoot Boots", "Shadowspear", "Hardened Scales",
        "Snakeskin Veil"],
    "Doble golpe y duplicar": [
        "Fireshrieker", "Leyline Axe", "Genji Glove", "Inquisitor's Flail", "Berserk", "Unnatural Growth",
        "Epic Fight", "Blanchwood Armor", "Crystalline Armor", "Blackblade Reforged", "Staff of Titania",
        "Strong Back", "Bear Umbra", "Lion Umbra", "Snake Umbra", "Ancestral Mask", "Colossification",
        "Colossus Hammer", "Hydra's Growth", "Level Up", "Swiftfoot Boots", "Lightning Greaves",
        "Commander's Plate", "Shadowspear", "Basilisk Collar", "Pariah's Shield", "Keen Sense",
        "Toski, Bearer of Secrets", "Colossal Majesty", "Fog", "Eternal Witness", "Rancor", "Indomitable Might",
        "Thran Power Suit"],
}

DECKS = {"Promedio EDHREC": EDHREC}
for k, v in STYLES.items():
    DECKS[k] = CORE + v


def check():
    for k, d in DECKS.items():
        bad = [c for c in d if c not in C]
        dup = {c for c in d if d.count(c) > 1 and c != "Forest"}
        print(f"{k:28s} {len(d):3d} cartas", "FALTAN:" if bad else "", bad, "DUP:" if dup else "", dup or "")


if __name__ == "__main__":
    check()

def swap_many(deck, outs, ins):
    d = list(deck)
    for o, i in zip(outs, ins):
        d[d.index(o)] = i
    return d


R1_OUT = ["Pariah's Shield", "Frenzied Baloth", "Epic Fight", "Gift of the Viper", "Shadowspear",
          "Emerald Medallion", "Eternal Witness", "Fog"]
R1_IN = ["Bone Sabres", "Crystalline Armor", "Belt of Giant Strength", "Indomitable Might", "Leyline Axe",
         "Sword of Truth and Justice", "Sylvan Library", "Sword of Fire and Ice"]
DECKS["Ruta 1 (8 cambios)"] = swap_many(DECKS["Mixto (auras + equipos)"], R1_OUT, R1_IN)

BLOR_10 = swap_many(DECKS["Ruta 1 (8 cambios)"], ["Colossification"], ["Overgrowth"])
DECKS["Blor 1.0"] = BLOR_10

ECO_OUT = ["Nykthos, Shrine to Nyx", "Boseiju, Who Endures", "Yavimaya, Cradle of Growth", "Buster Sword",
           "Commander's Plate", "Sword of Truth and Justice", "Sylvan Library", "Delighted Halfling",
           "Sword of Fire and Ice", "The Earth Crystal", "Bear Umbra"]
ECO_IN = ["Forest", "Forest", "Forest", "Sixth Sense", "Rancor", "Colossus Hammer", "Skyshroud Claim",
          "Drover of the Mighty", "Curse of Predation", "Hardened Scales", "Spider Umbra"]
DECKS["Blor 1.0 económica"] = swap_many(BLOR_10, ECO_OUT, ECO_IN)

RAP_OUT = ["Ram Through", "Bridgeworks Battle", "Kenrith's Transformation", "Spore Frog", "Silent Arbiter",
           "The Earth Crystal", "Toski, Bearer of Secrets"]
RAP_IN = ["Arbor Elf", "Colossus Hammer", "Rancor", "Sixth Sense", "Explore", "Mask of Memory", "Thought Vessel"]
DECKS["Rápida B2"] = swap_many(BLOR_10, RAP_OUT, RAP_IN)
RAP3_OUT = ["Sword of Fire and Ice", "Forest", "Sakura-Tribe Elder"]
RAP3_IN = ["The One Ring", "Ancient Tomb", "Chrome Mox"]
DECKS["Rápida B3"] = swap_many(DECKS["Rápida B2"], RAP3_OUT, RAP3_IN)

RAPE_OUT = ["Ram Through", "Bridgeworks Battle", "Kenrith's Transformation", "Spore Frog", "Silent Arbiter",
            "Hardened Scales", "Toski, Bearer of Secrets"]
RAPE_IN = ["Arbor Elf", "Explore", "Mask of Memory", "Thought Vessel", "Emerald Medallion", "Avarice Amulet",
           "Garruk, Primal Hunter"]
DECKS["Rápida económica"] = swap_many(DECKS["Blor 1.0 económica"], RAPE_OUT, RAPE_IN)

DEF_OUT = ["Rancor", "Sixth Sense", "Thought Vessel"]
DEF_IN = ["Shadowspear", "Long-Lost Lances", "Moment's Peace"]
DECKS["Rápida defensiva"] = swap_many(DECKS["Rápida B2"], DEF_OUT, DEF_IN)

V11_OUT = ["Sixth Sense", "Thought Vessel", "Explore", "Mask of Memory", "Arbor Elf"]
V11_IN = ["Short Bow", "Long-Lost Lances", "Avarice Amulet", "Tarrian's Soulcleaver", "Silent Arbiter"]
DECKS["Blor 1.1 (vigilancia)"] = swap_many(DECKS["Rápida B2"], V11_OUT, V11_IN)
DECKS["Blor 1.1 económica"] = swap_many(DECKS["Rápida económica"], V11_OUT,
                                        ["Short Bow", "Long-Lost Lances", "Moment's Peace", "Tarrian's Soulcleaver", "Silent Arbiter"])

# 15/11 (Juan aprobó): Pariah's Shield por Krosan Grip y Allosaurus Shepherd por Colossus Hammer
DECKS["Blor 1.2"] = swap_many(DECKS["Blor 1.1 (vigilancia)"], ["Forest"], ["Dryad Arbor"])
DECKS["Blor 1.3"] = swap_many(DECKS["Blor 1.2"], ["Krosan Grip", "Colossus Hammer"], ["Pariah's Shield", "Allosaurus Shepherd"])

# 15/11 (Juan aprobó): Talon Gates of Madara por un Forest
DECKS["Blor 1.4"] = swap_many(DECKS["Blor 1.3"], ["Forest"], ["Talon Gates of Madara"])

# 15/11 (Juan aprobó): Primal Bellow por Tajuru Preserver (Tajuru al sideboard para mesas de edictos)
DECKS["Blor 1.5"] = swap_many(DECKS["Blor 1.4"], ["Tajuru Preserver"], ["Primal Bellow"])

# 15/11 (Juan aprobó): Ohran Frostfang (suya) por Sword of Truth and Justice
DECKS["Blor 1.6"] = swap_many(DECKS["Blor 1.5"], ["Sword of Truth and Justice"], ["Ohran Frostfang"])

# 24/11 (Juan aprobó): Lotus Bloom (suya) por Snake Umbra. Orientada a B2, sin Game Changers
DECKS["Blor 1.7"] = swap_many(DECKS["Blor 1.6"], ["Snake Umbra"], ["Lotus Bloom"])

# 25/11 (Juan aprobó): candidatas de EDHREC + paquete anterior. +5,0 en B2 y +3,8 en B3 (15.000 partidas, semillas nuevas)
DECKS["Blor 1.8"] = swap_many(DECKS["Blor 1.7"],
    ["Sword of Fire and Ice", "Heroic Intervention", "Forest", "Long-Lost Lances", "Inquisitor's Flail",
     "Archdruid's Charm", "Allosaurus Shepherd"],
    ["Sword of Truth and Justice", "Skyshroud Claim", "Castle Garenbrig", "Super State", "Court of Garenbrig",
     "Obscuring Haze", "Thickest in the Thicket"])

# 25/11: versión física provisional (Juan): solo cartas que Juan tiene libres hoy (no las de otros mazos).
# Parte de la 1.8; lo que falta se cubre con cartas propias (sueltas, banca, ManaBox y bulk) y Forests.
BLOR_PROPIAS_18 = ["Arcane Signet", "Cultivate", "Delighted Halfling", "Elvish Mystic", "Llanowar Elves", "Overgrowth",
    "Sakura-Tribe Elder", "Sol Ring", "Three Visits", "Wild Growth", "Rancor", "Lotus Bloom", "Blackblade Reforged",
    "Genji Glove", "Leyline Axe", "Ohran Frostfang", "Unnatural Growth", "Pariah's Shield", "Silent Arbiter",
    "Tarrian's Soulcleaver", "Return of the Wildspeaker", "Sylvan Library", "Sword of Truth and Justice",
    "Blanchwood Armor"]
BLOR_RELLENO_FISICA = [
    # maná (10)
    "Elvish Rejuvenator", "Fertilid", "Far Wanderings", "Drover of the Mighty", "Elfhame Druid", "Gemhide Sliver",
    "Goobbue Gardener", "Mind Stone", "Thought Vessel", "Coalition Relic",
    # voltron (14)
    "Gaea's Embrace", "Silken Strength", "Cultist's Staff", "Spider-Suit", "Colossus Hammer", "Gavel of the Righteous",
    "Conqueror's Flail", "Shadowspear", "Swiftfoot Boots", "The Earth Crystal", "World War Hulk", "Long-Lost Lances",
    "Heroic Intervention", "Skullclamp",
    # contadores y trucos (8)
    "Efflorescence", "Stony Strength", "Satyr Grovedancer", "Pollenbright Druid", "Wild Onslaught",
    "Implement of Ferocity", "Bestow Greatness", "Mammoth Growth",
    # respuestas (5)
    "Thrashing Brontodon", "Prey Upon", "Rabid Bite", "Run Over", "Root Snare",
    # robo y cuerpos (4)
    "Adventurous Impulse", "Tanglespan Lookout", "Zopandrel, Hunger Dominus", "Hexhaven Invigorator",
]
DECKS["Blor física 0"] = BLOR_PROPIAS_18 + BLOR_RELLENO_FISICA + ["Forest"] * 34
assert len(DECKS["Blor física 0"]) == 99, len(DECKS["Blor física 0"])
# Primera limpieza (25/11): +2,2 ±0,5 en B2 y +0,4 en B3 sobre la física 0 (10.000 partidas, semillas nuevas)
DECKS["Blor física"] = swap_many(DECKS["Blor física 0"],
    ["Root Snare", "Cultist's Staff", "Swiftfoot Boots", "Spider-Suit"],
    ["Flourishing Strike", "Toski, Bearer of Secrets", "Moss Diamond", "Oasis Gardener"])

# 25/11 (Juan): Far Wanderings ya no está; tierras libres: 17 Forest, Command Tower, Path of Ancestry, Study Hall y
# Access Tunnel (21). Los 14 cupos que quedan van a las cartas propias que sobraban. Worldslayer queda fuera
# (destruye todas las tierras rivales: destrucción masiva de tierras, fuera de B2/B3).
BLOR_RELLENO_2 = ["Root Snare", "Cultist's Staff", "Swiftfoot Boots", "Spider-Suit", "Millikin", "Chromatic Lantern",
    "Potioner's Trove", "Expedition Map", "Bloom Hulk", "Colossal Dreadmaw", "Fynn, the Fangbearer",
    "Helm of Awakening", "Ancient Brontodon", "Emergent Growth"]
_f = [c for c in DECKS["Blor física"] if c not in ("Forest", "Far Wanderings")]
DECKS["Blor física 2"] = _f + BLOR_RELLENO_2 + ["Forest"] * 17 + ["Command Tower", "Path of Ancestry", "Study Hall", "Access Tunnel"]
assert len(DECKS["Blor física 2"]) == 99, len(DECKS["Blor física 2"])
# Medido (25/11, semillas nuevas, 10.000 partidas): física 2 = B2 9,6%, B3 2,8%. Con 13 Forest más por las 13
# cartas más flojas: +10,6 en B2, +3,2 en B3. Con eso y el paso 1 (8 cartas, USD 8,94): +21,4 en B2, +6,2 en B3.

# 25/11 (Juan): eran 16 Forest + Roiling Canopy (21 tierras). Con 13 Forest comprados por las 13 cartas más flojas
# del relleno quedan 34 tierras (29 Forest). Helm of Awakening sale (acelera también a los rivales).
_f3 = list(DECKS["Blor física 2"]); _f3.remove("Forest"); _f3.append("Roiling Canopy")
DECKS["Blor física 3"] = _f3
DECKS["Blor física 3 + 13 Forest"] = swap_many(_f3,
    ["Helm of Awakening", "Heroic Intervention", "Cultist's Staff", "Spider-Suit", "Swiftfoot Boots", "Fynn, the Fangbearer",
     "Chromatic Lantern", "Gemhide Sliver", "Expedition Map", "Bloom Hulk", "Ancient Brontodon", "Run Over", "Root Snare"],
    ["Forest"] * 13)
# Medido (25/11, semillas nuevas, 10.000): física 3 + 13 Forest = B2 20,4%, B3 5,6%, goldfish T10,3. Cambiar Study Hall,
# Access Tunnel, Path of Ancestry y Roiling Canopy por Forest: 0. Helm of Awakening por Mind Stone −0,5, por Millikin −0,9.
# 25/11 (Juan, armada en físico): se quedaron Heroic Intervention, Gemhide Sliver y Run Over, y Helm of Awakening va en el
# cupo de Far Wanderings, en lugar de Millikin, Potioner's Trove, Colossal Dreadmaw y Emergent Growth. Todo temporal.
DECKS["Blor física armada"] = swap_many(DECKS["Blor física 3 + 13 Forest"],
    ["Millikin", "Potioner's Trove", "Colossal Dreadmaw", "Emergent Growth"],
    ["Heroic Intervention", "Gemhide Sliver", "Run Over", "Helm of Awakening"])

# Plan por fases de la física armada hacia 1.8 (27/11). Cada paso parte del anterior.
DECKS["Blor física paso 1"] = swap_many(DECKS["Blor física armada"],
    ["Helm of Awakening", "Pollenbright Druid", "Goobbue Gardener", "Conqueror's Flail", "Wild Onslaught",
     "Gemhide Sliver", "Satyr Grovedancer", "Mammoth Growth", "Bestow Greatness", "Flourishing Strike"],
    ["Level Up", "Lion Umbra", "Forgotten Ancient", "Avarice Amulet", "Short Bow",
     "Keen Sense", "Bugenhagen, Wise Elder", "Beast Within", "Nature's Claim", "Harmonize"])
DECKS["Blor física paso 2"] = swap_many(DECKS["Blor física paso 1"],
    ["Tanglespan Lookout", "Heroic Intervention", "Run Over", "Thrashing Brontodon",
     "Silken Strength", "Stony Strength", "Efflorescence", "Hexhaven Invigorator"],
    ["Bone Sabres", "Staff of Titania", "Hydra's Growth", "Strong Back",
     "Crystalline Armor", "Indomitable Might", "Fireshrieker", "Ancestral Mask"])
DECKS["Blor física paso 3"] = swap_many(DECKS["Blor física paso 2"],
    ["Elfhame Druid", "Oasis Gardener", "Coalition Relic", "Moss Diamond", "Adventurous Impulse",
     "Fertilid", "Drover of the Mighty", "Elvish Rejuvenator", "Prey Upon", "Rabid Bite"],
    ["Rampant Growth", "Nature's Lore", "Kodama's Reach", "Utopia Sprawl", "Fyndhorn Elves",
     "Rishkar's Expertise", "Hunter's Insight", "Primal Bellow", "Basilisk Collar", "Belt of Giant Strength"])
DECKS["Blor física paso 4"] = swap_many(DECKS["Blor física paso 3"],
    ["Toski, Bearer of Secrets", "World War Hulk", "Mind Stone", "Thought Vessel", "Skullclamp", "Path of Ancestry"],
    ["Super State", "Court of Garenbrig", "Thickest in the Thicket", "Obscuring Haze", "Skyshroud Claim", "Castle Garenbrig"])
DECKS["Blor física paso 5"] = swap_many(DECKS["Blor física paso 4"],
    ["Implement of Ferocity", "Long-Lost Lances", "The Earth Crystal", "Gaea's Embrace", "Shadowspear", "Gavel of the Righteous"],
    ["Power Fist", "Necklace of Girion", "Birds of Paradise", "Berserk", "Bear Umbra", "Fanatic of Rhonas"])
DECKS["Blor física paso 6"] = swap_many(DECKS["Blor física paso 5"],
    ["Zopandrel, Hunger Dominus", "Access Tunnel", "Command Tower", "Study Hall", "Roiling Canopy", "Forest", "Forest"],
    ["Commander's Plate", "Talon Gates of Madara", "Dryad Arbor", "Reliquary Tower", "Witch's Clinic", "Rogue's Passage", "War Room"])
DECKS["Blor física paso 7"] = swap_many(DECKS["Blor física paso 6"],
    ["Colossus Hammer", "Forest", "Forest", "Forest"],
    ["Buster Sword", "Nykthos, Shrine to Nyx", "Boseiju, Who Endures", "Yavimaya, Cradle of Growth"])
