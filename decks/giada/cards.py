# Card database for the Giada, Font of Hope simulator (mono-white angels + lifegain).
# cost = (generic, white_pips). t: C creature, A artifact, E enchantment, S sorcery, I instant.
# p/x = power/toughness (verified on mtg.wtf / Scryfall, 11/11/2026; Ob Nixilis checked on playgroup.gg).
# kw: flying, vigilance, first, lifelink, flash.  angel: True if the card is an Angel on the stack.

def C(g, w, p, x, kw="flying", angel=True, **extra):
    d = dict(cost=(g, w), t="C", p=p, x=x, kw=set(kw.split()) if kw else set(), angel=angel)
    d.update(extra)
    return d

def N(t, g, w, **extra):
    d = dict(cost=(g, w), t=t, angel=False)
    d.update(extra)
    return d

CARDS = {
    "Giada, Font of Hope": C(1, 1, 2, 2, "flying vigilance"),
    # --- precon creatures ---
    "Angel of Finality": C(3, 1, 3, 4),
    "Angel of Vitality": C(2, 1, 2, 2),
    "Angel of the Ruins": C(5, 2, 5, 7, artifact=True),
    "Angelic Field Marshal": C(2, 2, 3, 3),
    "Angelic Sleuth": C(2, 1, 2, 3),
    "Archangel of Tithes": C(1, 3, 3, 5),
    "Bishop of Wings": C(0, 2, 1, 4, "", angel=False, cleric=True),
    "Dazzling Angel": C(2, 1, 2, 3),
    "Emeria Shepherd": C(5, 2, 4, 4),
    "Exemplar of Light": C(2, 2, 3, 3),
    "Firemane Commando": C(3, 1, 4, 3),
    "Herald of Eternal Dawn": C(4, 3, 6, 6, "flying flash"),
    "Herald of War": C(3, 2, 3, 3),
    "Inspiring Overseer": C(2, 1, 2, 1, cleric=True),
    "Linvala, the Preserver": C(4, 2, 5, 5),
    "Lyra Dawnbringer": C(3, 2, 5, 5, "flying first lifelink"),
    "Merchant of Truth": C(2, 2, 2, 5),
    "Metallic Mimic": C(2, 0, 2, 1, "", angel=False, artifact=True),
    "Metropolis Reformer": C(2, 1, 2, 3, "flying vigilance", cleric=True),
    "Norn's Choirmaster": C(3, 2, 5, 4, "flying first"),
    "Reya Dawnbringer": C(6, 3, 4, 6),
    "Righteous Valkyrie": C(2, 1, 2, 4, cleric=True),
    "Segovian Angel": C(0, 1, 1, 1, "flying vigilance"),
    "Sephara, Sky's Blade": C(4, 3, 7, 7, "flying lifelink"),
    "Seraph of the Sword": C(3, 1, 3, 3),
    "Serra Avenger": C(0, 2, 3, 3, "flying vigilance"),
    "Speaker of the Heavens": C(0, 1, 1, 1, "vigilance lifelink", angel=False, cleric=True),
    "Starnheim Aspirant": C(2, 1, 2, 2, "", angel=False, cleric=True),
    "Sunblast Angel": C(4, 2, 4, 5),
    "Thraben Watcher": C(2, 2, 2, 2, "flying vigilance"),
    "Vanguard Seraph": C(3, 1, 3, 3),
    "Wojek Investigator": C(2, 1, 2, 4, "flying vigilance"),
    "Youthful Valkyrie": C(1, 1, 1, 1),
    # --- precon noncreatures ---
    "Destroy Evil": N("I", 1, 1, ans={"cre", "ae"}),
    "Fateful Absence": N("I", 1, 1, ans={"cre"}),
    "Invoke the Divine": N("I", 2, 1, ans={"ae"}),
    "Swords to Plowshares": N("I", 0, 1, ans={"cre"}),
    "Valorous Stance": N("I", 1, 1, ans={"cre"}, prot=True),
    "Austere Command": N("S", 4, 2, wipe=True),
    "Cleansing Nova": N("S", 3, 2, wipe=True),
    "Cut a Deal": N("S", 2, 1, draw=3),
    "Day of Judgment": N("S", 2, 2, wipe=True),
    "Defy Death": N("S", 3, 2),
    "Exorcise": N("S", 1, 1, sans={"cre", "ae"}),
    "Secret Rendezvous": N("S", 1, 2, draw=3),
    "Arcane Signet": N("A", 2, 0, rock="W"),
    "Commander's Sphere": N("A", 3, 0, rock="W"),
    "Cryptic Gateway": N("A", 5, 0),
    "Endless Atlas": N("A", 2, 0),
    "Heraldic Banner": N("A", 3, 0, rock="W"),
    "Herald's Horn": N("A", 3, 0),
    "Marble Diamond": N("A", 2, 0, rock="W", etb_tapped=True),
    "Mind Stone": N("A", 2, 0, rock="C"),
    "Patchwork Banner": N("A", 3, 0, rock="W"),
    "Sol Ring": N("A", 1, 0, rock="CC"),
    "Swiftfoot Boots": N("A", 2, 0),
    "Tome of Legends": N("A", 2, 0),
    "Vanquisher's Banner": N("A", 5, 0),
    "Always Watching": N("E", 1, 2),
    "Angelic Destiny": N("E", 2, 2),
    "Court of Grace": N("E", 2, 2),
    "Grasp of Fate": N("E", 1, 2, sans={"cre", "ae", "other"}),
    "Search the Premises": N("E", 3, 1),
    # --- candidates (upgrade guides, EDHREC) ---
    "Path to Exile": N("I", 0, 1, ans={"cre"}),
    "Generous Gift": N("I", 2, 1, ans={"cre", "ae", "other"}),
    "Valkyrie Harbinger": C(4, 2, 4, 5, "flying lifelink", cleric=True),
    "Resplendent Angel": C(1, 2, 3, 3),
    "Lyra, Archangel of Dawn": C(2, 1, 3, 3),
    "Pearl Medallion": N("A", 2, 0),
    "Guide of Souls": C(0, 1, 1, 2, "", angel=False, cleric=True),
    "Soul Warden": C(0, 1, 1, 1, "", angel=False, cleric=True),
    "Folk Hero": N("E", 1, 1),
    "Lightning Greaves": N("A", 2, 0),
    "Flawless Maneuver": N("I", 2, 1),
    "Kindred Judgment": N("S", 5, 2, wipe=True, onesided=True),
    "Ob Nixilis, the Ascended": C(5, 2, 4, 4),
    "Blinding Angel": C(3, 2, 2, 4),
    "Sigarda's Vanguard": C(4, 1, 3, 3, "flying flash"),
    "Felidar Sovereign": C(4, 2, 4, 6, "vigilance lifelink", angel=False),
    "Akroma's Will": N("I", 3, 1),
    "Karmic Guide": C(3, 2, 2, 2),
    "Archangel of Thune": C(3, 2, 3, 4, "flying lifelink"),
    "Avacyn, Angel of Hope": C(5, 3, 8, 8, "flying vigilance"),
    "Serra Ascendant": C(0, 1, 1, 1, "lifelink", angel=False),
    "Smothering Tithe": N("E", 3, 1),
    "Emeria's Call": N("S", 4, 3, mdfc=True),
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
    "Lingering Souls": N("S", 2, 1, spirits=2),            # flashback needs {B}: not usable here
    "Disenchant": N("I", 1, 1, ans={"ae"}),
    "Millikin": N("A", 2, 0, rock="C", etb_tapped=True),   # 0/1 mana creature: modelled as a rock that waits a turn
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
    "Urza's Incubator": N("A", 3, 0),                         # Angel creature spells cost {2} less
    "Starnheim Unleashed": N("S", 2, 2, starn=True),          # 4/4 flying vigilance Angel; foretell {X}{X}{W}: X tokens
    "Herald of the Host": C(3, 2, 4, 4, "flying vigilance", myriad=True),
    "Restoration Angel": C(3, 1, 3, 4, "flying flash"),
    "Serra Angel": C(3, 2, 4, 4, "flying vigilance"),
})
PRICE.update({"Urza's Incubator": None, "Starnheim Unleashed": None, "Herald of the Host": None,
              "Restoration Angel": None, "Serra Angel": None})
CARDS["Leader's Talent"] = N("E", 1, 1)   # Class: L1 attack -> +1/+1 counter; L2 {2}{W}; L3 {3}{W} (oracle mtg.wtf 12/11/2026)
PRICE["Leader's Talent"] = None

# 12/11/2026: physical change Cryptic Gateway -> Lyra, Archangel of Dawn
ACTUAL = swap(ACTUAL, "Cryptic Gateway", "Lyra, Archangel of Dawn")
