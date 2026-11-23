import random, copy
from cards import C, RITUAL_NET, VALUE

C["Gandalf"] = dict(t="creature", g=2, r=1, red=True, wiz=True)
C["Flameshape"] = dict(t="sorcery", g=1, r=1, red=True)
C["Emeritus Bolt"] = dict(t="instant", g=0, r=1, red=True)
C["Molten Tide"] = dict(t="instant", g=0, r=1, red=True)
C["Lindblum Siege"] = dict(t="instant", g=2, r=1, red=True)
THREATS = {"Guttersnipe", "Kessig Flamebreather", "Coruscation Mage", "Erebor Flamesmith", "Thunderdrum Soloist",
           "Fiery Inscription", "Mysidian Elder", "Longshot, Rebel Bowman", "Urabrask", "Ojer Axonil, Deepest Might",
           "Harmonic Prodigy", "Tomik, Izzet Sparkmage", "Krark, the Thumbless", "Storm-Kiln Artist"}
LEGENDS = {"Neheb, the Eternal", "Gandalf", "Ojer Axonil, Deepest Might", "Krark, the Thumbless", "Tomik, Izzet Sparkmage", "Longshot, Rebel Bowman",
           "Electro, Assaulting Battery", "Urabrask", "Ashling, Flame Dancer", "Wiccan, Young Avenger", "Torbran, Thane of Red Fell",
           "Birgi, God of Storytelling", "Solphim, Mayhem Dominus"}
VISIBLE = THREATS | {"Neheb, the Eternal", "Runaway Steam-Kin", "Gandalf", "Torbran, Thane of Red Fell", "Birgi, God of Storytelling", "Solphim, Mayhem Dominus",
                     "Firebrand Archer", "Electrostatic Field", "Thermo-Alchemist", "Electro, Assaulting Battery",
                     "Ashling, Flame Dancer", "Urabrask", "Burning Prophet", "Emeritus of Conflict"}
THREAT_RANK = {n: i for i, n in enumerate(["Ojer Axonil, Deepest Might", "Neheb, the Eternal", "Harmonic Prodigy", "Torbran, Thane of Red Fell",
               "Solphim, Mayhem Dominus", "Birgi, God of Storytelling", "Longshot, Rebel Bowman", "Krark, the Thumbless",
               "Guttersnipe", "Storm-Kiln Artist", "Tomik, Izzet Sparkmage", "Kessig Flamebreather", "Coruscation Mage",
               "Fiery Inscription", "Firebrand Archer", "Thermo-Alchemist", "Electrostatic Field", "Erebor Flamesmith",
               "Thunderdrum Soloist", "Mysidian Elder", "Electro, Assaulting Battery", "Ashling, Flame Dancer", "Urabrask", "Gandalf"])}
# ---- amenaza percibida (14/11/2026, estructura de la IA de Forge) ----
THREAT_W = {  # v2 14/11 (Juan): amplificadores y motores de storm > pingers; Gandalf es un pinger mas
            "Harmonic Prodigy": 0.6, "Birgi, God of Storytelling": 0.6, "Solphim, Mayhem Dominus": 0.6,
            "Ojer Axonil, Deepest Might": 0.6, "Neheb, the Eternal": 0.6,
            "Torbran, Thane of Red Fell": 0.5, "Electro, Assaulting Battery": 0.5, "Ashling, Flame Dancer": 0.5,
            "Storm-Kiln Artist": 0.5,
            "Gandalf": 0.4, "Tomik, Izzet Sparkmage": 0.4, "Guttersnipe": 0.4, "Runaway Steam-Kin": 0.4}
THREAT_W_DEFAULT = 0.3
COUNTER_KEYS = {"Mana Geyser", "Underworld Breach", "Bonus Round", "Fiery Emancipation", "Ruby Medallion"}
COUNTER_BY_CMC = {0: 0.02, 1: 0.02, 2: 0.05, 3: 0.15}
COUNTER_HI = 0.3
WIPE_MARGIN = 1.5
KEEP_LAST = 0.4
REM_THR = 0.5
KEY_CLOSERS = {"Mizzix's Mastery", "Past in Flames", "Will of the Jeskai", "Jeska's Will", "Fiery Confluence", "Wheel of Misfortune", "The One Ring"}
KEY_AMPS = {"Ojer Axonil, Deepest Might", "Harmonic Prodigy", "Torbran, Thane of Red Fell", "Krark, the Thumbless",
            "Birgi, God of Storytelling", "Solphim, Mayhem Dominus"}
DEV_TUTOR = ["Harmonic Prodigy", "Ojer Axonil, Deepest Might", "Ruby Medallion", "Past in Flames"]
SCEN = {"geyser_f": 0.5, "jeska_top": 7, "jeska_min": 2}
SPECIAL = {"Flameshape", "Emeritus Bolt", "Molten Tide", "Lindblum Siege", "Gandalf", "Embereth Blaze"}
BR_MIZZIX = [True]
AMP_SET = {"Ojer Axonil, Deepest Might", "Harmonic Prodigy", "Fiery Emancipation", "Tomik, Izzet Sparkmage"}
ISIS = lambda n: C[n]["t"] in ("instant", "sorcery")
NONCRE = lambda n: C[n]["t"] not in ("creature", "land")
COPYWORTHY = {"Unexpected Windfall": 3, "Seething Song": 5, "Jeska's Will": 5, "Fiery Confluence": 6, "Mana Geyser": 6, "Big Score": 3,
              "Pyretic Ritual": 2, "Desperate Ritual": 2}
TOKEN = "Wizard token"
NB_FRAC = [0.5]   # 22/11: fraccion de tierras no basicas de los rivales (Price of Progress); la mesa la fija con ix["nb"]


class Lose(Exception):
    pass


class State:
    def __init__(self, deck, rng, strat):
        self.rng = rng
        self.strat = strat
        self.lib = deck[:]
        rng.shuffle(self.lib)
        self.hand, self.gy, self.exile_play, self.fs_exile, self.exiled = [], [], [], [], []
        self.lands, self.perms = [], []
        self.treasures = 0
        self.pool = {"R": 0, "C": 0}
        self.opp = [40, 40, 40]
        self.gandalf = "cmd"
        self.turn = 0
        self.spells = 0
        self.land_played = False
        self.molten = False
        self.dcast = 0
        self.artist = 0
        self.amulet = 0
        self.ash_res = 0
        self.emeritus_prep = False
        self.pyre_prep = False
        self.dbf_foretold = 0
        self.ring = 0
        self.ring_used = False
        self.pif = False
        self.bauble_draws = 0
        self.sagas = []
        self.casts_guard = 0
        self.dmg_turn = 0
        self.log = None
        self.first_threat = None
        self.ix = None
        self.cmd_casts = 0
        self.counter_ready = False
        self.inst_used = False
        self.hist = []
        self.mode = "dev"
        self.blooms = []

    def __deepcopy__(self, memo):
        n = copy.copy(self)
        for k in ("lib", "hand", "gy", "fs_exile", "exiled", "opp", "sagas", "hist", "diag", "cf", "blooms"):
            if hasattr(self, k):
                setattr(n, k, list(getattr(self, k)))
        n.exile_play = [list(e) for e in self.exile_play]
        n.lands = [dict(l) for l in self.lands]
        n.perms = [dict(p) for p in self.perms]
        n.pool = dict(self.pool)
        n.log = list(self.log) if self.log is not None else None
        return n

    # ---------------- helpers ----------------
    def L(self, *a):
        if self.log is not None:
            self.log.append(" ".join(str(x) for x in a))

    def has(self, name):
        return any(p["name"] == name for p in self.perms)

    def count(self, name):
        return sum(1 for p in self.perms if p["name"] == name)

    def wizard_in_play(self):
        return any(p.get("wiz") for p in self.perms)

    def mult(self, p):
        if not (p.get("wiz") or p.get("shaman")):
            return 1
        n = sum(1 for q in self.perms if q["name"] == "Harmonic Prodigy" and q is not p)
        return 1 + n

    def alive(self):
        return [i for i in range(3) if self.opp[i] > 0]

    def dead(self):
        return all(x <= 0 for x in self.opp)

    def draw(self, n=1):
        for _ in range(n):
            if not self.lib:
                raise Lose()
            self.hand.append(self.lib.pop(0))

    def impulse(self, n, expiry):
        for _ in range(n):
            if not self.lib:
                return
            self.exile_play.append([self.lib.pop(0), expiry])

    def need_wipe(self):
        if not self.ix:
            return False
        t = self.turn - getattr(self, "opp_wiped_t", 0)
        mu = min(self.ix.get("opp_v0", 0.3) + self.ix.get("opp_dv", 0.1) * t, self.ix.get("opp_vmax", 1.2))
        soon = any(k <= self.turn + 1 for k in getattr(self, "K", [99]))
        return (mu >= 0.6 or soon) and self.board_value() < 1.0

    def creatures_in_play(self):
        ours = sum(1 for p in self.perms if C.get(p["name"], {}).get("t") == "creature" or p["name"] in ("Gandalf", TOKEN) or p.get("token"))
        if not self.ix:
            return ours
        t = self.turn - getattr(self, "opp_wiped_t", 0)
        return ours + len(self.alive()) * min(4, int(0.5 * t))

    def escape_keep(self, c):
        if C.get(c, {}).get("t") == "land":
            return 0
        if c == "Lotus Petal":
            return 10
        if c == "Grapeshot":
            return 9
        if c in RITUAL_NET or c in ("Rite of Flame", "Mana Geyser", "Jeska's Will"):
            return 8
        if c in ("Unexpected Windfall", "Big Score", "Seize the Spoils", "Pirate's Pillage", "Faithless Looting",
                 "Thrill of Possibility", "Tormenting Voice", "Demand Answers", "Reckless Impulse", "Light Up the Stage",
                 "Wrenn's Resolve", "Needle Drop", "Crash Through", "Magmatic Insight", "Cathartic Reunion"):
            return 7
        if ISIS(c):
            g, r = C[c]["g"], C[c]["r"]
            return 6 if g + r <= 1 else (5 if g + r <= 2 else 3)
        if c in ("Mox Amber", "Sol Ring", "Arcane Signet", "Mishra's Bauble"):
            return 4
        return 1

    def escape_ok(self, c):
        others = sorted([x for x in self.gy if x is not c], key=self.escape_keep)
        if c in others: others.remove(c)
        if len(others) < 3:
            return False
        worst3 = max(self.escape_keep(x) for x in others[:3])
        limit = 6 if c == "Lotus Petal" else self.escape_keep(c)
        return worst3 < limit or (c == "Grapeshot" and worst3 <= 9)

    def card_value(self, c):
        if c == "Blasphemous Act":
            return 6 if self.need_wipe() else 0
        if c == "Redirect Lightning":
            return 6 if any(self.threat_w(p) >= 0.5 for p in self.perms if p["name"] in VISIBLE) else 1
        return VALUE.get(c, 5)

    def junk(self, cards, k):
        lands_bf = len(self.lands)
        def val(c):
            if C[c]["t"] == "land":
                return 2 if lands_bf + sum(1 for x in self.hand if C[x]["t"] == "land") > 7 else (6 if lands_bf < 5 else 3)
            return self.card_value(c)
        return sorted(cards, key=val)[:k]

    def discard(self, k):
        for c in self.junk(self.hand, k):
            self.hand.remove(c)
            self.gy.append(c)

    # ---------------- damage ----------------
    def mod(self, a, red):
        bonus = (2 if (red and self.turn in [k + 2 for k in getattr(self, "keld", [])]) else 0) + (1 if self.has("Tomik, Izzet Sparkmage") else 0) + (2 if self.artist >= 3 else 0) + (2 if (red and self.has("Torbran, Thane of Red Fell")) else 0) + self.count("Fated Firepower")
        effs = []
        if bonus: effs.append(lambda x: x + bonus)
        if self.has("Solphim, Mayhem Dominus"): effs.append(lambda x: 2 * x)
        if self.has("Fiery Emancipation"): effs.append(lambda x: 3 * x)
        if red and self.has("Ojer Axonil, Deepest Might"): effs.append(lambda x: max(x, 4))
        if len(effs) <= 1:
            return effs[0](a) if effs else a
        import itertools
        best = None
        for perm in itertools.permutations(effs):
            x = a
            for f in perm: x = f(x)
            best = x if best is None else min(best, x)
        return best

    def hit(self, i, a, red):
        d = self.mod(a, red)
        self.opp[i] -= d
        self.dmg_turn += d
        if self.has("Virtue of Courage") and len(self.lib) > d + 15:
            self.impulse(d, self.turn)

    def dmg_each(self, a, red=True):
        for i in self.alive():
            self.hit(i, a, red)

    def dmg_target(self, a, red=True):
        al = self.alive()
        if al:
            f = getattr(self, "focus_idx", None)
            i = f if (f is not None and f in al) else max(al, key=lambda j: self.opp[j])
            self.hit(i, a, red)

    # ---------------- mana ----------------
    def r_sources(self, isis):
        out = []
        for l in self.lands:
            if not l["tapped"] and l["prod"] in ("R", "A"):
                amt = 2 if (self.molten and l.get("mtn")) else 1
                out.append(("land", l, amt))
        for p in self.perms:
            if p["tapped"]:
                continue
            if p["name"] in ("Arcane Signet", "Fire Diamond", "Chromatic Lantern"):
                out.append(("rock", p, 1))
            if p["name"] == "Tablet of Discovery":
                out.append(("rock", p, 2 if isis else 1))
            if p["name"] == "Mox Amber" and any(q["name"] in LEGENDS for q in self.perms):
                out.append(("rock", p, 1))
            if p["name"] in ("Chrome Mox", "Mox Diamond") and p.get("live"):
                out.append(("rock", p, 1))
            if p["name"] == "Lotus Bloom" and self.mode == "allin":
                out.append(("bloom", p, 3))
        if self.mode == "allin":
            for _ in range(self.hand.count("Simian Spirit Guide")):
                out.append(("ssg", {"name": "SSG"}, 1))
        return out

    def c_sources(self):
        out = []
        for l in self.lands:
            if not l["tapped"] and l["prod"] == "C":
                out.append(("land", l, 1))
            if not l["tapped"] and l["prod"] == "C2":
                out.append(("land", l, 2))
        for p in self.perms:
            if p["tapped"]:
                continue
            if p["name"] == "Sol Ring":
                out.append(("rock", p, 2))
            if p["name"] == "Mind Stone":
                out.append(("rock", p, 1))
            if p["name"] in ("Mana Vault", "Grim Monolith"):
                out.append(("rock", p, 3))
        return out

    def avail(self, isis=False):
        R = self.pool["R"] + sum(a for _, _, a in self.r_sources(isis)) + self.treasures
        Cc = self.pool["C"] + sum(a for _, _, a in self.c_sources())
        return R, Cc

    def _use(self, kind, obj):
        if kind == "ssg":
            self.hand.remove("Simian Spirit Guide"); self.exiled.append("Simian Spirit Guide")
        elif kind == "bloom":
            self.perms.remove(obj); self.gy.append("Lotus Bloom")
        else:
            obj["tapped"] = True

    def can_pay(self, g, r, isis=False):
        R, Cc = self.avail(isis)
        return r <= R and g + r <= R + Cc

    def pay(self, g, r, isis=False, want_ws=False):
        if not self.can_pay(g, r, isis):
            return None
        used_ws = False
        rs = self.r_sources(isis)
        def key(s):
            kind, obj, amt = s
            if obj.get("name") == "Primal Wellspring":
                return 0 if want_ws else 5
            if kind == "land" and not obj.get("mtn"):
                return 1
            if kind == "rock":
                return 2
            if kind == "bloom":
                return 4
            return 3
        rs.sort(key=key)
        need_r = r
        while need_r > 0:
            if self.pool["R"] > 0:
                take = min(self.pool["R"], need_r)
                self.pool["R"] -= take; need_r -= take; continue
            if rs:
                kind, obj, amt = rs.pop(0)
                self._use(kind, obj)
                if obj.get("name") == "Primal Wellspring":
                    used_ws = True
                self.pool["R"] += amt
                continue
            if self.treasures:
                self.treasures -= 1; self.pool["R"] += 1; continue
            raise RuntimeError("pay red")
        need = g
        cs = self.c_sources()
        while need > 0:
            if self.pool["C"] > 0:
                take = min(self.pool["C"], need); self.pool["C"] -= take; need -= take; continue
            if cs:
                kind, obj, amt = cs.pop(0); self._use(kind, obj); self.pool["C"] += amt; continue
            if self.pool["R"] > 0:
                take = min(self.pool["R"], need); self.pool["R"] -= take; need -= take; continue
            rs = [s for s in self.r_sources(isis)]
            rs.sort(key=key)
            if rs:
                kind, obj, amt = rs.pop(0); self._use(kind, obj)
                if obj.get("name") == "Primal Wellspring":
                    used_ws = True
                self.pool["R"] += amt; continue
            if self.treasures:
                self.treasures -= 1; self.pool["R"] += 1; continue
            raise RuntimeError("pay generic")
        return used_ws

    # ---------------- costs ----------------
    def ignus_loop(self, maxn=30):
        n = 0
        while n < maxn and any(p["name"] == "Grinning Ignus" for p in self.perms) and self.can_pay(0, 1):
            g, r = self.cost("Grinning Ignus")
            birgi = self.count("Birgi, God of Storytelling")
            if 3 + birgi - 1 - (g + r) < 0 and n > 0:
                break
            self.pay(0, 1)
            for p in self.perms:
                if p["name"] == "Grinning Ignus":
                    self.perms.remove(p); break
            self.pool["C"] += 2; self.pool["R"] += 1
            self.hand.append("Grinning Ignus")
            if self.can_pay(g, r):
                self.cast("Grinning Ignus", "hand")
            else:
                break
            n += 1
        self.ignus_loops = getattr(self, "ignus_loops", 0) + n
        return n

    def crown_loop(self):
        if any(p["name"] == "Crown of Flames" for p in self.perms) and self.can_pay(0, 2):
            self.pay(0, 1)
            for p in self.perms:
                if p["name"] == "Crown of Flames":
                    self.perms.remove(p); break
            self.hand.append("Crown of Flames")
            self.cast("Crown of Flames", "hand")
            return True
        return False

    def breach_cleanup(self):
        self.perms = [p for p in self.perms if not p.get("eot")]
        self.overmaster = False
        self.bonus_round = False
        if getattr(self, "breach", False):
            self.breach = False
            if any(p["name"] == "Underworld Breach" for p in self.perms):
                self.perms = [p for p in self.perms if p["name"] != "Underworld Breach"]
                self.gy.append("Underworld Breach")

    def cost(self, name, alt=None):
        d = C[name]
        g, r = d["g"], d["r"]
        if alt in ("sac1", "sac2"):
            return 0, 0
        if alt == "escape":
            alt = None
        if name == "Flameshape" or (name == "Gandalf" and self.gandalf == "cmd"):
            g += 2 * self.cmd_casts
        if alt:
            g, r = alt
        if name == "Light Up the Stage" and self.dmg_turn > 0 and not alt:
            g, r = 0, 1
        if name == "Blasphemous Act":
            g -= self.creatures_in_play()
        red = d["red"] if name != "Gandalf" else True
        if d["t"] != "land":
            g -= self.count("Helm of Awakening")
            if red:
                g -= self.count("Ruby Medallion") + self.count("The Fire Crystal")
            if NONCRE(name):
                g -= self.count("Longshot, Rebel Bowman") + (1 if self.artist >= 2 else 0)
            if ISIS(name):
                g -= self.count("Primal Amulet")
        return max(g, 0), r

    # ---------------- casting ----------------
    def cast(self, name, zone, alt=None, is_copy=False, free=False, extra=0, xval=0):
        self.casts_guard += 1
        if self.casts_guard > 400:
            raise Lose()
        isis = ISIS(name)
        spent = 0
        used_ws = False
        if not free:
            g, r = self.cost(name, alt)
            g += extra + xval
            used_ws = self.pay(g, r, isis, want_ws=(isis and name in COPYWORTHY))
            if used_ws is None:
                raise RuntimeError("cannot pay " + name)
            spent = g + r
        if alt == "escape":
            others = [c for c in self.gy]
            others.remove(name)
            others.sort(key=self.escape_keep)
            for c in others[:3]:
                self.gy.remove(c); self.exiled.append(c)
        if alt in ("sac1", "sac2"):
            k = 1 if alt == "sac1" else 2
            ms = sorted([l for l in self.lands if l.get("mtn")], key=lambda l: not l["tapped"])[:k]
            for l in ms:
                self.lands.remove(l)
        if name == "Flameshape" or (name == "Gandalf" and self.gandalf == "cmd"):
            self.cmd_casts += 1
        if zone == "hand":
            self.hand.remove(name)
        elif zone == "exile":
            for e in self.exile_play:
                if e[0] == name:
                    self.exile_play.remove(e); break
        elif zone == "fs":
            self.fs_exile.remove(name)
        elif zone == "gy":
            self.gy.remove(name)
        elif zone == "foretell":
            self.dbf_foretold -= 1
        self.spells += 1
        if self.has("Aetherflux Reservoir"):
            self.ae_life = getattr(self, "ae_life", 40) + (self.spells - 1) * self.count("Aetherflux Reservoir")
            while self.ae_life >= 51 and self.alive():
                self.ae_life -= 50; self.ae_shots = getattr(self, "ae_shots", 0) + 1
                self.dmg_target(50, red=False)
        self.L(f"  cast {name} ({zone}{' copy' if is_copy else ''}) storm={self.spells} opp={self.opp} pool={self.pool} tr={self.treasures}")
        # additional costs
        if name in ("Big Score", "Seize the Spoils", "Tormenting Voice", "Thrill of Possibility", "Unexpected Windfall", "Pirate's Pillage") and self.hand:
            self.discard(1)
        if name == "Magmatic Insight":
            ls = [c for c in self.hand if C[c]["t"] == "land"]
            if ls: self.hand.remove(ls[0]); self.gy.append(ls[0])
        if name == "Cathartic Reunion":
            for c in self.junk(self.hand, min(2, len(self.hand))):
                self.hand.remove(c); self.gy.append(c)
        if name == "Demand Answers":
            if self.treasures:
                self.treasures -= 1
            elif self.hand:
                self.discard(1)
        returned = False
        copies = 0
        for p in self.perms:
            if p["name"] == "Birgi, God of Storytelling":
                self.pool["R"] += 1
            if p["name"] == "Runaway Steam-Kin" and (C[name]["red"] if name in C else True):
                p["ctr"] = p.get("ctr", 0) + 1
                if p["ctr"] >= 3 and self.mode == "allin":
                    p["ctr"] = 0; self.pool["R"] += 3
        if NONCRE(name):
            self.gandalf_pings(1)
            if self.artist >= 1 and self.hand:
                j = self.junk(self.hand, 1)[0]
                if self.card_value(j) <= 3 or (C[j]["t"] == "land" and len(self.lands) >= 6):
                    self.hand.remove(j); self.gy.append(j); self.draw(1)
        if isis and not is_copy:
            self.isis_turn = getattr(self, "isis_turn", 0) + 1
        if isis:
            for p in list(self.perms):
                n = p["name"]; m = self.mult(p)
                if n in ("Erebor Flamesmith", "Electrostatic Field", "Thermo-Alchemist"):
                    self.dmg_each(1)
                elif n == "Guttersnipe":
                    for _ in range(m): self.dmg_each(2)
                elif n == "Fiery Inscription":
                    self.dmg_each(2)
                elif n == "Thunderdrum Soloist":
                    self.dmg_each(3 if spent >= 5 else 1)
                elif n == "Urabrask":
                    self.dmg_target(1); self.pool["R"] += 1
                elif n == "Electro, Assaulting Battery":
                    self.pool["R"] += 1
            if self.has("Primal Amulet"):
                self.amulet += self.count("Primal Amulet")
                if self.amulet >= 4:
                    self.perms = [p for p in self.perms if p["name"] != "Primal Amulet"]
                    self.lands.append(dict(name="Primal Wellspring", prod="A", tapped=False))
                    self.amulet = 0
                    self.L("    Primal Amulet flips")
            for p in self.perms:
                if p["name"] == "Krark, the Thumbless":
                    for _ in range(self.mult(p)):
                        if self.rng.random() < 0.5:
                            copies += 1
                        elif not is_copy and name not in SPECIAL:
                            returned = True
            if getattr(self, "bonus_round", False) and (not is_copy or (getattr(self, "_cast_copy", False) and BR_MIZZIX[0])) and name != "Bonus Round":
                copies += 1
            if self.dcast and name != "Doublecast":
                copies += self.dcast; self.dcast = 0
            if used_ws:
                copies += 1
        if self.spells == 3 and self.has("Emeritus of Conflict"):
            self.emeritus_prep = True
        if isis:
            self.magecraft()
        if isis and name in COPYWORTHY and self.strat_allows_copy():
            copies += self.respond_copy(name)
        countered = False
        om = getattr(self, "overmaster", False) and ISIS(name) and not is_copy and name != "Overmaster"
        if om:
            self.overmaster = False
        bait = (name == "Overmaster" and self.ix and self.counter_ready and not is_copy
                and self.rng.random() < SCEN.get("bite", 0.0))
        hold_last = (getattr(self, "cnt_stock", None) and sum(self.cnt_stock) == 1
                     and name not in KEY_CLOSERS and name not in COUNTER_KEYS)
        if self.ix and self.counter_ready and not is_copy and not om and not hold_last and (bait or self.rng.random() < self.counter_p(name)):
            self.counter_ready = int(self.counter_ready) - 1
            if getattr(self, "cnt_stock", None): self.spend_counter()
            countered = True
            self.L(f"    COUNTERED {name}")
        for _ in range(copies):
            self.resolve(name, copy_=True, spent=spent)
            self.magecraft()
        if countered:
            if name in SPECIAL:
                return False
            if zone == "gy" and alt != "escape":
                self.exiled.append(name)
            else:
                self.gy.append(name)
            return False
        if returned:
            self.L(f"    Krark returns {name}")
            if not is_copy:
                self.hand.append(name)
            return False
        self.resolve(name, copy_=is_copy, spent=spent, zone=zone)
        if is_copy or name in SPECIAL:
            return True
        if getattr(self, "_rebound_exile", False):
            self._rebound_exile = False
            return True
        if C[name]["t"] in ("instant", "sorcery"):
            if (name == "Mizzix's Mastery" or zone == "gy") and alt != "escape":
                self.exiled.append(name)
            else:
                self.gy.append(name)
        return True

    def gandalf_pings(self, k=1):
        """disparos de 'cada vez que lanzas un hechizo que no es criatura' (Gandalf y compania)"""
        for _ in range(k):
            for p in list(self.perms):
                n = p["name"]; m = self.mult(p)
                if n in ("Gandalf", "Coruscation Mage", "Kessig Flamebreather", "Firebrand Archer"):
                    for _ in range(m): self.dmg_each(1)
                elif n == TOKEN:
                    for _ in range(m): self.dmg_each(1, red=p.get("red", False))
                elif n == "Longshot, Rebel Bowman":
                    self.dmg_each(2)
                elif n == "Wiccan, Young Avenger":
                    self.impulse(1, self.turn)
                elif n == "Burning Prophet":
                    for _ in range(m): self.scry1()

    def strat_allows_copy(self):
        return True

    def respond_copy(self, target):
        n = 0
        if target == "Mana Geyser" and "Reiterate" in self.hand and self.geyser() >= 6 and self.can_pay(4, 2, True):
            pingers = [p for p in self.perms if p["name"] in ("Gandalf", "Coruscation Mage", "Kessig Flamebreather", "Firebrand Archer", "Longshot, Rebel Bowman")]
            if pingers or "Grapeshot" in self.hand:
                self.L("    Reiterate + Mana Geyser: loop infinito")
                self.reit_combo = getattr(self, "reit_combo", 0) + 1
                self.dmg_each(999)
                return 1
        for cp in ("Reverberate", "Return the Favor", "Reiterate", "Fork", "Increasing Vengeance"):
            for zone in ("hand", "exile"):
                if self.in_zone(cp, zone) and self.can_pay(*self.cost(cp), True):
                    g, r = self.cost(cp)
                    if COPYWORTHY[target] >= g + r:
                        if self.cast(cp, zone):
                            n += 1
                        break
        return n

    def in_zone(self, name, zone):
        if zone == "hand":
            return name in self.hand
        if zone == "exile":
            return any(e[0] == name and e[1] >= self.turn for e in self.exile_play)
        return False

    def magecraft(self):
        for p in list(self.perms):
            if p["name"] == "Storm-Kiln Artist":
                self.treasures += self.mult(p)
            elif p["name"] == "Ashling, Flame Dancer":
                for _ in range(self.mult(p)):
                    self.ash_res += 1
                    if self.hand:
                        self.discard(1)
                    if self.lib:
                        self.draw(1)
                    if self.ash_res == 2:
                        self.dmg_each(2)
                    elif self.ash_res == 3:
                        self.pool["R"] += 4

    def scry1(self):
        if self.lib and C[self.lib[0]]["t"] == "land" and len(self.lands) >= 6:
            self.lib.append(self.lib.pop(0))

    # ---------------- resolution ----------------
    def resolve(self, name, copy_=False, spent=0, zone=None):
        t = C[name]["t"]
        if name == "Flameshape":
            if getattr(self, "fs_turn", None) is None: self.fs_turn = self.turn
            for _ in range(2):
                if self.lib:
                    self.fs_exile.append(self.lib.pop(0))
            self.gandalf = "exile"
            return
        if name == "Gandalf":
            self.perms.append(dict(name="Gandalf", tapped=False, wiz=True))
            if getattr(self, "g_turn", None) is None: self.g_turn = self.turn
            self.gandalf = "bf"
            return
        if t in ("creature", "artifact", "enchantment") and not copy_:
            p = dict(name=name, tapped=False, wiz=C[name].get("wiz", False), shaman=C[name].get("shaman", False))
            if name == "Artist's Talent":
                self.artist = max(self.artist, 1)
            if name in ("Sol Ring", "Arcane Signet", "Mind Stone", "Tablet of Discovery"):
                p["tapped"] = False
            self.perms.append(p)
            if name in AMP_SET and getattr(self, "amp_turn", None) is None: self.amp_turn = self.turn
            if name in THREATS and self.first_threat is None:
                self.first_threat = self.turn
            self.etb(name)
            if self.ix and not self.inst_used and C[name]["t"] == "creature" and THREAT_W.get(name, 0) >= REM_THR \
                    and getattr(self, "rem_stock", None):
                hold = [i for i in self.alive() if self.rem_stock[i] > 0]
                if hold and self.rng.random() < self.ix["p_inst"] and self.rival_uses_removal(hold[0], forced_us=True):
                    self.inst_used = True
                    self.remove_best()
            return
        if name in RITUAL_NET:
            self.pool["R"] += RITUAL_NET[name]
        elif name == "Mana Geyser":
            self.pool["R"] += self.geyser()
        elif name == "Jeska's Will":
            if self.gandalf == "bf":
                self.pool["R"] += self.jeska_h(); self.impulse(3, self.turn)
            else:
                self.pool["R"] += self.jeska_h()
        elif name in ("Unexpected Windfall", "Pirate's Pillage"):
            self.draw(2); self.treasures += 2
        elif name == "Big Score":
            self.draw(2); self.treasures += 2
        elif name == "Seize the Spoils":
            self.draw(2); self.treasures += 1
        elif name in ("Tormenting Voice", "Demand Answers", "Thrill of Possibility", "Magmatic Insight"):
            self.draw(2)
        elif name == "Cathartic Reunion":
            self.draw(3)
        elif name == "Boltwave":
            self.dmg_each(3)
        elif name == "Price of Progress":
            nb = int(round(NB_FRAC[0] if not self.ix else self.ix.get("nb", NB_FRAC[0]), 2) * min(self.turn, 8) + 0.5)
            if nb > 0:
                self.dmg_each(2 * nb)
        elif name == "Faithless Salvaging":
            if self.hand:
                self.discard(1)
            self.draw(1)
            if zone == "hand" and not copy_:
                self.rebound = getattr(self, "rebound", 0) + 1
                self._rebound_exile = True
        elif name == "Faithless Looting":
            self.draw(2); self.discard(2)
        elif name in ("Reckless Impulse", "Wrenn's Resolve", "Light Up the Stage"):
            self.impulse(2, self.turn + 1)
        elif name == "Commune with Lava":
            self.impulse(self._x, self.turn + 1)
        elif name == "Valakut Awakening":
            bad = [c for c in self.hand if self.card_value(c) <= 3 or (C[c]["t"] == "land" and len(self.lands) >= 6)]
            for c in bad:
                self.hand.remove(c); self.lib.append(c)
            self.draw(len(bad) + 1)
        elif name == "Gamble":
            tgt = self.tutor_target()
            if tgt and tgt in self.lib:
                self.lib.remove(tgt); self.hand.append(tgt)
            if self.hand:
                d = self.rng.choice(self.hand); self.hand.remove(d); self.gy.append(d)
            self.rng.shuffle(self.lib)
        elif name == "Grapeshot":
            n = self.spells
            self.dmg_target(1)
            if copy_ and not getattr(self, "_cast_copy", False):
                return
            for _ in range(self.spells - 1):
                self.dmg_target(1); self.magecraft()
        elif name == "Fiery Confluence":
            for _ in range(3): self.dmg_each(2)
        elif name == "Delayed Blast Fireball":
            self.dmg_each(5 if zone == "foretell" else 2)
        elif name in ("Lightning Bolt", "Emeritus Bolt"):
            self.dmg_target(3)
        elif name in ("Gut Shot", "Lava Dart", "Spikefield Hazard"):
            self.dmg_target(1)
        elif name in ("Burst Lightning", "Shock", "Play with Fire"):
            self.dmg_target(2)
        elif name == "Lightning Strike":
            self.dmg_target(3)
        elif name == "Fireblast":
            self.dmg_target(4)
        elif name in ("Frost Bite", "Demon Bolt", "Abrade", "Fiery Impulse", "Magma Spray", "Unholy Heat"):
            pass
        elif name in ("Searing Spear", "Skullcrack"):
            self.dmg_target(3)
        elif name == "Rite of Flame":
            self.pool["R"] += 2 + sum(1 for c in self.gy if c == "Rite of Flame")
        elif name == "Strike It Rich":
            self.treasures += 1
        elif name == "Wheel of Misfortune":
            self.gy.extend(self.hand); self.hand = []; self.draw(7)
        elif name == "Will of the Jeskai":
            if self.gandalf == "bf":
                if len(self.hand) <= 2:
                    self.gy.extend(self.hand); self.hand = []; self.draw(5)
                self.pif = True
            else:
                self.pif = True
        elif name == "Blasphemous Act":
            self.wipe()
            self.opp_wiped_t = self.turn
        elif name == "Manamorphose":
            self.pool["R"] += 2; self.draw(1)
        elif name == "Crash Through":
            self.draw(1)
        elif name == "Needle Drop":
            if self.dmg_turn > 0:
                self.dmg_target(1)
            self.draw(1)
        elif name == "Bonus Round":
            self.bonus_round = True
        elif name == "Overmaster":
            self.overmaster = True; self.draw(1)
        elif name == "Past in Flames":
            self.pif = True
        elif name == "Flashback":
            cands = [c for c in self.gy if ISIS(c) and c not in ("Flashback", "Mizzix's Mastery")]
            cands.sort(key=lambda c: -(COPYWORTHY.get(c, RITUAL_NET.get(c, 1)) + (10 if c in ("Past in Flames", "Will of the Jeskai") else 0)))
            for c in cands:
                if self.can_pay(*self.cost(c), ISIS(c)):
                    self.cast(c, "gy"); break
        elif name == "Doublecast":
            self.dcast += 1
        elif name == "Molten Tide":
            self.molten = True
        elif name == "Mizzix's Mastery":
            self.mizzix(overload=self._mz_over)
        elif name in ("Reverberate", "Return the Favor"):
            pass
        elif name == "Embereth Blaze":
            self.dmg_target(2)
            if not copy_ and getattr(self, "_adventure", False):
                self._adventure = False
                self.exile_play.append(["Virtue of Courage", 999])
        elif name == "Lindblum Siege":
            self.perms.append(dict(name=TOKEN, tapped=False, wiz=True, red=False))
            self.exile_play.append(["Lindblum, Industrial Regency", 999])

    def mizzix(self, overload):
        pool = [c for c in self.gy if ISIS(c)]
        if not overload:
            pool = sorted(pool, key=lambda c: -COPYWORTHY.get(c, RITUAL_NET.get(c, 1)))[:1]
        order = sorted(pool, key=lambda c: (c == "Grapeshot", -RITUAL_NET.get(c, 0)))
        for c in order:
            self.gy.remove(c); self.exiled.append(c)
        for c in order:
            if c == "Commune with Lava":
                self._x = 0
            self._cast_copy = True
            try:
                self.cast(c, "none", is_copy=True, free=True)
            finally:
                self._cast_copy = False

    def etb(self, name):
        if name in ("Mana Vault", "Grim Monolith"):
            self.perms[-1]["nountap"] = True
        if name == "Chrome Mox":
            cand = [c for c in self.hand if C[c]["t"] != "land" and C[c].get("red", True) and c not in ("Gandalf",)]
            if cand:
                c = min(cand, key=lambda c: VALUE.get(c, 5)); self.hand.remove(c); self.exiled.append(c); self.perms[-1]["live"] = True
        if name == "Mox Diamond":
            lands = [c for c in self.hand if C[c]["t"] == "land"]
            if lands:
                c = "Mountain" if "Mountain" in lands else lands[0]; self.hand.remove(c); self.gy.append(c); self.perms[-1]["live"] = True
            else:
                self.perms.pop(); self.gy.append("Mox Diamond")
        if name == "Underworld Breach":
            self.breach = True
        if name == "Implement of Combustion":
            self.implements = getattr(self, "implements", 0) + 1
        elif name == "Renegade Map":
            self.perms = [p for p in self.perms if p["name"] != "Renegade Map"]; self.gy.append(name)
            if "Mountain" in self.lib:
                self.lib.remove("Mountain"); self.hand.append("Mountain")
        elif name == "The Flame of Keld":
            self.gy.extend(self.hand); self.hand = []
            self.keld = getattr(self, "keld", []) + [self.turn]
        elif name == "Lotus Petal":
            self.perms = [p for p in self.perms if p["name"] != "Lotus Petal"]; self.gy.append(name); self.treasures += 1
        elif name == "Mishra's Bauble":
            self.perms = [p for p in self.perms if p["name"] != "Mishra's Bauble"]; self.gy.append(name); self.bauble_draws += 1
        elif name == "Mysidian Elder":
            for _ in range(2 if self.has("Harmonic Prodigy") else 1):
                self.perms.append(dict(name=TOKEN, tapped=False, wiz=True, red=False))
        elif name == "Pyre Rhymer":
            self.pyre_prep = True
        elif name == "Pinnacle Monk":
            cands = [c for c in self.gy if ISIS(c)]
            if cands:
                best = max(cands, key=lambda c: COPYWORTHY.get(c, RITUAL_NET.get(c, 1)) + (10 if c in ("Mizzix's Mastery", "Past in Flames") else 0))
                self.gy.remove(best); self.hand.append(best)
        elif name == "Tablet of Discovery":
            if self.lib:
                self.exile_play.append([self.lib.pop(0), self.turn])
        elif name == "Burn, Burn, Tree and Fern":
            self.sagas.append(self.turn)
        elif name == "Coruscation Mage" and getattr(self, "_offspring", False):
            for _ in range(2 if self.has("Harmonic Prodigy") else 1):
                self.perms.append(dict(name="Coruscation Mage", tapped=False, wiz=True, token=True))
            self._offspring = False

    # ---- 22/11: Lotus Bloom (suspender) y Skullclamp ----
    def suspend_bloom(self):
        """Lotus Bloom desde la mano: se suspende (no se lanza); llega dentro de 3 turnos"""
        self.hand.remove("Lotus Bloom"); self.blooms.append(self.turn + 3)
        self.L("  suspende Lotus Bloom")

    def bloom_upkeep(self):
        for b in list(self.blooms):
            if self.turn >= b:
                self.blooms.remove(b)
                self.spells += 1                       # se lanza al quitar el ultimo contador: cuenta como hechizo
                self.gandalf_pings(1)                  # hechizo que no es criatura: Gandalf pinguea (es en tu mantenimiento)
                self.perms.append(dict(name="Lotus Bloom", tapped=False, wiz=False, shaman=False))
                self.blooms_in = getattr(self, "blooms_in", 0) + 1

    def clamp(self):
        """Skullclamp: equipar {1} a una ficha 1/1 -> muere, robas 2 (Coruscation, Wizard tokens)"""
        if not self.has("Skullclamp"):
            return False
        tk = [p for p in self.perms if p.get("token") or p["name"] == TOKEN]
        if not tk or not self.can_pay(1, 0):
            return False
        self.pay(1, 0); self.perms.remove(tk[0]); self.draw(2)
        self.clamp_draws = getattr(self, "clamp_draws", 0) + 2
        return True

    # ---------------- Urabrask // The Great Work ----------------
    def keld_upkeep(self):
        for k in getattr(self, "keld", []):
            if self.turn == k + 1:
                self.draw(2)

    def use_implements(self):
        while getattr(self, "implements", 0) and self.can_pay(1, 0):
            self.pay(1, 0); self.implements -= 1
            self.perms = [p for p in self.perms if not (p["name"] == "Implement of Combustion")] + \
                         [p for p in self.perms if p["name"] == "Implement of Combustion"][1:]
            self.gy.append("Implement of Combustion")
            self.dmg_target(1); self.draw(1)

    def urabrask_upkeep(self):
        for gw in list(getattr(self, "great_work", [])):
            age = self.turn - gw
            if age == 1:
                self.treasures += 3
            elif age == 2:
                self.pif_any = True
                self.great_work.remove(gw)
                self.perms.append(dict(name="Urabrask", tapped=False, wiz=False, shaman=False))

    def urabrask_activate(self):
        if self.has("Urabrask") and getattr(self, "isis_turn", 0) >= 3 and self.can_pay(0, 1):
            self.pay(0, 1)
            self.perms = [p for p in self.perms if p["name"] != "Urabrask"]
            if not hasattr(self, "great_work"):
                self.great_work = []
            self.great_work.append(self.turn)
            self.dmg_target(3)
            return True
        return False

    def temple_ready(self):
        return any(l["name"] == "Temple of Power" for l in self.lands) and self.dmg_turn >= 4

    def temple_flip(self):
        tl = [l for l in self.lands if l["name"] == "Temple of Power" and not l["tapped"]]
        if not tl or not self.temple_ready():
            return False
        tl[0]["tapped"] = True
        if not self.can_pay(2, 1):
            tl[0]["tapped"] = False
            return False
        self.pay(2, 1)
        self.lands.remove(tl[0])
        self.perms.append(dict(name="Ojer Axonil, Deepest Might", tapped=False, wiz=False, shaman=False))
        self.temple_flips = getattr(self, "temple_flips", 0) + 1
        return True

    FC_TARGETS = ["Harmonic Prodigy", "Storm-Kiln Artist", "Guttersnipe", "Coruscation Mage", "Kessig Flamebreather", "Firebrand Archer"]

    def fire_crystal(self):
        fc = [p for p in self.perms if p["name"] == "The Fire Crystal" and not p["tapped"]]
        if not fc:
            return False
        tg = next((n for n in self.FC_TARGETS if any(q["name"] == n and not q.get("token") for q in self.perms)), None)
        if tg is None or not self.can_pay(4, 2):
            return False
        self.pay(4, 2); fc[0]["tapped"] = True
        self.perms.append(dict(name=tg, tapped=True, wiz=C[tg].get("wiz", False), shaman=C[tg].get("shaman", False), token=True, eot=True))
        self.fc_copies = getattr(self, "fc_copies", 0) + 1
        return True

    def harnfel(self, mode):
        if not self.has("Harnfel, Horn of Bounty") or not self.hand or len(self.lib) < 8:
            return False
        lands_ok = len(self.lands) >= 5 or self.land_played
        def junk(c):
            if C[c]["t"] == "land":
                return lands_ok
            return self.card_value(c) <= 3
        pool = [c for c in self.hand if junk(c)]
        if not pool and mode == "allin":
            pool = [c for c in self.hand if not self.can_pay(*self.cost(c), ISIS(c)) or C[c]["t"] == "land"]
        if not pool:
            return False
        c = self.junk(pool, 1)[0]
        self.hand.remove(c); self.gy.append(c)
        self.impulse(2, self.turn)
        self.harnfel_uses = getattr(self, "harnfel_uses", 0) + 1
        return True

    # ---------------- interaction ----------------
    def threats(self):
        return sum(1 for p in self.perms if p["name"] in VISIBLE)

    def key_spell(self, name):
        if name in KEY_CLOSERS or name in COUNTER_KEYS or THREAT_W.get(name, 0) >= 0.5:
            return True
        if name == "Grapeshot":
            return self.spells >= 5
        return False

    def counter_p(self, name):
        if self.key_spell(name):
            return 1.0
        if C.get(name, {}).get("t") == "land":
            return 0.0
        cmc = C.get(name, {}).get("g", 0) + C.get(name, {}).get("r", 0)
        return COUNTER_BY_CMC.get(cmc, COUNTER_HI)

    def threat_w(self, p):
        return THREAT_W.get(p["name"], THREAT_W_DEFAULT)

    def best_target(self):
        cands = [p for p in self.perms if p["name"] in VISIBLE and not p.get("prot")]
        return max(cands, key=self.threat_w) if cands else None

    def opp_best_value(self):
        ix = self.ix
        t = self.turn - getattr(self, "opp_wiped_t", 0)
        mu = min(ix.get("opp_v0", 0.3) + ix.get("opp_dv", 0.1) * t, ix.get("opp_vmax", 1.2))
        return max(0.0, self.rng.gauss(mu, ix.get("opp_noise", 0.25)))

    def us_value(self):
        tgt = self.best_target()
        if tgt is None:
            return None
        v = self.threat_w(tgt)
        if self.ix.get("arch", 0) and self.alive():
            lost = 1 - sum(max(x, 0) for x in self.opp) / 120
            v += self.ix["arch"] * lost
        return v

    def rival_uses_removal(self, i, forced_us=False):
        stock = self.rem_stock[i]
        if stock <= 0:
            return False
        thr = REM_THR if stock == 1 else REM_THR - 0.1
        v = self.us_value()
        cands = []
        if v is not None and v >= thr:
            cands.append(("us", v))
        if not forced_us:
            for _ in range(max(0, len(self.alive()) - 1)):
                o = self.opp_best_value()
                if o >= thr:
                    cands.append(("opp", o))
        if not cands:
            return False
        if stock == 1 and max(x for _, x in cands) < 0.8 and self.rng.random() < KEEP_LAST:
            return False
        import math
        tau = self.ix.get("tau", 0.3)
        ws = [math.exp(x / tau) for _, x in cands]
        r = self.rng.random() * sum(ws)
        for (who, _), w in zip(cands, ws):
            r -= w
            if r <= 0:
                break
        self.rem_stock[i] -= 1
        return who == "us"

    def table_targets_us(self):
        for i in self.alive():
            if getattr(self, "rem_stock", None) and self.rem_stock[i] > 0:
                return self.rival_uses_removal(i)
        return False

    def spend_counter(self):
        for i in self.blue:
            if self.cnt_stock[i] > 0:
                self.cnt_stock[i] -= 1
                return

    def opp_draws(self):
        ix = self.ix
        if not getattr(self, "rem_stock", None):
            return
        cpt = ix.get("cpt", 1.3)
        for i in self.alive():
            n = int(cpt) + (self.rng.random() < cpt - int(cpt))
            for _ in range(n):
                if self.rng.random() < ix.get("rem", 5) / 99: self.rem_stock[i] += 1
                if i in self.blue and self.rng.random() < ix.get("cnt", 3) / 99: self.cnt_stock[i] += 1
                if self.rng.random() < ix.get("wipes", 2) / 99: self.wipe_stock[i] += 1
        self.counter_ready = sum(self.cnt_stock[i] for i in self.blue if i in self.alive() and self.rng.random() < ix.get("cnt_up", 0.75))

    def keeps_red(self):
        return any(p["name"] in ("Electro, Assaulting Battery", "Ashling, Flame Dancer") for p in self.perms)

    def bank_red(self):
        if not self.keeps_red():
            return 0
        n = 0
        for kind, obj, amt in self.r_sources(False):
            if kind in ("ssg", "bloom"):
                continue
            obj["tapped"] = True; self.pool["R"] += amt; n += amt
        self.banked = getattr(self, "banked", 0) + n
        return n

    def kill_perm(self, p):
        self.perms.remove(p)
        n = p["name"]
        if n == "Electro, Assaulting Battery" and not p.get("token"):
            x = self.pool["R"] + sum(a for k_, _, a in self.r_sources(False) if k_ not in ("ssg", "bloom"))
            if x > 0:
                self.pool["R"] = 0
                for kind, obj, amt in self.r_sources(False):
                    if kind not in ("ssg", "bloom"): obj["tapped"] = True
                self.electro_x = getattr(self, "electro_x", 0) + x
                self.dmg_target(x)
        if n == "Gandalf":
            self.gandalf = "cmd"
        elif n == "Ojer Axonil, Deepest Might":
            self.lands.append(dict(name="Temple of Power", prod="R", tapped=True))
        elif not p.get("token") and n != TOKEN:
            self.gy.append(n)
        self.L(f"    REMOVED {n}")

    def remove_best(self):
        p = self.best_target()
        if p is None:
            return False
        if "Redirect Lightning" in self.hand and self.can_pay(0, 1) and self.threat_w(p) >= 0.4:
            self.pay(0, 1); self.hand.remove("Redirect Lightning"); self.gy.append("Redirect Lightning")
            self.redirects = getattr(self, "redirects", 0) + 1
            return True
        if "Return the Favor" in self.hand and self.can_pay(1, 2) and self.threat_w(p) >= 0.4:
            self.pay(1, 2); self.hand.remove("Return the Favor"); self.gy.append("Return the Favor")
            return True
        if "Untimely Malfunction" in self.hand and self.can_pay(1, 1) and self.threat_w(p) >= 0.4:
            self.pay(1, 1); self.hand.remove("Untimely Malfunction"); self.gy.append("Untimely Malfunction")
            return True
        self.kill_perm(p)
        return True

    def board_value(self):
        return sum(self.threat_w(p) for p in self.perms if p["name"] in VISIBLE and
                   (C.get(p["name"], {}).get("t") == "creature" or p["name"] == "Gandalf"))

    def rival_wipes(self, i):
        if self.wipe_stock[i] <= 0 or self.turn < 3:
            return False
        others = [self.opp_best_value() * 1.5 for _ in range(max(0, len(self.alive()) - 1))]
        own = self.opp_best_value() * 1.5
        if self.board_value() + sum(others) >= own + WIPE_MARGIN:
            self.wipe_stock[i] -= 1
            self.opp_wiped_t = self.turn
            return True
        return False

    def wipe(self):
        for p in [p for p in self.perms if C.get(p["name"], {}).get("t") == "creature" or p["name"] in ("Gandalf", TOKEN) or p.get("token")]:
            self.kill_perm(p)
        self.L("    BOARD WIPE")

    def opp_phase(self):
        if not self.ix:
            return
        if getattr(self, "rem_stock", None):
            for i in self.alive():
                while self.rem_stock[i] > 0:
                    before = self.rem_stock[i]
                    if self.rival_uses_removal(i):
                        self.remove_best()
                    elif self.rem_stock[i] < before and self.ix.get("rem_slows", 0):
                        self.slow_rival(i)
                    if self.rem_stock[i] == before:
                        break
                    if self.rem_stock[i] > 0 and self.rng.random() < 0.5:
                        break
        else:
            for _ in range(3):
                if self.rng.random() < self.ix.get("p_rem", 0):
                    if self.rng.random() < 0.33:
                        self.remove_best()
        if getattr(self, "wipe_stock", None):
            for i in self.alive():
                if self.rival_wipes(i):
                    self.wipes_seen = getattr(self, "wipes_seen", 0) + 1
                    self.wipe(); break
        elif self.turn == self.ix.get("wipe_turn"):
            self.wipe()
        if self.turn == self.ix.get("gyh_turn"):
            self.exiled += self.gy; self.gy = []
            if self.ix.get("gyh_perm"):
                self.gy_locked = True
        if self.turn == self.ix.get("arth_turn"):
            for p in [p for p in self.perms if C.get(p["name"], {}).get("t") == "artifact" and p["name"] != "The One Ring"]:
                self.perms.remove(p); self.gy.append(p["name"])
        if getattr(self, "edict_on", False) and self.turn >= 3 and 2 in self.alive() \
                and self.rng.random() < self.ix.get("edict_rate", 0):
            self.edict()
        if getattr(self, "ld_on", False) and self.turn >= 3 and 0 in self.alive() \
                and self.rng.random() < self.ix.get("ld_rate", 0):
            self.lose_land()

    def slow_rival(self, by):
        order = [j for j in getattr(self, "mz_order", [0, 1, 2]) if j != by and j in self.alive()]
        if not order or self.rng.random() >= self.ix["rem_slows"]:
            return False
        j = order[0]
        self.slow[j] = self.slow[j] + 1
        self.slowed = getattr(self, "slowed", 0) + 1
        return True

    def edict(self):
        cre = [p for p in self.perms if C.get(p["name"], {}).get("t") == "creature" or p["name"] in ("Gandalf", TOKEN) or p.get("token")]
        self.edicts_seen = getattr(self, "edicts_seen", 0) + 1
        if not cre:
            return False
        p = min(cre, key=lambda q: (0 if (q.get("token") or q["name"] == TOKEN) else 1, self.threat_w(q)))
        self.edicts_hit = getattr(self, "edicts_hit", 0) + 1
        if p["name"] == "Gandalf":
            self.gandalf_edicted = getattr(self, "gandalf_edicted", 0) + 1
        self.kill_perm(p)
        return True

    def lose_land(self):
        cand = [l for l in self.lands if l["name"] != "Temple of Power"]
        if not cand:
            return False
        l = next((x for x in cand if x.get("mtn")), cand[0])
        self.lands.remove(l)
        if C.get(l["name"], {}).get("t") == "land":
            self.gy.append(l["name"])
        self.lands_lost = getattr(self, "lands_lost", 0) + 1
        return True

    def equip(self):
        eq = [p for p in self.perms if p["name"] in ("Swiftfoot Boots", "Lightning Greaves")]
        for p in self.perms:
            p["prot"] = False
        cre = sorted([p for p in self.perms if p["name"] in VISIBLE], key=lambda p: -self.threat_w(p))
        for q, tgt in zip(eq, cre):
            if q["name"] == "Swiftfoot Boots":
                if not self.can_pay(1, 0):
                    continue
                self.pay(1, 0)
            tgt["prot"] = True

    def geyser(self):
        return int(SCEN["geyser_f"] * 3 * min(self.turn, 8))

    def jeska_h(self):
        return max(SCEN["jeska_min"], SCEN["jeska_top"] - self.turn // 2)

    def tutor_target(self):
        want = []
        if self.mode == "allin":
            gyi = sum(1 for c in self.gy if ISIS(c))
            if gyi >= 4:
                want.append("Mizzix's Mastery")
            want += ["Ojer Axonil, Deepest Might", "Harmonic Prodigy", "Seething Song", "Past in Flames"]
        else:
            want = list(DEV_TUTOR)
        for w in want:
            if w in self.lib and not self.has(w) and w not in self.hand:
                return w
        return None
