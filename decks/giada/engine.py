"""Monte Carlo simulator for Giada, Font of Hope (mono-white angels, lifegain, combat in the air).

Same table model as the Gorma simulator (rival kill clocks, removal, one wipe, one counter, rival combat),
with a combat engine for our side: flying attackers, rival air blockers, anthems, Giada counters, lifelink.
Abstractions are listed in simulador-montecarlo.md (section 8).
"""
import random
from dataclasses import dataclass
from cards import CARDS, LANDS, COMMANDER
from mesa import MesaV2

G = COMMANDER


@dataclass
class TableCfg:
    clocks: tuple = ((8, 10), (9, 11), (10, 12))
    p_stoppable: float = 0.7
    delay: int = 2
    p_visible: float = 0.6
    p_removal: float = 0.30
    wipe_window: tuple = (6, 10)
    p_counter: float = 0.5
    n_counters: int = 1
    target: str = "sometimes"
    kinds: tuple = ("combat", "combo", "combat")
    combat: bool = True
    combat_start: int = 5
    combat_k: float = 2.0
    hold_from_turn: int = 6
    p_air: float = 0.5          # chance a rival deck has flyers/reach
    air_rate: float = 0.4       # per rival turn, chance to add an air blocker (max 2)
    attack: str = "smart"       # all / smart / keep1 / keep2
    gate_keep: int = 1          # untapped blockers to keep when using Cryptic Gateway
    hold_herald: bool = True    # keep Herald of Eternal Dawn for a rival's turn
    no_commander: bool = False  # test: never cast Giada
    # ---- mesa v2 (16/11, mesa.py; solo con bracket) ----
    bracket: str = ""
    opp_curve: tuple = (0.1, 0.1, 1.0)
    opp_noise: float = 0.2
    w_arch: float = 0.3
    rem: float = 5
    cpt: float = 1.3
    wipes: float = 2
    n_blue: int = 1
    cnt: float = 5
    cnt_up: float = 0.75
    rem_types: tuple = (("cre", 0.33), ("cre_x", 0.22), ("any", 0.20), ("ae", 0.20), ("edict", 0.05))
    p_instant: float = 0.5
    p_edict_each: float = 0.5
    wipe_types: tuple = (("destroy", 0.41), ("destroy_ae", 0.14), ("minus", 0.15), ("exile", 0.075),
                         ("exile_ae", 0.075), ("bounce", 0.075), ("rift", 0.075))
    wipe_margin: float = 1.5
    aem: float = 0.3
    aem_types: tuple = (("art", 0.55), ("both", 0.35), ("ench", 0.10))
    mus: tuple = (7, 8, 9)
    spread: float = 0.9
    retry: float = 0.7
    win_types: tuple = (("combat", 0.66), ("dmg", 0.10), ("loss", 0.09), ("combo", 0.15))
    win_blue: tuple = ()


@dataclass
class Perm:
    name: str
    token: bool = False
    p: int = 0
    x: int = 0
    counters: int = 0
    sick: bool = True
    tapped: bool = False
    angel: bool = False
    creature: bool = True
    kw: frozenset = frozenset()
    destiny: bool = False
    boots: bool = False
    pages: int = 0
    attacked: bool = False


# Fase 4: roles y pesos por carta en data/efectos.yaml (comunes o en el bloque "motor" de este mazo)
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", ".."))
from core import efectos as EF
import cards as _cards_mod
_CD = _cards_mod.C if isinstance(getattr(_cards_mod, "C", None), dict) else _cards_mod.CARDS
_NAMES = list(_CD)
ANTHEM_ANGELS = set(EF.motor_roles("giada", "anthem_angels", _NAMES))
KEY_TARGETS = EF.motor_order("giada", "key_target", _NAMES)


class Game(MesaV2):
    PRIORITY = {
        "Sol Ring": 1, "Arcane Signet": 2, "Mind Stone": 3, "Marble Diamond": 3, "Pearl Medallion": 3,
        G: 5, "Commander's Sphere": 8, "Heraldic Banner": 9, "Patchwork Banner": 9, "Starnheim Aspirant": 10,
        "Herald's Horn": 11, "Folk Hero": 12, "Smothering Tithe": 12, "Soul Warden": 13, "Guide of Souls": 13,
        "Righteous Valkyrie": 14, "Bishop of Wings": 15, "Youthful Valkyrie": 16, "Dazzling Angel": 17,
        "Lyra, Archangel of Dawn": 17, "Speaker of the Heavens": 18, "Serra Ascendant": 12,
        "Angelic Field Marshal": 20, "Always Watching": 21, "Thraben Watcher": 22, "Tome of Legends": 23,
        "Swiftfoot Boots": 24, "Lightning Greaves": 24, "Archangel of Thune": 25,
        "Segovian Angel": 30, "Serra Avenger": 31, "Metallic Mimic": 32, "Angel of Vitality": 33,
        "Inspiring Overseer": 34, "Angelic Sleuth": 35, "Metropolis Reformer": 36, "Wojek Investigator": 37,
        "Resplendent Angel": 33, "Exemplar of Light": 38, "Herald of War": 39, "Archangel of Tithes": 40,
        "Merchant of Truth": 41, "Firemane Commando": 42, "Angel of Finality": 43, "Seraph of the Sword": 44,
        "Vanguard Seraph": 45, "Blinding Angel": 46, "Lyra Dawnbringer": 26, "Norn's Choirmaster": 47,
        "Court of Grace": 48, "Vanquisher's Banner": 49, "Angelic Destiny": 50, "Search the Premises": 51,
        "Cryptic Gateway": 52, "Linvala, the Preserver": 53, "Sunblast Angel": 54, "Valkyrie Harbinger": 50,
        "Sigarda's Vanguard": 55, "Felidar Sovereign": 52, "Karmic Guide": 56, "Sephara, Sky's Blade": 57,
        "Emeria Shepherd": 58, "Angel of the Ruins": 59, "Ob Nixilis, the Ascended": 58,
        "Herald of Eternal Dawn": 60, "Avacyn, Angel of Hope": 58, "Reya Dawnbringer": 61,
        "Endless Atlas": 27, "Defy Death": 62, "Cut a Deal": 63, "Secret Rendezvous": 63,
        "Emeria's Call": 64, "Leader's Talent": 19, "Urza's Incubator": 7, "Restoration Angel": 36, "Serra Angel": 44,
        "Herald of the Host": 43, "Starnheim Unleashed": 46, "Lingering Souls": 40, "Millikin": 4,
    }

    def __init__(self, deck, rng, mode="table", cfg=None, mull_policy="guide", log=False):
        self.rng = rng
        self.mode = mode
        self.cfg = cfg or TableCfg()
        self.logon = log
        self.library = list(deck)
        rng.shuffle(self.library)
        self.hand, self.gy, self.bf, self.lands = [], [], [], []
        self.land_tapped_now = 0
        self.tax = 0
        self.g_in_cmd = True
        self.opp = [40, 40, 40]
        self.cmd_dmg = [0, 0, 0]
        self.turn = 0
        self.on_play = rng.random() < 0.25
        self.life = 40
        self.W = self.Cl = self.GW = 0
        self.treas = 0
        self.clues = 0
        self.energy = 0
        self.reserve = 0
        self.monarch = None      # "us" or rival index
        self.won = self.lost = False
        self.win_turn = None
        self.g_turn = None
        self.loss = None
        self.stats = dict(mulls=0, cast={}, dmg_turn={})
        self.counters_left = self.cfg.n_counters
        self.rival_next = [rng.randint(*c) for c in self.cfg.clocks]
        self.wipe_turn = rng.randint(*self.cfg.wipe_window)
        self.wipe_done = False
        self.has_air = [rng.random() < self.cfg.p_air for _ in range(3)]
        self.air = [0, 0, 0]
        self.board_reset = [0, 0, 0]
        self.skip_combat = [False, False, False]
        self.threat = {}
        self._our = True
        self.counter_up = None
        self.herald_held = False
        self.foretold = []
        self._reset_turn()
        if self.cfg.bracket and mode == "table":
            self.v2_init()
        self.mulligan(mull_policy)

    # ------------------------------------------------------------ utils
    def log(self, *a):
        if self.logon:
            print(f"[T{self.turn}{'' if self._our else 'r'}]", *a)

    def _reset_turn(self):
        self.lifegain_turn = 0
        self.ex_drawn = set()
        self.folk_used = False
        self.attacked2 = False

    def act(self, n):
        k = "(act) " + n
        self.stats["cast"][k] = self.stats["cast"].get(k, 0) + 1

    def on_bf(self, n):
        return any(p.name == n for p in self.bf)

    def count_bf(self, n):
        return sum(1 for p in self.bf if p.name == n)

    def creatures(self):
        return [p for p in self.bf if p.creature]

    def giada(self):
        for p in self.bf:
            if p.name == G:
                return p
        return None

    def alive(self):
        return [i for i in range(3) if self.opp[i] > 0]

    def draw(self, n=1):
        for _ in range(n):
            if self.library:
                self.hand.append(self.library.pop())

    def check_win(self):
        if not self.won and not self.lost and not self.alive():
            self.won = True
            self.win_turn = self.turn
            self.log("WIN")

    # ------------------------------------------------------------ statics
    def bonus(self, p):
        """(power, toughness) bonus from static effects."""
        if not p.creature:
            return 0, 0
        bp = bx = 0
        for q in self.bf:
            n = q.name
            if n == "Lyra Dawnbringer" and p.angel and q is not p:
                bp += 1; bx += 1
            elif n == "Thraben Watcher" and q is not p and not p.token:
                bp += 1; bx += 1
            elif n == "Always Watching" and not p.token:
                bp += 1; bx += 1
            elif n in ANTHEM_ANGELS and p.angel:
                bp += 1; bx += 1
            elif n == "Heraldic Banner" and p.name != "Metallic Mimic":
                bp += 1
            elif n == "Righteous Valkyrie" and self.life >= 47:
                bp += 2; bx += 2
        if p.name == "Angel of Vitality" and self.life >= 25:
            bp += 2; bx += 2
        if p.name == "Angelic Field Marshal" and self.giada():
            bp += 2; bx += 2
        if p.name == "Serra Ascendant" and self.life >= 30:
            bp += 5; bx += 5
        if p.destiny:
            bp += 4; bx += 4
        return bp, bx

    def power(self, p):
        return max(0, p.p + p.counters + self.bonus(p)[0])

    def tough(self, p):
        return p.x + p.counters + self.bonus(p)[1]

    def has_kw(self, p, k):
        if k in p.kw:
            return True
        if k == "flying" and (p.destiny or (p.name == "Serra Ascendant" and self.life >= 30)):
            return True
        if k == "vigilance":
            if self.on_bf("Angelic Field Marshal") and self.giada():
                return True
            if not p.token and self.on_bf("Always Watching"):
                return True
            if not p.token and any(q.name == "Thraben Watcher" and q is not p for q in self.bf):
                return True
        if k == "lifelink" and p.angel and any(q.name == "Lyra Dawnbringer" and q is not p for q in self.bf):
            return True
        if k == "first" and p.destiny:
            return True
        return False

    def indestructible(self, p):
        if p.name == "Avacyn, Angel of Hope" or (self.on_bf("Avacyn, Angel of Hope")):
            return True
        if p.creature and self.has_kw(p, "flying") and any(q.name == "Sephara, Sky's Blade" and q is not p for q in self.bf):
            return True
        return False

    # ------------------------------------------------------------ life & counters
    def gain_life(self, n):
        if n <= 0:
            return
        n += self.count_bf("Angel of Vitality")
        self.life += n
        self.lifegain_turn += n
        for q in self.bf:
            if q.name == "Exemplar of Light":
                q.counters += 1
                if id(q) not in self.ex_drawn:
                    self.ex_drawn.add(id(q)); self.draw(1)
            elif q.name == "Lyra, Archangel of Dawn":
                for a in self.creatures():
                    if a.angel:
                        a.counters += 1
            elif q.name == "Archangel of Thune":
                for a in self.creatures():
                    a.counters += 1

    def proliferate(self):
        for p in self.bf:
            if p.counters > 0:
                p.counters += 1
            if p.pages > 0 and p.name != "Leader's Talent":
                p.pages += 1

    def commander_trigger(self):
        for q in self.bf:
            if q.name == "Norn's Choirmaster":
                self.proliferate()
            if q.name == "Tome of Legends":
                q.pages += 1

    # ------------------------------------------------------------ mulligan
    EARLY = {"Segovian Angel", "Youthful Valkyrie", "Serra Avenger", "Angel of Vitality", "Angelic Sleuth",
             "Dazzling Angel", "Inspiring Overseer", "Metropolis Reformer", "Righteous Valkyrie",
             "Wojek Investigator", "Bishop of Wings", "Speaker of the Heavens", "Starnheim Aspirant",
             "Soul Warden", "Guide of Souls", "Resplendent Angel", "Lyra, Archangel of Dawn", "Serra Ascendant"}
    ROCKS = {"Sol Ring", "Arcane Signet", "Mind Stone", "Marble Diamond", "Pearl Medallion"}

    def is_land_card(self, c):
        return c in LANDS and c != "Emeria's Call"

    def hand_ok(self, hand, free_left, policy):
        lands = sum(1 for c in hand if c in LANDS)
        if policy == "naive":
            return 2 <= lands <= 5
        if policy == "keep7":
            return True
        rocks = sum(1 for c in hand if c in self.ROCKS)
        early = sum(1 for c in hand if c in self.EARLY)
        if lands <= 1 or lands >= 6:
            return False
        if lands == 2:
            if rocks:
                return True
            return (not self.on_play) and early >= 2
        return True

    def mulligan(self, policy):
        mulls = 0
        while True:
            self.library += self.hand
            self.hand = []
            self.rng.shuffle(self.library)
            self.draw(7)
            if self.hand_ok(self.hand, mulls == 0, policy) or mulls >= 3:
                break
            mulls += 1
        self.stats["mulls"] = mulls
        for _ in range(max(0, mulls - 1)):
            self.hand.sort(key=self.bottom_key)
            self.library.insert(0, self.hand.pop())

    def bottom_key(self, c):
        lands = sum(1 for x in self.hand if x in LANDS)
        if c in LANDS:
            return 100 if lands > 4 else -1
        if c in self.ROCKS or c in self.EARLY:
            return 0
        g, w = CARDS[c]["cost"]
        return g + w + (5 if CARDS[c].get("wipe") else 0)

    # ------------------------------------------------------------ lands & mana
    def play_land(self):
        lands = [c for c in self.hand if c in LANDS]
        if "Emeria's Call" in lands and len(lands) > 1:
            lands.remove("Emeria's Call")
        if "Emeria's Call" in lands and len(self.lands) >= 6:
            lands.remove("Emeria's Call")
        if not lands:
            return
        def score(l):
            if l == "Plains":
                return 0
            if LANDS[l].get("tapped"):
                return 2 if self.turn > 1 else -1
            return 1
        lands.sort(key=score)
        l = lands[0]
        self.hand.remove(l)
        self.lands.append(l)
        tapped = LANDS[l].get("tapped") or (l == "Minas Tirith" and not self.giada())
        if l == "Emeria's Call":
            if self.life > 15:
                self.life -= 3
            else:
                tapped = True
        if tapped:
            self.land_tapped_now += 1
        if LANDS[l].get("gain"):
            self.gain_life(LANDS[l]["gain"])
        if l == "Radiant Fountain":
            self.gain_life(2)
        if l == "Seraph Sanctuary":
            self.gain_life(1)
        self.landfall(l)
        self.log("land", l)

    def landfall(self, l):
        for q in list(self.bf):
            if q.name == "Emeria Shepherd":
                t = self.best_gy_permanent()
                if t:
                    self.gy.remove(t)
                    if l == "Plains":
                        self.put_onto_bf(t)
                    else:
                        self.hand.append(t)

    def compute_pool(self):
        W = C = 0
        n_untapped = len(self.lands) - self.land_tapped_now
        for l in self.lands[:max(0, n_untapped)]:
            if LANDS[l].get("temple"):
                C += 2 if len(self.lands) >= 5 else 0
            elif LANDS[l]["col"]:
                W += 1
            else:
                C += 1
        for p in self.bf:
            if p.tapped or p.creature:
                continue
            r = CARDS.get(p.name, {}).get("rock")
            if r:
                if r == "W":
                    W += 1
                elif r == "C":
                    C += 1
                elif r == "CC":
                    C += 2
                p.tapped = True
        self.W, self.Cl, self.GW = W, C, 0
        if self.on_bf("Smothering Tithe"):
            pass

    def giada_mana(self):
        g = self.giada()
        if g and not g.sick and not g.tapped:
            g.tapped = True
            self.GW += 1

    def avail(self, angel=False):
        return self.W + self.Cl + self.treas + (self.GW if angel else 0)

    def cost_of(self, c):
        g, w = CARDS[c]["cost"]
        if c == G:
            g += self.tax
        info = CARDS[c]
        if info.get("angel") and info["t"] == "C":
            g -= 2 * self.count_bf("Starnheim Aspirant")
            g -= sum(q.counters for q in self.bf if q.name == "Herald of War")
            g -= self.count_bf("Herald's Horn")
            g -= 2 * self.count_bf("Urza's Incubator")
        if w > 0 and self.on_bf("Pearl Medallion"):
            g -= self.count_bf("Pearl Medallion")
        return max(0, g), w

    def is_angel_spell(self, c):
        info = CARDS[c]
        return info["t"] == "C" and info.get("angel")

    def can_pay(self, g, w, angel=False, extra=0):
        colored = self.W + self.treas + (self.GW if angel else 0)
        return colored >= w and self.avail(angel) >= g + w + extra

    def pay(self, g, w, angel=False):
        if not self.can_pay(g, w, angel):
            return False
        need = w
        if angel:
            u = min(self.GW, need); self.GW -= u; need -= u
        u = min(self.W, need); self.W -= u; need -= u
        self.treas -= need
        need = g
        u = min(self.Cl, need); self.Cl -= u; need -= u
        if angel:
            u = min(self.GW, need); self.GW -= u; need -= u
        u = min(self.W, need); self.W -= u; need -= u
        u = min(self.treas, need); self.treas -= u; need -= u
        return need == 0

    # ------------------------------------------------------------ permanents
    def new_perm(self, name, token=False, p=0, x=0, angel=False, kw=()):
        if token:
            return Perm(name=name, token=True, p=p, x=x, angel=angel, kw=frozenset(kw))
        info = CARDS[name]
        if info["t"] == "C":
            ang = info.get("angel") or name == "Metallic Mimic"
            return Perm(name=name, p=info["p"], x=info["x"], angel=ang, kw=frozenset(info["kw"]))
        return Perm(name=name, creature=False, sick=False)

    def enter(self, p):
        """p: Perm entering the battlefield (card or token)."""
        if p.creature:
            angels = sum(1 for q in self.bf if q.creature and q.angel)
            if p.angel and p.name not in (G, "Metallic Mimic") and self.giada():
                p.counters += angels
            if p.angel:
                p.counters += sum(1 for q in self.bf if q.name == "Metallic Mimic")
        self.bf.append(p)
        if not p.creature:
            self.enter_noncreature(p)
            return p
        # triggers of others
        for q in list(self.bf):
            if q is p:
                continue
            n = q.name
            if n == "Youthful Valkyrie" and p.angel:
                q.counters += 1
            elif n == "Righteous Valkyrie" and (p.angel or CARDS.get(p.name, {}).get("cleric")):
                self.gain_life(self.tough(p))
            elif n == "Bishop of Wings" and p.angel:
                self.gain_life(4)
            elif n in ("Dazzling Angel", "Soul Warden"):
                self.gain_life(1)
            elif n == "Guide of Souls":
                self.gain_life(1); self.energy += 1
        if p.angel:
            for l in self.lands:
                if l == "Seraph Sanctuary":
                    self.gain_life(1)
        if p.name == "Soul Warden":
            pass
        # own ETB
        n = p.name
        if n == G:
            self.commander_trigger()
        elif n == "Inspiring Overseer":
            self.gain_life(1); self.draw(1)
        elif n == "Linvala, the Preserver":
            if any(self.opp[i] > self.life for i in self.alive()):
                self.gain_life(5)
            if self.mode == "table" and self.rival_creatures() > len(self.creatures()):
                self.make_token("angel3")
        elif n == "Sunblast Angel" or n == "Ob Nixilis, the Ascended":
            if self.mode == "table":
                k = 0
                for i in self.alive():
                    if self.is_combat_rival(i) and self.turn >= self.cfg.combat_start:
                        self.board_reset[i] = self.turn; k += 2
                if n == "Ob Nixilis, the Ascended":
                    self.gain_life(k)
                self.preempt_kind("cre", free=True)
            if n == "Sunblast Angel":
                for q in list(self.bf):
                    if q.creature and q.tapped and q is not p:
                        self.destroy(q)
        elif n == "Angel of the Ruins":
            if self.mode == "table":
                self.preempt_kind("ae", free=True)
        elif n == "Karmic Guide":
            t = self.best_gy_creature()
            if t:
                self.gy.remove(t); self.put_onto_bf(t)
        return p

    def enter_noncreature(self, p):
        n = p.name
        if n == "Court of Grace":
            self.monarch = "us"
        elif n == "Tome of Legends":
            p.pages = 1
        elif n == "Leader's Talent":
            p.pages = 1
        elif n == "Swiftfoot Boots" or n == "Lightning Greaves":
            g = self.giada()
            if g and not g.boots:
                if n == "Lightning Greaves" or self.pay(1, 0):
                    g.boots = True
                    g.sick = False
                    if n == "Lightning Greaves":
                        g.sick = False
        elif n == "Angelic Destiny":
            tgt = self.giada()
            if not tgt or (tgt.boots and self.on_bf("Lightning Greaves")):
                cs = [q for q in self.creatures() if q.angel]
                tgt = max(cs, key=self.power) if cs else None
            if tgt:
                tgt.destiny = True
            else:
                self.bf.remove(p); self.hand.append(n)
        elif CARDS[n].get("rock"):
            r = CARDS[n]["rock"]
            if not CARDS[n].get("etb_tapped"):
                p.tapped = True
                if r == "W":
                    self.W += 1
                elif r == "C":
                    self.Cl += 1
                elif r == "CC":
                    self.Cl += 2
            else:
                p.tapped = True

    def make_token(self, kind):
        if kind == "angel4":
            t = self.new_perm("Angel token", token=True, p=4, x=4, angel=True, kw=("flying",))
        elif kind == "angel4v":
            t = self.new_perm("Angel token", token=True, p=4, x=4, angel=True, kw=("flying", "vigilance"))
        elif kind == "angel3":
            t = self.new_perm("Angel token", token=True, p=3, x=3, angel=True, kw=("flying",))
        else:  # spirit 1/1 flier
            t = self.new_perm("Spirit token", token=True, p=1, x=1, angel=False, kw=("flying",))
        self.enter(t)

    def put_onto_bf(self, name):
        p = self.new_perm(name)
        return self.enter(p)

    def leaves(self, p):
        """common leave-the-battlefield bookkeeping (p already removed from bf)."""
        if p.counters > 0:
            self.clues += self.count_bf("Angelic Sleuth") if p.name != "Angelic Sleuth" else 0
            for q in self.bf:
                if q.name == "Leader's Talent" and q.pages >= 2:
                    self.gain_life(2)

    def destroy(self, p, exile=False):
        if p not in self.bf:
            return
        self.bf.remove(p)
        self.leaves(p)
        if not p.creature:
            if not p.token:
                self.gy.append(p.name)
            return
        if p.destiny:
            self.hand.append("Angelic Destiny")
            self.gy.remove("Angelic Destiny") if "Angelic Destiny" in self.gy else None
            for q in list(self.bf):
                if q.name == "Angelic Destiny":
                    self.bf.remove(q)
        if exile:
            if p.name == G:
                self.g_in_cmd = True; self.tax += 2
            return
        if p.angel:
            for q in self.bf:
                if q.name == "Bishop of Wings":
                    self.make_token("spirit")
        if not p.token:
            for q in self.bf:
                if q.name == "Merchant of Truth":
                    self.clues += 1
        if p.name == G:
            self.g_in_cmd = True
            self.tax += 2
            return
        if not p.token:
            self.gy.append(p.name)

    def best_gy_creature(self):
        cs = [c for c in self.gy if c in CARDS and CARDS[c]["t"] == "C"]
        if not cs:
            return None
        return max(cs, key=lambda c: (CARDS[c]["p"] + CARDS[c]["x"], sum(CARDS[c]["cost"])))

    def best_gy_permanent(self):
        ps = [c for c in self.gy if c in CARDS and CARDS[c]["t"] in ("C", "A", "E") and c != "Angelic Destiny"]
        if not ps:
            return None
        return max(ps, key=lambda c: sum(CARDS[c]["cost"]))

    # ------------------------------------------------------------ casting
    def key_spell(self, c):
        return sum(CARDS[c]["cost"]) >= 4 and CARDS[c]["t"] in ("C", "A", "E", "S")

    def countered(self, c):
        if self.cfg.bracket and self.mode == "table":
            return self.countered_v2(c)
        if self.mode != "table" or self.counters_left <= 0 or not self.key_spell(c):
            return False
        if self.counter_up is None:
            self.counter_up = self.rng.random() < self.cfg.p_counter
        if self.counter_up:
            self.counters_left -= 1
            self.counter_up = False
            self.log("COUNTERED", c)
            return True
        return False

    def cast(self, c, alt=None):
        ang = self.is_angel_spell(c)
        if alt == "sephara":
            fl = [q for q in self.creatures() if not q.tapped and self.has_kw(q, "flying")]
            fl.sort(key=lambda q: self.power(q))
            g, w = self.cost_of(c)
            k = min(len(fl), g)
            if not self.can_pay(g - k, w, ang):
                return False
            for q in fl[:k]:
                q.tapped = True
            self.pay(g - k, w, ang)
        else:
            g, w = self.cost_of(c)
            if not self.pay(g, w, ang):
                return False
        self.stats["cast"][c] = self.stats["cast"].get(c, 0) + 1
        for q in self.bf:
            if q.name == "Leader's Talent" and q.pages >= 3:
                for a in self.creatures():
                    a.counters += 1
        if c == G:
            self.g_in_cmd = False
            self.g_turn = self.g_turn or self.turn
            self.log("cast Giada")
            p = self.new_perm(G)
            self.enter(p)
            if self.cfg.bracket and self.mode == "table":
                self.instant_response(p)
            return True
        self.hand.remove(c)
        self.log("cast", c)
        # cast triggers
        if ang:
            if self.on_bf("Vanquisher's Banner"):
                self.draw(self.count_bf("Vanquisher's Banner"))
            g = self.giada()
            if g and self.on_bf("Folk Hero") and not self.folk_used:
                self.folk_used = True; self.draw(1)
        if self.countered(c):
            self.gy.append(c)
            return True
        info = CARDS[c]
        t = info["t"]
        if c == "Emeria's Call":
            self.gy.append(c)
            for _ in range(2):
                self.make_token("angel4")
            return True
        if t in ("S", "I"):
            self.gy.append(c)
            if info.get("draw"):
                self.draw(info["draw"])
            elif info.get("spirits"):
                for _ in range(info["spirits"]):
                    self.make_token("spirit")
            elif c == "Defy Death":
                tgt = self.best_gy_creature()
                if tgt:
                    self.gy.remove(tgt)
                    p = self.put_onto_bf(tgt)
                    if p.angel:
                        p.counters += 2
            elif info.get("wipe"):
                self.cast_wipe(c)
            return True
        p = self.put_onto_bf(c)
        if self.cfg.bracket and self.mode == "table":
            self.instant_response(p)
        return True

    def cast_wipe(self, c):
        self.log("OUR WIPE", c)
        if self.mode == "table":
            for i in self.alive():
                self.board_reset[i] = self.turn
                self.air[i] = 0
            if self.cfg.bracket:
                self.opp_wiped_t = self.turn
        if CARDS[c].get("onesided"):
            for q in list(self.bf):
                if q.creature and not q.angel:
                    self.destroy(q)
            return
        for q in list(self.bf):
            if q.creature and not self.indestructible(q):
                self.destroy(q)

    # ------------------------------------------------------------ development
    def dev_ok(self, c):
        if c == G:
            return not self.cfg.no_commander
        info = CARDS[c]
        if info.get("ans") or info.get("sans") or info.get("wipe") or info.get("prot"):
            return False
        if c in ("Flawless Maneuver", "Akroma's Will"):
            return False
        if c == "Herald of Eternal Dawn" and self.mode == "table" and self.cfg.hold_herald:
            return False
        if c == "Serra Avenger" and self.turn <= 3:
            return False
        if c in ("Cut a Deal", "Secret Rendezvous"):
            return sum(1 for x in self.hand if x not in LANDS) <= 3
        if c == "Defy Death":
            t = self.best_gy_creature()
            return t is not None and sum(CARDS[t]["cost"]) >= 4
        if c == "Angelic Destiny":
            return bool(self.creatures())
        if c == "Starnheim Unleashed":
            return False          # always foretold (end of turn), cast later for X
        if c == "Cryptic Gateway":
            return sum(1 for x in self.hand if x in CARDS and self.is_angel_spell(x)) >= 1
        if c == "Emeria's Call":
            return len(self.lands) >= 6
        if c == "Sunblast Angel":
            return not any(q.tapped and q.creature and not self.indestructible(q) for q in self.bf)
        return True

    def candidates(self):
        out = [c for c in set(self.hand) if c in self.PRIORITY and c not in LANDS or c == "Emeria's Call" and c in self.hand]
        if self.g_in_cmd:
            out.append(G)
        return sorted(set(out), key=lambda c: self.PRIORITY.get(c, 99))

    def develop(self, reserve=0):
        guard = 0
        while guard < 40 and not self.won:
            guard += 1
            done = False
            for c in self.candidates():
                if c == G and not self.g_in_cmd:
                    continue
                if c != G and c not in self.hand:
                    continue
                if not self.dev_ok(c):
                    continue
                if c == "Sephara, Sky's Blade":
                    fl = [q for q in self.creatures() if not q.tapped and self.has_kw(q, "flying")]
                    sg, sw = self.cost_of(c)
                    if fl and self.can_pay(max(0, sg - len(fl)), sw, True, extra=reserve):
                        if self.cast(c, alt="sephara"):
                            done = True; break
                g, w = self.cost_of(c)
                if self.can_pay(g, w, self.is_angel_spell(c) if c != G else True, extra=reserve):
                    if self.cast(c):
                        done = True; break
            if not done:
                done = self.use_utilities(reserve)
            if not done:
                break

    def use_utilities(self, reserve):
        for q in self.bf:
            if q.name == "Leader's Talent" and q.pages < 3:
                g = 2 if q.pages <= 1 else 3
                if self.can_pay(g, 1, extra=reserve):
                    self.pay(g, 1); q.pages = max(q.pages, 1) + 1; self.act(f"Leader's Talent L{q.pages}")
                    return True
        if self.foretold and self.foretold[0] < self.turn:
            x = (self.avail() - reserve - 1) // 2
            if x >= 2 and self.can_pay(2 * x, 1, extra=reserve):
                self.pay(2 * x, 1); self.foretold.pop(0); self.gy.append("Starnheim Unleashed")
                self.stats["cast"]["Starnheim Unleashed"] = self.stats["cast"].get("Starnheim Unleashed", 0) + 1
                for _ in range(x):
                    self.make_token("angel4v")
                self.log("Starnheim foretold X =", x)
                return True
        for q in self.bf:
            if q.name == "Speaker of the Heavens" and not q.sick and not q.tapped and self.life >= 47:
                q.tapped = True; self.make_token("angel4"); self.act("Speaker of the Heavens"); return True
        # equip boots to Giada
        g = self.giada()
        if g and not g.boots and self.on_bf("Swiftfoot Boots") and self.can_pay(1, 0, extra=reserve):
            self.pay(1, 0); g.boots = True; g.sick = False; return True
        if g and not g.boots and self.on_bf("Lightning Greaves"):
            g.boots = True; return True
        # Secluded Steppe cycling / Angel of the Ruins plainscycling
        if "Secluded Steppe" in self.hand and len(self.lands) >= 5 and self.can_pay(0, 1, extra=reserve):
            self.pay(0, 1); self.hand.remove("Secluded Steppe"); self.gy.append("Secluded Steppe"); self.draw(1)
            return True
        if "Angel of the Ruins" in self.hand and not any(c in LANDS for c in self.hand) and len(self.lands) < 5 \
                and self.can_pay(2, 0, extra=reserve):
            self.pay(2, 0); self.hand.remove("Angel of the Ruins"); self.gy.append("Angel of the Ruins")
            if "Plains" in self.library:
                self.library.remove("Plains"); self.hand.append("Plains"); self.rng.shuffle(self.library)
            return True
        return False

    def end_draws(self, reserve):
        """Spend leftover mana on card draw at the end of our turn."""
        if "Starnheim Unleashed" in self.hand and self.can_pay(2, 0, extra=reserve):
            self.pay(2, 0); self.hand.remove("Starnheim Unleashed")
            self.foretold.append(self.turn); self.act("Starnheim foretell")
        for q in self.bf:
            if q.name == "Tome of Legends" and q.pages > 0 and not q.tapped and self.can_pay(1, 0, extra=reserve):
                self.pay(1, 0); q.pages -= 1; q.tapped = True; self.draw(1)
        while self.clues > 0 and self.can_pay(2, 0, extra=reserve):
            self.pay(2, 0); self.clues -= 1; self.draw(1)
        if "Minas Tirith" in self.lands and self.attacked2 and self.can_pay(2, 1, extra=reserve):
            self.pay(2, 1); self.draw(1)          # {1}{W} + tapping Minas itself
        for q in self.bf:
            if q.name == "Endless Atlas" and not q.tapped and self.can_pay(2, 0, extra=reserve) and \
                    max(self.lands.count(l) for l in set(self.lands)) >= 3:
                self.pay(2, 0); q.tapped = True; self.draw(1); self.act("Endless Atlas")
        if "War Room" in self.lands and self.can_pay(4, 0, extra=reserve) and self.life > 15:
            self.pay(4, 0); self.life -= 1; self.draw(1)
        if "Bonders' Enclave" in self.lands and self.can_pay(4, 0, extra=reserve) and \
                any(self.power(q) >= 4 for q in self.creatures()):
            self.pay(4, 0); self.draw(1)
        if len(self.lands) >= 7:
            for q in list(self.bf):
                if q.name == "Mind Stone" and self.can_pay(1, 0, extra=reserve):
                    self.pay(1, 0); self.bf.remove(q); self.gy.append(q.name); self.draw(1)
                if q.name == "Commander's Sphere" and len(self.lands) >= 9:
                    self.bf.remove(q); self.gy.append(q.name); self.draw(1)

    def gateway(self):
        if not self.on_bf("Cryptic Gateway"):
            return
        for _ in range(6):
            angels_in_hand = [c for c in self.hand if c in CARDS and self.is_angel_spell(c)]
            if not angels_in_hand:
                return
            untapped = [q for q in self.creatures() if q.angel and not q.tapped]
            keep = self.cfg.gate_keep if self.mode == "table" else 0
            if len(untapped) - keep < 2:
                return
            untapped.sort(key=lambda q: self.power(q))
            # keep the biggest untapped as blockers
            usable = untapped[:len(untapped) - keep]
            a, b = usable[0], usable[1]
            a.tapped = b.tapped = True
            best = max(angels_in_hand, key=lambda c: sum(CARDS[c]["cost"]))
            self.hand.remove(best)
            self.stats["cast"]["(Gateway) " + best] = self.stats["cast"].get("(Gateway) " + best, 0) + 1
            self.stats["cast"]["Cryptic Gateway"] = self.stats["cast"].get("Cryptic Gateway", 0)
            self.log("Gateway puts", best)
            self.put_onto_bf(best)

    # ------------------------------------------------------------ hold
    def answers_in_hand(self, kind=None, instant=True):
        out = []
        for c in self.hand:
            info = CARDS.get(c, {})
            a = info.get("ans") if instant else (info.get("ans") or info.get("sans"))
            if a and (kind is None or kind in a):
                g, w = info["cost"]
                out.append((g + w, c))
        if instant and "Herald of Eternal Dawn" in self.hand:
            out.append((7, "Herald of Eternal Dawn"))
        out.sort()
        return out

    def hold_amount(self):
        if self.mode != "table" or self.turn < self.cfg.hold_from_turn:
            return 0
        a = [x for x in self.answers_in_hand() if x[1] != "Herald of Eternal Dawn"]
        return a[0][0] if a else 0

    # ------------------------------------------------------------ combat (ours)
    def rival_creatures(self):
        return 2 + self.turn // 3

    def attackers(self):
        out = []
        for p in self.creatures():
            if p.tapped or p.sick or self.power(p) <= 0:
                continue
            if self.mode == "table" and not self.has_kw(p, "flying") and p.name != "Felidar Sovereign":
                continue
            if self.mode == "table" and p.name in ("Bishop of Wings", "Starnheim Aspirant", "Soul Warden",
                                                    "Guide of Souls", "Felidar Sovereign"):
                continue
            out.append(p)
        if self.mode != "table" or not self.cfg.combat:
            return out
        pol = self.cfg.attack
        if pol == "all":
            return out
        nonvig = sorted([p for p in out if not self.has_kw(p, "vigilance")], key=self.tough, reverse=True)
        keep_n = 0
        if pol == "keep1":
            keep_n = 1
        elif pol == "keep2":
            keep_n = 2
        elif pol == "smart":
            threat = self.expected_rival_attack()
            if threat > 0:
                vig_def = sum(1 for p in self.creatures() if not p.tapped and (self.has_kw(p, "vigilance")
                                                                              and p in out or p not in out and not p.sick))
                lethal = threat >= self.life * 0.6
                keep_n = max(0, (2 if lethal else 1) - vig_def)
        keep = nonvig[:keep_n]
        return [p for p in out if p not in keep]

    def expected_rival_attack(self):
        if self.mode != "table" or not self.cfg.combat:
            return 0
        tot = 0
        for i in self.alive():
            if (self.cfg.bracket or self.cfg.kinds) and not self.is_combat_rival(i):
                continue
            tot = max(tot, self.rival_dmg(i, self.turn + 1))
        return tot

    def blocker_stats(self):
        return 2 + self.turn // 5, 3 + self.turn // 6

    def eaten(self, p):
        """True if a rival air blocker would kill p without dying."""
        bpow, btou = self.blocker_stats()
        dies = bpow >= self.tough(p) and not self.indestructible(p) and p.name != "Seraph of the Sword" \
            and not self.has_kw(p, "first")
        return dies and self.power(p) < btou

    def pick_target(self, atk):
        al = self.alive()
        if not al:
            return None
        def dmg_vs(i):
            b = self.air[i] if self.mode == "table" else 0
            if any(p.name == "Archangel of Tithes" for p in atk):
                b = max(0, b - 1)
            order = sorted(atk, key=self.power, reverse=True)
            return sum(self.power(p) for p in order[b:])
        killable = [i for i in al if self.opp[i] <= dmg_vs(i)]
        if killable:
            return min(killable, key=lambda i: (self.rival_next[i], self.opp[i]))
        return min(al, key=lambda i: (self.air[i] if self.mode == "table" else 0, self.opp[i]))

    def combat(self):
        atk = self.attackers()
        if not atk or not self.alive():
            return
        tgt = self.pick_target(atk)
        if self.mode == "table" and self.air[tgt] > 0:
            safe = [p for p in atk if not self.eaten(p)]
            tot = sum(self.power(p) for p in atk)
            if tot - max(self.power(p) for p in atk) * self.air[tgt] < self.opp[tgt]:
                atk = safe
            if not atk:
                return
        # Akroma's Will (commander on battlefield: both modes)
        dstrike = set()
        if "Akroma's Will" in self.hand and len(atk) >= 3 and self.can_pay(3, 1):
            self.pay(3, 1); self.hand.remove("Akroma's Will"); self.gy.append("Akroma's Will")
            self.stats["cast"]["Akroma's Will"] = self.stats["cast"].get("Akroma's Will", 0) + 1
            dstrike = {id(p) for p in atk}
        for p in atk:
            p.attacked = True
            if not self.has_kw(p, "vigilance"):
                p.tapped = True
            if p.name == "Herald of War":
                p.counters += 1
            if p.name == G:
                self.commander_trigger()
        if any(p.name == "Sigarda's Vanguard" for p in atk):
            seen = set()
            for p in sorted(atk, key=self.power, reverse=True):
                pw = self.power(p)
                if pw not in seen:
                    seen.add(pw); dstrike.add(id(p))
        if self.energy >= 3 and self.on_bf("Guide of Souls"):
            self.energy -= 3
            big = max(atk, key=self.power)
            big.counters += 2; big.angel = True
        for q in self.bf:
            if q.name == "Leader's Talent":
                max(atk, key=self.power).counters += 1
        if len(atk) >= 2:
            self.attacked2 = True
            for q in self.bf:
                if q.name == "Firemane Commando":
                    self.draw(1)
        mult = lambda p: 2 if id(p) in dstrike else 1
        # split: the smallest set of attackers that kills the target (after its blockers), the rest to another rival
        groups = []
        rest = sorted(atk, key=self.power, reverse=True)
        while rest:
            t = tgt if not groups else self.pick_target(rest)
            if t is None or any(g[0] == t for g in groups):
                groups[-1][1].extend(rest); break
            b = self.air[t] if self.mode == "table" else 0
            if any(p.name == "Archangel of Tithes" for p in atk):
                b = max(0, b - 1)
            need = self.opp[t]
            take, dm = [], 0
            for p in rest:
                take.append(p)
                if len(take) > b:
                    dm = sum(self.power(q) * mult(q) for q in sorted(take, key=self.power)[:len(take) - b])
                if dm >= need + 2:
                    break
            if dm < need + 2 or len(self.alive()) <= len(groups) + 1:
                take = rest
            groups.append((t, take))
            rest = [p for p in rest if p not in take]
        life_ev = 0
        for t, grp in groups:
            life_ev += self.resolve_attack(t, grp, dstrike, mult)
            for p in grp:
                if p.name == "Herald of the Host" and p in self.bf:
                    pw = max(0, p.p + self.bonus(p)[0])     # token copies: no counters
                    for o in self.alive():
                        if o != t:
                            self.opp[o] -= pw
                            self.stats["dmg_turn"][self.turn] = self.stats["dmg_turn"].get(self.turn, 0) + pw
        if life_ev:
            self.gain_life(life_ev)   # simultaneous combat damage = one life-gain event
        self.check_win()

    def resolve_attack(self, tgt, atk, dstrike, mult):
        blockers = 0
        if self.mode == "table":
            blockers = self.air[tgt]
            if any(p.name == "Archangel of Tithes" for p in atk):
                blockers = max(0, blockers - 1)
        bpow, btou = self.blocker_stats()
        total = sum(self.power(p) * mult(p) for p in atk)
        blocked = set()
        for _ in range(blockers):
            free = [p for p in atk if id(p) not in blocked]
            if not free:
                break
            kill = [p for p in free if bpow >= self.tough(p) and not self.indestructible(p)
                    and p.name != "Seraph of the Sword" and not (self.has_kw(p, "first") and self.power(p) >= btou)]
            left = total - sum(self.power(p) * mult(p) for p in atk if id(p) in blocked)
            if kill:
                p = max(kill, key=self.power)
            elif left >= self.opp[tgt]:
                p = max(free, key=self.power)      # chump to survive
            else:
                break
            blocked.add(id(p))
            if self.power(p) >= btou:
                self.air[tgt] = max(0, self.air[tgt] - 1)
            if p in kill:
                self.destroy(p)
        dmg = 0
        life = 0
        for p in atk:
            if id(p) in blocked:
                continue
            d = self.power(p) * mult(p)
            if d <= 0:
                continue
            dmg += d
            if p.name == G:
                self.cmd_dmg[tgt] += d
            if self.has_kw(p, "lifelink") or (id(p) in dstrike and "Akroma's Will" in self.gy):
                life += d
            if p.name == "Blinding Angel":
                self.skip_combat[tgt] = True
        self.opp[tgt] -= dmg
        if self.cmd_dmg[tgt] >= 21:
            self.opp[tgt] = min(self.opp[tgt], 0)
        self.stats["dmg_turn"][self.turn] = self.stats["dmg_turn"].get(self.turn, 0) + dmg
        if dmg > 0 and self.monarch == tgt:
            self.monarch = "us"
        self.log("attack", tgt, "with", len(atk), "dmg", dmg, "opp", self.opp)
        return life

    # ------------------------------------------------------------ turns
    def our_turn(self):
        self._our = True
        self.turn += 1
        self._reset_turn()
        self.land_tapped_now = 0
        self.counter_up = None
        if self.cfg.bracket and self.mode == "table":
            self._cnt_up = {}
            self._instant_used = False
            self.roll_attempts()
        for p in self.bf:
            p.tapped = False
            p.sick = False
            p.attacked = False
        self.upkeep()
        if self.won:
            return
        if not (self.turn == 1 and self.on_play):
            self.draw(1)
        self.play_land()
        self.compute_pool()
        if self.on_bf("Smothering Tithe"):
            self.treas += 1 + (self.rng.random() < 0.5)
        self.log("hand", len(self.hand), "lands", len(self.lands), "pool", self.W, self.Cl, "life", self.life)
        reserve = self.hold_amount()
        self.develop(reserve)
        self.combat()
        if self.won:
            return
        self.giada_mana()
        self.develop(reserve)
        self.gateway()
        self.develop(reserve)
        self.end_draws(reserve)
        self.end_step(ours=True)
        g = self.giada()
        self.reserve = self.W + self.Cl + self.treas
        self.herald_mana = self.reserve + (1 if g and not g.tapped and not g.sick else 0)
        self._our = False

    def upkeep(self):
        for p in list(self.bf):
            n = p.name
            if n == "Felidar Sovereign" and self.life >= 40:
                self.log("Felidar wins"); self.act("Felidar win")
                for i in self.alive():
                    self.opp[i] = 0
                self.check_win()
                return
            if n == "Reya Dawnbringer":
                t = self.best_gy_creature()
                if t:
                    self.gy.remove(t); self.put_onto_bf(t)
            if n == "Court of Grace":
                self.make_token("angel4" if self.monarch == "us" else "spirit")
            if n == "Herald's Horn" and self.library:
                top = self.library[-1]
                if top in CARDS and self.is_angel_spell(top):
                    self.draw(1)
            if n == "Wojek Investigator":
                if len(self.hand) < 3:
                    self.clues += len(self.alive()) if self.mode == "table" else 1

    def end_step(self, ours):
        if ours and self.monarch == "us":
            self.draw(1)
        for p in list(self.bf):
            if p.name == "Valkyrie Harbinger" and self.lifegain_turn >= 4:
                self.make_token("angel4v")
            if p.name == "Resplendent Angel" and self.lifegain_turn >= 5:
                self.make_token("angel4v")
            if p.name == "Ob Nixilis, the Ascended" and self.lifegain_turn >= 1:
                self.make_token("angel4")

    # ------------------------------------------------------------ rivals
    def p_us(self):
        t = self.cfg.target
        if t == "always":
            return 1.0
        if t == "spread":
            return 1 / 3
        return 0.75 if self.threatening() else 0.25

    def threatening(self):
        tot = sum(self.power(p) for p in self.creatures() if self.has_kw(p, "flying"))
        return tot >= 15 or any(p.destiny for p in self.bf) or self.on_bf("Felidar Sovereign")

    def rival_dmg(self, i, turn):
        cfg = self.cfg
        start = max(cfg.combat_start, self.board_reset[i] + 1)
        if turn < start:
            return 0
        return int(round(cfg.combat_k * (turn - start + 1)))

    def rival_combat(self, i):
        cfg = self.cfg
        if not cfg.combat or self.turn < cfg.combat_start or self.opp[i] <= 0:
            return
        if (cfg.bracket or cfg.kinds) and not self.is_combat_rival(i):
            return
        if self.skip_combat[i]:
            self.skip_combat[i] = False
            return
        if self.rng.random() >= (self.p_us_combat() if cfg.bracket else self.p_us()):
            return
        dmg = self.rival_dmg(i, self.turn)
        if dmg <= 0:
            return
        if self.on_bf("Archangel of Tithes") and any(q.name == "Archangel of Tithes" and not q.tapped for q in self.bf):
            dmg = int(dmg * 0.7)
        for q in self.bf:
            if q.name == "Search the Premises":
                self.clues += 1
        n_att = max(1, min(4, 1 + (self.turn - cfg.combat_start) // 2))
        a = dmg / n_att
        blockers = sorted([p for p in self.creatures() if not p.tapped], key=lambda p: -self.tough(p))
        incoming = n_att
        left = dmg
        # safe blocks first
        for p in blockers:
            if incoming <= 0:
                break
            safe = self.tough(p) > a or p.name == "Seraph of the Sword" or self.indestructible(p)
            if safe:
                incoming -= 1; left -= a
        # chump blocks only if lethal
        if left >= self.life:
            for p in sorted([q for q in blockers if self.tough(q) <= a and q.name != "Seraph of the Sword"
                             and not self.indestructible(q)], key=self.power):
                if incoming <= 0 or left < self.life:
                    break
                incoming -= 1; left -= a
                self.destroy(p)
        left = max(0, int(round(left)))
        if left > 0:
            self.life -= left
            if self.on_bf("Metropolis Reformer"):
                pass
            if self.monarch == "us":
                self.monarch = i
            self.log("rival", i, "hits us for", left, "life", self.life)
        if self.life <= 0:
            if self.on_bf("Herald of Eternal Dawn"):
                self.life = max(self.life, 0)
                return
            self.lost = True; self.loss = "combat"

    def roll_threat(self, i):
        if self.cfg.bracket:
            return self.roll_threat_v2(i)
        r = self.rng.random()
        if self.cfg.kinds:
            kind = "cre" if self.cfg.kinds[i] == "combat" else ("ae" if r < 0.5 else "other")
        else:
            kind = "cre" if r < 0.5 else ("ae" if r < 0.75 else "other")
        self.threat[i] = dict(kind=kind, stoppable=self.rng.random() < self.cfg.p_stoppable,
                              visible=self.rng.random() < self.cfg.p_visible, stopped=False, t=self.turn)

    def preempt_kind(self, kind, free=False):
        """Sorcery-speed answer (or an ETB like Sunblast/Angel of the Ruins) to a visible rival attempt due soon."""
        for i in self.alive():
            if self.rival_next[i] in (self.turn, self.turn + 1):
                th = self.threat.get(i)
                if th is None or th["t"] < self.turn - 1:
                    self.roll_threat(i); th = self.threat[i]
                if th["stoppable"] and th["visible"] and not th["stopped"] and th["kind"] == kind:
                    th["stopped"] = True
                    self.log("pre-empted rival", i)
                    return True
        return False

    def preempt(self):
        for i in self.alive():
            if self.rival_next[i] not in (self.turn, self.turn + 1):
                continue
            th = self.threat.get(i)
            if th is None or th["t"] < self.turn - 1:
                self.roll_threat(i); th = self.threat[i]
            if not (th["stoppable"] and th["visible"]) or th["stopped"]:
                continue
            # sorcery answers first (keep instants for later)
            for c in list(self.hand):
                info = CARDS.get(c, {})
                if info.get("sans") and th["kind"] in info["sans"]:
                    g, w = info["cost"]
                    if self.can_pay(g, w):
                        self.pay(g, w); self.hand.remove(c)
                        self.stats["cast"][c] = self.stats["cast"].get(c, 0) + 1
                        if c == "Grasp of Fate":
                            self.bf.append(self.new_perm(c))
                        else:
                            self.gy.append(c)
                        th["stopped"] = True
                        self.log("pre-empt", i, "with", c)
                        break
            if th["stopped"] or th["kind"] != "cre":
                continue
            # one-sided wipe (Sephara on battlefield) or a desperate wipe
            for c in list(self.hand):
                info = CARDS.get(c, {})
                if not info.get("wipe"):
                    continue
                g, w = info["cost"]
                onesided = info.get("onesided") or (self.on_bf("Sephara, Sky's Blade")) or self.on_bf("Avacyn, Angel of Hope")
                mine = sum(self.power(q) for q in self.creatures() if not self.indestructible(q))
                if (onesided or mine < 8) and self.can_pay(g, w):
                    self.pay(g, w)
                    self.stats["cast"][c] = self.stats["cast"].get(c, 0) + 1
                    self.hand.remove(c); self.gy.append(c); self.cast_wipe(c)
                    th["stopped"] = True
                    break

    def table_events(self, i):
        cfg = self.cfg
        if cfg.bracket:
            return self.table_events_v2(i)
        # rival board: air blockers
        if self.has_air[i] and self.turn >= 3 and self.air[i] < 2 and self.rng.random() < cfg.air_rate:
            self.air[i] += 1
        self.rival_combat(i)
        if self.lost:
            return
        # wipe
        if not self.wipe_done and self.turn >= self.wipe_turn and self.rng.random() < 0.5:
            self.wipe_done = True
            if "Flawless Maneuver" in self.hand and self.giada():
                self.hand.remove("Flawless Maneuver"); self.gy.append("Flawless Maneuver")
                self.stats["cast"]["Flawless Maneuver"] = self.stats["cast"].get("Flawless Maneuver", 0) + 1
                self.log("Flawless Maneuver saves the board")
            else:
                self.log("RIVAL WIPE")
                for p in [q for q in self.bf if q.creature]:
                    if not self.indestructible(p):
                        self.destroy(p)
        # spot removal
        if self.rng.random() < cfg.p_removal and self.rng.random() < self.p_us():
            self.removal_on_us()
        # kill attempt
        if self.opp[i] > 0 and self.rival_next[i] == self.turn:
            th = self.threat.get(i)
            if th is None or th["t"] < self.turn - 1:
                self.roll_threat(i); th = self.threat[i]
            self.threat.pop(i, None)
            if th["stopped"]:
                self.rival_next[i] = self.turn + cfg.delay
                return
            if self.on_bf("Herald of Eternal Dawn"):
                h = next(q for q in self.bf if q.name == "Herald of Eternal Dawn")
                if self.rng.random() < 0.6:
                    self.destroy(h)
                    self.rival_next[i] = self.turn + 1
                else:
                    self.rival_next[i] = self.turn + cfg.delay
                self.log("Herald of Eternal Dawn stops rival", i)
                return
            if th["stoppable"]:
                for cost, c in self.answers_in_hand(th["kind"]):
                    pool = self.herald_mana if c == "Herald of Eternal Dawn" else self.reserve
                    if pool >= cost:
                        self.reserve -= min(self.reserve, cost)
                        self.herald_mana -= cost
                        self.hand.remove(c)
                        self.stats["cast"][c] = self.stats["cast"].get(c, 0) + 1
                        if c == "Herald of Eternal Dawn":
                            self.bf.append(self.new_perm(c))
                            self.bf[-1].sick = True
                        else:
                            self.gy.append(c)
                            if c == "Invoke the Divine":
                                self.gain_life(4)
                        self.rival_next[i] = self.turn + cfg.delay
                        self.log("answered rival", i, "with", c)
                        return
                # Herald of Eternal Dawn with flash also works against unanswerable-by-removal threats
            if not th["stoppable"] and "Herald of Eternal Dawn" in self.hand and self.herald_mana >= 7:
                self.hand.remove("Herald of Eternal Dawn"); self.herald_mana -= 7
                self.bf.append(self.new_perm("Herald of Eternal Dawn"))
                self.stats["cast"]["Herald of Eternal Dawn"] = self.stats["cast"].get("Herald of Eternal Dawn", 0) + 1
                self.rival_next[i] = self.turn + cfg.delay
                self.log("flash Herald stops rival", i)
                return
            self.lost = True
            self.loss = "rival"
            self.log("LOSS: rival", i, "wins")

    def table_events_v2(self, i):
        cfg = self.cfg
        self.opp_draws(i)
        if self.has_air[i] and self.turn >= 3 and self.air[i] < 2 and self.rng.random() < cfg.air_rate:
            self.air[i] += 1
        self.rival_combat(i)
        if self.lost:
            return
        self.rival_wipes(i)
        self.rival_aem(i)
        self.rival_removal_phase(i)
        if self.opp[i] <= 0 or self.rival_next[i] != self.turn:
            return
        th = self.threat.get(i)
        if th is None or th["t"] < self.turn - 1:
            self.roll_threat(i); th = self.threat[i]
        self.threat.pop(i, None)
        self._st("att")
        self.ready_t[i] = self.turn + cfg.delay
        if th["stopped"]:
            self._st("we_stop")
            return
        if self.on_bf("Herald of Eternal Dawn"):
            self._st("herald_stop")
            return
        if self.others_stop(i):
            return
        if th["stoppable"]:
            for cost, c in self.answers_in_hand(th["kind"]):
                pool = self.herald_mana if c == "Herald of Eternal Dawn" else self.reserve
                if pool >= cost:
                    self.reserve -= min(self.reserve, cost)
                    self.herald_mana -= cost
                    self.hand.remove(c)
                    self.stats["cast"][c] = self.stats["cast"].get(c, 0) + 1
                    if c == "Herald of Eternal Dawn":
                        self.bf.append(self.new_perm(c)); self.bf[-1].sick = True
                    else:
                        self.gy.append(c)
                        if c == "Invoke the Divine":
                            self.gain_life(4)
                    self._st("we_stop")
                    self.log("answered rival", i, "with", c)
                    return
        if "Herald of Eternal Dawn" in self.hand and self.herald_mana >= 7:
            self.hand.remove("Herald of Eternal Dawn"); self.herald_mana -= 7
            self.bf.append(self.new_perm("Herald of Eternal Dawn"))
            self.stats["cast"]["Herald of Eternal Dawn"] = self.stats["cast"].get("Herald of Eternal Dawn", 0) + 1
            self._st("we_stop")
            return
        self.lost = True
        self.loss = "rival_" + th.get("wtype", "?")
        self.log("LOSS: rival", i, "wins (", th.get("wtype"), ")")

    def removal_on_us(self):
        g = self.giada()
        keys = [p for n in KEY_TARGETS for p in self.bf if p.name == n]
        victim = None
        if g and not g.boots and (self.rng.random() < 0.5 or not keys):
            victim = g
        elif keys:
            victim = keys[0] if self.rng.random() < 0.7 else self.rng.choice(keys)
        if victim is None:
            cs = [p for p in self.creatures() if not (p is g and g.boots)]
            if not cs:
                return
            victim = max(cs, key=self.power)
        exile = self.rng.random() < 0.4
        if victim.creature and not exile and self.indestructible(victim):
            self.log("removal bounces off (indestructible)")
            return
        if victim.creature and not exile:
            if "Valorous Stance" in self.hand and self.reserve >= 2 and victim in self.creatures():
                self.hand.remove("Valorous Stance"); self.gy.append("Valorous Stance"); self.reserve -= 2
                self.stats["cast"]["Valorous Stance"] = self.stats["cast"].get("Valorous Stance", 0) + 1
                return
            if "Flawless Maneuver" in self.hand and g:
                self.hand.remove("Flawless Maneuver"); self.gy.append("Flawless Maneuver")
                self.stats["cast"]["Flawless Maneuver"] = self.stats["cast"].get("Flawless Maneuver", 0) + 1
                return
        self.log("removal on", victim.name)
        self.destroy(victim, exile=exile)

    def opp_turns(self):
        self._our = False
        for i in range(3):
            if self.won or self.lost:
                return
            self.lifegain_turn = 0
            if self.mode == "table" and self.opp[i] > 0:
                self.table_events(i)
            if self.mode == "table" and self.opp[i] > 0:
                self.end_step(ours=False)

    def run(self, max_turns=20):
        while self.turn < max_turns and not self.won and not self.lost:
            self.our_turn()
            if self.won:
                break
            if self.mode == "table":
                self.preempt_next = True
            self.opp_turns()
            if self.turn in (4, 6, 8) and not self.won and not self.lost:
                self.stats[f"ang{self.turn}"] = sum(1 for p in self.creatures() if p.angel)
            if self.turn == 8 and not self.won and not self.lost:
                self.stats["t8"] = self.snapshot()
        return self

    def snapshot(self):
        fl = [p for p in self.creatures() if self.has_kw(p, "flying")]
        anthem = any(self.on_bf(n) for n in ("Lyra Dawnbringer", "Thraben Watcher", "Always Watching",
                                             "Patchwork Banner", "Vanquisher's Banner", "Heraldic Banner"))
        return dict(power=sum(self.power(p) for p in fl), flyers=len(fl), giada=self.giada() is not None,
                    anthem=anthem, lands=len(self.lands), hand=sum(1 for c in self.hand if c not in LANDS),
                    opp_life=sum(max(0, x) for x in self.opp), life=self.life,
                    answers=len(self.answers_in_hand()), boots=bool(self.giada() and self.giada().boots),
                    alive=len(self.alive()))


# hook the sorcery-speed pre-emption into our main phase
_orig_develop = Game.develop


def _develop(self, reserve=0):
    if self.mode == "table" and self._our:
        self.preempt()
    return _orig_develop(self, reserve)


Game.develop = _develop


def play(deck, seed, **kw):
    rng = random.Random(seed)
    g = Game(deck, rng, **kw)
    g.run()
    return g
