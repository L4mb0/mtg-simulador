"""Card data for the Blor the Impervious voltron simulator.

Oracle text checked in Gatherer on 13/11/2026 (see mazo-blor.md). Each entry keeps only what the engine needs:
  t     land / cre / aura / equip / ench / art / inst / sorc / pw
  cost  (generic, green pips)
  For effects, the engine looks the card up by name.
"""

COMMANDER = "Blor the Impervious"

C = {}


def card(name, t, gen=0, g=0, **kw):
    d = dict(t=t, cost=(gen, g))
    d.update(kw)
    C[name] = d


# ------------------------------------------------------------------ commander
card(COMMANDER, "cre", 3, 2, p=3, x=3)

# ------------------------------------------------------------------ lands
# col: "G" or "C"; tapped: enters tapped; extra behaviours in engine
LANDS = {
    "Forest": dict(col="G", forest=True, basic=True),
    "Rogue's Passage": dict(col="C"),
    "Reliquary Tower": dict(col="C"),
    "War Room": dict(col="C"),
    "Witch's Clinic": dict(col="C"),
    "Boseiju, Who Endures": dict(col="G", ans="ae"),
    "Nykthos, Shrine to Nyx": dict(col="C"),
    "Yavimaya, Cradle of Growth": dict(col="G", forest=True),
    "Roiling Canopy": dict(col="G", tapped=True),
    "Castle Garenbrig": dict(col="G"),
    "Cavern of Souls": dict(col="C"),
    "Myriad Landscape": dict(col="C", tapped=True),
    "Gaea's Cradle": dict(col="G"),
    "Ancient Tomb": dict(col="CC"),
    "Oran-Rief, the Vastwood": dict(col="G", tapped=True),
    "Command Tower": dict(col="G"),
    "Evolving Wilds": dict(col="fetch"),
    "Terramorphic Expanse": dict(col="fetch"),
    "Thriving Grove": dict(col="G", tapped=True),
    "Hickory Woodlot": dict(col="GG", tapped=True),
    "Path of Ancestry": dict(col="G", tapped=True),
    "Gemstone Mine": dict(col="G"),
    "Rishadan Port": dict(col="C"),
    "Khalni Ambush": dict(col="G", tapped=True, mdfc=True),   # Khalni Territory side
}
for n in LANDS:
    if n != "Khalni Ambush":
        card(n, "land")

# ------------------------------------------------------------------ mana
card("Llanowar Elves", "cre", 0, 1, p=1, x=1)
card("Elvish Mystic", "cre", 0, 1, p=1, x=1)
card("Fyndhorn Elves", "cre", 0, 1, p=1, x=1)
card("Birds of Paradise", "cre", 0, 1, p=0, x=1)
card("Delighted Halfling", "cre", 0, 1, p=1, x=2)
card("Drover of the Mighty", "cre", 1, 1, p=1, x=1)
card("Fanatic of Rhonas", "cre", 1, 1, p=1, x=4)          # 4 with a 4-power creature
card("Bugenhagen, Wise Elder", "cre", 1, 1, p=1, x=3)
card("Sanctum Weaver", "cre", 1, 1, p=0, x=2)    # X = enchantments
card("Kami of Whispered Hopes", "cre", 2, 1, p=1, x=1)
card("Sakura-Tribe Elder", "cre", 1, 1, p=1, x=1)
card("Tireless Provisioner", "cre", 2, 1, p=3, x=2)
card("Millikin", "cre", 2, 0, p=0, x=1)
card("Sol Ring", "art", 1, 0)
card("Arcane Signet", "art", 2, 0)
card("Thought Vessel", "art", 2, 0)
card("Herd Heirloom", "art", 1, 1)
card("Necklace of Girion", "art", 2, 1)
card("Emerald Medallion", "art", 2, 0)
card("The Earth Crystal", "art", 2, 2)
card("Mana Vault", "art", 1, 0)
card("Grim Monolith", "art", 2, 0)
card("Chrome Mox", "art", 0, 0)
card("Mox Diamond", "art", 0, 0)
card("Wild Growth", "ench", 0, 1)
card("Utopia Sprawl", "ench", 0, 1)
card("Wolfwillow Haven", "ench", 1, 1)
card("Overgrowth", "ench", 2, 1)
card("Rampant Growth", "sorc", 1, 1)       # (to bf, to hand, tapped)
card("Nature's Lore", "sorc", 1, 1)
card("Three Visits", "sorc", 1, 1)
card("Farseek", "sorc", 1, 1)                # no Plains/Island/Swamp/Mountain in mono-G
card("Cultivate", "sorc", 2, 1)
card("Kodama's Reach", "sorc", 2, 1)
card("Skyshroud Claim", "sorc", 3, 1)
card("Far Wanderings", "sorc", 2, 1)
card("Explore", "sorc", 1, 1)
card("Crop Rotation", "inst", 0, 1)
card("Expedition Map", "art", 1, 0)

# ------------------------------------------------------------------ card advantage
card("Rishkar's Expertise", "sorc", 4, 2)
card("Return of the Wildspeaker", "inst", 4, 1)
card("Hunter's Insight", "inst", 2, 1)
card("Harmonize", "sorc", 2, 2)
card("Garruk, Primal Hunter", "pw", 2, 3)
card("Sylvan Library", "ench", 1, 1)
card("Colossal Majesty", "ench", 2, 1)
card("Garruk's Uprising", "ench", 2, 1)
card("Enchantress's Presence", "ench", 2, 1)
card("Season of Growth", "ench", 1, 1)
card("The One Ring", "art", 4, 0)
card("Toski, Bearer of Secrets", "cre", 3, 1, p=1, x=1)
card("Ohran Frostfang", "cre", 3, 2, p=2, x=6)
card("Eidolon of Blossoms", "cre", 2, 2, p=2, x=2)
card("Setessan Champion", "cre", 2, 1, p=1, x=3)
card("Verduran Enchantress", "cre", 1, 2, p=0, x=2)
card("Argothian Enchantress", "cre", 1, 1, p=0, x=1)
card("Adventurous Impulse", "sorc", 0, 1)
card("Pia, Aether Ascetic", "cre", 2, 1, p=2, x=2)
card("Eternal Witness", "cre", 1, 2, p=2, x=1)

# ------------------------------------------------------------------ auras on Blor
# bonus is applied by the engine (some depend on board)
card("Blanchwood Armor", "aura", 2, 1)
card("Crystalline Armor", "aura", 3, 1)
card("Strong Back", "aura", 2, 1)
card("Level Up", "aura", 1, 1)
card("Ancestral Mask", "aura", 2, 1)
card("Bear Umbra", "aura", 2, 2)
card("Lion Umbra", "aura", 0, 2)
card("Snake Umbra", "aura", 2, 1)
card("Spider Umbra", "aura", 0, 1)
card("Rancor", "aura", 0, 1)
card("Hydra's Growth", "aura", 2, 1)
card("Colossification", "aura", 5, 2)
card("Indomitable Might", "aura", 3, 1)
card("Keen Sense", "aura", 0, 1)
card("Sixth Sense", "aura", 0, 1)
card("Curse of Predation", "ench", 2, 1)        # enchants a rival
card("Unnatural Growth", "ench", 1, 4)
card("Hardened Scales", "ench", 0, 1)
card("Branching Evolution", "ench", 2, 1)
card("Primal Rage", "ench", 1, 1)

# ------------------------------------------------------------------ equipment (eq = equip cost; leq = equip legendary/commander)
card("Blackblade Reforged", "equip", 2, 0)
card("Staff of Titania", "equip", 2, 0)
card("Commander's Plate", "equip", 1, 0)
card("Shadowspear", "equip", 1, 0)
card("Basilisk Collar", "equip", 1, 0)
card("Fireshrieker", "equip", 3, 0)
card("Leyline Axe", "equip", 4, 0)
card("Genji Glove", "equip", 5, 0)
card("Inquisitor's Flail", "equip", 2, 0)
card("Power Fist", "equip", 1, 1)
card("Buster Sword", "equip", 3, 0)
card("Bone Sabres", "equip", 2, 1)
card("Colossus Hammer", "equip", 1, 0)
card("World War Hulk", "ench", 3, 2)   # saga: I criatura R/G gratis (ignorado); II +3 contadores; III duplica poder y arrollar hasta fin de turno
card("Gavel of the Righteous", "equip", 2, 0)   # contador cada combate tuyo; +1/+1 por contador; 4+: doble golpe; equipar 3 (o quitar un contador)
card("Sword of Feast and Famine", "equip", 3, 0)
card("Sword of Fire and Ice", "equip", 3, 0)
card("Sword of Truth and Justice", "equip", 3, 0)
card("Sword of Hearth and Home", "equip", 3, 0)
card("Sword of the Animist", "equip", 2, 0)
card("Grafted Exoskeleton", "equip", 4, 0)
card("Pariah's Shield", "equip", 5, 0)
card("Avarice Amulet", "equip", 4, 0)
card("Mask of Memory", "equip", 2, 0)
card("Umezawa's Jitte", "equip", 2, 0)
card("Loxodon Warhammer", "equip", 3, 0)
card("Thran Power Suit", "equip", 2, 0)
card("Swiftfoot Boots", "equip", 2, 0)
card("Lightning Greaves", "equip", 2, 0)
card("Assault Suit", "equip", 4, 0)
card("Tarrian's Soulcleaver", "equip", 1, 0)
card("Belt of Giant Strength", "equip", 1, 1)
card("Trailblazer's Boots", "equip", 2, 0)
card("Long-Lost Lances", "equip", 2, 0)
card("Short Bow", "equip", 2, 0)
card("Helm of the Host", "equip", 4, 0)

# ------------------------------------------------------------------ pump / tricks
card("Berserk", "inst", 0, 1)
card("Become Immense", "inst", 5, 1)
card("Primal Bellow", "inst", 0, 1)
card("Giant Growth", "inst", 0, 1)
card("Invigorate", "inst", 2, 1)
card("Might of Old Krosa", "inst", 0, 1)
card("Gift of the Viper", "inst", 0, 1)
card("Tyvar's Stand", "inst", 0, 1)
card("Overprotect", "inst", 1, 1)
card("Vines of Vastwood", "inst", 0, 2)
card("Blossoming Defense", "inst", 0, 1)
card("Snakeskin Veil", "inst", 0, 1)
card("Stony Strength", "inst", 0, 1)
card("Triumph of the Hordes", "sorc", 2, 2)
card("Epic Fight", "sorc", 2, 1)

# ------------------------------------------------------------------ interaction
card("Beast Within", "inst", 2, 1)
card("Archdruid's Charm", "inst", 0, 3)
card("Krosan Grip", "inst", 2, 1)
card("Nature's Claim", "inst", 0, 1)
card("Return to Nature", "inst", 1, 1)
card("Ram Through", "inst", 1, 1)
card("Khalni Ambush", "inst", 2, 1)
card("Inscription of Abundance", "inst", 1, 1)
card("Bridgeworks Battle", "sorc", 2, 1)
card("Primal Might", "sorc", 0, 1)
card("Song of the Dryads", "aura", 2, 1)
card("Kenrith's Transformation", "aura", 1, 1)
card("Heroic Intervention", "inst", 1, 1)
card("Veil of Summer", "inst", 0, 1)
card("Fog", "inst", 0, 1)
card("Moment's Peace", "inst", 1, 1)
card("Constant Mists", "inst", 1, 1)

# ------------------------------------------------------------------ creatures (utility)
card("Silent Arbiter", "cre", 4, 0, p=1, x=5)
card("Spore Frog", "cre", 0, 1, p=1, x=1)
card("Tajuru Preserver", "cre", 1, 1, p=2, x=1)
card("Forgotten Ancient", "cre", 3, 1, p=0, x=3)
card("Frenzied Baloth", "cre", 0, 2, p=3, x=2)
card("Questing Beast", "cre", 2, 2, p=4, x=4)
card("Hexhaven Invigorator", "cre", 0, 4, p=6, x=6)
card("Evolution Sage", "cre", 2, 1, p=3, x=2)
card("Fynn, the Fangbearer", "cre", 1, 1, p=1, x=3)
card("Seedborn Muse", "cre", 3, 2, p=2, x=4)
card("Scavenging Ooze", "cre", 1, 1, p=2, x=2)
card("Crawlspace", "art", 3, 0)
card("Worldly Tutor", "inst", 0, 1)
card("Natural Order", "sorc", 2, 2)
card("Survival of the Fittest", "ench", 1, 1)

# speed candidates (Gatherer 13/11/2026)
card("Brass Squire", "cre", 3, 0, p=1, x=3)
card("Lavaspur Boots", "equip", 1, 0)
card("Wayfarer's Bauble", "art", 1, 0)
card("Arbor Elf", "cre", 0, 1, p=1, x=1)
card("Elvish Spirit Guide", "cre", 2, 1, p=2, x=2)
card("Selvala, Heart of the Wilds", "cre", 1, 2, p=2, x=3)
card("Somberwald Sage", "cre", 2, 1, p=0, x=1)
card("Exploration", "ench", 0, 1)
card("Burgeoning", "ench", 0, 1)
card("Harrow", "inst", 2, 1)
card("Priest of Titania", "cre", 1, 1, p=1, x=1)
card("Karametra's Acolyte", "cre", 3, 1, p=1, x=4)
card("Sylvan Caryatid", "cre", 1, 1, p=0, x=3)
card("Paradise Druid", "cre", 1, 1, p=2, x=1)
card("Lotus Cobra", "cre", 1, 1, p=2, x=1)
card("Sakura-Tribe Scout", "cre", 0, 1, p=1, x=1)
card("Elemental Bond", "ench", 2, 1)
card("Guardian Project", "ench", 3, 1)

# edict fodder / extra ramp (Gatherer 13/11/2026)
card("Tendershoot Dryad", "cre", 4, 1, p=2, x=2)
card("Esika's Chariot", "art", 3, 1)
card("Scute Swarm", "cre", 2, 1, p=1, x=1)
card("Wood Elves", "cre", 2, 1, p=1, x=1)
card("Saproling Migration", "sorc", 1, 1)
card("Sprout Swarm", "inst", 1, 1)
card("Kodama of the West Tree", "cre", 2, 1, p=3, x=3)
LANDS["Dryad Arbor"] = dict(col="G", forest=True, creature=True)
card("Dryad Arbor", "land")

# token makers (Gatherer 13/11/2026)
card("Verdant Embrace", "aura", 3, 2)
card("Awakening Zone", "ench", 2, 1)
card("From Beyond", "ench", 3, 1)
card("Nettlecyst", "equip", 3, 0)
card("Batterskull", "equip", 5, 0)
card("Flayer Husk", "equip", 1, 0)
LANDS["Lair of the Hydra"] = dict(col="G", manland=2)
LANDS["Treetop Village"] = dict(col="G", tapped=True, manland=2)
LANDS["Mutavault"] = dict(col="C", manland=1)
for _n in ("Lair of the Hydra", "Treetop Village", "Mutavault"):
    card(_n, "land")

card("Lotus Petal", "art", 0, 0)   # {T}, sacrifice: one mana of any color (Gatherer 13/11/2026)

# "Blank": an empty slot for ablation
card("Blank", "sorc", 99, 0)

GAME_CHANGERS = {n for n, d in C.items() if d.get("gc")} | {"Gaea's Cradle", "Ancient Tomb"}


def is_land(n):
    return C.get(n, {}).get("t") == "land"

# regla 9 (15/11): candidatas contra counters (textos de Gatherer)
card("Conqueror's Flail", "equip", 2, 0)          # +1/+1 por color (mono-verde: +1); equipado: los rivales no lanzan hechizos en tu turno
card("Destiny Spinner", "cre", 1, 1, p=2, x=3)  # hechizos de criatura y encantamiento: no se pueden contrarrestar
card("Allosaurus Shepherd", "cre", 0, 1, p=1, x=1)     # hechizos verdes: no se pueden contrarrestar

# 15/11 (Juan): reductores de costo de artefactos / equipar (textos de Gatherer)
card("Semblance Anvil", "art", 3, 0)        # imprint: lo que comparte tipo con lo exiliado cuesta {2} menos
card("Foundry Inspector", "cre", 3, 0, p=3, x=2)   # artefactos cuestan {1} menos
card("Cloud Key", "art", 3, 0)              # el tipo elegido cuesta {1} menos (elige artefacto)
card("Jhoira's Familiar", "cre", 4, 0, p=2, x=2)   # historicos (artefactos y legendarios) {1} menos
card("Hammer of Nazahn", "equip", 4, 0)   # cada equipo que entra se equipa gratis; +2/+0, indestructible
card("Shuko", "equip", 1, 0)          # +1/+0, equipar {0}
card("Helm of Awakening", "art", 2, 0)       # todos los hechizos cuestan {1} menos (tambien los de los rivales)
card("Whispersilk Cloak", "equip", 3, 0)    # imbloqueable y shroud (tampoco tus auras/equipos lo apuntan)
card("Darksteel Plate", "equip", 3, 0)      # indestructible ella misma (sobrevive odio a artefactos de destruir)
card("Crystal Chimes", "art", 3, 0)               # {3},T,sac: vuelven a la mano los encantamientos del cementerio

# 15/11 (Juan): candidatas nuevas (textos de Gatherer)
LANDS["Talon Gates of Madara"] = dict(col="C")       # al entrar, una criatura sale de fase; {4}: ponerla desde la mano
card("Talon Gates of Madara", "land")
card("Spinning Wheel Kick", "sorc", 2, 2)   # X=1: Blor pega a una criatura (frena un rival de combate)
card("Tanuki Transplanter", "equip", 3, 1)    # al atacar, {G} igual a su poder (dura el turno)
card("Nightshade Peddler", "cre", 1, 1, p=1, x=1)   # soulbond con Blor: ambos con toque mortal
card("Quietus Spike", "equip", 3, 0)          # toque mortal; al golpear, el rival pierde la mitad de su vida
card("Gorgon's Head", "equip", 1, 0)          # toque mortal
card("Hunter's Blowgun", "equip", 1, 0)      # +1/+1; toque mortal en tu turno, alcance en el resto
card("Lure", "aura", 1, 2)                          # todas las criaturas que pueden bloquear al encantado lo hacen

# --- 16/11: cartas de la coleccion de Juan para la version fisica ---
card("Gaea's Embrace", "aura", 2, 2)                      # {2}{G}{G} (corregido 23/11) +3/+3, arrollar, {G}: regenera
card("Tower Above", "inst", 0, 3)             # CONJURO {2/G}x3: +4/+4, arrollar, marchitar hasta fin de turno (modelado como truco antes del combate)
card("Pollenbright Druid", "cre", 1, 1, p=1, x=1)         # ETB: contador +1/+1 en Blor (o proliferar)
card("Studious First-Year", "cre", 0, 1, p=1, x=1)        # {G} 1/1, entra "prepared": luego se puede lanzar una copia de Rampant Growth
card("Gemhide Sliver", "cre", 1, 1, p=1, x=1)
card("Coalition Relic", "art", 3, 0)
card("Mind Stone", "art", 2, 0)
card("Scuttlemutt", "cre", 3, 0, p=2, x=2)

# --- 16/11: bulk de Juan (textos de Forge/Oracle) ---
card("Elfhame Druid", "cre", 1, 1, p=0, x=2)
card("Goobbue Gardener", "cre", 1, 1, p=1, x=3)
card("Guy in the Chair", "cre", 2, 1, p=2, x=3)
card("Moss Diamond", "art", 2, 0)               # entra girada (no modelado)
card("Glittering Frost", "ench", 2, 1)
card("Fertilid", "cre", 2, 1, p=2, x=2)                   # {1}{G}, quitar contador: Forest (modelado: 1 Forest al entrar)
card("Elvish Rejuvenator", "cre", 2, 1, p=1, x=1)         # mira 5, tierra al campo girada (modelado: Forest girado)
card("Silken Strength", "aura", 1, 1)                     # flash, +1/+2, alcance, endereza al entrar
card("Cultist's Staff", "equip", 2, 0)
card("Spider-Suit", "equip", 1, 0)
card("Neglected Heirloom", "equip", 1, 0)
card("Bestow Greatness", "inst", 2, 1)
card("Grow Extra Arms", "inst", 1, 1)
card("Mammoth Growth", "inst", 2, 1)
card("Flourishing Strike", "inst", 1, 1)
card("Efflorescence", "inst", 2, 1)            # 2 contadores +1/+1 (permanentes; modelado como truco)
card("Satyr Grovedancer", "cre", 1, 1, p=1, x=1)          # ETB: contador +1/+1
card("Vinelasher Adept", "cre", 4, 2, p=2, x=4)           # ETB: 3 contadores +1/+1
card("Bloom Hulk", "cre", 3, 1, p=4, x=4)                 # ETB: proliferar
card("Slice in Twain", "inst", 2, 2)            # + roba

# --- 19/11: lista de venta (Moxfield "Vendo CKx3") y candidatas de Juan; textos de Forge/Oracle ---
card("Glorious Sunrise", "ench", 3, 2)        # inicio de combate: +1/+1 y arrollar / GGG / roba si tienes criatura de poder 3+ / 3 vidas
card("Mithril Coat", "equip", 3, 0)     # flash, indestructible, se adjunta al entrar; da indestructible (Blor ya lo es)
card("Sylvan Safekeeper", "cre", 0, 1, p=1, x=1)   # sacrifica una tierra: shroud (Blor ya tiene antimaleficio)
card("Finale of Devastation", "sorc", 3, 2)   # X G G: tutor de criatura (modelado con X=3); el modo X>=10 no se modela
card("Akroma's Memorial", "art", 7, 0)        # vuelo, primer golpe, vigilancia, arrollar, prisa, proteccion negro/rojo
card("Tamiyo's Safekeeping", "inst", 0, 1)    # antimaleficio e indestructible a un permanente tuyo
card("Spellskite", "art", 2, 0)               # 0/4: cambia el objetivo de un hechizo a si misma ({U/P}: 2 vidas)
card("Thran Dynamo", "art", 4, 0)
card("Bloom Tender", "cre", 1, 1, p=1, x=1)
card("Azusa, Lost but Seeking", "cre", 2, 1, p=1, x=2)
card("Collector Ouphe", "cre", 1, 1, p=2, x=2)

# 22/11 (fotos de Juan; textos de los scripts de Forge): Skullclamp, Lotus Bloom, Chromatic Lantern
card("Skullclamp", "equip", 1, 0)
card("Lotus Bloom", "art", 0, 0)          # suspend 3 por {0}; {T}, sacrificar: tres manas de un color
card("Chromatic Lantern", "art", 3, 0)
card("Colossal Dreadmaw", "cre", 4, 2, p=6, x=6)

# Fase 4: los efectos de cada carta (roles, palabras clave, respuestas, rocas...) viven en data/efectos.yaml;
# aquí quedan coste, tipo y P/T. core/mapeo.py los vuelve a poner con las claves de siempre.
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", ".."))
from core import mapeo as _MP
for _n in list(C):
    C[_n] = _MP.importar("blor", _n, C[_n])
