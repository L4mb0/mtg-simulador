"""Simulador Monte Carlo del mazo Blight Curse (Auntie Ool, Cursewretch; contadores -1/-1).

Diferencias con el simulador de Gorma (mismas convenciones de mesa, harness y escenarios):
- Los rivales tienen TABLERO (criaturas con poder/resistencia/contadores). El mazo vive de poner
  contadores en criaturas rivales: Auntie hace perder 1 al controlador por cada criatura que recibe
  contadores, y las barridas de contadores frenan a los rivales de combate.
- Los rivales de combate atacan con su tablero real; su intento de ganar falla si el tablero quedó por
  debajo de la mitad de lo que tendrían sin interferencia (control) o si Kulrath Knight los bloquea.
- Loops de Blowfly Infestation (+ Hapatra / Flourishing Defenses / Nest of Scarabs) y de Yawgmoth se
  resuelven por regla, respetando el robo obligatorio de Auntie y de The Scorpion God (no se roba de
  una biblioteca vacía).
Abstracciones: maná por colores con fuentes de un uso; los rivales no se atacan entre sí; un counter
del jugador azul solo sobre hechizos clave (Auntie, piezas que completan un combo, remates).
"""
import random
from dataclasses import dataclass
from cards import CARDS, LANDS, COMMANDER, parse_cost, mv

# Fase 4: roles y pesos por carta en data/efectos.yaml (comunes o en el bloque "motor" de este mazo)
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", ".."))
from core import efectos as EF
import cards as _cards_mod
_CD = _cards_mod.C if isinstance(getattr(_cards_mod, "C", None), dict) else _cards_mod.CARDS
_NAMES = list(_CD)
ENGINES = set(EF.motor_roles("blight", "engine", _NAMES))
# disparadores de muerte compartidos (data/efectos.yaml): drenar a todos / drenar a uno (Blood Artist y similares)
EACH_DRAIN = set(EF.with_death_effect("drain_each", _NAMES))
DRAIN_ONE = set(EF.with_death_effect("drain_one", _NAMES))
DRAIN_ANY = set(EF.with_death_effect("drain_one", _NAMES, controla="cualquiera"))   # también cuando muere una rival
EACH_GAIN = {n for n in EACH_DRAIN if n in EF.with_death_effect("gain", [n])}        # drenan y además ganan
GAIN_RIVAL = set(EF.rival_death_effect("gain", _NAMES))                              # ganan cuando muere una rival (Meathook)
INSTANT_ANS = EF.motor_field("blight", "instant_ans", _NAMES)
# probabilidad de que una respuesta frene la amenaza de un rival de combate (resistencia limitada)
ANS_P = {"cre1": 0.35, "cre3": 0.6, "cre4": 0.8}
SELF_COUNTER = set(EF.motor_roles("blight", "self_counter", _NAMES))
KEEP_HOME = set(EF.motor_roles("blight", "keep_home", _NAMES))


@dataclass
class TableCfg:
    clocks: tuple = ((8, 10), (9, 11), (10, 12))
    kinds: tuple = ("combat", "combo", "combat")
    p_stoppable: float = 0.7
    delay: int = 2
    p_visible: float = 0.6
    p_removal: float = 0.30
    target: str = "sometimes"
    wipe_window: tuple = (6, 10)
    p_counter: float = 0.5
    n_counters: int = 1
    hold_from_turn: int = 6
    combat: bool = True
    combat_start: int = 5
    grow_combat: float = 0.75     # prob. de que un rival de combate baje criatura en su turno
    grow_combo: float = 0.35
    size: float = 1.0             # multiplicador del tamaño de las criaturas rivales
    control_ratio: float = 0.5    # el intento de un rival de combate falla si su poder < ratio * esperado
    p_others: float = 0.0         # prob. de que OTRO rival frene el intento (mesa real: no solo tú interactúas)
    flyer_p: float = 0.15
    v2: str = ""                  # mesa v2 por bracket ("B1".."B5", "B3+B4"); ver mesa2.py


class Cr:
    __slots__ = ("name", "kind", "tok", "owner", "pw", "tg", "m", "plus", "dmg", "sick", "tapped", "tags",
                 "black", "uses", "steal", "dead", "flying", "eq", "mod")

    def __init__(self, name, owner, pw, tg, kind="card", tok="", tags=(), black=False, flying=False):
        self.name, self.owner, self.pw, self.tg, self.kind, self.tok = name, owner, pw, tg, kind, tok
        self.m = self.plus = self.dmg = self.uses = self.mod = 0
        self.sick, self.tapped, self.steal, self.dead = True, False, False, False
        self.tags = set(tags)
        self.black = black
        self.flying = flying or "fly" in self.tags
        self.eq = ""


class Game:
    def __init__(self, deck, rng, mode="table", cfg=None, log=False, policy=None):
        self.rng, self.mode, self.cfg, self.logon = rng, mode, cfg or TableCfg(), log
        self.policy = policy or {}
        self.library = list(deck)
        rng.shuffle(self.library)
        self.hand, self.gy, self.lands, self.cre, self.perms = [], [], [], [], {}
        self.boards = [[], [], []]
        self.natural = [0.0, 0.0, 0.0]
        self.opp_gy = [[], [], []]
        self.opp = [40, 40, 40]
        self.poison = [0, 0, 0]
        self.cmd_dmg = [0, 0, 0]
        self.life = 40
        self.turn = 0
        self.tax = 0
        self.in_cmd = True
        self.won = self.lost = False
        self.win_turn = None
        self.win_how = None
        self.auntie_turn = None
        self.treasures = 0
        self.src = []
        self.depth = 0
        self.monarch = False
        self.goat = None              # dict(ctrl, m) si el Goat está en mesa
        self.charge = 0               # Wickersmith's Tools
        self.loyal = {}
        self.ctr_flag = False
        self.deaths_turn = 0
        self.puca_used = self.reaper_used = False
        self.scorpion_back = False
        self.counters_left = self.cfg.n_counters
        self.heroic_used = False
        self.wipe_turn = rng.randint(*self.cfg.wipe_window)
        self.wipe_done = False
        self.rival_next = [rng.randint(*c) for c in self.cfg.clocks]
        self._threat = {}
        self.cast_count = {}
        self.stats = dict(mulls=0, combo=None, draws=0, drain=0, t8=None)
        self.our = True
        self._tapped_lands = set()
        self.treasures_tapped = 0
        self._loop_turn = None
        self.binding_lore = 0
        self.on_play = rng.random() < 0.25
        self.mulligan()

    # ================================================================ utilidades
    def log(self, *a):
        if self.logon:
            print(f"[T{self.turn}]", *a)

    def alive(self):
        return [i for i in range(3) if self.opp[i] > 0 and self.poison[i] < 10]

    def check_win(self):
        if not self.won and not self.lost and not self.alive():
            self.won, self.win_turn = True, self.turn
            self.log("WIN", self.win_how)

    def lose_opp(self, i, n, how="drain"):
        if self.opp[i] > 0 and self.poison[i] < 10 and n > 0 and not self.won:
            self.opp[i] -= n
            self.stats["dmg_" + how] = self.stats.get("dmg_" + how, 0) + n
            if self.opp[i] <= 0:
                self.boards[i] = []
                if not self.alive():
                    self.win_how = self.win_how or how
            self.check_win()

    def drain_each(self, n, how="drain"):
        for i in self.alive():
            self.lose_opp(i, n, how)

    def drain_target(self, n, how="drain"):
        al = self.alive()
        if al:
            self.lose_opp(min(al, key=lambda k: self.opp[k]), n, how)

    def gain(self, n):
        self.life += n

    def draw(self, n=1):
        for _ in range(n):
            if self.library:
                self.hand.append(self.library.pop())
                self.stats["draws"] += 1
            else:
                self.lost = True   # robar de biblioteca vacía
                self.log("LOSS: decked")
                return

    def on(self, name):
        return name in self.perms or any(c.name == name for c in self.cre)

    def count(self, name):
        return self.perms.get(name, 0) + sum(1 for c in self.cre if c.name == name)

    def auntie(self):
        return next((c for c in self.cre if c.name == COMMANDER), None)

    def tags(self, n):
        return CARDS[n]["tags"] if n in CARDS else set()

    def eff_tg(self, c):
        base = c.tg
        if c.owner != "us" and self.on("Maha, Its Feathers Night"):
            base = 1
        return base + c.plus - c.m - c.dmg + c.mod

    def eff_pw(self, c):
        return max(0, c.pw + c.plus - c.m + c.mod)

    def all_cre(self):
        out = list(self.cre)
        for b in self.boards:
            out += b
        return out

    def opp_cre(self):
        out = []
        for i in self.alive():
            out += self.boards[i]
        return out

    # ================================================================ mulligan (Guía de juego)
    def mulligan(self):
        mulls = 0
        while True:
            self.library += self.hand
            self.hand = []
            self.rng.shuffle(self.library)
            self.draw(7)
            if self.keep(mulls == 0) or mulls >= 3:
                break
            mulls += 1
        self.stats["mulls"] = mulls
        for _ in range(max(0, mulls - 1)):
            self.hand.sort(key=self.bottom_key)
            self.library.insert(0, self.hand.pop())

    def keep(self, free):
        lands = [c for c in self.hand if c in LANDS]
        nl = [c for c in self.hand if c not in LANDS]
        n = len(lands)
        ramp = {"Sol Ring", "Arcane Signet", "Ignoble Hierarch", "Channeler Initiate", "Devoted Druid",
                "Farseek", "Rampant Growth", "Nature's Lore"}
        if n <= 1 or n >= 6:
            return False
        if n == 2:
            return any(c in ramp for c in nl) and (self.rng.random() < 0.75 or not free)
        cols = set()
        for l in lands:
            cols |= set(LANDS[l]["col"]) if LANDS[l]["mode"] != "fetch" else {"B", "R", "G"}
        early = [c for c in nl if mv(c) <= 3]
        if n in (3, 4):
            return (len(cols) >= 2 and early) or not free
        return any(mv(c) in (3, 4) for c in nl) or not free

    def bottom_key(self, c):
        if c in LANDS:
            return 100 if sum(1 for x in self.hand if x in LANDS) > 4 else -1
        if c in ("Sol Ring", "Arcane Signet", "Ignoble Hierarch"):
            return 0
        if c in ("Black Sun's Zenith", "Chain Reaction"):
            return 60
        return mv(c)

    # ================================================================ maná
    def land_tapped(self, l):
        m = LANDS[l]["mode"]
        if m == "U":
            return False
        if m in ("T", "bounce"):
            return True
        if m == "basics2":
            return sum(1 for x in self.lands if LANDS[x].get("basic")) < 2
        if m.startswith("check:"):
            need = set(m[6:].split(","))
            return not any(LANDS[x].get("types", set()) & need for x in self.lands)
        return True

    def fetch_basic(self, kinds=("Swamp", "Mountain", "Forest"), tapped=True):
        have = {k: sum(1 for x in self.lands if x == k) for k in kinds}
        pref = sorted(kinds, key=lambda k: have[k])
        for k in pref:
            if k in self.library:
                self.library.remove(k)
                self.rng.shuffle(self.library)
                self.put_land(k, tapped)
                return True
        return False

    def put_land(self, l, tapped):
        self.lands.append(l)
        if not tapped and self.our:
            self.src.append(LANDS[l]["col"] or "C")
        self.landfall()

    def landfall(self):
        for _ in range(self.count("Evolution Sage")):
            self.proliferate()

    def play_land(self):
        lands = [c for c in self.hand if c in LANDS]
        if not lands:
            return
        need = self.missing_colors()

        def score(l):
            t = self.land_tapped(l) or LANDS[l]["mode"] == "fetch"
            col = set(LANDS[l]["col"]) if LANDS[l]["mode"] != "fetch" else {"B", "R", "G"}
            s = (0 if not t else 1) * (1 if self.turn > 1 else -1)
            s -= 2 * len(col & need)
            if LANDS[l]["mode"] == "bounce" and len(self.lands) < 2:
                s += 10
            return s
        lands.sort(key=score)
        l = lands[0]
        self.hand.remove(l)
        mode = LANDS[l]["mode"]
        self.log("land", l)
        if mode == "fetch":
            self.gy.append(l)
            self.fetch_basic(tapped=True)
            return
        if mode == "bounce":
            self.lands.append(l)
            back = next((x for x in self.lands if x != l and LANDS[x].get("basic")), None) or \
                next((x for x in self.lands if x != l), None)
            if back:
                self.lands.remove(back)
                self.hand.append(back)
                # la tierra devuelta ya se había contado en el pool de este turno si estaba sin girar
                if (LANDS[back]["col"] or "C") in self.src:
                    self.src.remove(LANDS[back]["col"] or "C")
            self.landfall()
            return
        self.put_land(l, self.land_tapped(l))

    def missing_colors(self):
        have = set()
        for l in self.lands:
            have |= set(LANDS[l]["col"])
        return {"B", "R", "G"} - have

    def compute_pool(self):
        src = []
        for l in self.lands:
            if l in self._tapped_lands:
                continue
            col = LANDS[l]["col"] or "C"
            src.append(col)
            if LANDS[l]["mode"] == "bounce":
                src.append(col)
        for name, n in self.perms.items():
            if name == "Sol Ring":
                src += ["C", "C"] * n
            elif name in ("Arcane Signet", "Commander's Sphere", "Wickersmith's Tools"):
                src += ["BRG"] * n
        for c in self.cre:
            if c.sick or c.tapped:
                continue
            if c.name == "Ignoble Hierarch":
                src.append("BRG"); c.tapped = True
            elif c.name == "Devoted Druid":
                src.append("G"); c.tapped = True
            elif c.name in ("Channeler Initiate", "Morselhoarder"):
                src += ["BRG*" + str(id(c))] * c.m
        self.src = src

    def avail(self):
        return len(self.src) + self.treasures

    def _plan(self, g, pips):
        pool = list(self.src) + ["BRG"] * self.treasures
        used = [False] * len(pool)
        for pip in sorted(pips, key=len):
            best = None
            for k, s in enumerate(pool):
                if not used[k] and any(ch in s for ch in pip):
                    if best is None or len(pool[best]) > len(s):
                        best = k
            if best is None:
                return None
            used[best] = True
        left = [k for k in range(len(pool)) if not used[k]]
        if len(left) < g:
            return None
        left.sort(key=lambda k: (pool[k] != "C", len(pool[k]), pool[k] == "BRG"))
        for k in left[:g]:
            used[k] = True
        return [pool[k] for k in range(len(pool)) if used[k]]

    def can_pay(self, cost, extra=0):
        g, pips = cost
        if self._plan(g, pips) is None:
            return False
        return self.avail() >= g + len(pips) + extra

    def pay(self, cost):
        plan = self._plan(*cost)
        if plan is None:
            return False
        for s in plan:
            if s in self.src:
                self.src.remove(s)
                if s.startswith("BRG*"):
                    cid = int(s[4:])
                    c = next((x for x in self.cre if id(x) == cid), None)
                    if c and c.m > 0:
                        c.m -= 1
            else:
                self.treasures -= 1
        return True

    def pay_generic(self, n):
        return self.pay((n, []))

    PHYREXIAN_LIFE = 10   # paga vida por un pip phyrexiano solo con más de 10 de vida

    def cost(self, name):
        g, pips = parse_cost(CARDS[name]["cost"])
        if name == COMMANDER:
            g += self.tax
        phy = [p for p in pips if "P" in p]
        if phy and not self.can_pay((g, pips)) and self.life - 2 * len(phy) > self.PHYREXIAN_LIFE:
            rest = [p for p in pips if "P" not in p]
            if self.can_pay((g, rest)):
                return g, rest      # pagar vida le deja lanzarla este turno
        return g, pips

    # ================================================================ contadores
    def put(self, c, n=1, by_us=True):
        """Pone n contadores -1/-1 en la criatura c y resuelve todos los triggers."""
        if n <= 0 or c.dead or self.won or self.lost:
            return
        self.depth += 1
        c.m += n
        if by_us:
            self.ctr_flag = True
        if self.auntie() is not None:
            if c.owner == "us":
                self.draw(1)
            else:
                self.lose_opp(c.owner, 1)
        if self.depth < 80:
            if by_us:
                for _ in range(self.count("Hapatra, Vizier of Poisons")):
                    self.token("snake")
                for _ in range(self.count("Nest of Scarabs")):
                    self.token("insect", n)
                for _ in range(self.count("Obelisk Spider")):
                    self.drain_each(1)
                    self.gain(1)
                if c.owner != "us":
                    for _ in range(self.count("Generous Patron")):
                        self.draw(1)
                if self.on("All Will Be One"):
                    self.awbo(n)
            ntok = sum(1 for x in self.cre if x.kind == "token")
            if not (self.auntie() and (len(self.library) < 30 or ntok >= 10)):   # "may": el piloto no infla el tablero si Auntie le vacía la biblioteca
                for _ in range(self.count("Flourishing Defenses")):
                    self.token("elf", n)
            self.charge += self.count("Wickersmith's Tools")
        self.depth -= 1
        if self.depth == 0:
            self.sba()

    def awbo(self, n):
        oc = [x for x in self.opp_cre() if not x.dead]
        if self.on("Everlasting Torment") and oc:
            t = min(oc, key=self.eff_tg)
            self.put(t, n)
        else:
            self.drain_target(n, "awbo")

    def damage_cre(self, c, n, wither=False):
        if n <= 0 or c.dead:
            return
        if wither or self.on("Everlasting Torment"):
            self.put(c, n, by_us=(c.owner != "us") or wither)
        else:
            c.dmg += n
            self.sba()

    def proliferate(self):
        targets = []
        for c in self.opp_cre():
            if c.m > 0:
                targets.append(c)
        for c in self.cre:
            if c.m > 0 and c.name != COMMANDER and self.eff_tg(c) >= 2:
                targets.append(c)
        self.depth += 1
        for c in targets:
            self.put(c, 1)
        self.depth -= 1
        for k in list(self.loyal):
            self.loyal[k] += 1
        if self.on("Wickersmith's Tools") and self.charge > 0:
            self.charge += 1
        for i in self.alive():
            if self.poison[i] > 0:
                self.poison[i] += 1
                if self.poison[i] >= 10:
                    self.boards[i] = []
                    if not self.alive():
                        self.win_how = self.win_how or "poison"
        if self.on("All Will Be One"):
            self.awbo(len(targets))
        self.sba()
        self.check_win()

    def token(self, tok, n=1):
        if n <= 0:
            return
        stats = dict(snake=(1, 1), elf=(1, 1), insect=(1, 1), zombie=(2, 2), sap=(1, 1), scarecrow=(2, 2),
                     soldier=(1, 1), stolen=(3, 3))
        tags = {"snake": ("dt",)}.get(tok, ())
        black = tok in ("insect", "zombie")
        for _ in range(min(n, max(0, 60 - len(self.cre)))):
            c = Cr(tok, "us", *stats[tok], kind="token", tok=tok, tags=tags, black=black)
            self.cre.append(c)

    # ================================================================ muertes
    def sba(self):
        if self.depth > 0:
            return
        guard = 0
        while guard < 400 and not self.won and not self.lost:
            guard += 1
            dying = [c for c in self.cre if self.eff_tg(c) <= 0 or c.dead]
            dying_o = [(i, c) for i in range(3) for c in self.boards[i] if self.eff_tg(c) <= 0 or c.dead]
            if not dying and not dying_o:
                break
            for c in dying:
                if c in self.cre:
                    self.die(c)
            for i, c in dying_o:
                if c in self.boards[i]:
                    self.opp_die(i, c)

    def blowfly(self):
        """Trigger de Blowfly: muere una criatura con contador -> contador en una criatura objetivo."""
        if self.loop_ready_natural() and self._loop_turn is None:
            self._loop_turn = (self.turn, self.our)   # sin cierre, un jugador hace el loop una sola vez por partida
            self.run_loop("blowfly")
            return
        oc = [c for c in self.opp_cre() if not c.dead]
        one = [c for c in oc if self.eff_tg(c) <= 1]
        if one:
            self.put(max(one, key=self.eff_pw))
            return
        if self.auntie() and self.hand_size() <= 4 and len(self.library) >= 40:
            ex = self.expendable(1)
            if ex:
                self.put(ex)
                return
        if oc:
            self.put(max(oc, key=self.eff_pw))
            return
        ex = self.expendable(1)
        if ex and self.auntie() and len(self.library) >= 25:
            self.put(ex)

    def hand_size(self):
        return sum(1 for c in self.hand if c not in LANDS)

    def expendable(self, n):
        """Criatura propia que sobrevive a n contadores y no es clave."""
        cs = [c for c in self.cre if not c.dead and self.eff_tg(c) > n and c.name not in (
            COMMANDER, "Hapatra, Vizier of Poisons", "The Scorpion God") and c.kind == "card"]
        if not cs:
            return None
        return max(cs, key=lambda c: (c.name in ("Tree of Perdition", "Sinister Gnarlbark", "Necroskitter",
                                                   "Oft-Nabbed Goat", "Channeler Initiate"), self.eff_tg(c)))

    def die(self, c):
        self.cre.remove(c)
        c.dead = True
        had = c.m
        self.deaths_turn += 1
        if c.name == COMMANDER:
            self.in_cmd = True
            self.tax += 2
            self.log("Auntie dies")
        if had:
            for _ in range(self.count("Blowfly Infestation")):
                self.blowfly()
            if self.on("The Scorpion God") or c.name == "The Scorpion God":
                self.draw(1)
            for _ in range(self.count("Dread Tiller") + (1 if c.name == "Dread Tiller" else 0)):
                self.tiller_land()
        if c.owner == "us":
            for n in EACH_DRAIN:
                k = self.count(n) + (1 if c.name == n else 0)
                for _ in range(k):
                    self.drain_each(1)
                    if n in EACH_GAIN:
                        self.gain(1)
        for _ in range(sum(self.count(n) for n in DRAIN_ONE) + (1 if c.name in DRAIN_ONE else 0)):
            self.drain_target(1)
            self.gain(1)
        if had and self.on("Puca's Covenant") and not self.puca_used:
            perms = [x for x in self.gy if x in CARDS and CARDS[x]["t"] in "CAEW" and mv(x) <= had]
            if perms:
                self.puca_used = True
                b = max(perms, key=mv)
                self.gy.remove(b)
                self.hand.append(b)
        if c.name == "Dusk Urchins" and had:
            self.draw(had)
        if c.kind == "card":
            for n in ("Agent Venom", "Grim Haruspex"):
                for _ in range(self.count(n)):
                    self.draw(1)
                    if n == "Agent Venom":
                        self.life -= 1
        if c.kind == "card" and c.name != "High-Society Hunter":
            for _ in range(self.count("High-Society Hunter")):
                self.draw(1)
        if c.eq == "clamp":
            self.draw(2)
        if had and self.on("Shadow Urchin"):
            self.draw(min(had, 3))
        if c.kind == "token" or c.steal:
            return
        if c.name == COMMANDER:
            return
        if "persist" in c.tags and had == 0:
            q = self.enter(c.name, persist=True)
            return
        if c.name == "The Scorpion God":
            self.scorpion_back = True
            return
        self.gy.append(c.name)

    def tiller_land(self):
        l = next((x for x in self.hand if x in LANDS and LANDS[x]["mode"] != "fetch"), None)
        if l:
            self.hand.remove(l)
            self.lands.append(l)
            self.landfall()
            return
        l = next((x for x in self.gy if x in LANDS and LANDS[x]["mode"] not in ("fetch",)), None)
        if l:
            self.gy.remove(l)
            self.lands.append(l)
            self.landfall()

    def opp_die(self, i, c):
        self.boards[i].remove(c)
        c.dead = True
        self.stats["okills"] = self.stats.get("okills", 0) + 1
        for _ in range(self.count("Massacre Wurm")):
            self.lose_opp(i, 2, "wurm")
        had = c.m
        if had or c.mod < 0:
            self.stats["okills_us"] = self.stats.get("okills_us", 0) + 1
        if c.kind == "card":
            self.opp_gy[i].append((c.pw, c.tg, c.flying))
        if had:
            for _ in range(self.count("Blowfly Infestation")):
                self.blowfly()
            if self.on("The Scorpion God"):
                self.draw(1)
            for _ in range(self.count("Dread Tiller")):
                self.tiller_land()
            stolen = False
            if c.kind == "card" and self.on("Necroskitter"):
                stolen = True
            elif c.kind == "card" and self.on("The Reaper, King No More") and not self.reaper_used:
                self.reaper_used = stolen = True
            if stolen and self.opp_gy[i]:
                self.opp_gy[i].pop()
                q = Cr("robada", "us", c.pw, c.tg, flying=c.flying)
                self.cre.append(q)
                self.log("steal", c.pw, c.tg)
            for _ in range(self.count("Village Pillagers")):
                self.treasures_tapped += 1
        if self.on("Massacre Girl, Known Killer") and c.tg + c.plus - c.m + c.mod < 1:
            self.draw(1)
        for _ in range(sum(self.count(n) for n in DRAIN_ANY)):
            self.drain_target(1)
            self.gain(1)
        for _ in range(sum(self.count(n) for n in GAIN_RIVAL)):
            self.gain(1)
        if c.kind == "card":
            for _ in range(self.count("High-Society Hunter")):
                self.draw(1)
        self.deaths_turn += 1

    # ================================================================ entrar al campo
    def enter(self, name, persist=False, extra=0):
        d = CARDS[name]
        if d["t"] != "C":
            self.perms[name] = self.perms.get(name, 0) + 1
            self.enter_perm(name)
            return None
        c = Cr(name, "us", d["p"], d["tg"], tags=d["tags"], black="black" in d["tags"])
        if "haste" in d["tags"]:
            c.sick = False
        self.cre.append(c)
        start = extra + (1 if persist else 0)
        if name == "Carnifex Demon":
            start += 2
        elif name == "Grim Poppet":
            start += 3
        elif name in ("Wickerbough Elder",):
            start += 1
        elif name == "Morselhoarder":
            start += 2
        if start:
            self.put(c, start)
        self.etb(c)
        return c

    def etb(self, c):
        n = c.name
        oc = [x for x in self.opp_cre() if not x.dead]
        if n == "Channeler Initiate":
            self.put(c, 3)
        elif n == "Dread Tiller":
            self.place_one(1)
        elif n == "Skinrender":
            if oc:
                kill = [x for x in oc if self.eff_tg(x) <= 3]
                t = max(kill, key=self.eff_pw) if kill else max(oc, key=self.eff_pw)
                self.put(t, 3)
            elif self.auntie():
                ex = self.expendable(3)
                if ex:
                    self.put(ex, 3)
        elif n == "Soul Snuffers":
            self.each_creature(1)
        elif n == "The Reaper, King No More":
            self.place_one(1)
            self.place_one(1)
        elif n == "Village Pillagers":
            for x in list(oc):
                self.damage_cre(x, 1, wither=True)
        elif n == "Grave Titan":
            self.token("zombie", 2)
        elif n == "Puppeteer Clique":
            pool = [g for i in self.alive() for g in self.opp_gy[i]]
            if pool and self.mode == "table":
                pw, tg, fl = max(pool, key=lambda x: x[0])
                q = Cr("robada", "us", pw, tg, flying=fl)
                q.sick, q.steal = False, True
                self.cre.append(q)
        elif n == "Ferrafor, Young Yew":
            ours = sum(x.m for x in self.cre)
            best = max([ours] + [sum(x.m for x in self.boards[i]) for i in self.alive()])
            self.token("sap", best)
        elif n == "Maha, Its Feathers Night":
            self.sba()
        elif n == "Generous Patron":
            if len(oc) >= 2:
                self.draw(2)
            elif len(oc) == 1:
                self.draw(1)
        elif n == "Banewhip Punisher":
            self.place_one(1)
        elif n == "Pollenbright Druid":
            if any(x.m > 0 for x in oc) or self.loyal or any(self.poison):
                self.proliferate()
        elif n in ("Massacre Wurm", "Archfiend of Sorrows"):
            self.minus_opp(2)
        elif n == "Oft-Nabbed Goat":
            self.cre.remove(c)
            self.goat = dict(ctrl="us", m=0)

    def enter_perm(self, name):
        if name == "The Meathook Massacre":
            self.minus_opp(2, ours=True)
        elif name == "Grave Venerations":
            self.monarch = True
        elif name == "Contagion Clasp":
            self.place_one(1)
        elif name == "Contagion Engine":
            al = self.alive()
            if al:
                i = max(al, key=lambda k: len(self.boards[k]))
                self.depth += 1
                for x in list(self.boards[i]):
                    self.put(x, 1)
                self.depth -= 1
                self.sba()
        elif name == "Vraska, Betrayal's Sting":
            self.loyal[name] = 6
        elif name == "Liliana, Death Wielder":
            self.loyal[name] = 5
        elif name == "Binding the Old Gods":
            self.binding_lore = 1
            self.binding_destroy()
        elif name == "Bastion of Remembrance":
            self.token("soldier")
        elif name in ("Swiftfoot Boots", "Lightning Greaves"):
            pass

    def binding_destroy(self):
        # destruye el permanente que más importa del rival con el reloj más cercano
        al = self.alive()
        if not al:
            return
        i = min(al, key=lambda k: self.rival_next[k])
        th = self._threat.get(i)
        if th and not th["stopped"] and th["kind"] != "other" and self.rival_next[i] <= self.turn + 2:
            th["stopped"] = True
            return
        if self.boards[i]:
            self.destroy_opp(i, max(self.boards[i], key=self.eff_pw))

    def destroy_opp(self, i, c):
        c.dead = True
        self.sba()

    def place_one(self, n=1):
        """Un contador (o n) en la mejor criatura objetivo."""
        oc = [c for c in self.opp_cre() if not c.dead]
        kill = [c for c in oc if self.eff_tg(c) <= n]
        if kill:
            self.put(max(kill, key=self.eff_pw), n)
            return
        if self.auntie() and (self.hand_size() <= 3 or not oc):
            ex = self.expendable(n)
            if ex:
                self.put(ex, n)
                return
        if oc:
            self.put(max(oc, key=self.eff_pw), n)
            return
        if self.auntie():
            ex = self.expendable(n)
            if ex:
                self.put(ex, n)

    def minus_opp(self, x, ours=False):
        """-X/-X hasta fin de turno a las criaturas rivales (y a las nuestras si ours)."""
        hit = [c for c in self.opp_cre() if not c.dead] + ([c for c in self.cre if not c.dead] if ours else [])
        for c in hit:
            c.mod -= x
        self.sba()
        for c in hit:
            if not c.dead:
                c.mod += x
        self.check_win()

    def each_creature(self, n, nonblack=False, only_opp=False, player=None):
        self.depth += 1
        targets = [c for c in self.all_cre() if not c.dead and (c.owner == "us" or c.owner in self.alive())]
        if only_opp:
            targets = [c for c in targets if c.owner != "us"]
        if nonblack:
            targets = [c for c in targets if not c.black]
        for c in targets:
            self.put(c, n)
        self.depth -= 1
        self.sba()
        self.check_win()

    # ================================================================ combos por regla
    def one_tough(self):
        return any(self.eff_tg(c) == 1 for c in self.cre) or any(self.eff_tg(c) == 1 for c in self.opp_cre())

    def loop_ready_natural(self):
        return self.on("Blowfly Infestation") and any(self.on(e) for e in ENGINES) and self.one_tough() \
            and not getattr(self, "_in_loop", False)

    def loop_numbers(self, kind):
        draws = (1 if self.auntie() else 0) + (1 if self.on("The Scorpion God") and kind == "blowfly" else 0)
        if kind == "yawg":
            draws += 1
        each = sum(self.count(n) for n in EACH_DRAIN) + self.count("Obelisk Spider")
        tgt = sum(self.count(n) for n in DRAIN_ONE) + (1 if self.on("All Will Be One") else 0)
        if kind == "yawg" and self.auntie():
            tgt += 1   # el contador va a una criatura rival que no muere: Auntie le quita 1
        gain = sum(self.count(n) for n in EACH_GAIN) + self.count("Obelisk Spider") + sum(self.count(n) for n in DRAIN_ONE)
        engines = sum(self.count(e) for e in ENGINES)
        return draws, each, tgt, gain, engines

    def loops_needed(self, each, tgt):
        lives = [self.opp[i] for i in self.alive()]
        if not lives:
            return 0
        if each == 0 and tgt == 0:
            return None
        lo, hi = 0, 400
        while lo < hi:
            mid = (lo + hi) // 2
            rest = sum(max(0, l - each * mid) for l in lives)
            if rest <= tgt * mid:
                hi = mid
            else:
                lo = mid + 1
        return lo if lo < 400 else None

    def run_loop(self, kind):
        """Resuelve un loop infinito por regla. Gana si hay pago y biblioteca suficiente."""
        self._in_loop = True
        draws, each, tgt, gain, engines = self.loop_numbers(kind)
        need = self.loops_needed(each, tgt)
        lib = len(self.library)
        maxl = (lib - 1) // draws if draws else 10 ** 6
        if kind == "yawg":
            net = gain - 1
            if net < 0:
                maxl = min(maxl, max(0, self.life - 8))
        self.ctr_flag = True
        if need is not None and need <= maxl:
            self.stats["combo"] = self.turn
            self.win_how = "combo"
            self.draw(draws * need) if draws else None
            for i in self.alive():
                self.opp[i] = 0
            self.won, self.win_turn = True, self.turn
            self.log("COMBO WIN", kind, "loops", need)
            self._in_loop = False
            return True
        # sin cierre: roba lo que convenga, deja fichas si hay 2 motores y drena lo posible
        # un jugador corta el loop a tiempo: roba como mucho 10 y nunca deja la biblioteca por debajo de 30
        safe = min(maxl, max(0, min(8, lib - 30)) // draws) if draws else 30
        for _ in range(safe):
            if each:
                self.drain_each(each)
            if tgt:
                self.drain_target(tgt)
        if draws:
            self.draw(draws * safe)
        self.charge += safe * self.count("Wickersmith's Tools")
        if engines >= 2 or (kind == "yawg" and engines >= 1):
            self.token("snake" if self.on("Hapatra, Vizier of Poisons") else "elf", 6)
        self.stats["loop_no_close"] = self.stats.get("loop_no_close", 0) + 1
        self.log("loop sin cierre", kind, "draws", draws * safe)
        self._in_loop = False
        self.sba()
        return self.won

    def starter(self):
        """¿Podemos poner el primer contador para arrancar el loop este turno? Devuelve costo o None."""
        for c in self.cre:
            if c.name == "Devoted Druid":
                return 0
            if c.name == "Grim Poppet" and c.m > 0:
                return 0
            if c.name == "Dawnhand Dissident" and not c.tapped and not c.sick:
                return 0
            if c.name == "Carnifex Demon" and c.m > 0:
                return 1
            if c.name == "The Scorpion God":
                return 3
            if c.name == "Sinister Gnarlbark":
                return 0
            if c.name == "Yawgmoth, Thran Physician":
                return 0
        if "Liliana, Death Wielder" in self.loyal:
            return 0
        best = None
        for h in self.hand:
            if h in ("Skinrender", "Dread Tiller", "Soul Snuffers", "Incremental Blight", "Black Sun's Zenith",
                     "Grim Affliction", "Whisper of the Dross", "Blight Rot", "Contagion Clasp", "Banewhip Punisher",
                     "Burning Curiosity", "Darkness Descends", "The Reaper, King No More", "Harbinger of Night"):
                g, p = parse_cost(CARDS[h]["cost"])
                v = g + len(p) + (1 if h == "Black Sun's Zenith" else 0)
                best = v if best is None else min(best, v)
        return best

    def try_combo(self):
        if self.won or self.lost:
            return False
        if self.on("Blowfly Infestation") and any(self.on(e) for e in ENGINES):
            st = self.starter()
            if st is not None and st <= self.avail():
                draws, each, tgt, gain, engines = self.loop_numbers("blowfly")
                need = self.loops_needed(each, tgt)
                if need is not None and (draws == 0 or need <= (len(self.library) - 1) // draws):
                    self.pay_generic(min(st, self.avail()))
                    return self.run_loop("blowfly")
        if self.on("Yawgmoth, Thran Physician") and any(self.on(e) for e in ENGINES) and \
                any(c.kind == "token" for c in self.cre):
            draws, each, tgt, gain, engines = self.loop_numbers("yawg")
            need = self.loops_needed(each, tgt)
            if need is not None and gain >= 1 and (draws == 0 or need <= (len(self.library) - 1) // draws):
                return self.run_loop("yawg")
        return False

    # ================================================================ hechizos y desarrollo
    PRIORITY = {
        "Sol Ring": 1, "Ignoble Hierarch": 2, "Arcane Signet": 3, "Channeler Initiate": 4, "Farseek": 4,
        "Rampant Growth": 4, "Nature's Lore": 4, "Devoted Druid": 5, "Commander's Sphere": 6,
        "Wickersmith's Tools": 7, "Dawnhand Dissident": 8, "Scuzzback Scrounger": 8, COMMANDER: 10,
        "Swiftfoot Boots": 11, "Lightning Greaves": 11, "Demonic Tutor": 12, "Vampiric Tutor": 12, "Worldly Tutor": 12,
        "Hapatra, Vizier of Poisons": 20, "Obelisk Spider": 21, "Lasting Tarfire": 22, "Nest of Scarabs": 23,
        "Grave Venerations": 24, "Sinister Gnarlbark": 25, "Dread Tiller": 26, "Generous Patron": 26,
        "Necroskitter": 27, "Blowfly Infestation": 28, "Flourishing Defenses": 29, "Evolution Sage": 29,
        "Contagion Clasp": 30, "Glissa Sunslayer": 31, "Kulrath Knight": 32, "Massacre Girl, Known Killer": 33,
        "Persistent Constrictor": 33, "The Scorpion God": 34, "Soul Snuffers": 35, "Village Pillagers": 36,
        "Harbinger of Night": 36, "Maha, Its Feathers Night": 37, "Skinrender": 37, "Carnifex Demon": 38,
        "Midnight Banshee": 39, "Dusk Urchins": 40, "Puppeteer Clique": 41, "Grave Titan": 42,
        "The Reaper, King No More": 43, "Wickerbough Elder": 44, "Oft-Nabbed Goat": 45, "Tree of Perdition": 46,
        "Vraska, Betrayal's Sting": 47, "Everlasting Torment": 48, "Binding the Old Gods": 49, "Grim Poppet": 50,
        "Ferrafor, Young Yew": 52, "Liliana, Death Wielder": 53, "Chimil, the Inner Sun": 54, "Puca's Covenant": 55,
        "Persist": 56, "Burning Curiosity": 57, "Night's Whisper": 58, "Painful Truths": 59, "Harmonize": 60,
        "Hoarder's Greed": 61, "Cathartic Reunion": 62, "Eventide's Shadow": 63, "Aberrant Return": 64,
        "Incremental Blight": 65, "Black Sun's Zenith": 70, "Chain Reaction": 71, "Darkness Descends": 70,
        "Soul Immolation": 72,
        "Ammit Eternal": 30, "Shadow Urchin": 34, "Banewhip Punisher": 36, "Mahadi, Emporium Master": 35,
        "Skullclamp": 15, "Yawgmoth, Thran Physician": 24, "All Will Be One": 31, "Contagion Engine": 50,
        "Crumbling Ashes": 28, "Zulaport Cutthroat": 23, "Blood Artist": 23, "Bastion of Remembrance": 25,
        "Cauldron of Essence": 27, "Morselhoarder": 45, "High-Society Hunter": 40, "Agent Venom": 33,
        "Grim Haruspex": 33, "Archfiend of Ifnir": 42, "Massacre Wurm": 37, "Archfiend of Sorrows": 41,
        "Diabolic Tutor": 12, "Grim Tutor": 12, "Diabolic Intent": 12, "Pollenbright Druid": 30, "Tezzeret's Gambit": 58,
        "The Meathook Massacre": 26,
    }

    def dev_ok(self, n):
        oc = self.opp_cre()
        if n in ("Soul Snuffers", "Black Sun's Zenith", "Darkness Descends", "Harbinger of Night", "Midnight Banshee") \
                and self.auntie() and len(self.library) - len(self.cre) < 30:
            return False   # el robo de Auntie es obligatorio: no vaciar la biblioteca
        if n == "Midnight Banshee" and self.auntie() and (self.on("Hapatra, Vizier of Poisons") or self.on("Flourishing Defenses")) and len(self.library) < 50:
            return False   # Banshee + Hapatra + Auntie: cada mantenimiento roba por cada serpiente
        if n in SELF_COUNTER and not self.auntie() and self.in_cmd and self.turn <= 5 and \
                self.policy.get("no_auntie") is not True:
            return False
        a = self.auntie()
        if n in ("Soul Snuffers", "Harbinger of Night") and a and self.eff_tg(a) <= 1:
            return False
        if n == "Darkness Descends" and a and self.eff_tg(a) <= 2:
            return False
        if n == "Soul Snuffers":
            return len(oc) >= 2 or (a and len(oc) >= 1)
        if n in ("Skinrender", "Incremental Blight"):
            return bool(oc) or (self.auntie() and self.expendable(3) is not None)
        if n == "Village Pillagers":
            return True
        if n == "Persist":
            return self.best_gy_creature() is not None
        if n == "Aberrant Return":
            return sum(1 for x in self.gy if x in CARDS and CARDS[x]["t"] == "C" and CARDS[x]["tg"] >= 2) >= 2
        if n == "Eventide's Shadow":
            return sum(c.m for c in self.cre if c.name != "Channeler Initiate") >= 3 and self.life > 15
        if n == "Cathartic Reunion":
            return len(self.hand) >= 4
        if n == "Black Sun's Zenith":
            return self.bsz_x() > 0
        if n == "Darkness Descends":
            return self.sweep_score(2) > 4
        if n == "The Meathook Massacre":
            return self.sweep_score(2) > 0 or self.turn >= 7
        if n in ("Massacre Wurm", "Archfiend of Sorrows"):
            return len(oc) >= 2 or self.turn >= 8
        if n == "Chain Reaction":
            return self.chain_ok()
        if n == "Soul Immolation":
            return self.immolation_x() >= 6
        if n in ("Night's Whisper", "Hoarder's Greed", "Painful Truths") and self.life < 12:
            return False
        if n in ("Swiftfoot Boots", "Lightning Greaves"):
            return True
        if n in ("Demonic Tutor", "Vampiric Tutor", "Worldly Tutor", "Diabolic Tutor", "Grim Tutor"):
            return self.tutor_target() is not None and (n != "Grim Tutor" or self.life > 10)
        if n == "Diabolic Intent":
            return self.tutor_target() is not None and self.intent_fodder() is not None
        if n == "Tezzeret's Gambit":
            return self.life > 10
        return True

    def intent_fodder(self):
        """Criatura para sacrificar a Diabolic Intent: una ficha o la criatura menos valiosa (nunca Auntie ni motores)."""
        keep = {COMMANDER, "Hapatra, Vizier of Poisons", "The Scorpion God", "Tree of Perdition"} | EACH_DRAIN | ENGINES
        toks = [c for c in self.cre if not c.dead and c.kind == "token"]
        if toks:
            return toks[0]
        cs = [c for c in self.cre if not c.dead and c.name not in keep]
        return min(cs, key=lambda c: (mv(c.name) if c.name in CARDS else 0)) if cs else None

    def auntie_ok(self):
        pol = self.policy.get("auntie")
        if self.policy.get("no_auntie"):
            return False
        if self.mode != "table" or pol is None:
            return True
        prot = self.on("Swiftfoot Boots") or self.on("Lightning Greaves")
        if pol == "wait_blue" and self.counters_left > 0 and self.turn < 9:
            if getattr(self, "_blue_roll", (None,))[0] != self.turn:
                self._blue_roll = (self.turn, self.rng.random() < self.cfg.p_counter)
            return not self._blue_roll[1]
        if pol == "protected":
            return prot or ("Heroic Intervention" in self.hand and self.avail() >= self.cost(COMMANDER)[0] + 5) or self.turn >= 8
        if pol == "late":
            return self.turn >= 7
        return True

    def castable(self):
        out = [c for c in set(self.hand) if c in self.PRIORITY]
        if self.in_cmd and self.auntie_ok():
            out.append(COMMANDER)
        return sorted(out, key=lambda c: self.PRIORITY[c])

    def develop(self):
        guard = 0
        while guard < 40 and not self.won and not self.lost:
            guard += 1
            if self.try_combo():
                return
            reserve = self.hold_amount()
            done = False
            for n in self.castable():
                if not self.dev_ok(n):
                    continue
                if self.can_pay(self.cost(n), extra=reserve if n != COMMANDER else 0):
                    if self.cast(n):
                        done = True
                        break
            if not done:
                done = self.utilities(reserve)
            if not done:
                break

    def is_key(self, n):
        if n == COMMANDER:
            return True
        if n == "Blowfly Infestation" and any(self.on(e) for e in ENGINES):
            return True
        if n in ENGINES and self.on("Blowfly Infestation"):
            return True
        return False

    def countered(self, n):
        if self.mode != "table" or self.counters_left <= 0 or not self.is_key(n):
            return False
        if self.rng.random() < self.cfg.p_counter:
            self.counters_left -= 1
            self.log("COUNTERED", n)
            return True
        return False

    def cast(self, n):
        c = self.cost(n)
        if not self.pay(c):
            return False
        phy_life = 2 * (len(parse_cost(CARDS[n]["cost"])[1]) - len(c[1]))
        if phy_life:
            self.life -= phy_life
            self.log("paga", phy_life, "de vida por maná phyrexiano")
        self.cast_count[n] = self.cast_count.get(n, 0) + 1
        if n == COMMANDER:
            if self.countered(n):
                self.tax += 2
                return True
            self.in_cmd = False
            c = Cr(COMMANDER, "us", 4, 4, tags=CARDS[COMMANDER]["tags"], black=True)
            self.cre.append(c)
            if self.auntie_turn is None:
                self.auntie_turn = self.turn
            self.log("cast Auntie")
            if self.on("Swiftfoot Boots") or self.on("Lightning Greaves"):
                c.eq = "boots"
            return True
        self.hand.remove(n)
        self.log("cast", n)
        if self.countered(n):
            self.gy.append(n)
            return True
        t = CARDS[n]["t"]
        if t in ("S", "I"):
            self.resolve_spell(n)
            if n != "Black Sun's Zenith":
                self.gy.append(n)
            return True
        self.enter(n)
        if n in ("Swiftfoot Boots", "Lightning Greaves") and self.auntie():
            if n == "Swiftfoot Boots":
                if self.avail() >= 1:
                    self.pay_generic(1)
                    self.auntie().eq = "boots"
            else:
                self.auntie().eq = "boots"
        return True

    def resolve_spell(self, n):
        oc = [c for c in self.opp_cre() if not c.dead]
        if n in ("Farseek",):
            self.fetch_basic(("Swamp", "Mountain"), tapped=True)
        elif n == "Rampant Growth":
            self.fetch_basic(tapped=True)
        elif n == "Nature's Lore":
            self.fetch_basic(("Forest",), tapped=False)
        elif n == "Night's Whisper":
            self.draw(2); self.life -= 2
        elif n == "Painful Truths":
            self.draw(3); self.life -= 3
        elif n == "Harmonize":
            self.draw(3)
        elif n == "Hoarder's Greed":
            self.life -= 2; self.draw(2)
            while self.rng.random() < 0.4 and self.life > 8:
                self.life -= 2; self.draw(2)
        elif n == "Burning Curiosity":
            ex = self.expendable(1) if self.auntie() else None
            if ex:
                self.put(ex)
                self.draw(2)
            else:
                self.draw(2)
        elif n == "Cathartic Reunion":
            self.discard(2)
            self.draw(3)
        elif n == "Eventide's Shadow":
            k = min(sum(c.m for c in self.cre if c.name != "Channeler Initiate"), self.life - 12, 6)
            for c in self.cre:
                take = min(c.m, k)
                c.m -= take
                k_ = take
            k = max(0, k)
            self.draw(k); self.life -= k
        elif n == "Persist":
            b = self.best_gy_creature()
            if b:
                self.gy.remove(b)
                self.enter(b, extra=1)
        elif n == "Aberrant Return":
            cs = sorted([x for x in self.gy if x in CARDS and CARDS[x]["t"] == "C" and CARDS[x]["tg"] >= 2],
                        key=lambda x: -mv(x))[:3]
            for x in cs:
                if x in self.gy:
                    self.gy.remove(x)
                    self.enter(x, extra=1)
        elif n == "Incremental Blight":
            for k in (3, 2, 1):
                cand = [c for c in self.opp_cre() if not c.dead]
                kill = [c for c in cand if self.eff_tg(c) <= k]
                if kill:
                    self.put(max(kill, key=self.eff_pw), k)
                elif cand:
                    self.put(max(cand, key=self.eff_pw), k)
                elif self.auntie():
                    ex = self.expendable(k)
                    if ex:
                        self.put(ex, k)
        elif n == "Black Sun's Zenith":
            x = self.bsz_x(pay=True)
            self.each_creature(x)
            self.library.insert(self.rng.randint(0, len(self.library)), n)
        elif n == "Darkness Descends":
            self.each_creature(2)
        elif n == "Chain Reaction":
            x = len([c for c in self.all_cre() if not c.dead])
            for c in list(self.all_cre()):
                self.damage_cre(c, x)
            self.sba()
        elif n == "Soul Immolation":
            x = self.immolation_x() if self.cre else 0
            if x:
                t = max(self.cre, key=self.eff_tg)
                self.put(t, x)
            self.drain_each(x, "immolation")
            for c in list(self.opp_cre()):
                self.damage_cre(c, x)
        elif n == "Tezzeret's Gambit":
            self.life -= 2
            self.draw(2)
            self.proliferate()
        elif n == "Diabolic Intent":
            f = self.intent_fodder()
            if f:
                f.dead = True
                self.sba()
            t = self.tutor_target()
            if t and t in self.library:
                self.library.remove(t)
                self.hand.append(t)
        elif n in ("Diabolic Tutor", "Grim Tutor"):
            t = self.tutor_target()
            if t:
                self.library.remove(t)
                self.hand.append(t)
            if n == "Grim Tutor":
                self.life -= 3
        elif n in ("Demonic Tutor", "Vampiric Tutor", "Worldly Tutor"):
            t = self.tutor_target(creature=(n == "Worldly Tutor"))
            if t:
                self.library.remove(t)
                if n == "Demonic Tutor":
                    self.hand.append(t)
                else:
                    self.library.append(t)
                if n == "Vampiric Tutor":
                    self.life -= 2
        elif n in INSTANT_ANS:
            # usado de forma proactiva (raro): mata la criatura rival más grande
            if oc:
                self.destroy_opp(oc[0].owner, max(oc, key=self.eff_pw))
            if n in ("Grim Affliction", "Atomize"):
                self.proliferate()

    def best_gy_creature(self):
        cs = [x for x in self.gy if x in CARDS and CARDS[x]["t"] == "C" and "legend" not in CARDS[x]["tags"]
              and CARDS[x]["tg"] >= 2]
        return max(cs, key=mv) if cs else None

    def tutor_target(self, creature=False):
        lib = [c for c in self.library if c in CARDS and (not creature or CARDS[c]["t"] == "C")]
        have = set(self.hand) | {c.name for c in self.cre} | set(self.perms)
        eng = any(e in have for e in ENGINES)
        if not creature:
            if eng and "Blowfly Infestation" not in have and "Blowfly Infestation" in lib:
                return "Blowfly Infestation"
            if "Blowfly Infestation" in have and not eng:
                for e in ("Hapatra, Vizier of Poisons", "Nest of Scarabs", "Flourishing Defenses"):
                    if e in lib:
                        return e
            if "Blowfly Infestation" in have and eng and not any(p in have for p in EACH_DRAIN | {"Obelisk Spider"}):
                for e in ("Grave Venerations", "Obelisk Spider", "Zulaport Cutthroat", "Bastion of Remembrance"):
                    if e in lib:
                        return e
        for e in ("Hapatra, Vizier of Poisons", "Obelisk Spider", "Massacre Girl, Known Killer", "Kulrath Knight"):
            if e in lib and e not in have:
                return e
        return lib[-1] if lib else None

    # ---------------------------------------------------------------- barridas
    def sweep_score(self, x):
        ours = [c for c in self.cre if c.name != "Tree of Perdition"]
        oc = self.opp_cre()
        kill_o = sum(self.eff_pw(c) + 1 for c in oc if self.eff_tg(c) <= x)
        kill_u = sum(self.eff_pw(c) + (6 if c.name in (COMMANDER, "Hapatra, Vizier of Poisons") else 1)
                     for c in ours if self.eff_tg(c) <= x and c.kind == "card")
        draws = sum(1 for c in ours) if self.auntie() and self.auntie() is not None and self.eff_tg(self.auntie()) > x else 0
        drains = len(oc) if self.auntie() and self.eff_tg(self.auntie()) > x else 0
        return kill_o + 0.8 * drains + 0.7 * min(draws, 5) - kill_u

    def bsz_x(self, pay=False):
        bud = self.avail() - 2
        best, bx = 3.5, 0
        for x in range(1, max(1, min(bud, 6)) + 1):
            s = self.sweep_score(x)
            if s > best:
                best, bx = s, x
        if pay and bx:
            self.pay_generic(min(bx, self.avail()))
        return bx

    def chain_ok(self):
        x = len(self.all_cre())
        oc = self.opp_cre()
        po = sum(self.eff_pw(c) for c in oc if self.eff_tg(c) <= x)
        pu = sum(self.eff_pw(c) + (6 if c.name == COMMANDER else 0) for c in self.cre if self.eff_tg(c) <= x)
        return po >= 10 and po >= 2 * pu

    def immolation_x(self):
        if not self.cre:
            return 0
        return max(0, max(self.eff_tg(c) for c in self.cre) - (0 if True else 1))

    # ---------------------------------------------------------------- respuestas guardadas
    def answers(self, kind, roll=True):
        out = []
        for c in self.hand:
            if c in INSTANT_ANS:
                k = INSTANT_ANS[c]
                if kind == "cre" or k == "any" or (kind == "ae" and k in ("cre_art",) and (not roll or self.rng.random() < 0.5)):
                    if roll and kind == "cre" and k in ANS_P and self.rng.random() > ANS_P[k]:
                        continue
                    g, p = parse_cost(CARDS[c]["cost"])
                    out.append((g + len(p), "hand", c))
        if kind == "cre":
            for c in self.cre:
                if c.name == "Grim Poppet" and c.m > 0:
                    out.append((0, "poppet", c))
                if c.name == "Banewhip Punisher":
                    out.append((1, "banewhip", c))
        if kind == "ae":
            for c in self.cre:
                if c.name == "Wickerbough Elder" and c.m > 0:
                    out.append((1, "wicker", c))
        out.sort(key=lambda x: x[0])
        return out

    def hold_amount(self):
        if self.mode != "table" or self.turn < self.cfg.hold_from_turn:
            return 0
        a = self.answers("cre", roll=False) + self.answers("ae", roll=False)
        return min([x[0] for x in a]) if a else 0

    def use_answer(self, ans, i):
        cost, where, ref = ans
        key = ref if where == "hand" else where
        self.cast_count[key] = self.cast_count.get(key, 0) + 1
        if where == "hand":
            self.hand.remove(ref)
            self.gy.append(ref)
            if ref == "Fire Covenant":
                self.life -= 4
            if ref in ("Grim Affliction", "Atomize"):
                self.proliferate()
        elif where == "poppet":
            ref.m -= 1
            if self.boards[i]:
                self.put(min(self.boards[i], key=self.eff_tg), 1)
        elif where == "banewhip":
            ref.dead = True
            self.sba()
        elif where == "wicker":
            ref.m -= 1

    # ---------------------------------------------------------------- habilidades
    def utilities(self, reserve):
        for c in self.cre:
            if c.sick or c.tapped:
                continue
            if c.name == "Dawnhand Dissident" and self.auntie():
                ex = self.expendable(1)
                if ex:
                    c.tapped = True
                    self.put(ex)
                    return True
            if c.name == "Ferrafor, Young Yew":
                oc = [x for x in self.opp_cre() if x.m > 0]
                if oc:
                    c.tapped = True
                    t = max(oc, key=lambda x: x.m)
                    self.put(t, t.m)
                    return True
            if c.name == "Tree of Perdition" and not getattr(self, "tree_used", False):
                al = self.alive()
                if al:
                    i = max(al, key=lambda k: self.opp[k])
                    if self.opp[i] >= 20:
                        c.tapped = True
                        self.tree_used = True
                        old = self.opp[i]
                        self.opp[i] = max(0, self.eff_tg(c))
                        c.tg = old + c.m
                        self.win_how = self.win_how or "tree"
                        self.check_win()
                        return True
        for c in self.cre:
            if c.name == "The Scorpion God" and self.avail() - reserve >= 3 and self.can_pay((1, ["B", "R"]), reserve):
                oc = [x for x in self.opp_cre() if self.eff_tg(x) == 1]
                if oc:
                    self.pay((1, ["B", "R"]))
                    self.put(max(oc, key=self.eff_pw))
                    return True
            if c.name == "Yawgmoth, Thran Physician" and self.life > 15:
                tok = next((x for x in self.cre if x.kind == "token" and x.tok != "stolen"), None)
                oc = [x for x in self.opp_cre() if self.eff_tg(x) == 1]
                if tok and (oc or self.auntie()) and len([x for x in self.cre if x.kind == "token"]) >= 2:
                    self.life -= 1
                    tok.dead = True
                    self.sba()
                    if oc:
                        self.put(max(oc, key=self.eff_pw))
                    else:
                        self.place_one(1)
                    self.draw(1)
                    return True
        if self.on("Skullclamp") and self.avail() - reserve >= 1:
            t = next((x for x in self.cre if x.kind == "token" and self.eff_tg(x) == 1), None)
            if t:
                self.pay_generic(1)
                t.eq = "clamp"
                t.dead = True
                self.sba()
                return True
        if self.on("Contagion Clasp") and self.avail() - reserve >= 4 and self.turn >= 5 and \
                not getattr(self, "_clasp_t", None) == self.turn:
            if any(x.m > 0 for x in self.opp_cre()) or "Vraska, Betrayal's Sting" in self.loyal or any(self.poison):
                self._clasp_t = self.turn
                self.pay_generic(4)
                self.proliferate()
                return True
        if self.on("Contagion Engine") and self.avail() - reserve >= 4 and not getattr(self, "_eng_t", None) == self.turn:
            if any(x.m > 0 for x in self.opp_cre()) or any(self.poison):
                self._eng_t = self.turn
                self.pay_generic(4)
                self.proliferate(); self.proliferate()
                return True
        if self.on("Wickersmith's Tools") and self.charge >= 4 and self.avail() - reserve >= 5 and self.turn >= 6:
            self.pay_generic(5)
            self.perms["Wickersmith's Tools"] -= 1
            if self.perms["Wickersmith's Tools"] <= 0:
                del self.perms["Wickersmith's Tools"]
            self.gy.append("Wickersmith's Tools")
            self.token("scarecrow", self.charge)
            self.charge = 0
            return True
        # ciclar tierras sobrantes
        if len(self.lands) >= 6:
            for l in self.hand:
                if l in LANDS and LANDS[l].get("cyc") and self.avail() - reserve >= LANDS[l]["cyc"]:
                    self.pay_generic(LANDS[l]["cyc"])
                    self.hand.remove(l)
                    self.gy.append(l)
                    self.on_discard(1)
                    self.draw(1)
                    return True
        return False

    def discard(self, n):
        for _ in range(n):
            if not self.hand:
                return
            lands = [c for c in self.hand if c in LANDS]
            if len(lands) >= 2 or (lands and len(self.lands) >= 6):
                c = lands[0]
            else:
                c = max(self.hand, key=lambda x: (x not in LANDS, mv(x) if x not in LANDS else 0))
            self.hand.remove(c)
            self.gy.append(c)
            self.on_discard(1)

    def on_discard(self, n):
        for _ in range(self.count("Archfiend of Ifnir") * n):
            self.each_creature(1, only_opp=True)

    # ================================================================ combate
    def our_combat(self):
        al = self.alive()
        if not al:
            return
        i = min(al, key=lambda k: self.opp[k])
        locked = self.on("Kulrath Knight")
        blockers = [b for b in self.boards[i] if not (locked and b.m > 0)]
        if self.mode != "table":
            blockers = []
        else:
            k = min(3, max(0, (self.turn - 2) // 2))
            blockers = sorted(blockers, key=self.eff_tg, reverse=True)[:k]
        anti_air = [b for b in blockers if b.flying]
        atk = []
        for c in self.cre:
            if c.tapped or c.sick or self.eff_pw(c) <= 0 or "defender" in c.tags or c.kind == "token" and c.tok == "insect" and False:
                continue
            if c.name in KEEP_HOME and blockers:
                continue
            evasive = c.flying and not anti_air
            safe = evasive or not any(self.eff_pw(b) >= self.eff_tg(c) and (not c.flying or b.flying) for b in blockers) \
                or "dt" in c.tags and self.eff_pw(c) >= 1 and c.kind == "card"
            if c.name == "Glissa Sunslayer":
                safe = True
            if c.name == COMMANDER and not safe:
                continue
            many = sum(1 for x in self.cre if x.kind == "token") > 12
            if safe or (c.kind == "token" and (len(blockers) <= 1 or many)):
                atk.append(c)
        if not atk:
            return
        # el rival bloquea para matar sin perder, o en chump si el daño es letal
        free = list(blockers)
        blocked = {}
        total = sum(self.eff_pw(a) for a in atk)
        for a in sorted(atk, key=self.eff_pw, reverse=True):
            cands = [b for b in free if (not a.flying or b.flying) and a.name != "Glissa Sunslayer"]
            good = [b for b in cands if self.eff_pw(b) >= self.eff_tg(a) and "dt" not in a.tags]
            if "menace" in a.tags:
                continue
            if good:
                b = min(good, key=self.eff_pw)
            elif cands and total >= self.opp[i]:
                b = min(cands, key=self.eff_pw)
            else:
                continue
            free.remove(b)
            blocked[id(a)] = b
        dmg = 0
        for a in atk:
            a.tapped = True
            if a.name == "Dusk Urchins":
                self.put(a, 1)
            if a.name == "Shadow Urchin":
                ex = self.expendable(1)
                if ex:
                    self.put(ex)
            if a.name == "Grave Titan":
                self.token("zombie", 2)
            if a.dead:
                continue
            b = blocked.get(id(a))
            wither = "wither" in a.tags or self.on("Massacre Girl, Known Killer")
            if b is not None:
                pa, pb = self.eff_pw(a), self.eff_pw(b)
                if "dt" in a.tags:
                    b.dead = True
                self.damage_cre(b, pa, wither=wither)
                if not b.dead or "dt" not in a.tags:
                    self.damage_cre(a, pb)
                continue
            p = self.eff_pw(a)
            dmg += p
            if a.name == COMMANDER:
                self.cmd_dmg[i] += p
            if a.name == "Glissa Sunslayer":
                self.draw(1); self.life -= 1
            if a.name == "Hapatra, Vizier of Poisons":
                self.place_one(1)
            if a.name == "Ammit Eternal":
                a.m = 0
        self.sba()
        if dmg:
            self.lose_opp(i, dmg, "combat")
            if self.cmd_dmg[i] >= 21:
                self.lose_opp(i, self.opp[i], "combat")
            if getattr(self, "monarch_owner", None) == i:
                self.monarch, self.monarch_owner = True, None
        self.log("attack", i, "dmg", dmg, "opp", self.opp)

    def rival_attack(self, i):
        cfg = self.cfg
        if not cfg.combat or self.turn < cfg.combat_start or cfg.kinds[i] != "combat":
            return
        if self.rng.random() >= self.p_us():
            return
        locked = self.on("Kulrath Knight")
        atk = [b for b in self.boards[i] if self.eff_pw(b) > 0 and not (locked and b.m > 0)]
        if not atk:
            return
        ours = [c for c in self.cre if not c.tapped and not c.dead and not c.steal]
        incoming = sum(self.eff_pw(a) for a in atk)
        desperate = incoming >= self.life - 5
        dmg = 0
        for a in sorted(atk, key=self.eff_pw, reverse=True):
            cand = [c for c in ours if (not a.flying or "reach" in c.tags or c.flying)]
            good = [c for c in cand if "dt" in c.tags or self.eff_tg(c) > self.eff_pw(a)
                    or ("wither" in c.tags or self.on("Massacre Girl, Known Killer")) and self.eff_pw(c) >= self.eff_tg(a)]
            good = [c for c in good if c.name not in (COMMANDER, "Hapatra, Vizier of Poisons") or desperate]
            chump = [c for c in cand if c.kind == "token"] if desperate else []
            pick = (min(good, key=lambda c: (c.kind != "token", self.eff_pw(c))) if good else
                    (chump[0] if chump else None))
            if pick is None:
                dmg += self.eff_pw(a)
                continue
            ours.remove(pick)
            wither = "wither" in pick.tags or self.on("Massacre Girl, Known Killer")
            pa = self.eff_pw(a)
            if "dt" in pick.tags and self.eff_pw(pick) > 0:
                a.dead = True
            self.damage_cre(a, self.eff_pw(pick), wither=wither)
            self.damage_cre(pick, pa)
        self.sba()
        for c in self.cre:
            c.dmg = 0
        if dmg > 0:
            self.life -= dmg
            if self.monarch:
                self.monarch = False
                self.monarch_owner = i
            self.log("rival", i, "attacks for", dmg, "life", self.life)
            if self.life <= 0:
                self.lost = True
                self.log("LOSS: combat")

    # ================================================================ turnos
    def p_us(self):
        t = self.cfg.target
        if t == "always":
            return 1.0
        if t == "spread":
            return 1 / 3
        return 0.75 if self.threatening() else 0.25

    def threatening(self):
        if self.won:
            return False
        eng = sum(1 for n in ("Blowfly Infestation", "Hapatra, Vizier of Poisons", "Flourishing Defenses",
                              "Grave Venerations", "Lasting Tarfire", "Kulrath Knight", "The Scorpion God",
                              "Nest of Scarabs", "Obelisk Spider") if self.on(n))
        power = sum(self.eff_pw(c) for c in self.cre)
        return (self.auntie() is not None and eng >= 2) or power >= 15

    def our_turn(self):
        self.our = True
        self.turn += 1
        self.deaths_turn = 0
        self.puca_used = self.reaper_used = False
        self.ctr_flag = False
        self.treasures += getattr(self, "treasures_tapped", 0)
        self.treasures_tapped = 0
        self._tapped_lands = set()
        for c in self.cre:
            c.tapped = c.sick = False
            c.dmg = 0
        n_lands_before = len(self.lands)
        self.upkeep()
        if self.won or self.lost:
            return
        if not (self.turn == 1 and self.on_play):
            self.draw(1)
        if self.lost:
            return
        self.compute_pool()
        self.play_land()
        # tierras que entraron giradas este turno no producen
        for c in self.cre:
            if c.name == "Scuzzback Scrounger" and not c.sick:
                ex = self.expendable(1) or (c if self.eff_tg(c) > 1 else None)
                if ex:
                    self.put(ex)
                    self.treasures += 1
        if self.mode == "table":
            self.preempt()
        self.develop()
        if self.won or self.lost:
            return
        self.walkers()
        self.our_combat()
        if self.won or self.lost:
            return
        self.develop()
        if self.won or self.lost:
            return
        if self.turn == 8:
            have = set(self.hand) | {c.name for c in self.cre} | set(self.perms)
            self.stats["t8"] = dict(
                auntie=self.auntie() is not None, lands=len(self.lands), hand=self.hand_size(),
                blowfly="Blowfly Infestation" in have, engine=any(e in have for e in ENGINES),
                payoff=any(p in have for p in EACH_DRAIN | {"Obelisk Spider"}),
                opp_cre=len(self.opp_cre()), opp_min=min(self.opp[i] for i in self.alive()) if self.alive() else 0)
        self.end_step()
        for c in list(self.cre):
            if c.steal:
                self.cre.remove(c)
        self.our = False

    def walkers(self):
        for w in list(self.loyal):
            if w == "Vraska, Betrayal's Sting":
                al = self.alive()
                if self.loyal[w] >= 9 and al:
                    i = max(al, key=lambda k: self.opp[k])
                    self.poison[i] = max(self.poison[i], 9)
                    self.loyal[w] -= 9
                    self.log("Vraska -9 on", i)
                else:
                    self.draw(1); self.life -= 1
                    self.proliferate()   # suma 1 de lealtad a Vraska y veneno a quien tenga
            elif w == "Liliana, Death Wielder":
                gyc = sum(1 for x in self.gy if x in CARDS and CARDS[x]["t"] == "C")
                if self.loyal[w] >= 10 and gyc >= 4:
                    for x in [x for x in self.gy if x in CARDS and CARDS[x]["t"] == "C"]:
                        if x in self.gy:
                            self.gy.remove(x)
                            self.enter(x)
                    self.loyal[w] -= 10
                else:
                    self.loyal[w] += 2
                    self.place_one(1)
            if self.loyal.get(w, 1) <= 0:
                self.loyal.pop(w, None)
                self.gy.append(w)
        self.sba()
        self.check_win()

    def upkeep(self):
        self.depth += 1
        if self.on("Midnight Banshee"):
            for _ in range(self.count("Midnight Banshee")):
                for c in [c for c in self.all_cre() if not c.black and not c.dead and (c.owner == "us" or c.owner in self.alive())]:
                    self.put(c, 1)
        if self.on("Harbinger of Night"):
            for _ in range(self.count("Harbinger of Night")):
                for c in [c for c in self.all_cre() if not c.dead and (c.owner == "us" or c.owner in self.alive())]:
                    self.put(c, 1)
        self.depth -= 1
        self.sba()
        if self.on("Crumbling Ashes"):
            oc = [c for c in self.opp_cre() if c.m > 0]
            if oc:
                self.destroy_opp(oc[0].owner, max(oc, key=self.eff_pw))
        if getattr(self, "binding_lore", 0) and self.on("Binding the Old Gods"):
            self.binding_lore += 1
            if self.binding_lore == 2:
                self.fetch_basic(("Forest",), tapped=True)
            elif self.binding_lore >= 3:
                self.perms["Binding the Old Gods"] -= 1
                if self.perms["Binding the Old Gods"] <= 0:
                    del self.perms["Binding the Old Gods"]
                self.gy.append("Binding the Old Gods")
                self.binding_lore = 0
        self.check_win()

    def end_step(self):
        self.depth += 1
        for c in list(self.cre):
            if c.name == "Sinister Gnarlbark" and not c.dead:
                self.draw(1)
                tok = next((x for x in self.cre if x.kind == "token" and self.eff_tg(x) == 1), None)
                if tok and self.on("Blowfly Infestation"):
                    self.put(tok)
                else:
                    ex = self.expendable(1) or c
                    self.put(ex)
        self.depth -= 1
        self.sba()
        if self.ctr_flag:
            for _ in range(self.count("Lasting Tarfire")):
                self.drain_each(2, "tarfire")
        if self.on("Chimil, the Inner Sun"):
            for k in range(len(self.library) - 1, -1, -1):
                x = self.library[k]
                if x in CARDS and mv(x) <= 5 and x not in INSTANT_ANS and x not in ("Black Sun's Zenith", "Soul Immolation"):
                    self.library.pop(k)
                    if CARDS[x]["t"] in "SI":
                        self.resolve_spell(x)
                        if x != "Black Sun's Zenith":
                            self.gy.append(x)
                    else:
                        self.enter(x)
                    break
        if self.on("Grave Venerations") and self.monarch:
            b = max([x for x in self.gy if x in CARDS and CARDS[x]["t"] == "C"], key=mv, default=None)
            if b:
                self.gy.remove(b)
                self.hand.append(b)
        if self.monarch:
            self.draw(1)
        if self.on("Mahadi, Emporium Master"):
            self.treasures += self.deaths_turn
        if self.scorpion_back:
            self.scorpion_back = False
            self.hand.append("The Scorpion God")
        while len(self.hand) > 7:
            self.discard(1)
        self.check_win()

    def opp_turns(self):
        self.our = False
        for i in range(3):
            if self.won or self.lost:
                return
            self.ctr_flag = False
            self.reaper_used = False
            if self.opp[i] <= 0 or self.poison[i] >= 10:
                continue
            # mantenimiento rival: Persistent Constrictor
            for _ in range(self.count("Persistent Constrictor")):
                self.lose_opp(i, 1)
                if self.boards[i]:
                    b = self.boards[i]
                    kill = [x for x in b if self.eff_tg(x) <= 1]
                    self.put(max(kill or b, key=self.eff_pw))
            if self.won:
                return
            self.rival_develop(i)
            for c in self.cre:
                if c.name == "Ammit Eternal" and not c.dead:
                    self.put(c, 1 + (self.rng.random() < 0.5))
            if self.goat and self.turn >= 4 and self.rng.random() < 0.35 and self.goat["m"] < 5:
                self.goat["ctrl"] = i
                self.goat["m"] += 1
                if self.auntie():
                    self.lose_opp(i, 1)
                if self.on("Flourishing Defenses"):
                    self.token("elf", self.count("Flourishing Defenses"))
                if self.goat["m"] >= 5:
                    self.goat_dies()
            self.instant_speed(i)
            if self.mode == "table":
                self.table_events(i)
            if self.ctr_flag:
                for _ in range(self.count("Lasting Tarfire")):
                    self.drain_each(2, "tarfire")
            self.sba()
            self.check_win()

    def goat_dies(self):
        m = self.goat["m"]
        self.goat = None
        if m:
            self.draw(m)
            self.drain_each(m, "goat")
        self.gy.append("Oft-Nabbed Goat")

    def instant_speed(self, i):
        # contadores en turno rival con habilidades instantáneas (activan Lasting Tarfire)
        for c in self.cre:
            if c.name == "Devoted Druid" and c.m == 0 and self.auntie():
                self.put(c)
            if c.name == "Grim Poppet" and c.m > 0:
                oc = [x for x in self.opp_cre() if self.eff_tg(x) <= 1]
                if oc:
                    c.m -= 1
                    self.put(max(oc, key=self.eff_pw))

    def rival_develop(self, i):
        cfg = self.cfg
        if self.mode == "table":
            for b in list(self.boards[i]):
                if self.rng.random() < 0.10:
                    self.boards[i].remove(b)
                    self.natural[i] -= b.pw
                    if b.kind == "card":
                        self.opp_gy[i].append((b.pw, b.tg, b.flying))
        p = cfg.grow_combat if cfg.kinds[i] == "combat" else cfg.grow_combo
        if self.turn >= 2 and self.rng.random() < p:
            r = self.rng.random()
            if r < 0.15:
                for _ in range(2):
                    self.boards[i].append(Cr("tok", i, 1, 1, kind="token"))
                self.natural[i] += 2
            else:
                sizes = [(1, 0.2), (2, 0.25), (3, 0.25), (4, 0.15), (5, 0.1), (6, 0.05)]
                if cfg.kinds[i] != "combat":
                    sizes = [(1, 0.35), (2, 0.35), (3, 0.2), (4, 0.1)]
                x, acc = self.rng.random(), 0
                for s, w in sizes:
                    acc += w
                    if x <= acc:
                        break
                s = max(1, int(round(s * cfg.size)))
                c = Cr("opp", i, s, s, black=self.rng.random() < 0.2, flying=self.rng.random() < cfg.flyer_p)
                self.boards[i].append(c)
                self.natural[i] += s

    def preempt(self):
        # en nuestro turno: amenaza visible de un rival -> respuestas de conjuro (Binding)
        for i in self.alive():
            if self.rival_next[i] == self.turn + 1 or self.rival_next[i] == self.turn:
                th = self.roll_threat(i)
                if th["visible"] and th["stoppable"] and not th["stopped"] and "Binding the Old Gods" in self.hand \
                        and self.can_pay(self.cost("Binding the Old Gods")):
                    self.pay(self.cost("Binding the Old Gods"))
                    self.hand.remove("Binding the Old Gods")
                    self.perms["Binding the Old Gods"] = self.perms.get("Binding the Old Gods", 0) + 1
                    self.binding_lore = 1
                    th["stopped"] = True

    def roll_threat(self, i):
        th = self._threat.get(i)
        if th and th["t"] == self.rival_next[i]:
            return th
        kind = "cre" if self.cfg.kinds[i] == "combat" else ("ae" if self.rng.random() < 0.5 else "other")
        th = dict(t=self.rival_next[i], kind=kind, stoppable=self.rng.random() < self.cfg.p_stoppable,
                  visible=self.rng.random() < self.cfg.p_visible, stopped=False)
        self._threat[i] = th
        return th

    def table_events(self, i):
        cfg = self.cfg
        self.rival_attack(i)
        if self.lost or self.won:
            return
        # barrida (una por partida)
        if not self.wipe_done and self.turn >= self.wipe_turn and self.rng.random() < 0.5:
            self.wipe_done = True
            if "Heroic Intervention" in self.hand and self.reserve_ok(2):
                self.hand.remove("Heroic Intervention"); self.gy.append("Heroic Intervention")
            else:
                self.log("WIPE")
                for c in self.cre:
                    c.dead = True
                if self.goat:
                    self.goat_dies()
            for k in range(3):
                for b in self.boards[k]:
                    b.dead = True
                self.natural[k] = 0
            self.sba()
            if self.won or self.lost:
                return
        # remoción puntual
        if self.rng.random() < cfg.p_removal and self.rng.random() < self.p_us():
            self.rival_removal(i)
        # intento de ganar del rival
        if self.opp[i] > 0 and self.rival_next[i] == self.turn:
            th = self.roll_threat(i)
            if th["stopped"]:
                self.rival_next[i] = self.turn + cfg.delay
                return
            if cfg.p_others > 0 and self.rng.random() < cfg.p_others:
                self.rival_next[i] = self.turn + cfg.delay
                self.stats["others"] = self.stats.get("others", 0) + 1
                return
            if th["kind"] == "cre":
                locked = self.on("Kulrath Knight")
                power = sum(self.eff_pw(b) for b in self.boards[i] if not (locked and b.m > 0))
                if self.natural[i] >= 4 and power < cfg.control_ratio * self.natural[i]:
                    self.rival_next[i] = self.turn + cfg.delay
                    self.stats["controlled"] = self.stats.get("controlled", 0) + 1
                    self.log("rival", i, "frenado por control", power, self.natural[i])
                    return
            if th["stoppable"]:
                for ans in self.answers(th["kind"] if th["kind"] != "other" else "any"):
                    if self.reserve_ok(ans[0]):
                        self.use_answer(ans, i)
                        self.rival_next[i] = self.turn + cfg.delay
                        self.log("answered rival", i, ans[2] if ans[1] == "hand" else ans[1])
                        return
            self.lost = True
            self.log("LOSS: rival", i, "wins")

    def reserve_ok(self, n):
        if n <= 0:
            return True
        if self.avail() >= n:
            self.pay_generic(n)
            return True
        return False

    def rival_removal(self, i):
        a = self.auntie()
        cands = [c for c in self.cre if c.kind == "card" and c.name in (
            "Hapatra, Vizier of Poisons", "The Scorpion God", "Kulrath Knight", "Massacre Girl, Known Killer",
            "Midnight Banshee", "Carnifex Demon", "Necroskitter", "Obelisk Spider", "Village Pillagers",
            "Yawgmoth, Thran Physician", "Maha, Its Feathers Night", "Persistent Constrictor", "Harbinger of Night",
            "Grave Titan", "Sinister Gnarlbark", "Evolution Sage", "Dread Tiller", "Massacre Wurm",
            "Archfiend of Sorrows")]
        ench = [n for n in ("Blowfly Infestation", "Grave Venerations", "Lasting Tarfire", "Flourishing Defenses",
                            "Nest of Scarabs", "All Will Be One", "The Meathook Massacre", "Crumbling Ashes") if n in self.perms]
        victim = None
        if a and a.eq != "boots" and (self.rng.random() < 0.6 or not cands):
            if not self.boards[i]:
                return   # ward—Blight 2 sin criaturas: no puede pagarlo
            b = max(self.boards[i], key=self.eff_tg)
            self.put(b, 2, by_us=False)   # el rival se pone los contadores: Auntie le quita 1
            victim = a
        elif ench and self.rng.random() < 0.3:
            n = self.rng.choice(ench)
            self.perms[n] -= 1
            if self.perms[n] <= 0:
                del self.perms[n]
            self.gy.append(n)
            self.log("removal on", n)
            return
        elif cands:
            victim = self.rng.choice(cands)
        if victim is None or victim.dead:
            return
        if "Heroic Intervention" in self.hand and self.reserve_ok(2):
            self.hand.remove("Heroic Intervention"); self.gy.append("Heroic Intervention")
            return
        self.log("removal on", victim.name)
        victim.dead = True
        self.sba()

    def run(self, max_turns=20):
        while self.turn < max_turns and not self.won and not self.lost:
            self.our_turn()
            if self.won or self.lost:
                break
            self.opp_turns()
        return self


def play(deck, seed, **kw):
    rng = random.Random(seed)
    cfg = kw.get("cfg")
    if cfg is not None and getattr(cfg, "v2", "") and kw.get("mode", "table") == "table":
        from mesa2 import Game2
        g = Game2(deck, rng, **kw)
    else:
        g = Game(deck, rng, **kw)
    g.run()
    return g
