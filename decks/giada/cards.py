# Card database for the Giada, Font of Hope simulator (mono-white angels + lifegain).
# cost = (generic, white_pips). t: C creature, A artifact, E enchantment, S sorcery, I instant.
# p/x = power/toughness (verified on mtg.wtf / Scryfall, 11/11/2026; Ob Nixilis checked on playgroup.gg).
# kw: flying, vigilance, first, lifelink, flash.  angel: True if the card is an Angel on the stack.

FORGE = "FORGE"   # coste, tipo y P/T desde core/cards_db.json (Forge); ver core/stats.py

def C(g, w, p, x):
    return dict(cost=(g, w), t="C", p=p, x=x)

def N(t, g, w):
    return dict(cost=(g, w), t=t)

CARDS = {
    "Giada, Font of Hope": FORGE,
    # --- precon creatures ---
    "Angel of Finality": FORGE,
    "Angel of Vitality": FORGE,
    "Angel of the Ruins": FORGE,
    "Angelic Field Marshal": FORGE,
    "Angelic Sleuth": FORGE,
    "Archangel of Tithes": FORGE,
    "Bishop of Wings": FORGE,
    "Dazzling Angel": FORGE,
    "Emeria Shepherd": FORGE,
    "Exemplar of Light": FORGE,
    "Firemane Commando": FORGE,
    "Herald of Eternal Dawn": FORGE,
    "Herald of War": FORGE,
    "Inspiring Overseer": FORGE,
    "Linvala, the Preserver": FORGE,
    "Lyra Dawnbringer": FORGE,
    "Merchant of Truth": FORGE,
    "Metallic Mimic": FORGE,
    "Metropolis Reformer": FORGE,
    "Norn's Choirmaster": FORGE,
    "Reya Dawnbringer": FORGE,
    "Righteous Valkyrie": FORGE,
    "Segovian Angel": FORGE,
    "Sephara, Sky's Blade": FORGE,
    "Seraph of the Sword": FORGE,
    "Serra Avenger": FORGE,
    "Speaker of the Heavens": FORGE,
    "Starnheim Aspirant": FORGE,
    "Sunblast Angel": FORGE,
    "Thraben Watcher": FORGE,
    "Vanguard Seraph": FORGE,
    "Wojek Investigator": FORGE,
    "Youthful Valkyrie": FORGE,   # 1/3 (corregido 23/11; antes 1/1)
    # --- precon noncreatures ---
    "Destroy Evil": FORGE,
    "Fateful Absence": FORGE,
    "Invoke the Divine": FORGE,
    "Swords to Plowshares": FORGE,
    "Valorous Stance": FORGE,
    "Austere Command": FORGE,
    "Cleansing Nova": FORGE,
    "Cut a Deal": FORGE,
    "Day of Judgment": FORGE,
    "Defy Death": FORGE,
    "Exorcise": FORGE,
    "Secret Rendezvous": FORGE,
    "Arcane Signet": FORGE,
    "Commander's Sphere": FORGE,
    "Cryptic Gateway": FORGE,
    "Endless Atlas": FORGE,
    "Heraldic Banner": FORGE,
    "Herald's Horn": FORGE,
    "Marble Diamond": FORGE,
    "Mind Stone": FORGE,
    "Patchwork Banner": FORGE,
    "Sol Ring": FORGE,
    "Swiftfoot Boots": FORGE,
    "Tome of Legends": FORGE,
    "Vanquisher's Banner": FORGE,
    "Always Watching": FORGE,
    "Angelic Destiny": FORGE,
    "Court of Grace": FORGE,
    "Grasp of Fate": FORGE,
    "Search the Premises": FORGE,
    # --- candidates (upgrade guides, EDHREC) ---
    "Path to Exile": FORGE,
    "Generous Gift": FORGE,
    "Valkyrie Harbinger": FORGE,
    "Resplendent Angel": FORGE,
    "Lyra, Archangel of Dawn": FORGE,
    "Pearl Medallion": FORGE,
    "Guide of Souls": FORGE,
    "Soul Warden": FORGE,
    "Folk Hero": FORGE,
    "Lightning Greaves": FORGE,
    "Flawless Maneuver": FORGE,
    "Kindred Judgment": FORGE,
    "Ob Nixilis, the Ascended": FORGE,
    "Blinding Angel": FORGE,
    "Sigarda's Vanguard": FORGE,
    "Felidar Sovereign": FORGE,
    "Akroma's Will": FORGE,
    "Karmic Guide": FORGE,
    "Archangel of Thune": FORGE,
    "Avacyn, Angel of Hope": FORGE,
    "Serra Ascendant": FORGE,
    "Smothering Tithe": FORGE,
    "Emeria's Call": FORGE,
    "Blank": N("S", 4, 0),
}

# lands: col True = produces W
LANDS = {
    "Plains": dict(col=True, basic=True),
    "Bonders' Enclave": dict(col=False),
    "Radiant Fountain": dict(col=False),
    "Secluded Steppe": dict(col=True, tapped=True),
    "Seraph Sanctuary": dict(col=False),
    "Temple of the False God": dict(col=False, temple=True),
    "War Room": dict(col=False),
    "Minas Tirith": dict(col=True),
    "Emeria's Call": dict(col=True),   # MDFC land side (pay 3 life to enter untapped)
}

COMMANDER = "Giada, Font of Hope"

PRECON = [
    "Angel of Finality", "Angel of Vitality", "Angel of the Ruins", "Angelic Field Marshal", "Angelic Sleuth",
    "Archangel of Tithes", "Bishop of Wings", "Dazzling Angel", "Emeria Shepherd", "Exemplar of Light",
    "Firemane Commando", "Herald of Eternal Dawn", "Herald of War", "Inspiring Overseer", "Linvala, the Preserver",
    "Lyra Dawnbringer", "Merchant of Truth", "Metallic Mimic", "Metropolis Reformer", "Norn's Choirmaster",
    "Reya Dawnbringer", "Righteous Valkyrie", "Segovian Angel", "Sephara, Sky's Blade", "Seraph of the Sword",
    "Serra Avenger", "Speaker of the Heavens", "Starnheim Aspirant", "Sunblast Angel", "Thraben Watcher",
    "Vanguard Seraph", "Wojek Investigator", "Youthful Valkyrie",
    "Destroy Evil", "Fateful Absence", "Invoke the Divine", "Swords to Plowshares", "Valorous Stance",
    "Austere Command", "Cleansing Nova", "Cut a Deal", "Day of Judgment", "Defy Death", "Exorcise",
    "Secret Rendezvous",
    "Arcane Signet", "Commander's Sphere", "Endless Atlas", "Heraldic Banner", "Marble Diamond", "Mind Stone",
    "Patchwork Banner", "Sol Ring", "Swiftfoot Boots", "Tome of Legends", "Vanquisher's Banner",
    "Always Watching", "Angelic Destiny", "Court of Grace", "Grasp of Fate", "Search the Premises",
] + ["Plains"] * 32 + ["Bonders' Enclave", "Radiant Fountain", "Secluded Steppe", "Seraph Sanctuary",
                       "Temple of the False God", "War Room"]
assert len(PRECON) == 99, len(PRECON)


def swap(deck, out, inn):
    d = list(deck)
    d[d.index(out)] = inn
    return d


ACTUAL = swap(swap(PRECON, "Speaker of the Heavens", "Cryptic Gateway"), "Endless Atlas", "Herald's Horn")


def load(path):
    out = []
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        n, name = line.split(" ", 1)
        if name == COMMANDER:
            continue
        out += [name] * int(n)
    return out

# --- Juan's own loose cards (claude/coleccion-cartas.md) ---
CARDS.update({
    "Lingering Souls": FORGE,            # flashback needs {B}: not usable here
    "Disenchant": FORGE,
    "Millikin": N("A", 2, 0),   # 0/1 mana creature: modelled as a rock that waits a turn
})
LANDS.update({
    "Scoured Barrens": dict(col=True, tapped=True, gain=1),
    "Blossoming Sands": dict(col=True, tapped=True, gain=1),
    "Tranquil Cove": dict(col=True, tapped=True, gain=1),
    "Thriving Heath": dict(col=True, tapped=True),
    "Memorial to Glory": dict(col=True, tapped=True),
    "Drifting Meadow": dict(col=True, tapped=True),
})

PRICE = {  # Card Kingdom USD (doc del mazo, 25/30-10-2026); 0 = ya es de Juan
    "Path to Exile": 2.49, "Generous Gift": 1.99, "Valkyrie Harbinger": 6.49, "Resplendent Angel": 12.99,
    "Lyra, Archangel of Dawn": 1.79, "Pearl Medallion": 10.99, "Emeria's Call": 7.49, "Guide of Souls": 5.49,
    "Soul Warden": 5.49, "Folk Hero": 1.29, "Minas Tirith": 12.99, "Kindred Judgment": 1.49,
    "Ob Nixilis, the Ascended": 1.79, "Felidar Sovereign": 4.99, "Karmic Guide": 0.99, "Sigarda's Vanguard": 1.99,
    "Lightning Greaves": 5.99, "Flawless Maneuver": 9.49, "Avacyn, Angel of Hope": 54.99,
    "Archangel of Thune": 22.99, "Serra Ascendant": 37.99, "Akroma's Will": 16.99, "Smothering Tithe": 69.99,
    "Plains": 0.35, "Blinding Angel": None,
    "Speaker of the Heavens": 0, "Endless Atlas": 0, "Lingering Souls": 0, "Disenchant": 0, "Millikin": 0,
    "Scoured Barrens": 0, "Blossoming Sands": 0, "Tranquil Cove": 0, "Thriving Heath": 0, "Memorial to Glory": 0,
    "Drifting Meadow": 0,
}

PHASE1 = [("Exorcise", "Path to Exile"), ("Invoke the Divine", "Generous Gift"), ("Sunblast Angel", "Valkyrie Harbinger"),
          ("Linvala, the Preserver", "Resplendent Angel"), ("Reya Dawnbringer", "Lyra, Archangel of Dawn"),
          ("Commander's Sphere", "Pearl Medallion"), ("Plains", "Emeria's Call"),
          ("Seraph of the Sword", "Guide of Souls"), ("Metallic Mimic", "Soul Warden"), ("Search the Premises", "Folk Hero"),
          ("Radiant Fountain", "Minas Tirith")]   # Tome -> Herald's Horn already done (Horn came in for Endless Atlas)

# --- go-wide candidates (oracle checked on Scryfall 12/11/2026) ---
CARDS.update({
    "Urza's Incubator": FORGE,                         # Angel creature spells cost {2} less
    "Starnheim Unleashed": FORGE,          # 4/4 flying vigilance Angel; foretell {X}{X}{W}: X tokens
    "Herald of the Host": FORGE,
    "Restoration Angel": FORGE,
    "Serra Angel": FORGE,
})
PRICE.update({"Urza's Incubator": None, "Starnheim Unleashed": None, "Herald of the Host": None,
              "Restoration Angel": None, "Serra Angel": None})
CARDS["Leader's Talent"] = N("E", 1, 1)   # Class: L1 attack -> +1/+1 counter; L2 {2}{W}; L3 {3}{W} (oracle mtg.wtf 12/11/2026)

# Fase 4: los efectos de cada carta (roles, palabras clave, respuestas, rocas...) viven en data/efectos.yaml;
# aquí quedan coste, tipo y P/T. core/mapeo.py los vuelve a poner con las claves de siempre.
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", ".."))
from core import mapeo as _MP, stats as _ST
for _n, _v in list(CARDS.items()):
    if _v is FORGE:
        CARDS[_n] = _ST.desde_forge("giada", _n)
for _n in list(CARDS):
    CARDS[_n] = _MP.importar("giada", _n, CARDS[_n])
PRICE["Leader's Talent"] = None

# 12/11/2026: physical change Cryptic Gateway -> Lyra, Archangel of Dawn
ACTUAL = swap(ACTUAL, "Cryptic Gateway", "Lyra, Archangel of Dawn")
