"""Monte Carlo simulator for the Gorma, the Gullet deck (goldfish + simple table).

Abstractions (documented so results can be read with the right caveats):
- Mana: colored vs colorless only (B/G treated as one colour pool).
- Opponents: 3 x 40 life. Goldfish = no blockers, no interaction.
  Table = blockers, rival kill clocks, low removal, one wipe, one counterspell (see TableCfg).
- Infinite loops are detected by rule (Gorma or Mazirek + persist creature + free outlet) and resolved
  abstractly: win if a closer is available (drainer, Jarad, infinite mana + any tutor/dig, etc.).
- Mesa v2 (16/11/2026): reglas activables una por una con TableCfg.rules (ver mesa.py).
"""
import random
from dataclasses import dataclass, field
from cards import CARDS, LANDS, COMMANDER, GREEN, LEGENDS
from mesa import MesaV2

PERSIST_LOOP = {"Putrid Goblin", "Puppeteer Clique", "Rendclaw Trow", "Lesser Masticore", "Wingrattle Scarecrow",
                "Lingering Tormentor", "Aerie Ouphes"}
OUTLETS = {"Viscera Seer", "Umbral Collar Zealot", "Yahenni, Undying Partisan", "Phyrexian Altar",
           "Ashnod's Altar", "Woe Strider", "Bloodflow Connoisseur", "Carrion Feeder",
           "Vampire Aristocrat", "Altar of Dementia", "Blasting Station", "Warren Soultrader",
           "Bloodthrone Vampire", "Spawning Pit", "Yawgmoth, Thran Physician"}
INF_MANA_OUTLETS = {"Phyrexian Altar", "Ashnod's Altar", "Warren Soultrader"}
DRAINERS = {"Blood Artist", "Zulaport Cutthroat", "Cauldron of Essence", "Vengeance Mission", "Bastion of Remembrance",
            "Poison-Tip Archer", "Falkenrath Noble", "Syr Konrad, the Grim", "Blasting Station",
            "Vengeful Bloodwitch", "Massacre Girl, Most Wanted", "Marionette Apprentice", "The Meathook Massacre",
            "Sephiroth, Fabled SOLDIER"}
ZOMBIES = {"Putrid Goblin", "Warren Soultrader", "Mikaeus, the Unhallowed"}
ENABLERS = {"Mazirek, Kraul Death Priest": 5, "Melira, Sylvok Outcast": 2, "Thran Vigil": 2, "Mikaeus, the Unhallowed": 6,
            "Support Mission": 3, "Renata, Called to the Hunt": 4, "Tribute to the World Tree": 3}
PACT = {"Butcher of Malakir", "Grave Pact", "Dictate of Erebos"}
RECUR = {"Reassembling Skeleton": (2, 2), "Teacher's Pest": (2, 2), "Tenacious Dead": (1, 2), "Gravecrawler": (1, 1)}
TUTORS = {"Diabolic Tutor", "Grim Tutor", "Diabolic Intent"}
FODDER = {"pest", "zombie", "snake", "spawn", "goat", "ninja", "stolen", "sap", "soldier", "squirrel"}
BASIC_TYPES = {"Forest", "Swamp"}


@dataclass
class TableCfg:
    clocks: tuple = ((8, 10), (9, 11), (10, 12))
    p_stoppable: float = 0.7
    delay: int = 2
    p_visible: float = 0.6
    p_removal: float = 0.10          # per rival turn
    wipe_window: tuple = (6, 10)
    p_counter: float = 0.5           # chance the counter is up when we go for the win
    threat_mix: tuple = (0.5, 0.25, 0.25)  # creature, artifact/enchantment, other
    blockers: bool = True
    hold_from_turn: int = 6
    hold_mode: str = "always"   # always (from hold_from_turn) / visible (only when a visible rival attempt is due)
    target: str = "always"      # always / sometimes / spread : who removal and attacks hit
    kinds: tuple = ()           # per rival: "combat" / "combo" (empty = random threat_mix, legacy)
    combat: bool = False        # combat rivals attack our life total
    combat_start: int = 5
    combat_k: float = 2.0       # damage per attacking rival = k * (turn - start + 1)
    n_counters: int = 1         # counters the blue player has per game
    policy: str = "rush"        # rush: combo asap / safe: wait for a window vs the blue player
    attack: str = "all"         # all / keep2 (keep 2 blockers when rivals attack)
    flyer_p: float = 0.6        # chance an opposing flyer exists (Aerie Ouphes target)
    # --- mesa v2 (16/11/2026) ---
    rules: tuple = ()           # reglas v2 activas: "rem" (pesos + remocion robada y guardada), "cnt" (counters del azul), "wipe", "clock", "edict", "hate", "combat"
    bracket: str = "B3"
    rem_mix: tuple = (0.65, 0.20, 0.07, 0.08)   # solo criaturas / cualquier permanente / artefacto-encantamiento / edicto
    p_inst: float = 0.5         # un rival con remocion responde al instante a un motor (peso >= 0,5)
    p_edict_each: float = 0.5   # un edicto usado en otro rival es "cada oponente" y tambien nos alcanza
    p_mill_escape: float = 0.03 # Altar of Dementia: algun rival se salva de perder al robar
    mz_mus: tuple = ()          # Mazmorra: turnos tipicos alternativos (optimista 4/5/7, pesimista 3/5/6)
    time_limit: bool = True     # Mazmorra: corte por tiempo
    time_life: tuple = ()       # Mazmorra: vida propia al corte sorteada (ej. (25, 38)); vacio = la del modelo
    mz_edict_p: float = 3 / 11
    mz_strip_p: float = 3 / 11
    gorma_policy: str = "asap"  # asap (apenas puede) / support (con outlet, drenador o 2 fichas; o desde el T6) / combo (solo en el turno del combo)


@dataclass
class Perm:
    name: str
    kind: str = "card"      # card / token
    tok: str = ""           # pest/zombie/snake/spawn/treasure/ninja/goat/stolen
    base: int = 0
    counters: int = 0
    minus: bool = False
    sick: bool = True
    tapped: bool = False
    creature: bool = True
    mutant: bool = False
    equipped: str = ""      # chopper / blade
    decayed: bool = False
    prepared: bool = False


class Game(MesaV2):
    def __init__(self, deck, rng, mode="goldfish", cfg=None, mull_policy="guide", log=False,
                 policy=None):
        self.rng = rng
        self.mode = mode
        self.cfg = cfg or TableCfg()
        self.logon = log
        self.policy = policy or {}
        self.deck = list(deck)
        self.library = list(deck)
        rng.shuffle(self.library)
        self.hand, self.gy, self.bf, self.lands = [], [], [], []
        self.land_tapped_now = 0
        self.tax = 0
        self.gorma_in_cmd = True
        self.opp = [40, 40, 40]
        self.cmd_dmg = [0, 0, 0]
        self.rad = [0.0, 0.0, 0.0]
        self.turn = 0
        self.on_play = rng.random() < 0.25
        self.life = 40
        self.col = self.cless = 0
        self.reserve = 0
        self.profane = []
        self.won = False
        self.lost = False
        self.win_turn = None
        self.gorma_turn = None
        self.stats = dict(mulls=0, combo_turn=None, loop_no_close=0, missing=[])
        self.counter_used = False
        self.counters_left = self.cfg.n_counters
        self.has_rival_flyer = rng.random() < self.cfg.flyer_p
        self.heroic_used = False
        self._our = True
        self.rival_next = [rng.randint(*c) for c in self.cfg.clocks]
        self.wipe_turn = rng.randint(*self.cfg.wipe_window)
        self.wipe_done = False
        self.opp_wiped_t = 0
        self._reset_turn_flags()
        if mode == "table" and "rem" in self.cfg.rules:
            self.v2_init()
        self.mulligan(mull_policy)

    # ------------------------------------------------------------------ utils
    def log(self, *a):
        if self.logon:
            print(f"[T{self.turn}]", *a)

    def _reset_turn_flags(self):
        self.deaths_turn = 0
        self.all_deaths_turn = 0
        self.lifegain_turn = 0
        self.opp_used = False
        self.dina_used = False
        self.vein_used = False
        self.inst_used = False

    def tags(self, name):
        if name in CARDS:
            return CARDS[name]["tags"]
        return set()

    def on_bf(self, name):
        return any(p.name == name for p in self.bf)

    def count_bf(self, name):
        return sum(1 for p in self.bf if p.name == name)

    def creatures(self):
        return [p for p in self.bf if p.creature]

    def creature_cards_in_gy(self):
        return sum(1 for c in self.gy if c in CARDS and CARDS[c]["t"] == "C")

    def power(self, p):
        pw = p.base + p.counters - (1 if p.minus else 0)
        if p.name == "Jarad, Golgari Lich Lord" or p.name == "Wight of the Reliquary":
            pw += self.creature_cards_in_gy()
        return max(pw, 0)

    def alive(self):
        return [i for i in range(3) if self.opp[i] > 0]

    def check_win(self):
        if not self.won and not self.lost and not self.alive():
            self.won = True
            self.win_turn = self.turn
            self.log("WIN")

    def lose_life_opp(self, i, n):
        if self.opp[i] > 0:
            self.opp[i] -= n

    def drain_each(self, n):
        for i in self.alive():
            self.lose_life_opp(i, n)
        self.check_win()

    def drain_target(self, n):
        al = self.alive()
        if al:
            i = min(al, key=lambda k: self.opp[k])
            self.lose_life_opp(i, n)
        self.check_win()

    def gain_life(self, n):
        if n <= 0:
            return
        if self.on_bf("Pest Rescuer"):
            n += self.count_bf("Pest Rescuer")
        self.life += n
        self.lifegain_turn += n
        # Veinwitch: pay B, return creature card from GY to hand (once per turn modelled)
        if self.on_bf("Veinwitch Coven") and not self.vein_used:
            target = self.best_gy_creature()
            if target and self.pay_any(0, 1):
                self.vein_used = True
                self.gy.remove(target)
                self.hand.append(target)
                self.log("Veinwitch returns", target)

    def draw(self, n=1):
        for _ in range(n):
            if self.library:
                self.hand.append(self.library.pop())

    # ------------------------------------------------------------------ mulligan
    def hand_ok_guide(self, hand, free_left):
        lands = [c for c in hand if c in LANDS]
        nl = [c for c in hand if c not in LANDS]
        n = len(lands)
        early_ramp = {"Sol Ring", "Elvish Mystic", "Arcane Signet", "Sakura-Tribe Elder", "Fanatic of Rhonas",
                      "Twitching Doll", "Llanowar Elves", "Three Visits", "Thought Vessel", "Elves of Deep Shadow",
                      "Fyndhorn Elves", "Arbor Elf", "Deathrite Shaman", "Talisman of Resilience", "Carpet of Flowers"}
        cheap = [c for c in nl if sum(CARDS[c]["cost"]) <= 2]
        heavy = [c for c in nl if sum(CARDS[c]["cost"]) >= 5]
        if n <= 1 or n >= 6:
            return False
        if n == 2:
            if any(c in early_ramp for c in hand):
                return True
            return (not self.on_play) and len(cheap) >= 2
        if len(heavy) >= 3 and free_left:
            return False
        if n == 5:
            engines = {"Morbid Opportunist", "Dina, Essence Brewer", "Gyre Sage", "Foot Chopper", "Jenova, Ancient Calamity",
                       "Garruk's Uprising", "Moldervine Reclamation", "Pest Rescuer", "Jadar, Ghoulcaller of Nephalia",
                       "Blight Mound", "Emeritus of Woe", "Diabolic Tutor", "Profane Tutor"}
            return sum(1 for c in nl if c in engines) >= 2 or not free_left
        if n == 3 and len(cheap) == 0 and free_left:
            return False
        return True

    def hand_ok_naive(self, hand, free_left):
        n = sum(1 for c in hand if c in LANDS)
        return 2 <= n <= 5

    def mulligan(self, policy):
        ok = self.hand_ok_guide if policy == "guide" else self.hand_ok_naive
        mulls = 0
        while True:
            self.library += self.hand
            self.hand = []
            self.rng.shuffle(self.library)
            self.draw(7)
            to_bottom = max(0, mulls - 1)   # first mulligan free
            free_left = mulls == 0
            if ok(self.hand, free_left) or mulls >= 3:
                break
            mulls += 1
        self.stats["mulls"] = mulls
        to_bottom = max(0, mulls - 1)
        for _ in range(to_bottom):
            self.hand.sort(key=self.bottom_key)
            c = self.hand.pop()
            self.library.insert(0, c)

    def bottom_key(self, c):
        lands = sum(1 for x in self.hand if x in LANDS)
        if c in LANDS:
            return 100 if lands > 4 else -1
        g, p = CARDS[c]["cost"]
        keep = {"Sol Ring", "Elvish Mystic", "Arcane Signet", "Sakura-Tribe Elder", "Fanatic of Rhonas",
                "Diabolic Tutor", "Profane Tutor", "Emeritus of Woe", "Putrid Goblin", "Viscera Seer"}
        if c in keep:
            return 0
        t = self.tags(c)
        if "wipe" in t or "wipe_small" in t:
            return 60
        return g + p

    # ------------------------------------------------------------------ lands & mana
    def basics_on_bf(self):
        return sum(1 for l in self.lands if LANDS[l].get("basic"))

    def has_type(self, ty):
        return any(ty in LANDS[l].get("types", set()) for l in self.lands)

    def land_enters_tapped(self, l):
        m = LANDS[l]["mode"]
        if m == "U":
            return False
        if m == "T":
            return True
        if m == "basics2":
            return self.basics_on_bf() < 2
        if m == "typed":
            return not (self.has_type("Swamp") or self.has_type("Forest"))
        if m == "snarl":
            return not any(c in ("Forest", "Swamp", "Haunted Mire", "Festering Thicket", "Turbulent Fen",
                                 "Vernal Fen") for c in self.hand)
        if m == "oppl8":
            return self.turn < 3
        if m == "deathcap":
            return len(self.lands) < 2
        return True

    def fetch_basic(self, untapped=False):
        for i in range(len(self.library) - 1, -1, -1):
            if self.library[i] in ("Forest", "Swamp"):
                b = self.library.pop(i)
                self.rng.shuffle(self.library)
                self.lands.append(b)
                if not untapped:
                    self.land_tapped_now += 1
                elif self._our:
                    self.col += 1
                self.landfall()
                return True
        return False

    def landfall(self):
        for p in self.bf:
            if p.name == "Tireless Provisioner":
                self.make_token("treasure")
        if "Bloodghast" in self.gy:
            self.gy.remove("Bloodghast")
            self.enter("Bloodghast")

    def play_land(self):
        lands = [c for c in self.hand if c in LANDS]
        if not lands:
            return
        # prefer: fetch/tapped early when nothing to cast for 1, else untapped
        def score(l):
            t = self.land_enters_tapped(l) or LANDS[l]["mode"] in ("fetch", "fabled")
            return (0 if not t else 1) if self.turn > 1 else (1 if not t else 0)
        lands.sort(key=score)
        l = lands[0]
        if self.turn == 1:
            # on turn 1 play tapped land unless we hold a 1-drop / Sol Ring
            ones = [c for c in self.hand if c not in LANDS and sum(CARDS[c]["cost"]) <= 1 and c != "Pest Infestation"]
            if ones:
                lands.sort(key=lambda x: 1 if (self.land_enters_tapped(x) or LANDS[x]["mode"] in ("fetch", "fabled")) else 0)
                l = lands[0]
        self.hand.remove(l)
        mode = LANDS[l]["mode"]
        if mode in ("fetch", "fabled"):
            self.gy.append(l)
            self.on_sacrifice_permanent()
            untapped = mode == "fabled" and len(self.lands) >= 3
            self.fetch_basic(untapped=untapped)
        else:
            tapped = self.land_enters_tapped(l)
            self.lands.append(l)
            if tapped:
                self.land_tapped_now += 1
            self.landfall()
        self.log("land", l)

    def compute_pool(self):
        col = cless = 0
        untapped_lands = self.lands[:max(0, len(self.lands) - self.land_tapped_now)]
        for l in untapped_lands:
            if LANDS[l]["col"]:
                col += 1
            else:
                cless += 1
        maxp = max([self.power(p) for p in self.creatures()] or [0])
        for p in self.bf:
            if p.tapped:
                continue
            if p.name == "Sol Ring":
                cless += 2
                p.tapped = True
            elif p.name in ("Arcane Signet", "Coalition Relic"):
                col += 1
                p.tapped = True
            elif p.name == "Thought Vessel":
                cless += 1
                p.tapped = True
            elif p.name == "Talisman of Resilience":
                col += 1; p.tapped = True
            elif p.name == "Mox Amber" and any(q.name in LEGENDS for q in self.bf if q.creature):
                col += 1; p.tapped = True
            elif p.name == "Carpet of Flowers" and not p.tapped:
                col += min(4, self.turn // 2); p.tapped = True     # Islands del azul (siempre hay uno en la mesa)
            elif p.creature and not p.sick:
                if p.name in ("Elvish Mystic", "Twitching Doll", "Xenobotanist", "Birds of Paradise", "Llanowar Elves",
                                "Elves of Deep Shadow", "Fyndhorn Elves", "Arbor Elf", "Deathrite Shaman"):
                    col += 1; p.tapped = True
                elif p.name == "Jadzia Dax":
                    col += max(1, p.counters); p.tapped = True
                elif p.name == "Fanatic of Rhonas":
                    col += 4 if maxp >= 4 else 1; p.tapped = True
                elif p.name == "Gyre Sage" and p.counters > 0:
                    col += p.counters; p.tapped = True
                elif p.name == "Selvala, Heart of the Wilds" and maxp >= 2 and col >= 1:
                    col += maxp - 1; p.tapped = True
        self.col, self.cless = col, cless

    def tokens(self, tok):
        return [p for p in self.bf if p.kind == "token" and p.tok == tok]

    def avail(self):
        return self.col + self.cless + len(self.tokens("treasure")) + len(self.tokens("spawn"))

    def can_pay(self, g, p, extra=0):
        col = self.col + len(self.tokens("treasure"))
        tot = self.avail()
        return col >= p and tot >= g + p + extra

    def pay_now(self, g, p):
        if not self.can_pay(g, p):
            return False
        # colored pips
        need_p = p
        use = min(self.col, need_p); self.col -= use; need_p -= use
        while need_p > 0:
            t = self.tokens("treasure")[0]; self.sacrifice(t); need_p -= 1
        need_g = g
        use = min(self.cless, need_g); self.cless -= use; need_g -= use
        use = min(self.col, need_g); self.col -= use; need_g -= use
        while need_g > 0 and self.tokens("spawn"):
            self.sacrifice(self.tokens("spawn")[0]); need_g -= 1
        while need_g > 0 and self.tokens("treasure"):
            self.sacrifice(self.tokens("treasure")[0]); need_g -= 1
        return need_g == 0

    # ------------------------------------------------------------------ permanents
    def make_token(self, tok, n=1, _sq=False):
        if not _sq and tok != "squirrel" and self.on_bf("Chatterfang, Squirrel General"):
            self.make_token("squirrel", n * self.count_bf("Chatterfang, Squirrel General"), _sq=True)
        if self.on_bf("Mirkwood Bats"):
            for _ in range(n):
                self.drain_each(self.count_bf("Mirkwood Bats"))
        for _ in range(n):
            base = {"pest": 1, "zombie": 2, "snake": 1, "spawn": 0, "goat": 0, "ninja": 1, "stolen": 3, "sap": 1, "soldier": 1, "squirrel": 1}.get(tok, 0)
            creature = tok != "treasure"
            p = Perm(name=tok, kind="token", tok=tok, base=base, creature=creature,
                     sick=tok not in ("stolen",), decayed=(tok == "zombie"))
            self.bf.append(p)
            if creature:
                self.on_creature_enter(p, token=True)

    def cmult(self):
        return 2 if self.on_bf("Dr. Joseph M'Benga") else 1

    def gorma(self):
        for p in self.bf:
            if p.name == COMMANDER:
                return p
        return None

    def enter(self, name, from_persist=False):
        c = CARDS[name]
        p = Perm(name=name, base=c.get("p", 0), creature=(c["t"] == "C"))
        if name == "Rampant Rejuvenator":
            p.counters = 2
        if p.creature and name != COMMANDER and self.gorma():
            p.counters += self.deaths_turn * self.cmult()
        if p.creature and "haste" in c["tags"]:
            p.sick = False
        self.bf.append(p)
        if p.creature:
            self.on_creature_enter(p, token=False)
        if name == "Emeritus of Woe":
            p.prepared = True
        if name == "Foot Chopper":
            self.make_token("ninja")
            for q in self.bf:
                if q.tok == "ninja" and not q.equipped:
                    q.equipped = "chopper"; break
        if name == "Merchant of Venom":
            f = self.pick_fodder()
            if f:
                self.sacrifice(f)
        if name == "Garruk's Uprising" and any(self.power(q) >= 4 for q in self.creatures()):
            self.draw(1)
        if name == "Bastion of Remembrance":
            self.make_token("soldier")  # 1/1 Human Soldier as fodder
        if name == "Sidisi, Undead Vizier":
            f = self.pick_fodder()
            if f:
                self.sacrifice(f); self.tutor()
        if name == "Sephiroth, Fabled SOLDIER":
            f = self.pick_fodder()
            if f:
                self.sacrifice(f); self.draw(1)
        if name == "Khan, Vengeful Heart":
            f = self.pick_fodder()
            if f:
                self.sacrifice(f); self.draw(2)
        if name == "Puppeteer Clique" and self.mode == "table" and self.turn >= 5:
            self.make_token("stolen")
        if not from_persist and self.mode == "table" and self._our and "rem" in self.cfg.rules:
            self.v2_instant(p)
        return p

    def on_creature_enter(self, p, token):
        if not token and self.on_bf("Garruk's Uprising") and self.power(p) >= 4:
            self.draw(1)
        for g in self.bf:
            if g.name == "Gyre Sage" and g is not p and self.power(p) > self.power(g):
                g.counters += 1
        if not token and self.on_bf("Selvala, Heart of the Wilds"):
            others = [self.power(q) for q in self.creatures() if q is not p]
            if all(self.power(p) > o for o in others):
                self.draw(1)

    def on_sacrifice_permanent(self):
        # Mazirek: whenever a player sacrifices another permanent
        for m in self.bf:
            if m.name == "Mazirek, Kraul Death Priest":
                for q in self.creatures():
                    q.counters += 1
                    if q.minus and q.counters > 0:
                        q.minus = False; q.counters -= 1
        for m in self.bf:
            if m.name == "Merchant of Venom":
                m.counters += 1

    def sacrifice(self, p):
        if p not in self.bf:
            return
        self.bf.remove(p)
        self.on_sacrifice_permanent()
        if p.kind == "token" and self.on_bf("Mirkwood Bats"):
            self.drain_each(self.count_bf("Mirkwood Bats"))
        if p.creature:
            self.dies(p, sacrificed=True)
        else:
            if p.kind == "card":
                self.gy.append(p.name)

    def destroy(self, p):
        if p in self.bf:
            self.bf.remove(p)
            if p.creature:
                self.dies(p, sacrificed=False)
            elif p.kind == "card":
                self.gy.append(p.name)

    def dies(self, p, sacrificed):
        self.deaths_turn += 1
        self.all_deaths_turn += 1
        pw = self.power(p)
        tok = p.kind == "token"
        # drains
        for q in self.bf + [p]:
            if q.name == "Blood Artist":
                self.drain_target(1); self.gain_life(1)
        for q in self.bf + [p]:
            if q.name == "Zulaport Cutthroat":
                self.drain_each(1); self.gain_life(1)
        for q in self.bf:
            if q.name == "Cauldron of Essence":
                self.drain_each(1); self.gain_life(1)
        for q in self.bf:
            if q.name == "Vengeance Mission":
                self.drain_target(1)
            if q.name == "Bastion of Remembrance":
                self.drain_each(1); self.gain_life(1)
            if q.name in ("Poison-Tip Archer", "Syr Konrad, the Grim") and q is not p:
                self.drain_each(1)
            if q.name == "Falkenrath Noble":
                self.drain_target(1); self.gain_life(1)
            if q.name == "Vengeful Bloodwitch":
                self.drain_target(1); self.gain_life(1)
            if q.name == "Massacre Girl, Most Wanted" and q is not p:
                self.drain_target(1); self.gain_life(1)
            if q.name == "Marionette Apprentice" and q is not p:
                self.drain_each(1)
            if q.name == "Sifter of Skulls" and not tok and q is not p:
                self.make_token("spawn")
            if q.name == "Blasting Station" and sacrificed:
                self.drain_target(1)
            if q.name == "Midnight Reaper" and not tok:
                self.draw(1)
            if q.name == "Grim Haruspex" and not tok and q is not p:
                self.draw(1)
            if q.name == "Fecundity" and not tok:
                self.draw(1)
        if self.on_bf("Grand Nagus Zek") and not getattr(self, "_zek", None) == (self.turn, self._our):
            self._zek = (self.turn, self._our); self.make_token("treasure")
        if sacrificed and self.on_bf("Yawgmoth, Thran Physician") and getattr(self, "_yawg", (None, 0))[0] != self.turn:
            self._yawg = (self.turn, 0)
        if sacrificed and self.on_bf("Yawgmoth, Thran Physician") and self._yawg[1] < 2 and self.life > 10 and p.name != "Yawgmoth, Thran Physician":
            self._yawg = (self.turn, self._yawg[1] + 1); self.life -= 1; self.draw(1)
        if self.on_bf("Sephiroth, Fabled SOLDIER") and p.name != "Sephiroth, Fabled SOLDIER":
            self.drain_target(1); self.gain_life(1)
        if self.on_bf("The Meathook Massacre"):
            self.drain_each(1)
        if self.mode == "table" and "edict" in self.cfg.rules and (any(self.on_bf(x) for x in PACT) or p.name == "Butcher of Malakir"):
            self.pact_t = getattr(self, "pact_t", []) + [self.turn]
            self.stats["pact_edicts"] = self.stats.get("pact_edicts", 0) + 1
        g = self.gorma()
        if g and p is not g:
            g.counters += self.cmult()
        for q in self.bf:
            if q.name == "Ygra, Eater of All" and q is not p:
                q.counters += 2
        for q in self.bf:
            if q.name == "Feral Ghoul":
                q.counters += 1
            if q.equipped == "blade":
                q.counters += 1
        for q in self.bf:
            if q.name == "Moldervine Reclamation":
                self.gain_life(1); self.draw(1)
        if self.on_bf("Morbid Opportunist") and not self.opp_used:
            self.opp_used = True; self.draw(1)
        if sacrificed and self.on_bf("Dina, Essence Brewer") and not self.dina_used:
            self.dina_used = True; self.draw(1)
        for q in self.bf:
            if q.name == "Pitiless Plunderer":
                self.make_token("treasure")
        if not tok:
            for q in self.bf + [p]:
                if q.name == "Pawn of Ulamog":
                    self.make_token("spawn")
            for q in self.bf:
                if q.name == "Blight Mound":
                    self.make_token("pest")
        if tok and p.tok == "pest":
            self.gain_life(1)
        if p.name == "Haywire Mite":
            self.gain_life(2)
        if p.name == "Rampant Rejuvenator":
            for _ in range(pw):
                self.fetch_basic(untapped=True)
        if p.mutant and self.in_our_turn:
            self.draw(pw)
        if p.name == "Feral Ghoul":
            for i in self.alive():
                self.rad[i] += pw * 0.6
        if p.name == COMMANDER:
            self.tax += 2
            self.gorma_in_cmd = True
            return
        if p.name == "Tenacious Dead" and not getattr(self, "gy_locked", False) and self.pay_any(1, 1):
            q = self.enter("Tenacious Dead", from_persist=True); q.tapped = True
            return
        # Nether Traitor return (another creature put into GY)
        if p.name != "Nether Traitor" and "Nether Traitor" in self.gy:
            if self.pay_any(0, 1):
                self.gy.remove("Nether Traitor"); self.enter("Nether Traitor", from_persist=True)
        if tok:
            return
        if getattr(self, "gy_locked", False):
            return              # Rest in Peace rival: va al exilio, sin persist ni cementerio
        # persist
        if "persist" in self.tags(p.name) or p.name == "Woodfall Primus":
            if not p.minus:
                q = self.enter(p.name, from_persist=True)
                q.minus = True
                if self.on_bf("Melira, Sylvok Outcast") or (self.on_bf("Thran Vigil") and self.in_our_turn):
                    q.minus = False
                if q.counters > 0 and q.minus:
                    q.minus = False; q.counters -= 1
                return
        if p.creature and p.kind == "card" and self.on_bf("Mikaeus, the Unhallowed") and p.name != "Mikaeus, the Unhallowed" \
                and p.counters <= 0:
            q = self.enter(p.name, from_persist=True)
            q.counters += 1; q.minus = False
            return
        self.gy.append(p.name)

    def pay_any(self, g, p):
        # in our turn use pool; in opponents' turns use reserve (untapped mana left)
        if self.in_our_turn:
            return self.pay_now(g, p)
        if self.reserve >= g + p:
            self.reserve -= g + p
            return True
        return False

    def pick_fodder(self, exclude=None):
        order = ["spawn", "pest", "squirrel", "soldier", "sap", "zombie", "snake", "goat", "ninja", "stolen"]
        for tok in order:
            for p in self.bf:
                if p.kind == "token" and p.tok == tok and p is not exclude and p.creature:
                    if tok == "spawn" and self.in_our_turn:
                        continue  # spawns better kept for mana
                    return p
        return None

    def free_outlet(self):
        for p in self.bf:
            if p.name == "Aerie Ouphes" and (self.has_rival_flyer or any("flying" in self.tags(q.name) for q in self.bf if q.kind == "card")):
                return p
            if p.name in OUTLETS:
                if p.name == "Yahenni, Undying Partisan" and len(self.creatures()) < 2:
                    continue
                return p
        return None

    def sac_with_outlet(self, f):
        o = self.free_outlet()
        if not o or f is o:
            return False
        if o.name in ("Phyrexian Altar",):
            self.col += 1
        elif o.name == "Ashnod's Altar":
            self.cless += 2
        self.sacrifice(f)
        return True

    def payoffs_present(self):
        return bool(self.gorma()) or any(self.on_bf(n) for n in (
            "Blood Artist", "Zulaport Cutthroat", "Cauldron of Essence", "Moldervine Reclamation",
            "Morbid Opportunist", "Dina, Essence Brewer", "Pitiless Plunderer", "Mazirek, Kraul Death Priest",
            "Phyrexian Altar", "Ashnod's Altar", "Feral Ghoul"))

    # ------------------------------------------------------------------ combo detection
    def loop_ready_on_bf(self):
        en = self.gorma() is not None or any(self.on_bf(x) for x in ENABLERS)
        pers = any(p.name in PERSIST_LOOP and not (p.minus and not any(self.on_bf(x) for x in ENABLERS))
                   for p in self.bf)
        out = self.free_outlet() is not None
        nether = (self.on_bf("Nether Traitor") or "Nether Traitor" in self.gy) and self.on_bf("Pawn of Ulamog") \
            and self.on_bf("Pitiless Plunderer") and out
        return (en and pers and out), nether

    def cost_of(self, name):
        g, p = CARDS[name]["cost"]
        if name == COMMANDER:
            g += self.tax
        return g, p

    def try_win(self):
        """Look for a combo kill this turn. Returns True if we won."""
        if self.won:
            return True
        M = self.avail() + (self.fodder_count() if self.on_bf("Phyrexian Altar") else 0)
        if "Dark Ritual" in self.hand:
            M += 2
        if "Culling the Weak" in self.hand and self.fodder_count() > 0:
            M += 3
        if "Cabal Ritual" in self.hand:
            M += 1
        if "Lotus Petal" in self.hand:
            M += 1
        hand = list(self.hand)
        swamp_forest = self.has_type("Swamp") and self.has_type("Forest")

        def opts_enabler():
            o = []
            if self.gorma():
                o.append((0, None))
            elif self.gorma_in_cmd:
                g, p = self.cost_of(COMMANDER); o.append((g + p, COMMANDER))
            for x, cx in ENABLERS.items():
                if self.on_bf(x):
                    o.append((0, None))
                elif x in hand:
                    o.append((cx, x))
            return o

        def opts_persist():
            o = []
            mz = any(self.on_bf(x) for x in ENABLERS)
            if any(p.name in PERSIST_LOOP and (not p.minus or mz) for p in self.bf):
                o.append((0, None))
            for c in hand:
                if c in PERSIST_LOOP:
                    o.append((sum(CARDS[c]["cost"]), c))
            gyp = [c for c in self.gy if c in PERSIST_LOOP]
            if gyp and self.on_bf("Cauldron of Essence") and self.fodder_count() > 0:
                o.append((3, "GY:" + gyp[0]))
            if gyp and "Dread Return" in hand:
                o.append((4, "GY:" + gyp[0]))
            if gyp and "Dread Return" in self.gy and len(self.sac_pool()) >= 3:
                o.append((0, "GY:" + gyp[0]))       # flashback: sacrificar 3 criaturas
            if gyp and "Persist" in hand and (self.fodder_count() > 0 or self.deaths_turn > 0):
                o.append((2, "GY:" + gyp[0]))
            return o

        def opts_outlet():
            o = []
            fo = self.free_outlet()
            if fo:
                o.append((0, None, fo.name))
            for c in hand:
                if c in OUTLETS:
                    o.append((sum(CARDS[c]["cost"]), c, c))
            if "Aerie Ouphes" in hand and self.has_rival_flyer:
                o.append((0, "OUPHES_HAND", "Aerie Ouphes"))  # same card as the persist piece (cost counted there)
            # Greater Good (22/11): outlet que roba = poder y descarta 3; el robo obligatorio limita el loop (~10 vueltas)
            if self.on_bf("Greater Good"):
                o.append((0, None, "Greater Good"))
            elif "Greater Good" in hand:
                o.append((4, "Greater Good", "Greater Good"))
            return o

        tutors = []   # (cost to get the piece into play-ready state, puts creature onto battlefield?)
        fod = self.fodder_count()
        ncre = len([p for p in self.creatures() if not p.tapped])
        TH = {"Diabolic Tutor": 4, "Grim Tutor": 3, "Dina's Guidance": 3, "Demonic Tutor": 2, "Archdruid's Charm": 3}
        for t, cst in TH.items():
            if t in hand:
                tutors.append((cst, False))
        if "Diabolic Intent" in hand and fod > 0:
            tutors.append((2, False))
        if "Eldritch Evolution" in hand and fod > 0:
            tutors.append((3, True))
        for xc in ("Chord of Calling", "Finale of Devastation"):
            if xc in hand:
                xt = self.tutor_target(creature_only=True)
                if xt:
                    tutors.append((self.x_tutor_cost(xc, xt), True))
        if "Green Sun's Zenith" in hand and "Aerie Ouphes" in self.library:
            tutors.append((7, True))
        if "Beseech the Mirror" in hand:
            tutors.append((4, fod > 0))
        if "Sidisi, Undead Vizier" in hand and fod > 0:
            tutors.append((5, False))
        if self.on_bf("Wishclaw Talisman"):
            tutors.append((1, False))
        elif "Wishclaw Talisman" in hand:
            tutors.append((3, False))
        for p in self.bf:
            if p.name == "Fauna Shaman" and not p.tapped and not p.sick and any(c in CARDS and CARDS[c]["t"] == "C" for c in hand):
                tutors.append((1, False))
            if p.name == "Emeritus of Woe" and p.prepared:
                tutors.append((2, False))
        if "Emeritus of Woe" in hand:
            tutors.append((6, False))
        tutors.sort()
        best_tutor = tutors[0][0] if tutors else None
        self._tutors = tutors
        lib = set(self.library)

        best = None
        for ce, en in opts_enabler():
            for cp, pe in opts_persist() + ([(None, "TUTOR")] if best_tutor is not None and any(c in lib for c in PERSIST_LOOP) else []):
                for oo in opts_outlet() + ([(None, "TUTOR", "Viscera Seer")] if best_tutor is not None and "Viscera Seer" in lib else []):
                    co, oc, oname = oo
                    if oc == "OUPHES_HAND":
                        if pe != "Aerie Ouphes":
                            continue
                        oc = None
                    used_tutor = 0
                    cost = ce
                    if pe == "TUTOR":
                        tc, tbf = tutors[used_tutor]; used_tutor += 1; cost += tc + (0 if tbf else 2)
                    else:
                        cost += cp
                    if oc == "TUTOR":
                        if used_tutor >= len(tutors):
                            continue
                        tc, tbf = tutors[used_tutor]; used_tutor += 1; cost += tc + (0 if tbf else 1)
                    else:
                        cost += co
                    if cost > M:
                        continue
                    left = M - cost
                    inf = (oname in INF_MANA_OUTLETS) or self.on_bf("Pitiless Plunderer") or \
                        (any(p.name in INF_MANA_OUTLETS for p in self.bf)) or \
                        ((self.on_bf("Pawn of Ulamog") or self.on_bf("Sifter of Skulls")) and left >= 2)   # 22/11: Spawn por cada muerte = maná incoloro infinito (los símbolos de color salen de lo que sobra)
                    tutor_left = used_tutor < len(tutors)
                    closed = self.closer_ok(left, inf, tutor_left, tutors[used_tutor][0] if tutor_left else None, hand, lib, swamp_forest,
                                            outlet_name=oname)
                    if closed:
                        if best is None or cost < best[0]:
                            best = (cost, en, pe, oc, closed)
        # --- alternative lines (not needing Gorma). Each: list of (piece options) + closer.
        def opt(name, cost_hand, extra_ok=True):
            if not extra_ok:
                return None
            if self.on_bf(name):
                return 0
            if name in hand:
                return cost_hand
            return None
        alt = []
        fo = self.free_outlet()
        # 1) recursive creature + Phyrexian Altar / Warren Soultrader (+ extra mana source when the return costs 2)
        engines = [(x, opt(x, 3)) for x in ("Phyrexian Altar", "Warren Soultrader")]
        extras = [(x, opt(x, c)) for x, c in (("Pitiless Plunderer", 4), ("Pawn of Ulamog", 3), ("Blight Mound", 3))]
        zombie_bf = any((p.kind == "card" and p.name in ZOMBIES) or (p.kind == "token" and p.tok == "zombie") for p in self.bf)
        for r, (cast_c, ret_c) in RECUR.items():
            if self.on_bf(r):
                rc = 0
            elif r in hand:
                rc = cast_c
            elif r in self.gy and r != "Tenacious Dead":
                rc = ret_c
            else:
                continue
            for en, ec in engines:
                if ec is None:
                    continue
                zc = 0
                if r == "Gravecrawler" and not zombie_bf:
                    if en == "Warren Soultrader":
                        zc = 0
                    elif "Putrid Goblin" in hand:
                        zc = 2
                    else:
                        continue
                if ret_c <= 1:
                    alt.append((rc + ec + zc, "recur:" + r + "+" + en))
                else:
                    for xn, xc in extras:
                        if xc is not None:
                            alt.append((rc + ec + xc, "recur:" + r + "+" + en + "+" + xn))
        # 2) Mazirek + Basking Broodscale (infinite spawns and deaths)
        mz = opt("Mazirek, Kraul Death Priest", 5)
        if mz is not None:
            bb = opt("Basking Broodscale", 2)
            if bb is not None:
                alt.append((mz + bb, "mazirek+broodscale"))
            so = opt("Scurry Oak", 3)
            if so is not None and fo is not None:
                alt.append((mz + so, "mazirek+scurry oak"))
        # 3) Beifong's Bounty Hunters + Bloodghast + free outlet
        bh = opt("Beifong's Bounty Hunters", 4)
        if bh is not None and fo is not None and (self.on_bf("Bloodghast") or "Bloodghast" in hand or "Bloodghast" in self.gy):
            bgc = 0 if self.on_bf("Bloodghast") else 2
            alt.append((bh + bgc, "hunters+bloodghast"))
        # 4) Chatterfang + Pitiless Plunderer
        ch = opt("Chatterfang, Squirrel General", 3)
        pl = opt("Pitiless Plunderer", 4)
        if ch is not None and pl is not None and (self.fodder_count() > 0 or self.creatures()):
            alt.append((ch + pl + 1, "chatterfang+plunderer"))
        # 5) Witherbloom Apprentice + Chain of Smog (sin Gorma): copias infinitas que drenan
        ap = opt("Witherbloom Apprentice", 2)
        if ap is not None and "Chain of Smog" in hand:
            alt.append((ap + 2, "apprentice+smog"))
        for cost, name in alt:
            if cost > M:
                continue
            if name == "apprentice+smog":
                if best is None or cost < best[0]:
                    best = (cost, None, None, None, "smog")
                continue
            infm = name.startswith("recur") or name.startswith("chatterfang")
            closed = self.closer_ok(M - cost, infm, best_tutor is not None, best_tutor, hand, lib, swamp_forest, outlet_name=name)
            if closed and (best is None or cost < best[0]):
                best = (cost, None, None, None, name + "+" + closed)
        if best is None:
            ready, nether = self.loop_ready_on_bf()
            if ready and not getattr(self, "_looped", None) == self.turn:
                self._looped = self.turn
                self.stats["loop_no_close"] += 1
                g = self.gorma()
                if g:
                    g.counters += 50
                    self.log("loop without closer: Gorma huge")
            return False
        cost, en, pe, oc, closed = best
        if self.mode == "table" and "cnt" in self.cfg.rules:
            urgent = any(self.opp[i] > 0 and self.rival_next[i] <= self.turn + 1 for i in range(3))
            if self.cfg.policy == "safe" and self.blue_open and cost > 0 and not urgent and self.turn < 16 \
                    and not ("Veil of Summer" in self.hand and M - cost >= 1):
                self.stats["waited"] = self.stats.get("waited", 0) + 1
                return False
            if cost > 0:
                pieces = [x for x in (en, pe, oc) if x and x != "TUTOR" and not str(x).startswith("GY:")]
                victim = max(pieces, key=lambda c: sum(CARDS[c]["cost"])) if pieces else "TUTOR"
                self.stats["combo_tries"] = self.stats.get("combo_tries", 0) + 1
                if self.counter_try(victim, win=True):
                    if victim == COMMANDER:
                        self.tax += 2
                    elif victim in self.hand:
                        self.hand.remove(victim); self.gy.append(victim)
                    return False
            return self._finish_combo(closed, en, pe, oc)
        # counterspell check (table)
        urgent = any(self.opp[i] > 0 and self.rival_next[i] <= self.turn + 1 for i in range(3))
        if getattr(self, "_uproll", (None, None))[0] != (self.turn, self.counters_left):
            self._uproll = ((self.turn, self.counters_left), self.rng.random() < self.cfg.p_counter)
        up = self.mode == "table" and self.counters_left > 0 and cost > 0 and self._uproll[1]
        veil_ok = "Veil of Summer" in self.hand and M - cost >= 1
        if up and self.cfg.policy == "safe" and not veil_ok and not urgent and self.turn < 16:
            self.log("safe: blue has a counter up, waiting")
            self.stats["waited"] = self.stats.get("waited", 0) + 1
            return False
        if up:
            self.stats["cnt_used"] = self.stats.get("cnt_used", 0) + 1
            self.counters_left -= 1
            self.counter_used = self.counters_left <= 0
            if "Veil of Summer" in self.hand and M - cost >= 1:
                self.hand.remove("Veil of Summer"); self.gy.append("Veil of Summer")
            else:
                # the most expensive piece we cast is countered
                pieces = [x for x in (en, pe, oc) if x and x != "TUTOR" and not str(x).startswith("GY:")]
                if pieces:
                    victim = max(pieces, key=lambda c: sum(CARDS[c]["cost"]))
                    self.pay_now(*self.cost_of(victim)) if self.can_pay(*self.cost_of(victim)) else None
                    if victim == COMMANDER:
                        self.tax += 2
                    elif victim in self.hand:
                        self.hand.remove(victim); self.gy.append(victim)
                    self.log("COUNTERED", victim)
                    return False
        return self._finish_combo(closed, en, pe, oc)

    def _finish_combo(self, closed, en, pe, oc):
        if str(closed).endswith("mill"):
            self.stats["mill"] = 1
            if self.mode == "table" and self.rng.random() < self.cfg.p_mill_escape:
                self.stats["mill_escape"] = 1
                g = self.gorma()
                if g:
                    g.counters += 50
                self.log("mill: a rival escapes")
                return False
        self.log("COMBO WIN via", closed, "pieces", en, pe, oc)
        self.stats["combo_turn"] = self.turn
        self.stats["closer"] = closed
        for i in self.alive():
            self.opp[i] = 0
        self.check_win()
        return True

    def closer_ok(self, left, inf, tutor_left, tcost, hand, lib, sf, outlet_name):
        if outlet_name == "Greater Good":
            # 22/11: con Greater Good el loop no es infinito (robo obligatorio): cava hasta un outlet de verdad y un cierre
            selfc = [sum(CARDS[c]["cost"]) for c in lib if c in ("Altar of Dementia", "Blasting Station")]
            outs = [sum(CARDS[c]["cost"]) for c in lib if c in OUTLETS]
            best = min(selfc) if selfc else None
            if outs:
                cand = min(outs) + (0 if any(self.on_bf(d) for d in DRAINERS) else 2)
                best = cand if best is None else min(best, cand)
            return "gg-dig" if best is not None and (inf or left >= best) else None
        if outlet_name == "Blasting Station":
            return "station"
        if self.on_bf("Mirkwood Bats") and any(self.on_bf(x) for x in ("Pitiless Plunderer", "Pawn of Ulamog", "Blight Mound", "Sifter of Skulls")):
            return "bats"
        if outlet_name == "Yawgmoth, Thran Physician" and self.life > 8 and (inf or left >= 3) and (any(c in lib for c in DRAINERS) or "Jarad, Golgari Lich Lord" in lib or any(c in hand for c in DRAINERS)):
            return "yawgmoth-dig"
        if any(self.on_bf(d) for d in DRAINERS):
            return "drainer"
        if self.on_bf("Feral Ghoul") or (("Feral Ghoul" in hand) and (inf or left >= 3)):
            return "feral"
        if self.on_bf("Defiling Daemogoth") and (self.on_bf("Moldervine Reclamation") or self.on_bf("Blight Mound")):
            return "daemogoth"
        if self.on_bf("Jarad, Golgari Lich Lord") and (inf or left >= 3):
            return "jarad"
        # Walking Ballista (17/11): tras el loop de Gorma entra con N contadores (X=0); en mesa, con maná infinito
        if "Walking Ballista" in hand or (self.on_bf("Walking Ballista") and inf):
            return "ballista"
        # Altar of Dementia (16/11): el loop muele las tres bibliotecas; pierden al robar
        if outlet_name == "Altar of Dementia" or self.on_bf("Altar of Dementia"):
            return "mill"
        # 22/11: cierres desde el cementerio. Zealot (vigilar 1 en cada vuelta) manda un drenador de criatura al cementerio;
        # Desperate Plea sacrifica la criatura con persist (ya enorme) y lo devuelve al campo; Find lo devuelve a la mano.
        cdr = [c for c in DRAINERS if c in CARDS and CARDS[c]["t"] == "C"]
        zealot = outlet_name == "Umbral Collar Zealot" or self.on_bf("Umbral Collar Zealot")
        reach = any(c in self.gy for c in cdr) or (zealot and any(c in lib for c in cdr))
        if reach and "Desperate Plea" in hand and (inf or left >= 2):
            return "plea"
        if reach and "Find // Finality" in hand and (inf or left >= 4):
            return "find"
        if zealot and any(c in lib for c in cdr):
            # dejar el drenador arriba con el vigilar y robarlo: Morbid Opportunist o Dina lanzados DESPUÉS de empezar el loop
            # (si ya estaban en mesa, su robo de una vez por turno salió en la primera muerte, antes de encontrarlo)
            if any(d in hand for d in ("Morbid Opportunist", "Dina, Essence Brewer")) and (inf or left >= 5):
                return "zealot-draw"
            # Veinwitch: cada Pest de Blight Mound que muere da 1 de vida -> pagar {B} y devolver el drenador a la mano
            if self.on_bf("Veinwitch Coven") and self.on_bf("Blight Mound") and (inf or left >= 3):
                return "zealot-veinwitch"
        # 22/11b: motores de robo por muerte (Grim Haruspex, Midnight Reaper, Smothering Abomination, Fecundity, Yawgmoth en mesa;
        # Skullclamp solo con maná infinito: equipar {1} por vuelta). Con el loop roban toda la biblioteca: falta pagar el cierre que aparezca.
        DD = {"Grim Haruspex": 3, "Midnight Reaper": 3, "Smothering Abomination": 4, "Fecundity": 3}
        ddc = None
        for d, c in DD.items():
            if d == "Midnight Reaper" and self.life <= 12:
                continue
            if self.on_bf(d):
                ddc = 0
            elif d in hand and (ddc is None or c < ddc):
                ddc = c
        if self.on_bf("Yawgmoth, Thran Physician") and self.life > 10:
            ddc = 0
        if inf and (self.on_bf("Skullclamp") or "Skullclamp" in hand):
            ddc = 0 if ddc is None else ddc
        if ddc is not None and (inf or left >= ddc):
            fin = [c for c in lib if c in DRAINERS or c in ("Jarad, Golgari Lich Lord", "Altar of Dementia", "Feral Ghoul")]
            if inf and fin:
                return "inf+deathdraw"
            rest = left - ddc
            need = [sum(CARDS[c]["cost"]) + (3 if c == "Jarad, Golgari Lich Lord" else 0) for c in fin]
            if fin:
                need += [sum(CARDS[c]["cost"]) for c in lib if c in ("Phyrexian Altar", "Ashnod's Altar", "Pitiless Plunderer")]
            if need and rest >= min(need):
                return "deathdraw"
        hand_closers = [c for c in hand if c in DRAINERS or c == "Jarad, Golgari Lich Lord"]
        if inf:
            if hand_closers:
                return "inf+hand"
            if "Jarad, Golgari Lich Lord" in self.gy and sf:
                return "inf+jaradgy"
            if tutor_left:
                return "inf+tutor"
            if self.on_bf("Moldervine Reclamation") or "Moldervine Reclamation" in hand or \
               self.on_bf("Greater Good") or "Greater Good" in hand or \
               self.on_bf("Garruk's Uprising") or "Garruk's Uprising" in hand:
                if any(c in lib for c in DRAINERS) or "Jarad, Golgari Lich Lord" in lib:
                    return "inf+dig"
            if outlet_name == "Umbral Collar Zealot" and sf and "Jarad, Golgari Lich Lord" in lib:
                return "inf+zealot"
            if "Defiling Daemogoth" in hand and ("Pest Infestation" in hand or self.on_bf("Blight Mound")
                                                 or "Moldervine Reclamation" in hand):
                return "inf+daemogoth"
            return None
        for c in hand_closers:
            g, p = CARDS[c]["cost"]
            need = g + p + (3 if c == "Jarad, Golgari Lich Lord" else 0)
            if need <= left:
                return "hand"
        if "Jarad, Golgari Lich Lord" in self.gy and sf and left >= 7:
            return "jaradgy"
        if tutor_left and left >= tcost + 2:
            return "tutor"
        if self.on_bf("Moldervine Reclamation") and left >= 2 and any(c in lib for c in ("Blood Artist", "Zulaport Cutthroat")):
            return "dig"
        # 22/11: Garruk's Uprising roba cada vez que entra una criatura con poder 4+; con Gorma, la criatura con persist
        # vuelve más grande en cada vuelta -> desde la 2.ª-3.ª vuelta roba 1 por vuelta (robo obligatorio: cortar a tiempo)
        upr = self.on_bf("Garruk's Uprising") or ("Garruk's Uprising" in hand and left >= 3)
        if upr and left - (0 if self.on_bf("Garruk's Uprising") else 3) >= 2 and any(c in lib for c in cdr):
            return "uprising-dig"
        if outlet_name == "Umbral Collar Zealot" and sf and left >= 7 and "Jarad, Golgari Lich Lord" in lib:
            return "zealot-jarad"
        return None

    def fodder_count(self):
        return sum(1 for p in self.bf if p.kind == "token" and p.tok in FODDER and p.creature)

    # ------------------------------------------------------------------ tutor targets
    def tutor_target(self, creature_only=False, green=False):
        lib = [c for c in self.library if (not creature_only or (c in CARDS and CARDS[c]["t"] == "C")) and (not green or c in GREEN)]
        cheap = lambda s: sorted([c for c in lib if c in s], key=lambda c: sum(CARDS[c]["cost"]))
        have = set(self.hand) | {p.name for p in self.bf}
        if not any(c in PERSIST_LOOP for c in have) and cheap(PERSIST_LOOP):
            return cheap(PERSIST_LOOP)[0]
        if not any(c in OUTLETS for c in have) and cheap(OUTLETS):
            return cheap(OUTLETS)[0]
        if not any(c in DRAINERS or c in ("Jarad, Golgari Lich Lord", "Walking Ballista", "Altar of Dementia") for c in have):
            cl = cheap(DRAINERS | {"Jarad, Golgari Lich Lord", "Walking Ballista"})
            if cl:
                return cl[0]
        for c in ("Moldervine Reclamation", "Pest Rescuer", "Morbid Opportunist"):
            if c in lib:
                return c
        return lib[-1] if lib else None

    def tutor(self, creature_only=False, top=False, to_bf=False, green=False):
        t = self.tutor_target(creature_only, green)
        if t:
            self.library.remove(t)
            self.rng.shuffle(self.library)
            if top:
                self.library.append(t)  # top of library = end of list (draw pops from the end)
            elif to_bf and t in CARDS and CARDS[t]["t"] == "C":
                self.enter(t)
            else:
                self.hand.append(t)
            self.log("tutor ->", t, "(top)" if top else ("(bf)" if to_bf else ""))

    def coco(self):
        """mira las 6 de arriba y pone hasta 2 criaturas de coste 3 o menos, primero las piezas del combo que faltan"""
        top = self.library[-6:]
        del self.library[-6:]
        have = {p.name for p in self.bf}
        def rank(c):
            if c in PERSIST_LOOP and not any(x in have for x in PERSIST_LOOP): return 0
            if c in OUTLETS and not any(x in have for x in OUTLETS): return 1
            if c in DRAINERS and not any(x in have for x in DRAINERS): return 2
            return 3
        cre = sorted([x for x in top if x in CARDS and CARDS[x]["t"] == "C" and sum(CARDS[x]["cost"]) <= 3], key=rank)[:2]
        for x in cre:
            top.remove(x); self.enter(x); have.add(x)
            self.log("CoCo ->", x)
        self.library[0:0] = top
        self.stats["coco_hits"] = self.stats.get("coco_hits", 0) + len(cre)

    def best_gy_creature(self):
        pref = ["Putrid Goblin", "Rendclaw Trow", "Viscera Seer", "Zulaport Cutthroat", "Blood Artist",
                "Haywire Mite", "Pest Rescuer", "Morbid Opportunist", "Jadar, Ghoulcaller of Nephalia",
                "Umbral Collar Zealot", "Puppeteer Clique", "Pitiless Plunderer", "Mazirek, Kraul Death Priest"]
        for c in pref:
            if c in self.gy:
                return c
        cs = [c for c in self.gy if c in CARDS and CARDS[c]["t"] == "C"]
        return cs[0] if cs else None

    # ------------------------------------------------------------------ development
    PRIORITY = {
        "Sol Ring": 1, "Elvish Mystic": 2, "Arcane Signet": 3, "Sakura-Tribe Elder": 4, "Fanatic of Rhonas": 4,
        "Twitching Doll": 5, "Wight of the Reliquary": 6,
        COMMANDER: 10,
        "Profane Tutor": 15,
        "Jadar, Ghoulcaller of Nephalia": 20, "Pest Rescuer": 21, "Blight Mound": 22, "Zulaport Cutthroat": 23,
        "Blood Artist": 24, "Viscera Seer": 25, "Umbral Collar Zealot": 25, "Putrid Goblin": 26,
        "Morbid Opportunist": 27, "Cauldron of Essence": 28, "Phyrexian Altar": 28, "Pawn of Ulamog": 29,
        "Pitiless Plunderer": 30, "Ophiomancer": 31, "Dina, Essence Brewer": 32, "Yahenni, Undying Partisan": 34,
        "Veinwitch Coven": 35, "Eccentric Pestfinder": 36, "Mazirek, Kraul Death Priest": 37,
        "Moldervine Reclamation": 38, "Defiling Daemogoth": 39, "Jenova, Ancient Calamity": 40,
        "Garruk's Uprising": 41, "Bloodghast": 42, "Nether Traitor": 43, "Feral Ghoul": 44,
        "Emeritus of Woe": 33, "Diabolic Tutor": 46, "Puppeteer Clique": 47, "Rendclaw Trow": 48,
        "Selvala, Heart of the Wilds": 49, "Rampant Rejuvenator": 50, "Gyre Sage": 51, "Insidious Fungus": 52,
        "Merchant of Venom": 53, "Priest of Forgotten Gods": 54, "Foot Chopper": 55,
        "The Gitrog, Ravenous Ride": 56, "Greater Good": 57, "Butcher of Malakir": 58,
        "Jarad, Golgari Lich Lord": 59, "Woodfall Primus": 60, "Traverse the Outlands": 45, "Blade of the Bloodchief": 62,
        "Haywire Mite": 63, "Thrashing Brontodon": 64, "Smothering Abomination": 50, "Woe Strider": 34,
        "Bloodflow Connoisseur": 35, "Carrion Feeder": 26, "Driver of the Dead": 55, "Ashnod's Altar": 28,
        "Skullclamp": 20,
        "Birds of Paradise": 2, "Xenobotanist": 4, "Jadzia Dax": 3, "Dr. Joseph M'Benga": 37,
        "Vengeance Mission": 30, "Bastion of Remembrance": 29, "Poison-Tip Archer": 30, "Falkenrath Noble": 32,
        "Syr Konrad, the Grim": 45, "Vampire Aristocrat": 33, "Altar of Dementia": 27, "Blasting Station": 29,
        "Khan, Vengeful Heart": 36, "Midnight Reaper": 31, "Grim Haruspex": 31, "Fecundity": 31, "Grand Nagus Zek": 33,
        "Diabolic Intent": 44, "Grim Tutor": 45, "Lesser Masticore": 40,
        "Bloodthrone Vampire": 24, "Spawning Pit": 27, "Yawgmoth, Thran Physician": 33, "The Meathook Massacre": 29,
        "Sephiroth, Fabled SOLDIER": 30, "Braids, Arisen Nightmare": 36, "Mirkwood Bats": 38, "Basking Broodscale": 26,
        "Scurry Oak": 37, "Teacher's Pest": 25, "Reassembling Skeleton": 25, "Tenacious Dead": 19, "Grave Pact": 45,
        "Dictate of Erebos": 50, "Tireless Provisioner": 8, "Support Mission": 40, "Renata, Called to the Hunt": 47,
        "Tribute to the World Tree": 43, "Beifong's Bounty Hunters": 46, "Chatterfang, Squirrel General": 35,
        "Cankerbloom": 52, "Melira, Sylvok Outcast": 39, "Mikaeus, the Unhallowed": 55, "Thran Vigil": 41,
        "Demonic Tutor": 12, "Vampiric Tutor": 11, "Imperial Seal": 11, "Worldly Tutor": 13,
        "Eldritch Evolution": 44, "Chord of Calling": 46, "Finale of Devastation": 47, "Fauna Shaman": 9,
        "Sidisi, Undead Vizier": 42, "Wishclaw Talisman": 14, "Beseech the Mirror": 43,
        "Gravecrawler": 18, "Wingrattle Scarecrow": 41, "Lingering Tormentor": 42, "Aerie Ouphes": 46, "Warren Soultrader": 30,
        "Vengeful Bloodwitch": 23, "Massacre Girl, Most Wanted": 40, "Marionette Apprentice": 24,
        "Dina's Guidance": 99, "Awakening Zone": 22, "Sifter of Skulls": 40, "Tendershoot Dryad": 38,
        "Creakwood Liege": 39,
        "Llanowar Elves": 2, "Three Visits": 5, "Thought Vessel": 3, "Coalition Relic": 6, "Cultivate": 7,
        "Collected Company": 32, "Ravenous Chupacabra": 58, "Archdruid's Charm": 99,
        "Ygra, Eater of All": 45, "Sylvan Library": 8, "Dread Return": 44,
        "Witherbloom Apprentice": 24, "Carpet of Flowers": 3, "Mox Amber": 1, "Elves of Deep Shadow": 2, "Fyndhorn Elves": 2,
        "Arbor Elf": 2, "Deathrite Shaman": 2, "Talisman of Resilience": 3, "Green Sun's Zenith": 45, "Allosaurus Shepherd": 6,
        "Defense Grid": 20, "Night's Whisper": 21,
    }

    def castable_dev(self):
        out = []
        for c in set(self.hand):
            if c in LANDS:
                continue
            if c in self.PRIORITY:
                out.append(c)
        return sorted(out)

    def x_tutor_cost(self, c, t):
        """Coste total real: Chord = X + GGG (X = valor de mana de la criatura) menos convoke (1 por criatura sin girar);
        Finale = X X G G. (17/11, Juan: antes el modelo cobraba ~3-5 fijo.)"""
        mv = sum(CARDS[t]["cost"]) if t else 0
        if c == "Chord of Calling":
            conv = len([p for p in self.creatures() if not p.tapped])
            return max(0, mv + 3 - conv)
        return 2 * mv + 2

    def dev_ok(self, c):
        """Conditions for casting a development card now."""
        if c in ("Chord of Calling", "Finale of Devastation"):
            t = self.tutor_target(creature_only=True)
            return t is not None and self.can_pay(self.x_tutor_cost(c, t), 0)
        if c == "Green Sun's Zenith":
            t = self.tutor_target(creature_only=True, green=True)
            return bool(t) and self.can_pay(sum(CARDS[t]["cost"]), 1)
        if c == "Dread Return":
            return any(x in self.gy for x in ("Putrid Goblin", "Rendclaw Trow", "Lesser Masticore", "Aerie Ouphes",
                                              "Zulaport Cutthroat", "Blood Artist", "Viscera Seer", "Puppeteer Clique"))
        if c == "Diabolic Tutor":
            return True
        if c in ("Diabolic Intent", "Eldritch Evolution"):
            return self.pick_fodder() is not None
        if c in ("Vengeance Mission", "Bastion of Remembrance") and not self.gorma() and self.turn < 5:
            return False
        if c == "Traverse the Outlands":
            return max([self.power(p) for p in self.creatures()] or [0]) >= 3 and len(self.lands) < 10
        return True

    def cast(self, c):
        g, p = self.cost_of(c)
        if c in ("Chord of Calling", "Finale of Devastation"):
            t = self.tutor_target(creature_only=True)
            if t is None:
                return False
            tot = self.x_tutor_cost(c, t)
            pips = min(p, tot)
            if not self.pay_now(tot - pips, pips):
                return False
            if c == "Chord of Calling":     # convoke: gira las criaturas que pagaron
                mv = sum(CARDS[t]["cost"])
                for q in [q for q in self.creatures() if not q.tapped][:mv + 3 - tot]:
                    q.tapped = True
            g = p = 0
        if not self.pay_now(g, p):
            return False
        if self.mode == "table" and "cnt" in self.cfg.rules and self._our and self.counter_try(c):
            if c == COMMANDER:
                self.tax += 2
            else:
                self.hand.remove(c); self.gy.append(c)
            return True
        if c == COMMANDER:
            self.gorma_in_cmd = False
            gp = Perm(name=COMMANDER, base=1, creature=True)
            self.bf.append(gp)
            self.on_creature_enter(gp, token=False)
            if self.gorma_turn is None:
                self.gorma_turn = self.turn
            self.log("cast Gorma")
            if self.mode == "table" and "rem" in self.cfg.rules:
                self.v2_instant(gp)
            return True
        self.hand.remove(c)
        t = CARDS[c]["t"]
        self.log("cast", c)
        self.stats.setdefault("cast", set()).add(c)
        if c == "Profane Tutor":
            self.profane.append(2)
            return True
        if c in ("Diabolic Tutor", "Grim Tutor", "Demonic Tutor"):
            self.gy.append(c); self.tutor(); return True
        if c in ("Vampiric Tutor", "Imperial Seal"):
            self.gy.append(c); self.life -= 2; self.tutor(top=True); return True
        if c == "Worldly Tutor":
            self.gy.append(c); self.tutor(creature_only=True, top=True); return True
        if c in ("Eldritch Evolution",):
            f = self.pick_fodder()
            if f:
                self.sacrifice(f)
            self.gy.append(c); self.tutor(creature_only=True, to_bf=True); return True
        if c in ("Chord of Calling", "Finale of Devastation"):
            self.gy.append(c); self.tutor(creature_only=True, to_bf=True); return True
        if c == "Green Sun's Zenith":
            t = self.tutor_target(creature_only=True, green=True)
            extra = max(0, sum(CARDS[t]["cost"]) - 1) if t else 0     # X = coste de la criatura (base {1}{G} cubre X=1)
            if t and self.pay_now(extra, 0):
                self.tutor(creature_only=True, to_bf=True, green=True)
            self.library.insert(0, c)                               # vuelve barajado a la biblioteca
            return True
        if c == "Night's Whisper":
            self.gy.append(c); self.draw(2); self.life -= 2; return True
        if c == "Beseech the Mirror":
            f = self.pick_fodder()
            if f:
                self.sacrifice(f)
            self.gy.append(c); self.tutor(); return True
        if c in ("Dina's Guidance", "Archdruid's Charm"):
            self.gy.append(c); self.tutor(creature_only=True); return True
        if c == "Three Visits":
            self.gy.append(c); self.fetch_basic(untapped=True); return True
        if c == "Cultivate":
            self.gy.append(c); self.fetch_basic(untapped=False)
            b = next((x for x in reversed(self.library) if x in ("Forest", "Swamp")), None)
            if b:
                self.library.remove(b); self.hand.append(b)
            return True
        if c == "Dread Return":
            self.gy.append(c)
            b = self.best_gy_creature()
            if b:
                self.gy.remove(b); self.enter(b)
            return True
        if c == "Collected Company":
            self.gy.append(c); self.coco(); return True
        if c == "Diabolic Intent":
            f = self.pick_fodder()
            if f:
                self.sacrifice(f)
            self.gy.append(c); self.tutor(); return True
        if c == "Lesser Masticore":
            junk = [x for x in self.hand if x in LANDS]
            if len(junk) >= 1 and len(self.lands) >= 4:
                self.hand.remove(junk[0]); self.gy.append(junk[0])
            elif self.hand:
                self.gy.append(self.hand.pop())
        if c == "Traverse the Outlands":
            x = max([self.power(q) for q in self.creatures()] or [0])
            for _ in range(min(x, 8)):
                self.fetch_basic(untapped=False)
            self.gy.append(c); return True
        if t in ("S", "I"):
            self.gy.append(c)
            return True
        self.enter(c)
        return True

    def develop(self):
        progress = True
        guard = 0
        while progress and guard < 30 and not self.won:
            guard += 1
            progress = False
            # sacrifice fodder before casting non-token creatures (Gorma bonus) if outlet + payoff
            self.sac_fodder_phase()
            cands = sorted(self.castable_dev(), key=lambda c: self.PRIORITY.get(c, 99))
            if self.gorma_in_cmd and COMMANDER not in cands:
                cands.append(COMMANDER)
                cands.sort(key=lambda c: self.PRIORITY.get(c, 99))
            reserve = self.hold_amount()
            for c in cands:
                if c == COMMANDER and not self.gorma_in_cmd:
                    continue
                if c == COMMANDER and not self.gorma_ok():
                    continue
                if not self.dev_ok(c):
                    continue
                g, p = self.cost_of(c)
                if self.can_pay(g, p, extra=reserve):
                    if self.cast(c):
                        progress = True
                        if self.try_win():
                            return
                        break
            if not progress:
                progress = self.use_utilities(reserve)

    def gorma_ok(self):
        pol = self.cfg.gorma_policy
        if pol == "asap" or self.mode != "table":
            return True
        if pol == "combo":
            return False
        return (self.free_outlet() is not None or any(self.on_bf(d) for d in DRAINERS)
                or self.fodder_count() >= 2 or self.turn >= 6)

    def hold_amount(self):
        if self.mode != "table" or self.turn < self.cfg.hold_from_turn:
            return 0
        if self.cfg.hold_mode == "visible":
            due = False
            for i in self.alive():
                if self.rival_next[i] == self.turn:
                    if getattr(self, "_threat_t", {}).get(i) != self.turn:
                        self._roll_threat(i)
                    th = self._threat[i]
                    if th["visible"] and not th["stopped"]:
                        due = True
            if not due:
                return 0
        costs = []
        for p in self.bf:
            if p.name in ("Haywire Mite", "Thrashing Brontodon"):
                costs.append(1)
            if p.name == "Insidious Fungus":
                costs.append(2)
        for c in self.hand:
            t = self.tags(c)
            if t & {"answer_any_inst", "answer_cre_inst"}:
                g, p = CARDS[c]["cost"]
                costs.append(g + p if c != "Mortality Spear" else 4)
            if c in ("Heroic Intervention", "Golgari Charm"):
                costs.append(2)
            if c in ("Snakeskin Veil", "Tamiyo's Safekeeping"):
                costs.append(1)
        return min(costs) if costs else 0

    def use_utilities(self, reserve):
        """Activated abilities and cheap spells for value. Returns True if something was done."""
        for p in self.bf:
            if p.name == "Fauna Shaman" and not p.tapped and not p.sick and self.can_pay(0, 1, reserve):
                junk = [c for c in self.hand if c in CARDS and CARDS[c]["t"] == "C" and c not in PERSIST_LOOP
                        and c not in OUTLETS and c not in DRAINERS]
                if junk and self.tutor_target(creature_only=True):
                    self.pay_now(0, 1); p.tapped = True
                    self.hand.remove(junk[0]); self.gy.append(junk[0]); self.tutor(creature_only=True)
                    return True
            if p.name == "Wishclaw Talisman" and not p.tapped and self.can_pay(1, 0, reserve) and self.turn >= 5:
                self.pay_now(1, 0); self.bf.remove(p); self.tutor(); self.log("Wishclaw (pasa a un rival)")
                return True
        # Emeritus prepared -> Demonic Tutor copy
        for p in self.bf:
            if p.name == "Emeritus of Woe" and p.prepared and self.can_pay(1, 1, reserve):
                self.pay_now(1, 1); p.prepared = False; self.tutor(); self.log("Emeritus tutor")
                self.stats["act_emeritus"] = self.stats.get("act_emeritus", 0) + 1
                return True
        # Pestfinder prepared -> Turn Stones (3 pests)
        for p in self.bf:
            if p.name == "Eccentric Pestfinder" and p.prepared and self.can_pay(0, 2, reserve):
                self.pay_now(0, 2); p.prepared = False; self.make_token("pest", 3); return True
        # Wight: tap, sac another -> land
        for p in self.bf:
            if p.name == "Wight of the Reliquary" and not p.sick and not p.tapped and len(self.lands) < 9:
                f = self.pick_fodder()
                if f:
                    p.tapped = True; self.sacrifice(f)
                    lands = [c for c in self.library if c in LANDS]
                    if lands:
                        l = lands[-1]; self.library.remove(l); self.lands.append(l); self.land_tapped_now += 1
                        self.landfall()
                    return True
        # Priest: tap, sac two others
        for p in self.bf:
            if p.name == "Priest of Forgotten Gods" and not p.sick and not p.tapped:
                fs = [q for q in self.bf if q.kind == "token" and q.creature and q.tok != "spawn"]
                if len(fs) >= 2:
                    p.tapped = True
                    self.sacrifice(fs[0]); self.sacrifice(fs[1])
                    self.drain_each(2); self.col += 2; self.draw(1)
                    return True
        # Rampant Rejuvenator: sac for lands when big
        for p in self.bf:
            if p.name == "Rampant Rejuvenator" and self.power(p) >= 3 and len(self.lands) < 9 and self.free_outlet():
                self.sac_with_outlet(p); return True
        # Village Rites / Deadly Dispute: sac fodder, draw 2
        for rc, (rg, rp) in (("Village Rites", (0, 1)), ("Deadly Dispute", (1, 1))):
            if rc in self.hand and sum(1 for c in self.hand if c not in LANDS) <= 3 and self.can_pay(rg, rp, reserve):
                f = self.pick_fodder() or next((q for q in self.bf if q.name in PERSIST_LOOP and not q.minus), None)
                if f:
                    self.pay_now(rg, rp); self.hand.remove(rc); self.gy.append(rc)
                    self.sacrifice(f); self.draw(2)
                    if rc == "Deadly Dispute":
                        self.make_token("treasure")
                    return True
        # Witherbloom Charm: sac a token, draw 2
        if "Witherbloom Charm" in self.hand and sum(1 for c in self.hand if c not in LANDS) <= 3 and self.pick_fodder() and \
                self.can_pay(0, 2, reserve) and self.mode == "goldfish":
            self.pay_now(0, 2); self.hand.remove("Witherbloom Charm"); self.gy.append("Witherbloom Charm")
            self.sacrifice(self.pick_fodder()); self.draw(2); return True
        # Insidious Fungus: {2}, sac: draw (goldfish only; table keeps it as an answer)
        if self.mode == "goldfish":
            for p in self.bf:
                if p.name == "Insidious Fungus" and self.can_pay(2, 0, reserve) and sum(1 for c in self.hand if c not in LANDS) <= 2:
                    self.pay_now(2, 0); self.sacrifice(p); self.draw(1); return True
        # Foot Chopper: equip {2} to a token if unattached
        if self.on_bf("Foot Chopper") and not any(q.equipped == "chopper" for q in self.bf):
            f = next((q for q in self.bf if q.kind == "token" and q.tok in ("zombie", "pest", "snake") ), None)
            if f and self.can_pay(2, 0, reserve):
                self.pay_now(2, 0); f.equipped = "chopper"; return True
        if self.on_bf("Blade of the Bloodchief") and not any(q.equipped == "blade" for q in self.bf):
            g = self.gorma()
            if g and self.can_pay(1, 0, reserve):
                self.pay_now(1, 0); g.equipped = "blade"; return True
        # Pest Infestation for fodder
        if "Pest Infestation" in self.hand and (self.mode == "goldfish" or self.turn >= 4):
            x = min(3, (self.avail() - reserve - 1) // 2)
            if x >= 1 and self.can_pay(2 * x, 1, reserve):
                self.pay_now(2 * x, 1); self.hand.remove("Pest Infestation"); self.gy.append("Pest Infestation")
                self.make_token("pest", 2 * x); return True
        # Find: return creatures
        if "Find // Finality" in self.hand and self.best_gy_creature() and self.can_pay(0, 2, reserve):
            self.pay_now(0, 2); self.hand.remove("Find // Finality"); self.gy.append("Find // Finality")
            for _ in range(2):
                c = self.best_gy_creature()
                if c:
                    self.gy.remove(c); self.hand.append(c)
            return True
        # Desperate Plea: sac fodder, reanimate small creature (goldfish or when not holding)
        if "Desperate Plea" in self.hand and self.can_pay(1, 1, reserve) and self.mode == "goldfish":
            f = max((q for q in self.bf if q.kind == "token" and q.creature), key=self.power, default=None)
            if f:
                c = next((x for x in ["Putrid Goblin", "Viscera Seer", "Zulaport Cutthroat", "Blood Artist",
                                      "Rendclaw Trow", "Pest Rescuer"] if x in self.gy and
                          CARDS[x].get("p", 0) <= self.power(f)), None)
                if c:
                    self.pay_now(1, 1); self.hand.remove("Desperate Plea"); self.gy.append("Desperate Plea")
                    self.sacrifice(f); self.gy.remove(c); self.enter(c); return True
        if "Victimize" in self.hand and self.can_pay(2, 1, reserve):
            cs = [c for c in self.gy if c in CARDS and CARDS[c]["t"] == "C"]
            f = self.pick_fodder()
            if len(cs) >= 2 and f:
                self.pay_now(2, 1); self.hand.remove("Victimize"); self.gy.append("Victimize")
                a = self.best_gy_creature(); self.gy.remove(a)
                b = self.best_gy_creature() or (cs[0] if cs[0] in self.gy else None)
                if b and b in self.gy:
                    self.gy.remove(b)
                self.sacrifice(f)
                self.enter(a).tapped = True
                if b:
                    self.enter(b).tapped = True
                return True
        # Skullclamp: equip 1 to a 1-toughness token -> dies, draw 2
        if self.on_bf("Skullclamp"):
            f = next((q for q in self.bf if q.kind == "token" and q.tok in ("pest", "snake", "ninja")), None)
            if f and self.can_pay(1, 0, reserve):
                self.pay_now(1, 0); self.bf.remove(f); self.dies(f, sacrificed=False); self.draw(2); return True
        # Jarad: sac a big non-key creature/token for damage
        if self.on_bf("Jarad, Golgari Lich Lord") and self.can_pay(1, 2, reserve):
            g = self.gorma()
            if g and self.alive() and self.power(g) >= max(self.opp[i] for i in self.alive()):
                pw = self.power(g)
                self.pay_now(1, 2); self.sacrifice(g); self.drain_each(pw)
                return True
            f = max((q for q in self.bf if q.kind == "token" and q.creature and q.tok != "spawn"), key=self.power, default=None)
            if f and self.power(f) >= 2:
                pw = self.power(f)
                self.pay_now(1, 2); self.sacrifice(f); self.drain_each(pw); return True
        return False

    def sac_fodder_phase(self):
        if not self.free_outlet() or not self.payoffs_present():
            return
        for _ in range(20):
            f = None
            for p in self.bf:
                if p.kind == "token" and p.creature and p.tok in ("pest", "snake", "goat") and not p.equipped:
                    if p.tok == "snake" and self.mode == "table":
                        continue
                    f = p; break
            if not f:
                break
            self.sac_with_outlet(f)
            if self.won:
                return

    # ------------------------------------------------------------------ combat
    def combat(self):
        al = self.alive()
        if not al:
            return
        target = min(al, key=lambda i: self.opp[i])
        jen = next((p for p in self.bf if p.name == "Jenova, Ancient Calamity"), None)
        if jen:
            f = next((q for q in self.bf if q.kind == "token" and q.creature and q.tok in ("pest", "zombie", "snake")), None)
            if f:
                f.counters += self.power(jen); f.mutant = True
        attackers = []
        for p in self.creatures():
            if p.tapped or (p.sick and not ("haste" in self.tags(p.name) or p.kind == "token" and p.tok == "stolen")):
                continue
            if p.tok in ("spawn", "goat", "treasure") or self.power(p) <= 0:
                continue
            if p.name in ("Blood Artist", "Zulaport Cutthroat", "Viscera Seer", "Elvish Mystic", "Fanatic of Rhonas",
                          "Gyre Sage", "Priest of Forgotten Gods", "Selvala, Heart of the Wilds") and self.mode == "table":
                continue
            if p.mutant:
                continue
            attackers.append(p)
        if self.mode == "table" and self.cfg.combat and self.cfg.attack == "keep2":
            attackers.sort(key=self.power, reverse=True)
            keep = sorted(attackers, key=self.power)[:2]
            attackers = [p for p in attackers if p not in keep or p.name == COMMANDER]
        uprising = self.on_bf("Garruk's Uprising")
        blockers = 0
        if self.mode == "table" and self.cfg.blockers:
            blockers = min(3, max(0, (self.turn - 2) // 2))
        def evasive(p):
            t = self.tags(p.name)
            return "flying" in t or "shadow" in t or p.equipped == "chopper"
        def menace(p):
            return "menace" in self.tags(p.name) or (p.tok == "pest" and self.on_bf("Blight Mound"))
        def trample(p):
            return uprising or "trample" in self.tags(p.name)
        # rivals chump the biggest blockable attackers
        blockable = sorted([p for p in attackers if not evasive(p)], key=self.power, reverse=True)
        blocked = {}
        b = blockers
        for p in blockable:
            need = 2 if menace(p) else 1
            if b >= need:
                b -= need; blocked[id(p)] = need
        dmg_total = 0
        connected = []
        for p in attackers:
            pw = self.power(p)
            if id(p) in blocked:
                dmg = max(0, pw - 1) if trample(p) else 0
            else:
                dmg = pw
            if dmg > 0:
                connected.append(p)
                dmg_total += dmg
                if p.name == COMMANDER:
                    self.cmd_dmg[target] += dmg
                    self.gain_life(dmg)
        self.lose_life_opp(target, dmg_total)
        self.log("attack", target, "dmg", dmg_total, "opp", self.opp)
        if self.cmd_dmg[target] >= 21:
            self.opp[target] = min(self.opp[target], 0)
        if self.on_bf("Defiling Daemogoth"):
            self.gain_life(len(connected) * self.count_bf("Defiling Daemogoth"))
        self.check_win()
        # Foot Chopper / Gitrog draws
        for p in connected:
            if p.equipped == "chopper" and p in self.bf:
                pw = self.power(p)
                if p.name != COMMANDER:
                    self.sacrifice(p); self.draw(pw)
        if any(p.name == "The Gitrog, Ravenous Ride" for p in connected):
            f = self.pick_fodder()
            if f:
                pw = self.power(f); self.sacrifice(f); self.draw(pw)
        # decayed attackers die at end of combat
        for p in list(attackers):
            if p.decayed and p in self.bf:
                self.sacrifice(p)
        for p in self.bf:
            if p in attackers and not "vigilance" in self.tags(p.name):
                p.tapped = True

    # ------------------------------------------------------------------ turns
    @property
    def in_our_turn(self):
        return self._our

    def our_turn(self):
        self._our = True
        self.turn += 1
        self._reset_turn_flags()
        self.land_tapped_now = 0
        if self.mode == "table" and "rem" in self.cfg.rules:
            self.v2_turn_start()
        for p in self.bf:
            p.tapped = False
            p.sick = False
        # upkeep
        self.upkeep_tokens()
        self.profane = [x - 1 for x in self.profane]
        while 0 in self.profane:
            self.profane.remove(0); self.tutor()
        if not (self.turn == 1 and self.on_play):
            self.draw(1)
            if self.on_bf("Sylvan Library") and self.life >= 20:
                self.draw(1); self.life -= 4
                self.stats["library"] = self.stats.get("library", 0) + 1
        self.log("hand", sorted(self.hand), "| bf", [p.name for p in self.bf if p.kind=='card'], "| tokens", [p.tok for p in self.bf if p.kind=='token'], "| lands", len(self.lands), "| opp", self.opp)
        self.play_land()
        self.compute_pool()
        if "Phyrexian Tower" in self.lands[:max(0, len(self.lands) - self.land_tapped_now)]:
            f = self.pick_fodder()
            if f:
                self.sacrifice(f); self.col += 1  # Tower: sac a creature for {B}{B} instead of {B}
        self.log("pool", self.col, self.cless)
        if self.mode == "table" and "hate" in self.cfg.rules:
            self.answer_gy_lock()
        if self.try_win():
            return
        # table: pre-empt visible threats with sorcery answers
        if self.mode == "table":
            self.preempt()
        self.develop()
        if self.won:
            return
        self.combat()
        if self.won:
            return
        # post combat: sac mutants for Jenova draws, remaining fodder
        for p in list(self.bf):
            if p.mutant and self.free_outlet():
                self.sac_with_outlet(p)
        self.develop()
        if self.won:
            return
        self.try_win()
        if self.turn == 8 and not self.won:
            have = set(self.hand) | {p.name for p in self.bf}
            self.stats["t8"] = dict(
                persist=any(c in PERSIST_LOOP for c in have),
                outlet=any(c in OUTLETS for c in have),
                closer=any(c in DRAINERS or c == "Jarad, Golgari Lich Lord" for c in have),
                tutor=any(c in ("Diabolic Tutor", "Emeritus of Woe") for c in have),
                lands=len(self.lands), hand=len([c for c in self.hand if c not in LANDS]))
        self.end_step()
        self.reserve = self.col + self.cless + len(self.tokens("treasure"))
        self._our = False

    def upkeep_tokens(self):
        if self._our:
            for p in self.bf:
                if p.name == "Jadzia Dax":
                    p.counters += self.cmult()
        for p in list(self.bf):
            if p.name == "Tendershoot Dryad":
                self.make_token("sap")
            if self._our and p.name in ("Awakening Zone",):
                self.make_token("spawn")
            if self._our and p.name == "Creakwood Liege":
                self.make_token("sap")
            if p.name == "Pest Rescuer" and not self.tokens("pest"):
                self.make_token("pest")
            if p.name == "Ophiomancer" and not self.tokens("snake"):
                self.make_token("snake")

    def end_step(self):
        if self.on_bf("Braids, Arisen Nightmare"):
            f = self.pick_fodder()
            if f:
                self.sacrifice(f); self.drain_each(1); self.draw(1)
        if self.on_bf("Jadar, Ghoulcaller of Nephalia") and not any(p.decayed for p in self.bf):
            self.make_token("zombie")
        if self.lifegain_turn > 0:
            for p in self.bf:
                if p.name == "Defiling Daemogoth":
                    self.drain_each(self.lifegain_turn)
                if p.name == "Eccentric Pestfinder":
                    p.prepared = True
        if self.all_deaths_turn >= 2:
            for p in self.bf:
                if p.name == "Emeritus of Woe":
                    p.prepared = True
        for p in list(self.bf):
            if p.tok == "stolen":
                self.bf.remove(p)
        # Sakura-Tribe Elder at end of turn
        for p in list(self.bf):
            if p.name == "Sakura-Tribe Elder":
                self.sacrifice(p); self.fetch_basic(untapped=True)

    def opp_turns(self):
        self._our = False
        for i in range(3):
            if self.won or self.lost:
                return
            self._reset_turn_flags()
            self.upkeep_tokens()
            if self.rad[i] > 0 and self.opp[i] > 0:
                self.lose_life_opp(i, int(round(self.rad[i]))); self.rad[i] = 0; self.check_win()
            # instant-speed fodder sacrifice in opponents' turns
            if self.free_outlet() and self.payoffs_present():
                for p in list(self.bf):
                    if p.kind == "token" and p.tok in ("pest",) and p.creature:
                        self.sac_with_outlet(p)
                    if p.kind == "token" and p.tok == "snake" and self.mode == "goldfish":
                        self.sac_with_outlet(p)
            if self.mode == "table":
                self.table_events(i)
            if self.lifegain_turn > 0:
                for p in self.bf:
                    if p.name == "Eccentric Pestfinder":
                        p.prepared = True

    # ------------------------------------------------------------------ table model
    def threat_answers(self, kind, instant_only):
        """Return list of (cost, kind, ref) usable answers."""
        out = []
        for c in self.hand:
            if c not in CARDS:
                continue
            t = self.tags(c)
            g, p = CARDS[c]["cost"]
            cost = g + p
            if c == "Mortality Spear":
                cost = 2 if self.lifegain_turn > 0 else 4
            if "answer_any_inst" in t:
                out.append((cost, "hand", c))
            if kind == "cre" and "answer_cre_inst" in t:
                if c == "Tragic Slip" and not (self.free_outlet() and self.pick_fodder()):
                    continue
                out.append((cost, "hand", c))
            if c == "Witherbloom Charm" and self.rng.random() < 0.2:
                out.append((cost, "hand", c))
            if not instant_only:
                if "answer_any_sorc" in t and self.fodder_count() > 0:
                    out.append((cost, "hand", c))
                if kind == "cre" and ("answer_cre_sorc" in t):
                    if c == "Desperate Plea" and not self.creatures():
                        continue
                    out.append((cost, "hand", c))
                if kind == "ae" and "answer_ae_sorc" in t:
                    out.append((3, "hand", c))
                if kind == "cre" and "wipe" in t and self.opp_wins_soon():
                    out.append((cost + 2, "hand", c))
        if kind == "cre" and self.edict_ready():
            out.append((0, "edict", None))
        if kind == "cre" and self.yawg_ready():
            out.append((0, "yawg", None))
        if kind == "ae":
            for p in self.bf:
                if p.name == "Cankerbloom":
                    out.append((1, "bf", p))
            for c in self.hand:
                if c in CARDS and "answer_ae_hand" in self.tags(c):
                    out.append((sum(CARDS[c]["cost"]), "hand", c))
            for p in self.bf:
                if p.name == "Haywire Mite":
                    out.append((1, "bf", p))
                if p.name == "Insidious Fungus":
                    out.append((2, "bf", p))
                if p.name == "Thrashing Brontodon":
                    out.append((1, "bf", p))
        out.sort(key=lambda x: x[0])
        return out

    def creatures_except(self, x):
        return [p for p in self.creatures() if p is not x]

    def sac_pool(self):
        """creatures we can sacrifice without losing a key piece (fodder + persist pieces without -1/-1)"""
        return [p for p in self.bf if p.creature and (p.kind == "token" or (p.name in PERSIST_LOOP and not p.minus))]

    def edict_ready(self):
        return any(self.on_bf(x) for x in PACT) and self.free_outlet() is not None and len(self.sac_pool()) >= 2

    def yawg_ready(self):
        return self.on_bf("Yawgmoth, Thran Physician") and len(self.sac_pool()) >= 3 and self.life > 5

    def threatening(self):
        g = self.gorma()
        if g and self.power(g) >= 6:
            return True
        roles = 0
        roles += any(p.name in PERSIST_LOOP for p in self.bf)
        roles += self.free_outlet() is not None
        roles += any(self.on_bf(d) for d in DRAINERS)
        return roles >= 2

    def p_us(self):
        t = self.cfg.target
        if t == "always":
            return 1.0
        if t == "spread":
            return 1 / 3
        return 0.75 if self.threatening() else 0.25

    def rival_combat(self, i):
        cfg = self.cfg
        if not cfg.combat or self.turn < cfg.combat_start or self.opp[i] <= 0:
            return
        if cfg.kinds and cfg.kinds[i] != "combat":
            return
        if self.rng.random() >= self.p_us():
            return
        self._combat_hit(i, int(round(cfg.combat_k * (self.turn - cfg.combat_start + 1))))

    def _combat_hit(self, i, dmg):
        if self.edict_ready():
            self.sacrifice(self.sac_pool()[0]); dmg //= 2
            self.log("edict before damage")
        blockers = sorted([p for p in self.creatures() if not p.tapped and self.power(p) >= 0],
                          key=lambda p: (p.kind != "token", self.power(p)))
        nb = 0
        for p in blockers:
            if nb >= 3 or dmg <= 0:
                break
            if p.name in PERSIST_LOOP or p.kind == "token" or self.power(p) >= 4 or p.name == COMMANDER:
                nb += 1
                dmg -= 3 if self.power(p) < 4 else 5
                if p.kind == "token" or (p.name in PERSIST_LOOP and not p.minus):
                    self.destroy(p)
        dmg = max(0, dmg)
        self.life -= dmg
        self.stats["dmg_taken"] = self.stats.get("dmg_taken", 0) + dmg
        self.log("rival", i, "attacks us for", dmg, "life", self.life)
        if self.life <= 0:
            self.lost = True
            self.log("LOSS: combat")

    def opp_wins_soon(self):
        return True

    def use_answer(self, ans):
        cost, where, ref = ans
        if where in ("edict", "yawg"):
            pool = self.sac_pool()
            n = 2 if where == "edict" else 3
            for p in pool[:n]:
                self.sacrifice(p)
                if where == "edict" and self.on_bf("Blood Artist"):
                    for _ in self.alive():
                        self.drain_target(1)
            if where == "yawg":
                self.life -= n; self.draw(n)
            return
        if where == "hand" and ref == "Ravenous Chupacabra":
            self.hand.remove(ref); self.enter(ref)
            return
        if where == "hand":
            self.hand.remove(ref); self.gy.append(ref)
            if ref == "Desperate Plea" or ref == "Immoral Bargain":
                f = self.pick_fodder() or (self.creatures()[0] if self.creatures() else None)
                if f:
                    self.sacrifice(f)
            if "wipe" in self.tags(ref):
                self.opp_wiped_t = self.turn
                for p in list(self.bf):
                    if p.creature and not (ref == "Find // Finality" and p.name == COMMANDER):
                        self.destroy(p)
        else:
            self.sacrifice(ref)

    def preempt(self):
        for i in self.alive():
            if self.rival_next[i] == self.turn and getattr(self, "_threat_t", {}).get(i) is None:
                self._roll_threat(i)
            th = getattr(self, "_threat", {}).get(i)
            if th and self.rival_next[i] == self.turn and th["stoppable"] and th["visible"] and not th["stopped"]:
                for ans in self.threat_answers(th["kind"], instant_only=False):
                    if ans[1] in ("bf", "edict", "yawg") or CARDS[ans[2]]["t"] in ("S", "C"):
                        if self.avail() >= ans[0]:
                            if ans[0] > 0:
                                self.pay_now(ans[0], 0)
                            self.use_answer(ans)
                            th["stopped"] = True
                            self.log("pre-empted rival", i)
                            break

    def _roll_threat(self, i):
        if not hasattr(self, "_threat"):
            self._threat = {}
            self._threat_t = {}
        r = self.rng.random()
        mix = self.cfg.threat_mix
        kind = "cre" if r < mix[0] else ("ae" if r < mix[0] + mix[1] else "other")
        kinds = getattr(self, "kinds", None) or self.cfg.kinds
        if kinds:
            kind = "cre" if kinds[i] == "combat" else ("ae" if r < 0.5 else "other")
        self._threat[i] = dict(kind=kind, stoppable=self.rng.random() < self.cfg.p_stoppable,
                               visible=self.rng.random() < self.cfg.p_visible, stopped=False)
        self._threat_t[i] = self.turn

    def table_events(self, i):
        cfg = self.cfg
        R = cfg.rules
        if "combat" in R:
            self.v2_combat(i)
        else:
            self.rival_combat(i)
        if self.lost:
            return
        if "hate" in R:
            self.v2_hate()
        if getattr(self, "mz", False):
            self.mz_events(i)
            if self.lost:
                return
        # wipe
        if "wipe" in R:
            self.v2_wipe_check(i)
        elif not self.wipe_done and self.turn >= self.wipe_turn and self.rng.random() < 0.5:
            self.wipe_done = True
            if "Heroic Intervention" in self.hand and self.reserve >= 2 and not self.heroic_used:
                self.hand.remove("Heroic Intervention"); self.gy.append("Heroic Intervention"); self.reserve -= 2
                self.heroic_used = True
            elif "Golgari Charm" in self.hand and self.reserve >= 2 and self.rng.random() < 0.7:
                self.hand.remove("Golgari Charm"); self.gy.append("Golgari Charm"); self.reserve -= 2
            else:
                self.log("WIPE")
                self.stats["wipes"] = self.stats.get("wipes", 0) + 1
                self.opp_wiped_t = self.turn
                self._our = False
                yah = next((q for q in self.bf if q.name == "Yahenni, Undying Partisan"), None)
                for p in [q for q in self.bf if q.creature and q is not yah]:
                    self.destroy(p)
                if yah and not self.creatures_except(yah):
                    self.destroy(yah)
        # spot removal
        if "rem" in cfg.rules:
            self.v2_removal_phase(i)
        elif self.rng.random() < cfg.p_removal:
            self.stats["rem_used"] = self.stats.get("rem_used", 0) + 1
            if self.rng.random() < self.p_us():
                g = self.gorma()
                targets = [p for p in self.bf if p.kind == "card" and p.name in (
                    "Phyrexian Altar", "Moldervine Reclamation", "Pitiless Plunderer", "Mazirek, Kraul Death Priest",
                    "Zulaport Cutthroat", "Blood Artist", "Cauldron of Essence", "Defiling Daemogoth", "Viscera Seer",
                    "Umbral Collar Zealot", "Morbid Opportunist", "Jarad, Golgari Lich Lord", "Dr. Joseph M'Benga",
                    "Blasting Station", "Bastion of Remembrance", "Vengeance Mission")]
                victim = g if (g and (self.rng.random() < 0.6 or not targets)) else (self.rng.choice(targets) if targets else None)
                if victim:
                    self.stat_rem_us(victim)
                    prot = next((x for x in ("Snakeskin Veil", "Tamiyo's Safekeeping") if x in self.hand), None)
                    if self.on_bf("Dr. Joseph M'Benga") and victim.creature and victim.name != "Dr. Joseph M'Benga" \
                            and victim.counters > 0:
                        self.log("removal fizzles (M'Benga hexproof)")
                    elif prot and victim.creature and self.reserve >= 1:
                        self.hand.remove(prot); self.gy.append(prot); self.reserve -= 1
                    elif "Heroic Intervention" in self.hand and self.reserve >= 2:
                        self.hand.remove("Heroic Intervention"); self.gy.append("Heroic Intervention"); self.reserve -= 2
                    elif "Veil of Summer" in self.hand and self.reserve >= 1 and self.rng.random() < 0.4:
                        self.hand.remove("Veil of Summer"); self.gy.append("Veil of Summer"); self.reserve -= 1
                    elif victim.name == "Yahenni, Undying Partisan" and self.pick_fodder():
                        self.sacrifice(self.pick_fodder()); self.log("Yahenni indestructible")
                    else:
                        self.log("removal on", victim.name)
                        self.destroy(victim)
        # kill attempt
        if self.opp[i] > 0 and self.rival_next[i] == self.turn:
            if i not in getattr(self, "_threat", {}) or self._threat_t.get(i) != self.turn:
                self._roll_threat(i)
            th = self._threat[i]
            clock = "clock" in R
            if th["stopped"]:
                if clock:
                    self.rival_rearms(i); self.stats["we_stop"] = self.stats.get("we_stop", 0) + 1
                else:
                    self.rival_next[i] = self.turn + cfg.delay
                self._threat_t[i] = None
                return
            if clock and self.v2_others_stop(i):
                self.rival_rearms(i); self._threat_t[i] = None
                self.stats["others_stop"] = self.stats.get("others_stop", 0) + 1
                return
            if th["stoppable"]:
                for ans in self.threat_answers(th["kind"], instant_only=True):
                    if self.reserve >= ans[0]:
                        self.reserve -= ans[0]
                        self.use_answer(ans)
                        if clock:
                            self.rival_rearms(i); self.stats["we_stop"] = self.stats.get("we_stop", 0) + 1
                        else:
                            self.rival_next[i] = self.turn + cfg.delay
                        self._threat_t[i] = None
                        self.log("answered rival", i)
                        return
            if getattr(self, "mz", False) and self.mz_partial(i):
                self.log("rival", i, "kills only one rival")
                return
            self.lost = True
            self.stats["loss_by"] = "rival"
            self.log("LOSS: rival", i, "wins")

    # ------------------------------------------------------------------ run
    def run(self, max_turns=20):
        self._our = True
        while self.turn < max_turns and not self.won and not self.lost:
            self.our_turn()
            if self.won:
                break
            self.opp_turns()
            if self.turn == 6 or self.turn == 7:
                self.stats.setdefault("life_t", {})[self.turn] = self.life
            if getattr(self, "mz", False) and self.cut_turn == self.turn and not self.won and not self.lost:
                self.mz_time()
        return self


def play(deck, seed, **kw):
    rng = random.Random(seed)
    g = Game(deck, rng, **kw)
    g.run()
    return g
