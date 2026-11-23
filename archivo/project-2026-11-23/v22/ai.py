import copy, random
from cards import C, RITUAL_NET, VALUE, FAST_NET
from engine import State, Lose, ISIS, NONCRE, COPYWORTHY

ROCKS = {"Fire Diamond", "Sol Ring", "Arcane Signet", "Mind Stone", "Tablet of Discovery", "Chromatic Lantern"}
REDUCERS = {"Ruby Medallion", "The Fire Crystal", "Primal Amulet"}
AMPS = {"Ojer Axonil, Deepest Might", "Harmonic Prodigy", "Tomik, Izzet Sparkmage", "Krark, the Thumbless"}
PINGERS = {"Guttersnipe", "Kessig Flamebreather", "Coruscation Mage", "Erebor Flamesmith", "Thunderdrum Soloist",
           "Fiery Inscription", "Mysidian Elder", "Longshot, Rebel Bowman", "Urabrask"}
ENGINES = {"Storm-Kiln Artist", "Electro, Assaulting Battery", "Ashling, Flame Dancer", "Pyre Rhymer"}
CARDPERMS = {"Wiccan, Young Avenger", "Virtue of Courage", "Party Thrasher", "Emeritus of Conflict", "Count on Luck",
             "The One Ring", "Burning Prophet", "Pinnacle Monk", "Skullclamp"}
RITUALS = {"Manamorphose", "Unexpected Windfall", "Pirate's Pillage", "Rite of Flame", "Seething Song", "Pyretic Ritual", "Desperate Ritual", "Jeska's Will", "Big Score", "Mana Geyser"}
DRAW = {"Crash Through", "Needle Drop", "Faithless Salvaging", "Thrill of Possibility", "Faithless Looting", "Reckless Impulse", "Wrenn's Resolve", "Light Up the Stage", "Demand Answers",
        "Valakut Awakening", "Seize the Spoils", "Tormenting Voice", "Commune with Lava", "Gamble", "Magmatic Insight", "Cathartic Reunion"}
FODDER = {"Skullcrack", "Frost Bite", "Implement of Combustion", "Renegade Map", "Play with Fire", "Unholy Heat", "Abrade", "Fiery Impulse", "Searing Spear", "Demon Bolt", "Mine Collapse", "Shock", "Magma Spray", "Lightning Strike", "Lava Dart", "Burst Lightning", "Spikefield Hazard", "Fireblast", "Strike It Rich", "Lotus Petal", "Gut Shot", "Lightning Bolt", "Vandalblast", "Untimely Malfunction", "Chaos Warp", "Shatterskull Smashing",
          "Sundering Eruption", "Thunderclap", "Lightning Greaves", "Swiftfoot Boots", "Burn, Burn, Tree and Fern",
          "Mishra's Bauble", "Emeritus Bolt", "Boltwave", "Price of Progress"}
CLOSERS = {"Bonus Round", "Fiery Confluence", "Delayed Blast Fireball", "Past in Flames", "Mizzix's Mastery", "Will of the Jeskai",
           "Wheel of Misfortune", "Grapeshot", "Doublecast", "Molten Tide", "Underworld Breach", "Flashback"}
NEVER = {"Fork", "Increasing Vengeance", "Overmaster", "The Flame of Keld", "Blasphemous Act", "Redirect Lightning", "Reverberate", "Reiterate", "Return the Favor", "Simian Spirit Guide", "Lotus Bloom"}

PRIO_ALL = {}
for n in ["Gandalf"]: PRIO_ALL[n] = 1
for n, v in [("Ojer Axonil, Deepest Might", 2), ("Harmonic Prodigy", 2.1), ("Ruby Medallion", 2.2), ("Tomik, Izzet Sparkmage", 2.5),
             ("Krark, the Thumbless", 2.6), ("Artist's Talent", 2.7), ("The Fire Crystal", 3.6), ("Sol Ring", 1.5),
             ("Guttersnipe", 3), ("Longshot, Rebel Bowman", 3.05), ("Kessig Flamebreather", 3.1), ("Coruscation Mage", 3.1),
             ("Mysidian Elder", 3.15), ("Fiery Inscription", 3.2), ("Erebor Flamesmith", 3.3), ("Thunderdrum Soloist", 3.3),
             ("Lindblum Siege", 3.4), ("Storm-Kiln Artist", 3.5), ("Electro, Assaulting Battery", 3.5), ("Urabrask", 3.7),
             ("Primal Amulet", 4.2), ("Ashling, Flame Dancer", 4.0), ("Pyre Rhymer", 4.5), ("Molten Tide", 4.6),
             ("Wiccan, Young Avenger", 4.8), ("Virtue of Courage", 4.9), ("Party Thrasher", 5.5), ("Emeritus of Conflict", 5.2),
             ("Doublecast", 5.9)]:
    PRIO_ALL[n] = v
for n in RITUALS: PRIO_ALL[n] = 6
for n in DRAW: PRIO_ALL[n] = 6.5
PRIO_ALL["Gamble"] = 6.4
for n in ["Past in Flames", "Will of the Jeskai", "Mizzix's Mastery", "Underworld Breach", "Flashback"]: PRIO_ALL[n] = 7
PRIO_ALL["Bonus Round"] = 5.8
for n in ["Fiery Confluence", "Delayed Blast Fireball"]: PRIO_ALL[n] = 7.5
for n, v in [("Neheb, the Eternal", 2.4), ("Runaway Steam-Kin", 3.4), ("Solphim, Mayhem Dominus", 2.04), ("Torbran, Thane of Red Fell", 2.05), ("Birgi, God of Storytelling", 2.3), ("Thermo-Alchemist", 3.2),
             ("Electrostatic Field", 3.3), ("Firebrand Archer", 3.3), ("Lotus Petal", 1.6), ("Mox Amber", 1.6),
             ("Mishra's Bauble", 1.7), ("Strike It Rich", 1.8), ("Fireblast", 9.6),
             ("Chrome Mox", 1.6), ("Mox Diamond", 1.6), ("Mana Vault", 1.5), ("Grim Monolith", 1.55)]:
    PRIO_ALL[n] = v
for n in FODDER | ROCKS | CARDPERMS: PRIO_ALL.setdefault(n, 8)
PRIO_ALL["Wheel of Misfortune"] = 9
PRIO_ALL["Harnfel, Horn of Bounty"] = 7.2
PRIO_ALL["Embereth Blaze"] = 8
PRIO_ALL["Flameshape"] = 0.95
PRIO_ALL["Grapeshot"] = 10

PRIO_DEV = dict(PRIO_ALL)
for n, v in [("Sol Ring", 0.5), ("Arcane Signet", 1.0),
             ("Ruby Medallion", 0.9), ("Mind Stone", 1.1), ("Tablet of Discovery", 1.2), ("Chromatic Lantern", 1.3),
             ("The Fire Crystal", 1.6), ("Primal Amulet", 1.8), ("The One Ring", 1.7), ("Count on Luck", 2.9), ("Skullclamp", 2.0),
             ("Lightning Greaves", 7), ("Swiftfoot Boots", 7), ("Burn, Burn, Tree and Fern", 7.5), ("Mox Amber", 0.6),
             ("Chrome Mox", 0.6), ("Mox Diamond", 0.6), ("Mana Vault", 0.7), ("Grim Monolith", 0.75)]:
    PRIO_DEV[n] = v
for n in CARDPERMS: PRIO_DEV.setdefault(n, 5)
PRIO_DEV["Harnfel, Horn of Bounty"] = 2.4
PRIO_DEV["Flameshape"] = 0.95
FC_PRIO = 2.2
ARTIST_LV = {False: {1: 1.0, 2: 2.5}, True: {1: 1.0, 2: 2.5}}
DFC_POLICY = {"Birgi, God of Storytelling": "front"}
FAST_OPEN = [True]
MULL_EXPL = [True]
BLAZE_DEV = [True]
PRIO_NOISE = [None]
BLAZE_ANY = [True]
TREASURE_DRAW = {"Big Score", "Unexpected Windfall", "Pirate's Pillage", "Strike It Rich"}
DEV_EXCL_C = (RITUALS - TREASURE_DRAW) | (FODDER - {"Lightning Greaves", "Swiftfoot Boots", "Burn, Burn, Tree and Fern"} - TREASURE_DRAW) | CLOSERS | NEVER
CREATURES_EXCEPT_G = {n for n, d in C.items() if d["t"] == "creature" and n != "Gandalf"}
DEV_EXCL_B = DEV_EXCL_C | CREATURES_EXCEPT_G | {"Fiery Inscription", "Lindblum Siege"}


def candidates(s):
    out = []
    for c in s.hand:
        out.append((c, "hand", None))
    for e in s.exile_play:
        if e[1] >= s.turn:
            out.append((e[0], "exile", None))
    if s.wizard_in_play():
        for c in s.fs_exile:
            out.append((c, "fs", None))
    nm = sum(1 for l in s.lands if l.get("mtn"))
    for c in list(out):
        if c[0] == "Fireblast" and nm >= 2:
            out.append(("Fireblast", c[1], "sac2"))
        if c[0] == "Mine Collapse" and nm >= 1:
            out.append(("Mine Collapse", c[1], "sac1"))
        if c[0] == "Thunderclap" and nm >= 1:
            out.append(("Thunderclap", c[1], "sac1"))
    for c in ([] if getattr(s, "gy_locked", False) else s.gy):
        if c == "Faithless Looting":
            out.append((c, "gy", (2, 1)))
        elif c == "Strike It Rich":
            out.append((c, "gy", (2, 1)))
        elif c == "Lava Dart" and nm >= 1:
            out.append((c, "gy", "sac1"))
        elif c == "Past in Flames":
            out.append((c, "gy", (4, 1)))
        elif (s.pif or getattr(s, "pif_any", False)) and ISIS(c):
            out.append((c, "gy", None))
    if getattr(s, "breach", False) and len(s.gy) >= 4 and not getattr(s, "gy_locked", False):
        for c in sorted(set(s.gy)):
            if ((ISIS(c) and c not in ("Past in Flames",)) or (BREACH_PERMS[0] and c in BREACH_PERM_SET)) \
                    and (not BREACH_PERMS[0] or s.escape_ok(c)):
                out.append((c, "gy", "escape"))
    if s.gandalf == "cmd":
        out.append(("Flameshape", "cmd", None))
        out.append(("Gandalf", "cmd", None))
    elif s.gandalf == "exile":
        out.append(("Gandalf", "cmd", None))
    if s.emeritus_prep and s.has("Emeritus of Conflict"):
        out.append(("Emeritus Bolt", "none", None))
    if s.pyre_prep and s.has("Pyre Rhymer"):
        out.append(("Molten Tide", "none", None))
    if s.dbf_foretold:
        out.append(("Delayed Blast Fireball", "foretell", (4, 2)))
    if "Virtue of Courage" in s.hand and BLAZE_ANY[0]:
        out.append(("Embereth Blaze", "adv_virtue", None))
    if "Birgi, God of Storytelling" in s.hand:
        pol = DFC_POLICY.get("Birgi, God of Storytelling", "front")
        if pol == "auto":
            pol = "back" if (s.turn >= 5 and len(s.lands) >= 5) else "front"
        if pol == "back":
            out = [o for o in out if not (o[0] == "Birgi, God of Storytelling" and o[1] == "hand")]
            out.append(("Harnfel, Horn of Bounty", "dfc_birgi", None))
    return out


def try_land(s):
    if s.land_played:
        return
    def play(name, zone, prod="R", tapped=False, mtn=False):
        if zone == "hand":
            s.hand.remove(name)
        elif zone == "fs":
            s.fs_exile.remove(name)
        else:
            for e in s.exile_play:
                if e[0] == name:
                    s.exile_play.remove(e); break
        s.lands.append(dict(name=name, prod=prod, tapped=tapped, mtn=mtn))
        s.land_played = True
    pool = [(c, "hand") for c in s.hand] + [(e[0], "exile") for e in s.exile_play if e[1] >= s.turn]
    if s.wizard_in_play():
        pool += [(c, "fs") for c in s.fs_exile]
    real = [(c, z) for c, z in pool if C[c]["t"] == "land" and c != "Lindblum, Industrial Regency"]
    real.sort(key=lambda x: (x[1] != "exile", x[0] != "Mountain"))
    if real:
        c, z = real[0]
        play(c, z, prod=C[c]["prod"], mtn=C[c].get("mtn", False)); return
    lind = [(c, z) for c, z in pool if c == "Lindblum, Industrial Regency"]
    if lind:
        play(*lind[0], prod="R", tapped=True); return
    if len(s.lands) < 6:
        for m in ["Spikefield Hazard", "Sundering Eruption", "Shatterskull Smashing", "Valakut Awakening", "Pinnacle Monk"]:
            for c, z in pool:
                if c == m:
                    play(c, z, prod="R", tapped=(m in ("Valakut Awakening", "Spikefield Hazard"))); return


def total_mana(s, isis=True):
    R, Cc = s.avail(isis)
    return R + Cc


BREACH_PERMS = [True]
BREACH_PERM_SET = {"Lotus Petal", "Mox Amber", "Sol Ring", "Arcane Signet", "Tablet of Discovery", "Mishra's Bauble"}
GS_EARLY = [True]
GS_REMOVAL = [True]


def grapeshot_early(s):
    if len(s.alive()) <= 1:
        return False
    for name, zone, alt in candidates(s):
        if name != "Grapeshot":
            continue
        g, r = s.cost(name, alt)
        if not s.can_pay(g, r, True):
            return False
        n, per = s.spells + 1, s.mod(1, True)
        kill = [i for i in s.alive() if s.opp[i] <= n * per]
        if not kill:
            return False
        K = getattr(s, "K", None) or [99, 99, 99]
        tgt = min(kill, key=lambda i: (K[i], s.opp[i]))
        old = getattr(s, "focus_idx", None); s.focus_idx = tgt
        s.cast(name, zone, alt=alt)
        s.focus_idx = old
        s.gs_early = getattr(s, "gs_early", 0) + 1
        return True
    return False


def act_once(s, mode, excl):
    if "Lotus Bloom" in s.hand:            # 22/11: se suspende apenas se puede (no cuesta mana)
        s.suspend_bloom()
        return True
    if mode == "allin" and GS_EARLY[0] and grapeshot_early(s):
        return True
    prio = PRIO_ALL if mode == "allin" else PRIO_DEV
    if getattr(s, "gy_locked", False) and s.gy:
        s.exiled += s.gy; s.gy = []
    cands = []
    for name, zone, alt in candidates(s):
        reload = name in ("Will of the Jeskai", "Wheel of Misfortune") and len(s.hand) <= 2 and mode != "allin"
        if (name in excl and not reload) or name in NEVER or C[name]["t"] == "land":
            continue
        if name == "Flameshape":
            if mode == "allin":
                continue
            tm = total_mana(s)
            fast = sum(FAST_NET[c] for c in s.hand if c in FAST_NET) if FAST_OPEN[0] else 0
            if not (tm == 2 or tm >= 5 or (tm < 2 and tm + fast >= 2)):
                continue
        if name == "Lindblum, Industrial Regency":
            continue
        if name == "Embereth Blaze" and mode != "allin":
            if not BLAZE_DEV[0] or total_mana(s) < 2 + sum(s.cost("Virtue of Courage")):
                continue
        if name in ("Past in Flames", "Will of the Jeskai") and sum(1 for c in s.gy if ISIS(c)) < 3:
            if not (name == "Will of the Jeskai" and len(s.hand) <= 1):
                continue
        if name == "Mizzix's Mastery" and sum(1 for c in s.gy if ISIS(c)) < 2:
            continue
        if name == "Flashback" and not any(ISIS(c) and c not in ("Flashback", "Mizzix's Mastery") and (c in RITUAL_NET or c in COPYWORTHY or c in ("Past in Flames", "Will of the Jeskai")) for c in s.gy):
            continue
        if name == "Underworld Breach" and (len(s.gy) < 6 or sum(1 for c in s.gy if ISIS(c)) < 3):
            continue
        if name == "Wheel of Misfortune" and len(s.hand) > 2:
            continue
        if name == "Magmatic Insight" and not any(C[c]["t"] == "land" for c in s.hand):
            continue
        if name == "Cathartic Reunion" and len(s.hand) < 3:
            continue
        if name == "Molten Tide" and sum(1 for l in s.lands if l.get("mtn") and not l["tapped"]) < 3:
            continue
        if name == "Commune with Lava":
            if total_mana(s) < 4:
                continue
        if name == "Gamble" and len(s.hand) < 3 and mode != "allin":
            continue
        if name == "Mox Diamond" and not any(C[c]["t"] == "land" for c in s.hand):
            continue
        if name == "Chrome Mox" and not any(C[c]["t"] != "land" and c != "Chrome Mox" for c in s.hand):
            continue
        pr = prio.get(name, 8)
        if PRIO_NOISE[0] is not None and mode == "allin":
            pr += PRIO_NOISE[0].get(name, 0)
        if name == "Mana Geyser" and s.geyser() < 5:
            pr = 8.5
        if name == "Mizzix's Mastery":
            g, r = s.cost(name, (5, 3))
            if s.can_pay(g, r, True):
                cands.append((pr, name, zone, (5, 3), "over")); continue
            if mode != "allin":
                continue
        cands.append((pr, name, zone, alt, None))
    if "Lindblum, Industrial Regency" in s.hand and "Lindblum Siege" not in excl and (s.land_played or any(C[c]["t"] == "land" and c != "Lindblum, Industrial Regency" for c in s.hand)):
        cands.append((prio.get("Lindblum Siege", 3.4), "Lindblum Siege", "lind", None, None))
    if s.has("Artist's Talent") and 1 <= s.artist < 3 and not (mode != "allin" and s.artist >= 2 and "ArtistL3" in excl):
        cands.append((ARTIST_LV[mode == "allin"][s.artist], "Artist's Talent", "level", None, None))
    if s.temple_ready():
        cands.append((prio.get("Ojer Axonil, Deepest Might", 2), "Ojer Axonil, Deepest Might", "temple", None, None))
    if mode == "allin" and s.has("The Fire Crystal"):
        cands.append((FC_PRIO, "The Fire Crystal", "fc_copy", None, None))
    cands.sort(key=lambda x: x[0])
    for pr, name, zone, alt, tag in cands:
        if zone == "temple":
            if s.temple_flip():
                return True
            continue
        if zone == "fc_copy":
            if s.fire_crystal():
                return True
            continue
        if zone == "level":
            if s.can_pay(2, 1):
                s.pay(2, 1); s.artist += 1
                return True
            continue
        g, r = s.cost(name, alt)
        if name == "Commune with Lava":
            tm = total_mana(s)
            s._x = tm - r - g
            g += s._x
        if not s.can_pay(g, r, ISIS(name)):
            continue
        if mode == "allin" and ISIS(name) and s.key_spell(name) and not getattr(s, "overmaster", False):
            for oz in ("hand", "exile"):
                if s.in_zone("Overmaster", oz):
                    og, orr = s.cost("Overmaster")
                    if s.can_pay(og + g, orr + r, True):
                        s.cast("Overmaster", oz)
                        return True
        if name in COPYWORTHY and mode == "allin":
            for dz in ("hand", "exile"):
                if s.in_zone("Doublecast", dz):
                    dg, dr = s.cost("Doublecast")
                    if s.can_pay(dg + g, dr + r, True):
                        s.cast("Doublecast", dz)
                        return True
        s._mz_over = (tag == "over")
        if zone == "adv_virtue":
            s.hand.remove("Virtue of Courage"); s._adventure = True
            s.cast("Embereth Blaze", "none")
            return True
        if zone == "dfc_birgi":
            s.hand.remove("Birgi, God of Storytelling")
            s.cast("Harnfel, Horn of Bounty", "none")
            return True
        if name == "Lindblum Siege":
            s.hand.remove("Lindblum, Industrial Regency")
            s.cast("Lindblum Siege", "none")
            return True
        if name == "Coruscation Mage" and s.can_pay(g + 2, r):
            s._offspring = True
            s.cast(name, zone, alt=alt, extra=2)
            return True
        if name == "Commune with Lava":
            s.cast(name, zone, xval=s._x)
            return True
        if name in ("Gandalf", "Flameshape"):
            s.cast(name, "none")
            return True
        if name == "Emeritus Bolt":
            s.emeritus_prep = False
        if name == "Molten Tide":
            s.pyre_prep = False
        s.cast(name, zone, alt=alt)
        return True
    # activations
    if mode == "allin" and any(p["name"] == "Grinning Ignus" for p in s.perms) and s.can_pay(0, 1) and \
       ("Grapeshot" in s.hand or ("Grapeshot" in s.gy and (s.pif or getattr(s, "breach", False))) or s.has("Birgi, God of Storytelling") or s.has("Aetherflux Reservoir")) and getattr(s, "_ign_turn", -1) != s.turn:
        s._ign_turn = s.turn
        if s.ignus_loop():
            return True
    if s.harnfel(mode):
        return True
    if mode == "allin" and s.crown_loop():
        return True
    if mode == "allin" and getattr(s, "implements", 0) and s.can_pay(1, 0):
        s.use_implements(); return True
    if mode != "allin" and "The Flame of Keld" in s.hand and len(s.hand) <= 2 and s.can_pay(*s.cost("The Flame of Keld")):
        s.cast("The Flame of Keld", "hand"); return True
    if s.has("Urabrask") and getattr(s, "isis_turn", 0) >= 3 and s.urabrask_activate():
        return True
    if s.has("Artist's Talent") and 1 <= s.artist < 3 and not (mode != "allin" and s.artist >= 2 and "ArtistL3" in excl):
        if s.can_pay(2, 1):
            s.pay(2, 1); s.artist += 1
            return True
    if s.clamp():
        return True
    if mode != "allin" and not NO_RIT_DEV[0]:
        best = None
        for name, zone, alt in candidates(s):
            if name in RITUAL_NET or name == "Big Score" or (FAST_OPEN[0] and name in FAST_NET):
                g, r = s.cost(name, alt)
                if s.can_pay(g, r, True):
                    net = (FAST_NET[name] if name in FAST_NET else RITUAL_NET.get(name, 2) - g - r)
                    if net > 0:
                        best = (name, zone, alt, net); break
        if best:
            tm = total_mana(s)
            for pr, name, zone, alt, tag in cands:
                g, r = s.cost(name, alt)
                if g + r <= tm + best[3] and not s.can_pay(g, r, ISIS(name)) and pr < 6:
                    s.cast(best[0], best[1], alt=best[2])
                    return True
    return False


URA_PLAN = [True]
def run_main(s, mode, excl=frozenset()):
    s.mode = mode
    if mode != "allin" and URA_PLAN[0] and s.has("Urabrask") and not getattr(s, "great_work", []):
        cheap = [c for c in s.hand if ISIS(c) and (c in RITUALS or c in FODDER or c in DRAW) and c not in NEVER]
        if len(cheap) + getattr(s, "isis_turn", 0) >= 3:
            excl = frozenset(set(excl) - set(cheap))
    while act_once(s, mode, excl):
        if s.dead():
            return
    if s.has("Neheb, the Eternal") and getattr(s, "neheb_turn", 0) != s.turn and s.dmg_turn > 0:
        s.neheb_turn = s.turn
        s.pool["R"] += s.dmg_turn
        while act_once(s, mode, excl):
            if s.dead():
                return


def end_step(s):
    s.mode = "dev"
    if "Delayed Blast Fireball" in s.hand and s.can_pay(2, 0):
        s.pay(2, 0); s.hand.remove("Delayed Blast Fireball"); s.dbf_foretold += 1
    if any(l["name"] == "War Room" and not l["tapped"] for l in s.lands):
        wr = [l for l in s.lands if l["name"] == "War Room" and not l["tapped"]][0]
        wr["tapped"] = True
        if s.can_pay(3, 0):
            s.pay(3, 0); s.draw(1)
        else:
            wr["tapped"] = False
    for p in list(s.perms):
        if p["name"] == "Mind Stone" and len(s.lands) >= 6:
            p["tapped"] = True
            if s.can_pay(1, 0):
                s.pay(1, 0); s.perms.remove(p); s.draw(1)
            else:
                p["tapped"] = False
    while len(s.hand) > 7:
        s.discard(1)


def mulligan(s):
    def ok(h, lo=3, hi=5):
        L = sum(1 for c in h if C[c]["t"] == "land" or C[c].get("mdfc"))
        rocks = sum(1 for c in h if c in ("Sol Ring", "Arcane Signet", "Mind Stone"))
        if MULL_EXPL[0] and L == 1 and "Sol Ring" in h and any(c in h for c in ("Arcane Signet", "Lotus Petal", "Mind Stone", "Mox Amber")):
            return True
        return lo <= L <= hi or (L == 2 and rocks >= 1)
    s.draw(7)
    if ok(s.hand):
        return
    s.lib += s.hand; s.hand = []; s.rng.shuffle(s.lib); s.draw(7)
    if ok(s.hand, 2, 5):
        return
    s.lib += s.hand; s.hand = []; s.rng.shuffle(s.lib); s.draw(7)
    worst = s.junk(s.hand, 1)[0]; s.hand.remove(worst); s.lib.append(worst)


PING_SET = PINGERS | {"Wizard token"}
NO_RIT_DEV = [False]


def play_game(deck, strat, seed, max_turn=14):
    """goldfish: sin interaccion; devuelve (turno del kill, estado)"""
    rng = random.Random(seed)
    s = State(deck, rng, strat)
    mulligan(s)
    excl = DEV_EXCL_C
    try:
        for t in range(1, max_turn + 1):
            s.turn = t
            for l in s.lands: l["tapped"] = False
            for p in s.perms:
                if not p.get("nountap"): p["tapped"] = False
            s.pool = {"R": s.pool["R"] if s.keeps_red() else 0, "C": 0}
            s.spells = 0; s.dmg_turn = 0; s.molten = False; s.dcast = 0; s.ash_res = 0
            s.land_played = False; s.pif = False; s.casts_guard = 0; s.breach_cleanup()
            s.inst_used = False
            if getattr(s, "rebound", 0):
                n_rb = s.rebound; s.rebound = 0
                for _ in range(n_rb):
                    s.cast("Faithless Salvaging", "none", free=True)
                    s._rebound_exile = False
                    s.gy.append("Faithless Salvaging")
            if s.bauble_draws:
                s.draw(s.bauble_draws); s.bauble_draws = 0
            for _ in range(s.count("Count on Luck")):
                s.impulse(1, t)
            s.draw(1)
            s.bloom_upkeep()
            try_land(s)
            if s.has("The One Ring"):
                s.ring += 1; s.draw(s.ring)
            s.isis_turn = 0; s.pif_any = False
            s.urabrask_upkeep(); s.keld_upkeep()
            for st in s.sagas:
                if t - st in (2, 3):
                    s.pool["R"] += 1
            try_land(s)
            k = copy.deepcopy(s); k.ix = None; k.log = None
            try:
                run_main(k, "allin")
            except Lose:
                pass
            if k.dead():
                return t, k
            run_main(s, "dev", excl)
            try_land(s)
            if s.dead():
                return t, s
            end_step(s)
            s.bank_red()
    except Lose:
        return 99, s
    return 99, s
