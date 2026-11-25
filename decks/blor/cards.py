"""Card data for the Blor the Impervious voltron simulator.

Oracle text checked in Gatherer on 13/11/2026 (see mazo-blor.md). Each entry keeps only what the engine needs:
  t     land / cre / aura / equip / ench / art / inst / sorc / pw
  cost  (generic, green pips)
  For effects, the engine looks the card up by name.
"""

COMMANDER = "Blor the Impervious"

C = {}


FORGE = "FORGE"   # coste, tipo y P/T desde core/cards_db.json (Forge); ver core/stats.py
def card(name, t=None, gen=0, g=0, **kw):
    """card(nombre): coste, tipo y P/T desde Forge (core/stats.py); con más argumentos, un ajuste a mano."""
    if t is None:
        C[name] = FORGE; return
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
card("Llanowar Elves")
card("Elvish Mystic")
card("Fyndhorn Elves")
card("Birds of Paradise")
card("Delighted Halfling")
card("Drover of the Mighty")
card("Fanatic of Rhonas")          # 4 with a 4-power creature
card("Bugenhagen, Wise Elder")
card("Sanctum Weaver")    # X = enchantments
card("Kami of Whispered Hopes")
card("Sakura-Tribe Elder")
card("Tireless Provisioner")
card("Millikin")
card("Sol Ring")
card("Arcane Signet")
card("Thought Vessel")
card("Herd Heirloom")
card("Necklace of Girion")
card("Emerald Medallion")
card("The Earth Crystal")
card("Mana Vault")
card("Grim Monolith")
card("Chrome Mox")
card("Mox Diamond")
card("Wild Growth")
card("Utopia Sprawl")
card("Wolfwillow Haven")
card("Overgrowth")
card("Rampant Growth")       # (to bf, to hand, tapped)
card("Nature's Lore")
card("Three Visits")
card("Farseek")                # no Plains/Island/Swamp/Mountain in mono-G
card("Cultivate")
card("Kodama's Reach")
card("Skyshroud Claim")
card("Far Wanderings")
card("Explore")
card("Crop Rotation")
card("Expedition Map")

# ------------------------------------------------------------------ card advantage
card("Rishkar's Expertise")
card("Return of the Wildspeaker")
card("Hunter's Insight")
card("Harmonize")
card("Garruk, Primal Hunter")
card("Sylvan Library")
card("Colossal Majesty")
card("Garruk's Uprising")
card("Enchantress's Presence")
card("Season of Growth")
card("The One Ring")
card("Toski, Bearer of Secrets")
card("Ohran Frostfang")
card("Eidolon of Blossoms")
card("Setessan Champion")
card("Verduran Enchantress")
card("Argothian Enchantress")
card("Adventurous Impulse")
card("Pia, Aether Ascetic")
card("Eternal Witness")

# ------------------------------------------------------------------ auras on Blor
# bonus is applied by the engine (some depend on board)
card("Blanchwood Armor")
card("Crystalline Armor")
card("Strong Back")
card("Level Up")
card("Ancestral Mask")
card("Bear Umbra")
card("Lion Umbra")
card("Snake Umbra")
card("Spider Umbra")
card("Rancor")
card("Hydra's Growth")
card("Colossification")
card("Indomitable Might")
card("Keen Sense")
card("Sixth Sense")
card("Curse of Predation")        # enchants a rival
card("Unnatural Growth")
card("Hardened Scales")
card("Branching Evolution")
card("Primal Rage")

# ------------------------------------------------------------------ equipment (eq = equip cost; leq = equip legendary/commander)
card("Blackblade Reforged")
card("Staff of Titania")
card("Commander's Plate")
card("Shadowspear")
card("Basilisk Collar")
card("Fireshrieker")
card("Leyline Axe")
card("Genji Glove")
card("Inquisitor's Flail")
card("Power Fist")
card("Buster Sword")
card("Bone Sabres")
card("Colossus Hammer")
card("World War Hulk")   # saga: I criatura R/G gratis (ignorado); II +3 contadores; III duplica poder y arrollar hasta fin de turno
card("Gavel of the Righteous")   # contador cada combate tuyo; +1/+1 por contador; 4+: doble golpe; equipar 3 (o quitar un contador)
card("Sword of Feast and Famine")
card("Sword of Fire and Ice")
card("Sword of Truth and Justice")
card("Sword of Hearth and Home")
card("Sword of the Animist")
card("Grafted Exoskeleton")
card("Pariah's Shield")
card("Avarice Amulet")
card("Mask of Memory")
card("Umezawa's Jitte")
card("Loxodon Warhammer")
card("Thran Power Suit")
card("Swiftfoot Boots")
card("Lightning Greaves")
card("Assault Suit")
card("Tarrian's Soulcleaver")
card("Belt of Giant Strength")
card("Trailblazer's Boots")
card("Long-Lost Lances")
card("Short Bow")
card("Helm of the Host")

# ------------------------------------------------------------------ pump / tricks
card("Berserk")
card("Become Immense")
card("Primal Bellow")
card("Giant Growth")
card("Invigorate")
card("Might of Old Krosa")
card("Gift of the Viper")
card("Tyvar's Stand")
card("Overprotect")
card("Vines of Vastwood", "inst", 0, 2)
card("Blossoming Defense")
card("Snakeskin Veil")
card("Stony Strength")
card("Triumph of the Hordes")
card("Epic Fight")

# ------------------------------------------------------------------ interaction
card("Beast Within")
card("Archdruid's Charm")
card("Krosan Grip")
card("Nature's Claim")
card("Return to Nature")
card("Ram Through")
card("Khalni Ambush")
card("Inscription of Abundance")
card("Bridgeworks Battle")
card("Primal Might")
card("Song of the Dryads")
card("Kenrith's Transformation")
card("Heroic Intervention")
card("Veil of Summer")
card("Fog")
card("Moment's Peace")
card("Constant Mists")

# ------------------------------------------------------------------ creatures (utility)
card("Silent Arbiter")
card("Spore Frog")
card("Tajuru Preserver")
card("Forgotten Ancient")
card("Frenzied Baloth")
card("Questing Beast")
card("Hexhaven Invigorator")
card("Evolution Sage")
card("Fynn, the Fangbearer")
card("Seedborn Muse")
card("Scavenging Ooze")
card("Crawlspace")
card("Worldly Tutor")
card("Natural Order")
card("Survival of the Fittest")

# speed candidates (Gatherer 13/11/2026)
card("Brass Squire")
card("Lavaspur Boots")
card("Wayfarer's Bauble")
card("Arbor Elf")
card("Elvish Spirit Guide")
card("Selvala, Heart of the Wilds")
card("Somberwald Sage")
card("Exploration")
card("Burgeoning")
card("Harrow")
card("Priest of Titania")
card("Karametra's Acolyte")
card("Sylvan Caryatid")
card("Paradise Druid")
card("Lotus Cobra")
card("Sakura-Tribe Scout")
card("Elemental Bond")
card("Guardian Project")

# edict fodder / extra ramp (Gatherer 13/11/2026)
card("Tendershoot Dryad")
card("Esika's Chariot")
card("Scute Swarm")
card("Wood Elves")
card("Saproling Migration")
card("Sprout Swarm")
card("Kodama of the West Tree")
LANDS["Dryad Arbor"] = dict(col="G", forest=True, creature=True)
card("Dryad Arbor")

# token makers (Gatherer 13/11/2026)
card("Verdant Embrace")
card("Awakening Zone")
card("From Beyond")
card("Nettlecyst")
card("Batterskull")
card("Flayer Husk")
LANDS["Lair of the Hydra"] = dict(col="G", manland=2)
LANDS["Treetop Village"] = dict(col="G", tapped=True, manland=2)
LANDS["Mutavault"] = dict(col="C", manland=1)
for _n in ("Lair of the Hydra", "Treetop Village", "Mutavault"):
    card(_n, "land")

card("Lotus Petal")   # {T}, sacrifice: one mana of any color (Gatherer 13/11/2026)

# "Blank": an empty slot for ablation
card("Blank", "sorc", 99, 0)



def is_land(n):
    return C.get(n, {}).get("t") == "land"

# regla 9 (15/11): candidatas contra counters (textos de Gatherer)
card("Conqueror's Flail")          # +1/+1 por color (mono-verde: +1); equipado: los rivales no lanzan hechizos en tu turno
card("Destiny Spinner")  # hechizos de criatura y encantamiento: no se pueden contrarrestar
card("Allosaurus Shepherd")     # hechizos verdes: no se pueden contrarrestar

# 15/11 (Juan): reductores de costo de artefactos / equipar (textos de Gatherer)
card("Semblance Anvil")        # imprint: lo que comparte tipo con lo exiliado cuesta {2} menos
card("Foundry Inspector")   # artefactos cuestan {1} menos
card("Cloud Key")              # el tipo elegido cuesta {1} menos (elige artefacto)
card("Jhoira's Familiar")   # historicos (artefactos y legendarios) {1} menos
card("Hammer of Nazahn")   # cada equipo que entra se equipa gratis; +2/+0, indestructible
card("Shuko")          # +1/+0, equipar {0}
card("Helm of Awakening")       # todos los hechizos cuestan {1} menos (tambien los de los rivales)
card("Whispersilk Cloak")    # imbloqueable y shroud (tampoco tus auras/equipos lo apuntan)
card("Darksteel Plate")      # indestructible ella misma (sobrevive odio a artefactos de destruir)
card("Crystal Chimes")               # {3},T,sac: vuelven a la mano los encantamientos del cementerio

# 15/11 (Juan): candidatas nuevas (textos de Gatherer)
LANDS["Talon Gates of Madara"] = dict(col="C")       # al entrar, una criatura sale de fase; {4}: ponerla desde la mano
card("Talon Gates of Madara")
card("Spinning Wheel Kick", "sorc", 2, 2)   # X=1: Blor pega a una criatura (frena un rival de combate)
card("Tanuki Transplanter")    # al atacar, {G} igual a su poder (dura el turno)
card("Nightshade Peddler")   # soulbond con Blor: ambos con toque mortal
card("Quietus Spike")          # toque mortal; al golpear, el rival pierde la mitad de su vida
card("Gorgon's Head")          # toque mortal
card("Hunter's Blowgun")      # +1/+1; toque mortal en tu turno, alcance en el resto
card("Lure")                          # todas las criaturas que pueden bloquear al encantado lo hacen

# --- 16/11: cartas de la coleccion de Juan para la version fisica ---
card("Gaea's Embrace")                      # {2}{G}{G} (corregido 23/11) +3/+3, arrollar, {G}: regenera
card("Tower Above", "inst", 0, 3)             # CONJURO {2/G}x3: +4/+4, arrollar, marchitar hasta fin de turno (modelado como truco antes del combate)
card("Pollenbright Druid")         # ETB: contador +1/+1 en Blor (o proliferar)
card("Studious First-Year")        # {G} 1/1, entra "prepared": luego se puede lanzar una copia de Rampant Growth
card("Gemhide Sliver")
card("Coalition Relic")
card("Mind Stone")
card("Scuttlemutt")

# --- 16/11: bulk de Juan (textos de Forge/Oracle) ---
card("Elfhame Druid")
card("Goobbue Gardener")
card("Guy in the Chair")
card("Moss Diamond")               # entra girada (no modelado)
card("Glittering Frost")
card("Fertilid", "cre", 2, 1, p=2, x=2)                   # {1}{G}, quitar contador: Forest (modelado: 1 Forest al entrar)
card("Elvish Rejuvenator")         # mira 5, tierra al campo girada (modelado: Forest girado)
card("Silken Strength")                     # flash, +1/+2, alcance, endereza al entrar
card("Cultist's Staff")
card("Spider-Suit")
card("Neglected Heirloom")
card("Bestow Greatness")
card("Grow Extra Arms")
card("Mammoth Growth")
card("Flourishing Strike")
card("Efflorescence")            # 2 contadores +1/+1 (permanentes; modelado como truco)
card("Satyr Grovedancer")          # ETB: contador +1/+1
card("Vinelasher Adept")           # ETB: 3 contadores +1/+1
card("Bloom Hulk")                 # ETB: proliferar
card("Slice in Twain")            # + roba

# --- 19/11: lista de venta (Moxfield "Vendo CKx3") y candidatas de Juan; textos de Forge/Oracle ---
card("Glorious Sunrise")        # inicio de combate: +1/+1 y arrollar / GGG / roba si tienes criatura de poder 3+ / 3 vidas
card("Mithril Coat")     # flash, indestructible, se adjunta al entrar; da indestructible (Blor ya lo es)
card("Sylvan Safekeeper")   # sacrifica una tierra: shroud (Blor ya tiene antimaleficio)
card("Finale of Devastation", "sorc", 3, 2)   # X G G: tutor de criatura (modelado con X=3); el modo X>=10 no se modela
card("Akroma's Memorial")        # vuelo, primer golpe, vigilancia, arrollar, prisa, proteccion negro/rojo
card("Tamiyo's Safekeeping")    # antimaleficio e indestructible a un permanente tuyo
card("Spellskite", "art", 2, 0)               # 0/4: cambia el objetivo de un hechizo a si misma ({U/P}: 2 vidas)
card("Thran Dynamo")
card("Bloom Tender")
card("Azusa, Lost but Seeking")
card("Collector Ouphe")

# 22/11 (fotos de Juan; textos de los scripts de Forge): Skullclamp, Lotus Bloom, Chromatic Lantern
card("Skullclamp")
card("Lotus Bloom")          # suspend 3 por {0}; {T}, sacrificar: tres manas de un color
card("Chromatic Lantern")
card("Colossal Dreadmaw")


# 24/11: candidatas de EDHREC para Blor (textos de los scripts de Forge en core/cards_db.json; efectos en data/efectos.yaml
# y en el motor). Las MDFC van como tierra (su cara de tierra).
card("Thrashing Brontodon", "cre", 2, 1, p=3, x=4)   # 24/11: {1}, sacrificar: destruir artefacto/encantamiento (no modelado; solo cuerpo y fodder)
LANDS["Disciple of Freyalise"] = dict(col="G", mdfc=True)
card("Disciple of Freyalise", "land")
LANDS["Vastwood Fortification"] = dict(col="G", tapped=True, mdfc=True)
card("Vastwood Fortification", "land")
LANDS["Bala Ged Recovery"] = dict(col="G", tapped=True, mdfc=True)
card("Bala Ged Recovery", "land")
LANDS["Mosswort Bridge"] = dict(col="G", tapped=True)
card("Mosswort Bridge", "land")
LANDS["Bonders' Enclave"] = dict(col="C")
card("Bonders' Enclave", "land")
LANDS["Urza's Saga"] = dict(col="C")
card("Urza's Saga", "land")
LANDS["Command Beacon"] = dict(col="C")
card("Command Beacon", "land")
LANDS["Shifting Woodland"] = dict(col="G")
card("Shifting Woodland", "land")
LANDS["Oakhollow Village"] = dict(col="C")
card("Oakhollow Village", "land")
LANDS["Okina, Temple to the Grandfathers"] = dict(col="G")
card("Okina, Temple to the Grandfathers", "land")
LANDS["Yavimaya Hollow"] = dict(col="C")
card("Yavimaya Hollow", "land")
LANDS["Temple of the False God"] = dict(col="CC")
card("Temple of the False God", "land")
LANDS["Snow-Covered Forest"] = dict(col="G", forest=True, basic=True)
card("Snow-Covered Forest", "land")
LANDS["Fabled Passage"] = dict(col="fetch")
card("Fabled Passage", "land")
LANDS["Urza's Cave"] = dict(col="C")
card("Urza's Cave", "land")
LANDS["Blighted Woodland"] = dict(col="C")
card("Blighted Woodland", "land")
card("Simulacrum Shaper")
card("Verdant Kraken")
card("Bristly Bill, Spine Sower")
card("Ulvenwald Tracker")
card("Reclamation Sage")
card("Poison Dart Frog")
card("Zopandrel, Hunger Dominus")
card("Frog Butler")
card("Ouroboroid")
card("Llanowar Tribe")
card("Vigor")
card("Clifftop Lookout")
card("Tanglespan Lookout")
card("Noxious Newt")
card("Rampant Frogantua")
card("Scythecat Cub")
card("Obscuring Haze")
card("Lifestream's Blessing")
card("Force of Vigor")
card("Tifa's Limit Break", "inst", 2, 1)   # modo Meteor Strikes ({G}+{2}): duplicar la fuerza
card("Entish Restoration")
card("Blessed Respite")
card("Fight for the Throne")
card("Collective Resistance")
card("Invigorating Surge")
card("Prizefight")
card("Ancient Animus")
card("Arachnogenesis")
card("Tangle")
card("Polliwallop")
card("Legolas's Quick Reflexes")
card("Heritage Reclamation")
card("Soul's Majesty")
card("Traverse the Outlands")
card("Season of Gathering")
card("Bushwhack")
card("Contest of Claws")
card("Ezuri's Predation")
card("Exponential Growth", "sorc", 0, 2)   # X X G G: el X lo elige el motor
card("Regrowth")
card("Hunter's Prowess")
card("Shared Roots")
card("Flare of Cultivation")
card("Fangs of Kalonia")
card("Green Sun's Zenith", "sorc", 3, 1)   # X G: tutor de criatura verde (modelado con X=3, como Finale)
card("Excalibur, Sword of Eden")
card("The Great Henge")
card("Captain America's Shield")
card("Ozolith, the Shattered Spire")
card("Strata Scythe")
card("Sword of Vengeance")
card("Bow of Nylea")
card("Brotherhood Regalia")
card("Haunted Cloak")
card("Aettir and Priwen")
card("Vibranium Strike Gauntlets")
card("Super State")
card("Eldrazi Conscription")
card("Well Rested")
card("Thickest in the Thicket")
card("Lignify")
card("Meltstrider's Resolve")
card("Raised by Giants")
card("Predatory Hunger")
card("Beorn's Hospitality")
card("Seismic Tutelage")
card("Mark of Sakiko")
card("Innkeeper's Talent")
card("Terrasymbiosis")
card("Boar Umbra")
card("One with Nature")
card("Druid's Call")
card("Fertile Ground")
card("Court of Garenbrig")
card("Forced Adaptation")
card("Instill Energy")
card("Ride the Shoopuf")
card("The Aetherspark")


# 25/11: cartas de Juan (bulk y sueltas) para la versión física provisional
LANDS["Study Hall"] = dict(col="C")        # {1},T: cualquier color (filtro, no se modela)
LANDS["Access Tunnel"] = dict(col="C")     # {3},T: imbloqueable si la fuerza es 3 o menos (no se modela)
card("Study Hall", "land"); card("Access Tunnel", "land")
for _n in ("Ancient Brontodon", "Emergent Growth", "Prey Upon", "Rabid Bite", "Run Over", "Root Snare", "Wild Onslaught", "Implement of Ferocity",
           "Potioner's Trove", "Oasis Gardener"):
    card(_n)

# Fase 4: los efectos de cada carta (roles, palabras clave, respuestas, rocas...) viven en data/efectos.yaml;
# aquí quedan coste, tipo y P/T. core/mapeo.py los vuelve a poner con las claves de siempre.
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", ".."))
from core import mapeo as _MP, stats as _ST
for _n, _v in list(C.items()):
    if _v is FORGE:
        C[_n] = _ST.desde_forge("blor", _n)
for _n in list(C):
    C[_n] = _MP.importar("blor", _n, C[_n])
# (después de cargar los efectos; desde la fase 4 hasta el 23/11 se calculaba sin ellos)
GAME_CHANGERS = {n for n, d in C.items() if d.get("gc")} | {"Gaea's Cradle", "Ancient Tomb"}
