"""Monte Carlo simulator for Blor the Impervious (mono-green voltron: one big hexproof, indestructible trampler).

Same table model as the Gorma / Giada / Blight Curse simulators (rival kill clocks, removal, one wipe, one counter,
rival combat, p_others), with a voltron combat engine for our side:
  * Blor's power from counters, auras, equipment and tricks; double strike, damage doubling, deathtouch + trample,
    infect / poison (Grafted Exoskeleton, Triumph of the Hordes, Fynn), extra combat (Genji Glove).
  * Rival blockers absorb damage up to their toughness (trample), or 1 with deathtouch; evasion skips the block.
  * What hurts a voltron: artifact/enchantment removal on the attachments, edicts, exile / -X/-X / bounce wipes,
    counterspells on the commander, fogs. Blor ignores targeted creature removal and destroy wipes.
Abstractions and calibration: see simulador-montecarlo.md (section 12).
"""
import random
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", ".."))
from core import mesa as M
from dataclasses import dataclass, field
from itertools import combinations
from cards import C, LANDS, COMMANDER, is_land

B = COMMANDER


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
    p_others: float = 0.0
    # voltron-specific
    p_block: float = 0.55          # rival blocks Blor when it has a creature (0.9 if the hit is lethal)
    p_green_blocker: float = 0.2   # share of rival blockers that are green (Commander's Plate)
    p_nonbasic: float = 0.9        # rival controls a nonbasic land (Trailblazer's Boots)
    p_fog: float = 0.03            # rival fogs our attack
    removal_mix: tuple = (0.55, 0.15, 0.30)     # artifact/enchantment-capable, edict, creature-only
    wipe_mix: tuple = (0.55, 0.15, 0.15, 0.15)  # destroy, -X/-X, exile, bounce
    p_wipe_ae: float = 0.25        # a destroy wipe also takes artifacts/enchantments (Austere, Bane of Progress)
    pump: str = "kill"             # kill: tricks only for a kill (or when the hand is full of them); greedy: spend spare mana
    focus: str = "progress"        # progress: the rival closest to dying; threat: the next rival to win
    rival_spells: float = 1.5      # spells per rival turn (Forgotten Ancient)
    deterrence: float = 0.0        # chance a rival skips attacking us when an untapped Blor of 8+ power waits
    attack_policy: str = "always"  # always / big:N (only lethal or power >= N) / safe (stay home if the swing back hurts)
    # ---- mesa v2 (14/11) ----
    bracket: str = ""              # "" = mesa v1; "B1".."B5", "B3+B4" = mesa v2 (ver scen.BRACKETS)
    opp_curve: tuple = (0.1, 0.1, 1.0)   # amenaza del rival tipico: min(v0 + dv*turno, vmax)
    opp_noise: float = 0.2
    w_plan: float = 0.1            # regla 2-B (Juan): +0,1 a Blor por ser el plan visible de todo el mazo
    w_arch: float = 0.3            # archienemigo de v2: +0,3 x fraccion del dano total que ya les hiciste
    w_cmd: float = 0.5             # regla 2-D (Juan): cada rival +0,5 x (su dano de comandante / 21)
    # regla 3 (14/11): cada rival ROBA y GUARDA su interaccion (datos de 6532 mazos de Archidekt)
    rem: float = 5                 # remocion puntual por mazo de 99
    cpt: float = 1.3               # cartas que ve cada rival por turno
    wipes: float = 2               # barridas por mazo
    n_blue: int = 1                # rivales azules (Juan: uno por mesa)
    cnt: float = 5                 # counters en el mazo azul
    # regla 5 (PROPUESTA, falta aprobar): tipo de cada remocion robada: solo criaturas / cualquier permanente /
    # solo artefacto o encantamiento / edicto (Juan: edictos raros)
    rem_types: tuple = (("cre", 0.55), ("any", 0.20), ("ae", 0.20), ("edict", 0.05))
    p_instant: float = 0.5         # regla 4 (Juan): respuesta al instante cuando un adjunto dispara el peso de Blor
    p_edict_each: float = 0.5      # regla 6 (aprobada): parte de los edictos son 'cada oponente sacrifica'
    # regla 7 PROPUESTA: barridas tipadas (destruir / destruir+art-ench / -X/-X / exiliar / exiliar todo / rebote / Rift)
    wipe_types: tuple = (("destroy", 0.41), ("destroy_ae", 0.14), ("minus", 0.15), ("exile", 0.075),
                         ("exile_ae", 0.075), ("bounce", 0.075), ("rift", 0.075))
    wipe_margin: float = 1.5
    # regla 8 PROPUESTA: odio masivo a artefactos/encantamientos (Vandalblast overload, Bane of Progress, Fracturing Gust,
    # Cleansing Nova, Tranquility, Back to Nature). Austere Command y Farewell ya estan en las barridas (regla 7).
    aem: float = 0.3               # por mazo de 99 (estimado: Vandalblast en 15% de mazos rojos en EDHREC, Bane 2,7%)
    aem_types: tuple = (("art", 0.55), ("both", 0.35), ("ench", 0.10))
    cnt_up: float = 0.75           # regla 9 PROPUESTA: el azul tiene mana arriba en tu turno (igual que Gandalf)
    cnt_blor: float = 0.75         # regla 9 (Juan): el azul responsable contrarresta a Blor al bajar (no siempre pasa)
    # regla 10 (Juan 15/11): relojes logisticos (como Gandalf) y tipo de victoria de cada rival
    mus: tuple = ()                # turno tipico de cada rival; vacio = mesa vieja
    spread: float = 0.9
    retry: float = 0.7
    win_types: tuple = (("combat", 0.66), ("dmg", 0.10), ("loss", 0.09), ("combo", 0.15))
    win_blue: tuple = ()           # reparto del jugador azul (Playgroup, comandantes azules)
    p_combat_us: float = 1.0       # SENSIBILIDAD (no aprobado): un intento de combate te mata a ti
    ceil_attach: bool = False      # TECHO: nada de los rivales puede quitar adjuntos (solo para medir)
    # 15/11 (Juan): piezas rivales que quitan antimaleficio (Shadowspear 3,6% de los mazos en EDHREC, Arcane Lighthouse 1,5%,
    # Glaring Spotlight...). Por mazo de 99; con una en mesa, la remocion de criaturas o de permanentes puede ir a Blor.
    hate: float = 0.06
    # ---- mesa "Mazmorra" (torneo B3 de La Mazmorra TCG, claude/mesa-mazmorra.md; 19/11) ----
    # todas detras de mz=True: las demas mesas no consumen azar extra
    mz: bool = False
    mz_turbo: tuple = (1, 0.85)    # regla 2: el turbo (turno tipico mas bajo) rearma en 1 turno y reintenta al 85%
    mz_rem_slows: float = 0.5      # regla 4: remocion entre rivales tumba el proximo intento del mas rapido
    mz_partial: float = 0.4        # regla 5: un intento sin frenar mata a UN solo jugador al azar
    mz_partial_us_w: float = 2.0   # regla 5 (Juan 19/11): si Blor ya pego fuerte (21+ de dano repartido), pesa el doble
    mz_edict_rival: float = 3 / 11 # regla 6: rival de edictos (Sephiroth) en la mesa
    mz_edict_p: float = 0.35       # desde T3, 35% por vuelta
    mz_strip_rival: float = 3 / 11 # regla 7: Tifa con Strip Mine en bucle (es el turbo)
    mz_strip_p: float = 0.5
    p_big: float = 0.0             # SENSIBILIDAD (Juan 15/11): bloqueador enorme desde el T6 (Darksteel Colossus 11/11 indestructible)


@dataclass
class Perm:
    name: str
    p: int = 0
    x: int = 0
    counters: int = 0
    sick: bool = True
    tapped: bool = False
    token: bool = False
    mana: int = 0


def P(n):
    return C.get(n, {})


# Fase 4: roles y pesos por carta en data/efectos.yaml (comunes o en el bloque "motor" de este mazo)
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", ".."))
from core import efectos as EF
import cards as _cards_mod
_CD = _cards_mod.C if isinstance(getattr(_cards_mod, "C", None), dict) else _cards_mod.CARDS
_NAMES = list(_CD)
AURA_FLAT = EF.field("power_bonus", [n for n in _NAMES if _CD[n]["t"] == "aura"])
EQUIP_FLAT = EF.field("power_bonus", [n for n in _NAMES if _CD[n]["t"] == "equip"])
CLAMP_AGGRO = False          # sensibilidad (22/11): clampear todo lo que se pueda
DOUBLE_STRIKE = set(EF.with_value("grants", "double_strike", _NAMES))
VIGILANCE_A = set(EF.with_value("grants", "vigilance", [n for n in _NAMES if _CD[n]["t"] == "aura"]))
VIGILANCE_E = set(EF.with_value("grants", "vigilance", [n for n in _NAMES if _CD[n]["t"] == "equip"]))
LIFELINK_E = set(EF.with_value("grants", "lifelink", [n for n in _NAMES if _CD[n]["t"] == "equip"]))
HASTE_E = set(EF.with_value("grants", "haste", [n for n in _NAMES if _CD[n]["t"] == "equip"]))
DRAW_ON_HIT_A = {n: v["draw"] for n, v in EF.field("on_hit", [n for n in _NAMES if _CD[n]["t"] == "aura"]).items()}
FOGS = set(EF.with_tag("fog", _NAMES))
DORK_NAMES = set(EF.with_tag("dork", _NAMES))
ELVES = set(EF.with_tag("elf", _NAMES))
ENCHANTRESS = set(EF.with_tag("enchantress", _NAMES))
FIGHT = {"Fight for the Throne", "Prizefight", "Ancient Animus", "Polliwallop", "Contest of Claws",
         "Prey Upon", "Rabid Bite", "Run Over"}   # necesitan a Blor


class Game:
    def __init__(self, deck, rng, mode="table", cfg=None, mull_policy="guide", log=False):
        self.rng = rng
        self.mode = mode
        self.cfg = cfg or TableCfg()
        self.logon = log
        self.library = list(deck)
        rng.shuffle(self.library)
        self.hand, self.gy, self.exiled = [], [], []
        self.lands = []            # dicts: name, aura (extra G), dep (counters), tapped_entry
        self.arts = []             # non-equipment artifacts on battlefield: dicts name, used
        self.cres = []             # other creatures (Perm)
        self.enchs = []            # global enchantments (names)
        self.equips = []           # dicts name, on (attached to Blor)
        self.auras = []            # auras on Blor
        self.blor = None           # Perm when on battlefield
        self.blor_zone = "cmd"
        self.tax = 0
        self.treas = 0
        self.poison = [0, 0, 0]
        self.cmd = [0, 0, 0]
        self.opp = [40, 40, 40]
        self.curse = None
        self.life = 40
        self.turn = 0
        self.on_play = rng.random() < 0.25
        self.won = self.lost = False
        self.win_turn = None
        self.blor_turn = None
        self.loss = None
        self.stats = dict(mulls=0, cast={}, kills=[], blor_casts=0, attach_lost=0, blor_left=0)
        self.counters_left = self.cfg.n_counters
        self.counter_up = None
        self._cnt_up = {}
        self.rival_next = [rng.randint(*c) for c in self.cfg.clocks]
        if self.cfg.mus:
            self.ready_t = [None, None, None]
            self.rival_next = [-1, -1, -1]
        self.wipe_turn = rng.randint(*self.cfg.wipe_window)
        self.wipe_done = False
        self.board_reset = [0, 0, 0]
        self.threat = {}
        self._our = True
        self.ring = 0               # The One Ring burden counters (-1: not on battlefield)
        self.ring_on = False
        self.ring_prot = False
        self.ancient = 0            # counters on Forgotten Ancient
        self.jitte = 0
        self.vault_used = False
        self.grim_used = False
        self.dryads = 0             # Forest Dryad tokens (Staff of Titania)
        self.extra_land = 0
        self.temp = 0               # Blor's temporary power this turn
        self.infect_turn = False
        self.deathtouch_ctr = False
        self.passage = False
        self.indomitable_turn = False
        self.W = 0                  # green mana in pool
        self.Cl = 0                 # colorless in pool
        self.creature_only = 0      # mana usable only for creature spells (Castle, Herd Heirloom)
        self.legend_only = 0        # Delighted Halfling's legendary-only mana
        self.reserve = 0
        self.uncounterable_blor = False
        self.cnt_names = {}
        self.phased = False
        self.hate_on = [False, False, False]
        self._cnt_up = {}
        self._precombat = True
        self.hunters = False
        self._untap_after = self._bear = self._ff = False
        self._buster = 0
        if self.cfg.bracket:          # solo consume azar con la mesa v2 (las mesas viejas siguen comparables)
            c = self.cfg
            self.rem = [[self.rem_type() for _ in range(7) if rng.random() < c.rem / 99] for _ in range(3)]
            self.wipe_stock = [[self.wipe_type() for _ in range(7) if rng.random() < c.wipes / 99] for _ in range(3)]
            self.aem_stock = [[self.pick(c.aem_types) for _ in range(7) if rng.random() < c.aem / 99] for _ in range(3)]
            self.stats["aem_drawn"] = sum(len(x) for x in self.aem_stock)
            self.blue = rng.sample(range(3), c.n_blue)
            self.cnt_stock = [sum(rng.random() < c.cnt / 99 for _ in range(7)) if i in self.blue else 0 for i in range(3)]
            self.stats["rem_drawn"] = sum(len(x) for x in self.rem)
            if c.mus:                    # regla 10: el tipo de victoria fija el reloj; el azul gana distinto (Playgroup)
                self.wtype = [self.pick_r(rng, c.win_blue if (i in self.blue and c.win_blue) else self.win_other())
                              for i in range(3)]
                avg = sum(p * self.MU_SHIFT[k] for k, p in c.win_types)   # el promedio de la mesa queda en mus
                self.mu = [m + self.MU_SHIFT[w] - avg for m, w in zip(c.mus, self.wtype)]
            self.stats["rem_drawn_edict"] = sum(x.count("edict") for x in self.rem)
            if c.mz:                     # Mazmorra: turbo, rival de edictos (regla 6) y de Strip Mine (regla 7)
                self.turbo = min(range(3), key=lambda i: self.mu[i])
                self.slowed = [False, False, False]
                self.mz_edictor = rng.randrange(3) if rng.random() < c.mz_edict_rival else None
                self.mz_strip = self.turbo if rng.random() < c.mz_strip_rival else None
                self.stats["mz_edict_table"] = self.mz_edictor is not None
                self.stats["mz_strip_table"] = self.mz_strip is not None
        self.mulligan(mull_policy)

    # ------------------------------------------------------------ utils
    def log(self, *a):
        if self.logon:
            print(f"[T{self.turn}{'' if self._our else 'r'}]", *a)

    def cast_stat(self, n):
        self.stats["cast"][n] = self.stats["cast"].get(n, 0) + 1

    def alive(self):
        return [i for i in range(3) if self.opp[i] > 0]

    def draw(self, n=1):
        for _ in range(int(n)):
            if self.library:
                self.hand.append(self.library.pop())

    def ench_on(self, n):
        return n in self.enchs

    def art_on(self, n):
        return any(a["name"] == n for a in self.arts)

    def cre_on(self, n):
        return any(c.name == n for c in self.cres)

    def equip_on_blor(self, n):
        return any(e["name"] == n and e["on"] for e in self.equips)

    def attached(self):
        return list(self.auras) + [e["name"] for e in self.equips if e["on"]]

    def forests(self):
        if any(l["name"] == "Yavimaya, Cradle of Growth" for l in self.lands):
            return len(self.lands) + self.dryads
        return sum(1 for l in self.lands if LANDS[l["name"]].get("forest")) + self.dryads

    def n_lands(self):
        return len(self.lands) + self.dryads

    def n_art_ench(self):
        return len(self.arts) + len(self.equips) + self.our_enchantments()

    def our_enchantments(self):
        n = len(self.enchs) + len(self.auras) + sum(1 for l in self.lands if l.get("aura"))
        n += sum(1 for c in self.cres if P(c.name).get("ench"))
        n += 1 if self.curse is not None else 0
        return n

    def check_win(self):
        for i in range(3):
            if self.opp[i] > 0 and (self.cmd[i] >= 21 or self.poison[i] >= 10):
                self.opp[i] = 0
        for i in range(3):
            if self.opp[i] <= 0 and i not in self.stats["kills"]:
                self.stats["kills"].append(i)
                self.stats[f"kill{len(self.stats['kills'])}"] = self.turn
        if not self.won and not self.lost and not self.alive():
            self.won = True
            self.win_turn = self.turn
            self.log("WIN")

    # ------------------------------------------------------------ Blor's stats
    def counters_mult(self, n):
        """+1/+1 counters actually put on Blor (Hardened Scales, Branching Evolution, The Earth Crystal, Kami)."""
        if n <= 0:
            return 0
        if self.ench_on("Hardened Scales"):
            n += 1
        if self.cre_on("Kami of Whispered Hopes"):
            n += 1
        if self.art_on("Ozolith, the Shattered Spire"):
            n += 1
        k = sum(1 for e in self.enchs if e == "Branching Evolution") + (1 if self.art_on("The Earth Crystal") else 0)
        k += 1 if self.ench_on("Innkeeper's Talent") and getattr(self, "inn_lvl", 1) >= 3 else 0
        return n * (2 ** k)

    def add_counters(self, n):
        if self.blor:
            m = self.counters_mult(n)
            self.blor.counters += m
            if m > 0 and self.ench_on("Terrasymbiosis") and getattr(self, "_terra_t", -1) != (self.turn, self._our):
                self._terra_t = (self.turn, self._our)            # una vez por turno; se roba hasta 4
                self.draw(min(m, 4)); self._st("terra_draw")

    def power(self, temp=True):
        b = self.blor
        if not b:
            return 0
        base = 10 if self.equip_on_blor("Belt of Giant Strength") else 3
        if "Super State" in self.auras:
            base = max(base, 9)
        if self.ench_on("Raised by Giants"):
            base = max(base, 10)
        if self.equip_on_blor("Aettir and Priwen"):
            base = max(base, self.life)
        p = base + b.counters
        n_att = len(self.attached())
        for a in self.auras:
            if a == "Blanchwood Armor":
                p += self.forests()
            elif a == "Crystalline Armor":
                p += self.n_lands()
            elif a == "Strong Back":
                p += 2 * n_att
            elif a == "Ancestral Mask":
                rival_ench = min(4, 1 + self.turn // 4) if self.mode == "table" else 0
                p += 2 * (self.our_enchantments() - 1 + rival_ench)
            else:
                p += AURA_FLAT.get(a, 0)
        for e in self.equips:
            if not e["on"]:
                continue
            n = e["name"]
            if n == "Blackblade Reforged":
                p += self.n_lands()
            elif n == "Staff of Titania":
                p += self.forests()
            elif n == "Thran Power Suit":
                p += n_att
            elif n == "Nettlecyst":
                p += self.n_art_ench()
            elif n in ("Cultist's Staff", "Spider-Suit"):
                p += 2
            elif n == "Neglected Heirloom":
                p += 1
            elif n == "Gavel of the Righteous":
                p += e.get("ctr", 0)
            elif n == "Strata Scythe":
                p += sum(1 for l in self.lands if l["name"] == "Forest")
            else:
                p += EQUIP_FLAT.get(n, 0)
        if temp:
            p += self.temp
        return max(0, p)

    def tough(self):
        return self.power(temp=False)  # close enough: same bonuses (Rancor/Hammer differences ignored)

    def double_strike(self):
        return any(self.equip_on_blor(n) for n in DOUBLE_STRIKE) or \
            any(e["name"] == "Gavel of the Righteous" and e["on"] and e.get("ctr", 0) >= 4 for e in self.equips)

    def _gavel_gain(self, p0, ds):
        c = max([e.get("ctr", 0) for e in self.equips if e["name"] == "Gavel of the Righteous"] or [0])
        return c + 1.5 + (0 if ds else (p0 + c) * (1 if c >= 3 else 0.4))

    def deathtouch(self):
        return self.equip_on_blor("Basilisk Collar") or self.deathtouch_ctr or self.cre_on("Ohran Frostfang") or \
            self.cre_on("Nightshade Peddler") or self.equip_on_blor("Quietus Spike") or self.equip_on_blor("Gorgon's Head") or \
            (self.equip_on_blor("Hunter's Blowgun") and self._our) or (self.art_on("Bow of Nylea") and self._our)

    def infect(self):
        return self.equip_on_blor("Grafted Exoskeleton") or self.infect_turn

    def vigilance(self):
        return any(a in VIGILANCE_A for a in self.auras) or any(self.equip_on_blor(n) for n in VIGILANCE_E) or \
            self.art_on("Akroma's Memorial")

    def haste(self):
        return any(self.equip_on_blor(n) for n in HASTE_E) or "Super State" in self.auras or "Instill Energy" in self.auras

    def lifelink(self):
        return any(self.equip_on_blor(n) for n in LIFELINK_E)

    # ------------------------------------------------------------ threat weights (mesa v2, regla 1, 14/11)
    # Escala de la mesa v2: 0,6 = motor que la mesa tiene que matar; 1,0 = bomba que gana sola.
    # Blor pesa segun el dano de UN golpe a un rival: poder, doble golpe, dano doble (Flail), combate extra (Genji),
    # Unnatural Growth, y lo que absorbe el bloqueador esperado (toque mortal = 1; sin bloqueo si no se puede bloquear).
    W_FLOOR = {"The Earth Crystal": 0.5, "Unnatural Growth": 0.5, "Genji Glove": 0.4, "Power Fist": 0.5}   # Power Fist: motor (Juan 15/11)
    W_CRE = {"Silent Arbiter": 0.4, "Tajuru Preserver": 0.3}
    W_DORK = 0.1

    def unblockable(self):
        return "Indomitable Might" in self.auras or self.equip_on_blor("Commander's Plate") or self.equip_on_blor("Whispersilk Cloak") \
            or self.equip_on_blor("Brotherhood Regalia")

    def blor_hit(self, power=None):
        """dano esperado de un golpe (todos los pasos y combates) a un rival, con el bloqueador esperado"""
        if not self.blor:
            return 0.0
        P_ = self.power(temp=False) if power is None else power
        if self.ench_on("Unnatural Growth"):
            P_ *= 2
        ds = self.double_strike()
        mult = 2 if self.equip_on_blor("Inquisitor's Flail") else 1
        if self.unblockable() or self.mode != "table":
            blk = 0
        else:
            blk = self.cfg.p_block * min(8, 3 + self.turn // 3)
        d = self.hit_damage(P_, blk, ds, mult)
        if self.equip_on_blor("Genji Glove"):
            d *= 2
        if self.infect():
            d *= 2.1                       # 10 de veneno equivalen a 21 de dano de comandante
        return d

    def w_blor(self):
        if not self.blor:
            return 0.0
        return min(1.2, 0.2 + self.blor_hit() / 25)

    def w_without(self, kind, obj):
        """peso de Blor si le quitan un adjunto (aura por nombre, equipo por dict)"""
        if kind == "aura":
            i = self.auras.index(obj); self.auras.pop(i)
            try:
                return self.w_blor()
            finally:
                self.auras.insert(i, obj)
        obj["on"] = False
        try:
            return self.w_blor()
        finally:
            obj["on"] = True

    def w_attach(self, kind, obj):
        name = obj if kind == "aura" else obj["name"]
        drop = max(0.0, self.w_blor() - self.w_without(kind, obj))
        return max(drop, self.W_FLOOR.get(name, 0.0))

    def w_attach_target(self):
        """Regla 1-B (Juan 14/11, rival frustrado): la remocion no puede tocar a Blor, asi que contra su mejor adjunto
        vale lo que pesa Blor (si eso es mas que lo que baja). Devuelve (peso, tipo, objeto) o None."""
        if self.cfg.ceil_attach:
            return None
        best = None
        for a in self.auras:
            d = self.w_attach("aura", a)
            if best is None or d > best[0]: best = (d, "aura", a)
        for e in self.equips:
            if e["on"] and e["name"] != "Darksteel Plate":      # indestructible: la remocion (de destruir) no la toca
                d = self.w_attach("equip", e)
                if best is None or d > best[0]: best = (d, "equip", e)
        if best is None:
            return None
        return (max(best[0], self.w_blor()), best[1], best[2])

    def w_seen(self, i):
        """peso con que el rival i ve a Blor (regla 2: B + D + archienemigo). None si Blor no esta en mesa"""
        if not self.blor:
            return None
        cfg = self.cfg
        lost = 1 - sum(max(x, 0) for x in self.opp) / 120
        return self.w_blor() + cfg.w_plan + cfg.w_arch * lost + cfg.w_cmd * min(1.0, self.cmd[i] / 21)

    def opp_best_value(self):
        """lo mas peligroso que tiene en mesa un rival tipico (misma escala; reconstruye desde cero tras una barrida)"""
        v0, dv, vmax = self.cfg.opp_curve
        t = self.turn - getattr(self, "opp_wiped_t", 0)
        return max(0.0, self.rng.gauss(min(v0 + dv * t, vmax), self.cfg.opp_noise))

    def w_perm(self, name):
        """peso de un permanente que no esta en Blor (artefactos, encantamientos globales, criaturas)"""
        if name in self.W_FLOOR:
            return self.W_FLOOR[name]
        if name in self.W_CRE:
            return self.W_CRE[name]
        if name == "Forgotten Ancient":
            return min(0.6, 0.2 + 0.05 * self.ancient)
        if name in DORK_NAMES or name.endswith("token"):
            return self.W_DORK
        return 0.2

    def threatening(self):
        if not self.blor:
            return False
        return self.power() >= 10 or max(self.cmd) >= 11 or max(self.poison) >= 5

    # ------------------------------------------------------------ mulligan
    RAMP1 = {"Llanowar Elves", "Elvish Mystic", "Fyndhorn Elves", "Birds of Paradise", "Delighted Halfling",
             "Sol Ring", "Arcane Signet", "Wild Growth", "Utopia Sprawl", "Rampant Growth", "Nature's Lore",
             "Three Visits", "Fanatic of Rhonas", "Mana Vault", "Grim Monolith", "Chrome Mox", "Mox Diamond",
             "Thought Vessel", "Herd Heirloom", "Drover of the Mighty", "Sakura-Tribe Elder", "Farseek",
             "Wolfwillow Haven", "Millikin", "Emerald Medallion", "Arbor Elf", "Sylvan Caryatid", "Paradise Druid",
             "Priest of Titania", "Lotus Cobra", "Sakura-Tribe Scout", "Exploration", "Wayfarer's Bauble",
             "Elvish Spirit Guide", "Lavaspur Boots", "Lotus Petal"}

    def hand_ok(self, policy):
        lands = sum(1 for c in self.hand if is_land(c) or c == "Khalni Ambush")
        if policy == "keep7":
            return True
        ramp = sum(1 for c in self.hand if c in self.RAMP1)
        if lands <= 1 or lands >= 6:
            return lands == 1 and ramp >= 2 and not self.on_play
        if lands == 2:
            return ramp >= 1
        return True

    def mulligan(self, policy):
        mulls = 0
        while True:
            self.library += self.hand
            self.hand = []
            self.rng.shuffle(self.library)
            self.draw(7)
            if self.hand_ok(policy) or mulls >= 3:
                break
            mulls += 1
        self.stats["mulls"] = mulls
        for _ in range(max(0, mulls - 1)):
            self.hand.sort(key=self.bottom_key)
            self.library.insert(0, self.hand.pop())

    def bottom_key(self, c):
        lands = sum(1 for x in self.hand if is_land(x))
        if is_land(c):
            return 100 if lands > 4 else -1
        if c in self.RAMP1:
            return 0
        g, w = C[c]["cost"]
        return g + w

    # ------------------------------------------------------------ lands & mana
    def play_land(self):
        if self.turn == 1 and "Leyline Axe" in self.hand:
            pass
        cand = [c for c in self.hand if is_land(c)]
        if "Talon Gates of Madara" in cand and (len(cand) > 1 or len(self.lands) >= 4):
            cand.remove("Talon Gates of Madara")          # se guarda en la mano para sacar a Blor de fase
        if not cand and "Khalni Ambush" in self.hand and len(self.lands) < 5:
            cand = ["Khalni Ambush"]
        if not cand:
            return False
        def score(l):
            d = LANDS[l]
            s = 0
            if d.get("tapped"):
                s += 3 if self.turn > 1 else -1
            if d["col"] == "C":
                s += 1
            if l == "Gaea's Cradle":
                s += 2
            if l == "Boseiju, Who Endures":
                s += 1
            if d["col"] == "fetch":
                s += 2 if self.turn > 1 else -1
            return s
        cand.sort(key=score)
        l = cand[0]
        self.hand.remove(l)
        d = LANDS[l]
        if d["col"] == "fetch":
            self.gy.append(l)
            if "Forest" in self.library:
                self.library.remove("Forest")
                self.rng.shuffle(self.library)
                self.put_land("Forest", tapped=True)
            return True
        self.put_land(l, tapped=d.get("tapped", False) or (l == "Khalni Ambush") or
                      (l == "Lair of the Hydra" and len(self.lands) >= 2))
        self.log("land", l)
        return True

    def put_land(self, name, tapped=False):
        rec = dict(name=name, aura=0, dep=2 if name == "Hickory Woodlot" else (3 if name == "Gemstone Mine" else 0),
                   tapped_entry=tapped)
        self.lands.append(rec)
        is_forest = LANDS[name].get("forest") or any(l["name"] == "Yavimaya, Cradle of Growth" for l in self.lands)
        if is_forest:
            if self.art_on("Necklace of Girion"):
                self.add_counters(1)
            if any(l["name"] == "Roiling Canopy" for l in self.lands) and self.forests() >= 6 and self.blor and self._our:
                self.temp += 3
        if self.cre_on("Evolution Sage"):
            self.proliferate()
        if name == "Disciple of Freyalise" and not tapped and self._our:
            self.life -= 3                         # Garden of Freyalise: 3 vidas para entrar enderezada
        if name == "Urza's Saga":
            rec["lore"] = 1
        if self.blor:
            nlf = sum(1 for q in self.cres if q.name == "Bristly Bill, Spine Sower") + \
                sum(1 for e in self.enchs if e in ("Beorn's Hospitality", "Ride the Shoopuf"))
            for _ in range(nlf):
                self.add_counters(1)
            for q in self.cres:
                if q.name == "Scythecat Cub":
                    k = (self.turn, self._our)
                    self._scy = (k, self._scy[1] + 1) if getattr(self, "_scy", (None, 0))[0] == k else (k, 1)
                    if self._scy[1] == 2:
                        self.add_counters(self.blor.counters)      # la segunda vez: duplica
                    else:
                        self.add_counters(1)
        for q in list(self.cres):
            if q.name == "Scute Swarm":
                self.make_token("Insect token")
        if self.cre_on("Tireless Provisioner"):
            self.treas += 1
        if self._our and getattr(self, "_pool_open", False):
            self.W += sum(1 for q in self.cres if q.name == "Lotus Cobra")
        if not tapped and self._our and getattr(self, "_pool_open", False):
            self.add_land_mana(rec)
        return rec

    def land_mana(self, rec):
        """(green, colorless) a land gives when tapped."""
        n = rec["name"]
        col = LANDS[n]["col"]
        g = c = 0
        if col == "G":
            g = 1
        elif col == "C":
            c = 1
        elif col == "CC":
            c = 2
        elif col == "GG":
            g = 2
        if n == "Gaea's Cradle":
            g = len(self.cres) + (1 if self.blor else 0)
        if n == "Temple of the False God" and len(self.lands) < 5:
            c = 0
        if any(l["name"] == "Yavimaya, Cradle of Growth" for l in self.lands) and col == "C":
            g, c = 1, 0
        g += rec["aura"]
        return g, c

    def add_land_mana(self, rec):
        g, c = self.land_mana(rec)
        if rec["name"] == "Ancient Tomb":
            self.life -= 2
        if rec["name"] == "Hickory Woodlot":
            rec["dep"] -= 1
            if rec["dep"] <= 0:
                self.lands.remove(rec); self.gy.append("Hickory Woodlot")
        if rec["name"] == "Gemstone Mine":
            rec["dep"] -= 1
            if rec["dep"] <= 0:
                self.lands.remove(rec); self.gy.append("Gemstone Mine")
        self.W += g
        self.Cl += c

    def compute_pool(self):
        self.W = self.Cl = 0
        self.creature_only = self.legend_only = 0
        self._pool_open = True
        for rec in list(self.lands):
            if rec.get("tapped_entry"):
                continue
            if rec["name"] == "Nykthos, Shrine to Nyx":
                dev = self.devotion()
                if dev >= 4:
                    self.W += dev - 2 - 1   # pay {2} from the rest of the pool (approximation)
                    continue
            self.add_land_mana(rec)
        for a in self.arts:
            n = a["name"]
            r = C[n].get("rock")
            if not r:
                continue
            if n == "Mana Vault" or n == "Grim Monolith":
                continue          # tapped on demand
            if n == "Herd Heirloom":
                self.creature_only += 1
                continue
            if r == "G":
                self.W += 1
            elif r == "C":
                self.Cl += 1
            elif r == "CC":
                self.Cl += 2
            elif r == "GG":
                self.W += 2
        for c in self.cres:
            if c.sick or c.tapped:
                continue
            n = c.name
            if n in DORK_NAMES:
                c.tapped = True
                if n == "Fanatic of Rhonas" and (self.power() >= 4 or any(q.p >= 4 for q in self.cres)):
                    self.W += 4
                elif n == "Sanctum Weaver":
                    self.W += self.our_enchantments()
                elif n == "Kami of Whispered Hopes":
                    self.W += c.p + c.counters
                elif n == "Millikin":
                    self.Cl += 1
                elif n == "Llanowar Tribe":
                    self.W += 3
                elif n == "Arbor Elf":
                    self.W += 1 + max([l["aura"] for l in self.lands if LANDS[l["name"]].get("forest")] or [0])
                elif n == "Priest of Titania":
                    self.W += sum(1 for q in self.cres if q.name in ELVES)
                elif n == "Karametra's Acolyte":
                    self.W += self.devotion()
                elif n == "Selvala, Heart of the Wilds":
                    self.W += max(0, self.greatest_power() - 1)
                elif n == "Somberwald Sage":
                    self.creature_only += 3
                elif n == "Delighted Halfling":
                    if self.blor_zone == "bf":
                        self.Cl += 1
                    else:
                        self.legend_only += 1
                else:
                    self.W += 1
            if n == "Bugenhagen, Wise Elder":
                c.tapped = True; self.W += 1
        if any(l["name"] == "Castle Garenbrig" for l in self.lands) and self.blor_zone != "bf" and len(self.lands) >= 4:
            self.creature_only += 2          # {2GG},{T}: six G for creature spells: net +2 for Blor
        self.W += 0

    def devotion(self):
        d = 2 if self.blor else 0
        for a in self.auras:
            d += C[a]["cost"][1]
        for e in self.enchs:
            d += C[e]["cost"][1]
        for c in self.cres:
            if not c.token:
                d += C[c.name]["cost"][1]
        for l in self.lands:
            if l["aura"]:
                d += 1
        return d

    def avail(self, creature=False, legend=False):
        return self.W + self.Cl + self.treas + (self.creature_only if creature else 0) + \
            (self.legend_only if legend else 0) + self.vault_mana()

    def vault_mana(self):
        m = 0
        if self.art_on("Mana Vault") and not self.vault_used:
            m += 3
        if self.art_on("Grim Monolith") and not self.grim_used:
            m += 3
        return m

    def cost_of(self, c):
        g, w = C[c]["cost"]
        if c == B:
            g += self.tax
        t = C[c]["t"]
        green = w > 0
        if green:
            g -= (1 if self.art_on("Emerald Medallion") else 0) + (1 if self.art_on("The Earth Crystal") else 0)
        if t == "aura" and "Strong Back" in self.auras and not C[c].get("rival_aura"):
            g -= 3
        if self.art_on("Helm of Awakening"):
            g -= 1                                       # simetrico: los rivales ganan 1 turno (roll_attempts)
        art = t in ("art", "equip") or C[c].get("artifact")
        if art:
            g -= self.cre_on("Foundry Inspector") + self.cre_on("Jhoira's Familiar") + self.art_on("Cloud Key")
        elif c == B:
            g -= self.cre_on("Jhoira's Familiar")
        anv = [a for a in self.arts if a["name"] == "Semblance Anvil" and a.get("imprint")]
        if anv:                           # comparte tipo con lo exiliado: artefacto (equipo) o encantamiento (aura)
            ench = t in ("aura", "ench") or C[c].get("ench")
            if (anv[0]["imprint"] == "art" and art) or (anv[0]["imprint"] == "aura" and ench):
                g -= 2
        if c == "Become Immense":
            g -= min(5, len(self.gy))
        if c == B and self.blor_zone == "hand" and getattr(self, "_beacon", False):
            g -= self.tax                                  # Command Beacon: desde la mano no paga impuesto
        if c == "Obscuring Haze" and self.blor:
            return 0, 0
        if c == "Force of Vigor" and not self._our and \
                sum(1 for x in self.hand if x not in (c, B) and not is_land(x) and C[x]["cost"][1] > 0) >= 1:
            return 0, 0                                    # exiliando otra carta verde (se descuenta al lanzarla)
        if c == "Excalibur, Sword of Eden":
            g -= sum(sum(C[a["name"]]["cost"]) for a in self.arts) + sum(sum(C[e["name"]]["cost"]) for e in self.equips) \
                + (5 if self.blor else 0)
        if c == "The Great Henge":
            g -= self.greatest_power()
        return max(0, g), w

    def can_pay(self, g, w, extra=0, creature=False, legend=False):
        green = self.W + self.treas + (self.creature_only if creature else 0) + (self.legend_only if legend else 0)
        return green >= w and self.avail(creature, legend) >= g + w + extra

    def pay(self, g, w, creature=False, legend=False):
        if not self.can_pay(g, w, creature=creature, legend=legend):
            return False
        need = w
        if legend:
            u = min(self.legend_only, need); self.legend_only -= u; need -= u
        if creature:
            u = min(self.creature_only, need); self.creature_only -= u; need -= u
        u = min(self.W, need); self.W -= u; need -= u
        u = min(self.treas, need); self.treas -= u; need -= u
        need = g
        if legend:
            u = min(self.legend_only, need); self.legend_only -= u; need -= u
        if creature:
            u = min(self.creature_only, need); self.creature_only -= u; need -= u
        u = min(self.Cl, need); self.Cl -= u; need -= u
        if need > 0:
            for n, flag in (("Mana Vault", "vault_used"), ("Grim Monolith", "grim_used")):
                if need > 0 and self.art_on(n) and not getattr(self, flag):
                    setattr(self, flag, True)
                    self.Cl += 3
                    u = min(self.Cl, need); self.Cl -= u; need -= u
        u = min(self.W, need); self.W -= u; need -= u
        u = min(self.treas, need); self.treas -= u; need -= u
        return need == 0

    # ------------------------------------------------------------ counters / proliferate
    def proliferate(self):
        if self.blor and self.blor.counters > 0:
            self.blor.counters += 1
        for i in self.alive():
            if self.poison[i] > 0:
                self.poison[i] += 1
        if self.jitte > 0:
            self.jitte += 1
        self.check_win()

    # ------------------------------------------------------------ casting
    def key_spell(self, c):
        return c == B or (sum(C[c]["cost"]) >= 5 and C[c]["t"] in ("aura", "equip", "cre", "sorc"))

    CNT_BY_CMC = M.COUNTER_BY_MV     # regla 9: hechizos que no son clave, segun su costo (Gandalf)
    CNT_HI = M.COUNTER_HI

    def flail_locks(self):
        return self.equip_on_blor("Conqueror's Flail") or any(e["name"] == "Conqueror's Flail" and e["on"] and e.get("cre")
                                                              for e in self.equips)

    def uncounterable(self, c):
        green = c == B or C[c]["cost"][1] > 0
        t = C[c]["t"]
        if green and self.cre_on("Allosaurus Shepherd"):
            return True
        if self.cre_on("Destiny Spinner") and (t in ("cre", "aura", "ench") or c == B or C[c].get("ench")):
            return True
        return c == B and self.uncounterable_blor

    def spell_threat(self, c):
        """regla 9: cuanto pesa para el azul lo que hace este hechizo al resolverse (misma escala que la remocion)"""
        t = C[c]["t"]
        if c == B:
            loose = [e for e in self.equips if not e["on"]]
            self.blor = Perm(name=B, p=3, x=3, sick=False)
            for x in loose: x["on"] = True
            try:
                return self.w_blor() + self.cfg.w_plan
            finally:
                for x in loose: x["on"] = False
                self.blor = None
        if c in self.W_FLOOR and t != "equip":
            base = self.W_FLOOR[c]
        else:
            base = 0.0
        if t == "aura" and self.blor:
            now = self.w_blor(); self.auras.append(c)
            try:
                return max(base, self.w_blor() - now)
            finally:
                self.auras.pop()
        if t == "equip" and self.blor:
            now = self.w_blor(); x = dict(name=c, on=True); self.equips.append(x)
            try:
                return max(self.W_FLOOR.get(c, 0.0), self.w_blor() - now)
            finally:
                self.equips.pop()
        if t == "cre":
            return self.w_perm(c)
        if t in ("art", "ench"):
            return max(base, self.w_perm(c))
        return base

    def lethal_need(self):
        """dano de un golpe que mata a algun rival vivo (vida o 21 de comandante)"""
        al = self.alive()
        return min(min(self.opp[i], 21 - self.cmd[i]) for i in al) if al else 99

    def projected(self, c):
        """(peso de Blor antes, despues, golpe antes, despues) si este hechizo resuelve; None si no toca a Blor"""
        t = C[c]["t"]
        if not self.blor or t not in ("aura", "equip", "ench"):
            return None
        w0, h0 = self.w_blor(), self.blor_hit()
        if t == "aura":
            self.auras.append(c); undo = self.auras.pop
        elif t == "equip":
            self.equips.append(dict(name=c, on=True)); undo = self.equips.pop
        else:
            self.enchs.append(c); undo = self.enchs.pop
        try:
            return w0, self.w_blor(), h0, self.blor_hit()
        finally:
            undo()

    def is_key(self, c):
        """regla 9 (Juan 15/11): clave = deja a Blor en 0,5+ con un salto real, lo vuelve letal de un golpe, o es un motor"""
        if c in self.W_FLOOR and self.W_FLOOR[c] >= 0.5:
            return True
        pr = self.projected(c)
        if pr:
            w0, w1, h0, h1 = pr
            need = self.lethal_need()
            if (w1 >= 0.5 and w1 - w0 >= 0.15) or (h1 >= need > h0):
                return True
        return self.spell_threat(c) >= self.REM_THR

    def countered_v2(self, c):
        """regla 9: el azul guarda counters; contrarresta lo que pesa >= 0,5 y el resto segun costo; guarda el ultimo"""
        if self.flail_locks() or self.uncounterable(c):
            return False
        for i in self.blue:
            if self.opp[i] <= 0 or self.cnt_stock[i] <= 0:
                continue
            if i not in self._cnt_up:
                self._cnt_up[i] = self.rng.random() < self.cfg.cnt_up
            if not self._cnt_up[i]:
                continue
            key = c == B or self.is_key(c)
            v = 0.8 if c == B else (self.REM_THR if key else 0.0)      # Blor: lo gasta aunque sea el ultimo
            p = self.cfg.cnt_blor if c == B else (1.0 if key else self.CNT_BY_CMC.get(sum(self.cost_of(c)), self.CNT_HI))
            if self.rng.random() >= p:
                continue
            if self.cnt_stock[i] == 1 and v < 0.8 and self.rng.random() < self.KEEP_LAST:
                self._st("cnt_kept")
                continue
            self.cnt_stock[i] -= 1
            self._cnt_up[i] = False                 # ya uso su mana
            if "Veil of Summer" in self.hand and self.can_pay(0, 1):
                self.pay(0, 1); self.hand.remove("Veil of Summer"); self.gy.append("Veil of Summer")
                self.cast_stat("Veil of Summer"); self._st("cnt_veil")
                return False
            self._st("cnt_us"); self._st("cnt_key" if key else "cnt_other")
            self.cnt_names[c] = self.cnt_names.get(c, 0) + 1
            if c == B:
                self._st("cnt_blor")
            self.log("COUNTERED", c)
            return True
        return False

    def countered(self, c):
        if self.cfg.bracket and self.mode == "table":
            return self.countered_v2(c)
        if self.mode != "table" or self.counters_left <= 0 or not self.key_spell(c):
            return False
        if c == B and (self.uncounterable_blor):
            return False
        if self.counter_up is None:
            self.counter_up = self.rng.random() < self.cfg.p_counter
        if self.counter_up:
            if "Veil of Summer" in self.hand and self.can_pay(0, 1):
                self.pay(0, 1); self.hand.remove("Veil of Summer"); self.gy.append("Veil of Summer")
                self.cast_stat("Veil of Summer")
                self.counters_left -= 1
                self.counter_up = False
                return False
            self.counters_left -= 1
            self.counter_up = False
            self.log("COUNTERED", c)
            return True
        return False

    def cast(self, c, free=False):
        if c == B:
            self.uncounterable_blor = (self.legend_only > 0 or any(l["name"] == "Cavern of Souls" for l in self.lands)
                                       or self.cre_on("Frenzied Baloth"))
        if not free:
            g, w = self.cost_of(c)
            cre = C[c]["t"] == "cre"
            leg = c == B
            if not self.pay(g, w, creature=cre, legend=leg):
                return False
        self.cast_stat(c)
        if c == B:
            self.stats["blor_casts"] += 1
            self._beacon = False
            if self.blor_zone == "hand":
                self.hand.remove(B)
            self.blor_turn = self.blor_turn or self.turn
            if self.countered(B):
                self.blor_zone = "cmd"; self.tax += 2
                return True
            self.blor = Perm(name=B, p=3, x=3, sick=True)
            self.blor_zone = "bf"
            self.log("cast Blor (tax", self.tax, ")")
            self.on_cast_green(c)
            self.creature_enters(self.blor)
            return True
        self.hand.remove(c)
        self.log("cast", c)
        if C[c]["cost"][1] > 0:
            self.on_cast_green(c)
        t = C[c]["t"]
        if t in ("aura", "ench") or (t == "cre" and C[c].get("ench")):
            self.on_cast_enchantment(c)
        if self.countered(c):
            self.gy.append(c)
            return True
        if t == "land":
            self.put_land(c)
        elif t == "cre":
            self.put_creature(c)
        elif t == "art":
            self.put_artifact(c)
        elif t == "equip":
            self.equips.append(dict(name=c, on=False))
            if C[c].get("germ"):
                self.make_token("Germ token", 0, 4 if c == "Batterskull" else 1)
                self.equips[-1]["germ"] = True
            if c == "The Aetherspark":
                self.equips[-1]["loy"] = 4
            if c in ("Lightning Greaves", "Mithril Coat", "Vibranium Strike Gauntlets", "The Aetherspark") and self.blor:
                self.attach_equip(self.equips[-1], free=True)
            elif self.blor and (c == "Hammer of Nazahn" or any(x["name"] == "Hammer of Nazahn" for x in self.equips)):
                self.attach_equip(self.equips[-1], free=True)      # Hammer of Nazahn: se equipa al entrar
        elif t == "aura":
            self.resolve_aura(c)
        elif t == "ench":
            self.resolve_ench(c)
        elif t == "pw":
            self.resolve_garruk()
        elif t in ("sorc", "inst"):
            self.resolve_spell(c)
        return True

    def on_cast_green(self, c):
        if self.art_on("Necklace of Girion") and self.blor:
            self.add_counters(1)
        if c != B and C[c].get("pump") or C[c]["t"] == "aura" and not C[c].get("rival_aura"):
            if self.ench_on("Season of Growth") and self.blor:
                self.draw(1)

    def on_cast_enchantment(self, c):
        for q in self.cres:
            if q.name in ("Verduran Enchantress", "Argothian Enchantress"):
                self.draw(1)
        if self.ench_on("Enchantress's Presence"):
            self.draw(1)

    def enchantment_enters(self):
        for q in self.cres:
            if q.name == "Eidolon of Blossoms":
                self.draw(1)
            if q.name == "Setessan Champion":
                q.counters += 1
                self.draw(1)

    def creature_enters(self, perm):
        if not perm.token and self.art_on("The Great Henge"):
            if perm is self.blor:
                self.add_counters(1)
            else:
                perm.counters += 1
            self.draw(1)
        if self.ench_on("Garruk's Uprising") and (perm.p + perm.counters >= 4):
            self.draw(1)
        if self.ench_on("Elemental Bond") and perm.p + perm.counters >= 3:
            self.draw(1)
        if self.ench_on("Guardian Project") and not perm.token:
            self.draw(1)

    def put_creature(self, c, free=False):
        d = C[c]
        perm = Perm(name=c, p=d.get("p", 0), x=d.get("x", 0), sick=True)
        self.cres.append(perm)
        if c == "Wood Elves" and "Forest" in self.library:
            self.library.remove("Forest"); self.put_land("Forest", tapped=False)
        if c == "Pollenbright Druid" and self.blor:
            self.add_counters(1)
        if c == "Studious First-Year":
            self.hand.append("Rampant Growth")           # copia preparada de Rampant Growth
        if c in ("Fertilid", "Elvish Rejuvenator", "Simulacrum Shaper", "Clifftop Lookout") and "Forest" in self.library:
            self.library.remove("Forest"); self.put_land("Forest", tapped=True)
        if c == "Satyr Grovedancer" and self.blor:
            self.add_counters(1)
        if c == "Vinelasher Adept" and self.blor:
            self.add_counters(3)
        if c == "Bloom Hulk" and self.blor and self.blor.counters:
            self.add_counters(1)
        if c == "Eternal Witness":
            best = self.best_gy_card()
            if best:
                self.gy.remove(best); self.hand.append(best)
        if c == "Pia, Aether Ascetic":
            if self.hand:
                worst = min(self.hand, key=self.card_value)
                if self.card_value(worst) < 4:
                    self.hand.remove(worst); self.gy.append(worst)
                    t = self.best_in_library(lambda n: C[n]["t"] in ("aura", "ench"))
                    if t:
                        self.library.remove(t); self.hand.append(t); self.rng.shuffle(self.library)
        if d.get("ench"):
            self.enchantment_enters()
        self.creature_enters(perm)
        return perm

    def make_token(self, name="Token", p=1, x=1):
        t = Perm(name=name, p=p, x=x, token=True, sick=True)
        self.cres.append(t)
        return t

    def put_artifact(self, c):
        a = dict(name=c, used=False)
        if c == "Chrome Mox":
            g = [x for x in self.hand if not is_land(x) and C[x]["t"] not in ("art", "equip") and C[x]["cost"][1] > 0]
            if not g:
                self.gy.append(c)
                return
            worst = min(g, key=self.card_value)
            self.hand.remove(worst); self.exiled.append(worst)
        if c == "Mox Diamond":
            ls = [x for x in self.hand if is_land(x)]
            if not ls:
                self.gy.append(c)
                return
            self.hand.remove(ls[0]); self.gy.append(ls[0])
        if c == "Semblance Anvil":       # imprint: el equipo mas debil de la mano (si no hay, el aura mas debil)
            for typ in ("equip", "aura"):
                xs = [x for x in self.hand if C[x]["t"] == typ]
                if len(xs) >= 2 or (xs and typ == "equip"):
                    w = min(xs, key=self.card_value)
                    self.hand.remove(w); self.exiled.append(w)
                    a["imprint"] = "art" if typ == "equip" else "aura"
                    break
        self.arts.append(a)
        r = C[c].get("rock")
        if r and c not in ("Mana Vault", "Grim Monolith"):
            if r == "G":
                if c == "Herd Heirloom":
                    self.creature_only += 1
                else:
                    self.W += 1
            elif r == "C":
                self.Cl += 1
            elif r == "CC":
                self.Cl += 2
            elif r == "GG":
                self.W += 2
        if c == "Lotus Petal":
            self.arts.remove(a); self.gy.append(c); self.treas += 1    # one-shot mana, kept until used
        if c == "Lotus Bloom":                                         # suspendida: llega en 3 mantenimientos
            self.arts.remove(a)
            self.bloom = getattr(self, "bloom", []) + [3]
        if c == "Esika's Chariot":
            self.make_token("Cat token", 2, 2); self.make_token("Cat token", 2, 2)
        if c == "The One Ring":
            self.ring_on = True
            self.ring = 0
            self.ring_prot = True

    def resolve_aura(self, c):
        if C[c].get("rival_aura"):
            # Song of the Dryads / Kenrith's Transformation on a rival threat
            if c == "Kenrith's Transformation":
                self.draw(1)
            self.gy.append(c)            # (the aura stays with the rival; we just stop tracking it)
            self.preempt_kind_with(c)
            return
        if not self.blor:
            self.hand.append(c)          # shouldn't happen: dev_ok checks
            return
        wb = self.seen_all() if self.cfg.bracket else None
        self.auras.append(c)
        self.enchantment_enters()
        if wb is not None:
            self.instant_response(wb)
        if c in ("Level Up", "Hydra's Growth", "Seismic Tutelage"):
            self.add_counters(1)
        for q in self.cres:
            if q.name == "Tanglespan Lookout":
                self.draw(1)
        if c == "Colossification":
            self.blor.tapped = True
        self.log("aura", c, "-> power", self.power())

    def resolve_ench(self, c):
        if c in ("Wild Growth", "Utopia Sprawl", "Wolfwillow Haven", "Overgrowth", "Fertile Ground"):
            tgt = [l for l in self.lands if LANDS[l["name"]].get("forest") or c != "Utopia Sprawl"]
            if tgt:
                tgt[0]["aura"] += C[c]["landaura"]
                # mana this turn: the enchanted land may already be tapped; give it next turn only
            self.enchantment_enters()
            return
        if c == "Curse of Predation":
            self.curse = self.focus_target()
            self.enchantment_enters()
            return
        self.enchs.append(c)
        if c == "World War Hulk":
            self.hulk_lore = 1                 # capitulo I (criatura roja/verde gratis): casi nunca aplica, se ignora
        self.enchantment_enters()
        if c == "Garruk's Uprising" and self.power() >= 4:
            self.draw(1)
        if c == "Court of Garenbrig":
            self.monarch = True
        if c == "Thickest in the Thicket" and self.blor:
            self.add_counters(self.power(temp=False))
        if c == "Innkeeper's Talent":
            self.inn_lvl = 1

    def resolve_garruk(self):
        # Garruk, Primal Hunter: -3 draw if Blor is big, else +1 beast
        if self.power() >= 5:
            self.draw(self.power())
            self.gy.append("Garruk, Primal Hunter")
        else:
            perm = Perm(name="Beast token", p=3, x=3, token=True)
            self.cres.append(perm)

    def resolve_spell(self, c):
        d = C[c]
        self.gy.append(c)
        if c == "Entish Restoration":
            worst = min(self.lands, key=lambda r: (r.get("aura", 0), LANDS[r["name"]].get("forest", False))) if self.lands else None
            if worst:
                self.lands.remove(worst); self.gy.append(worst["name"])
            for _ in range(3 if self.greatest_power() >= 4 else 2):
                if "Forest" in self.library:
                    self.library.remove("Forest"); self.put_land("Forest", tapped=True)
            self.rng.shuffle(self.library)
            return
        if c == "Traverse the Outlands":
            for _ in range(self.greatest_power()):
                if "Forest" in self.library:
                    self.library.remove("Forest"); self.put_land("Forest", tapped=True)
            self.rng.shuffle(self.library)
            return
        if c == "Soul's Majesty":
            self.draw(self.power(temp=False) if self.blor else self.greatest_power())
            return
        if c == "Season of Gathering":
            self.add_counters(1); self.add_counters(1)
            self.draw(self.greatest_power())
            return
        if c == "Regrowth":
            best = self.best_gy_card()
            if best:
                self.gy.remove(best); self.hand.append(best)
            return
        if c == "Wild Onslaught":
            if self.blor:
                kick = self.can_pay(4, 0)
                if kick:
                    self.pay(4, 0)
                self.add_counters(2 if kick else 1)
            return
        if c == "Fangs of Kalonia":
            if self.blor:
                self.add_counters(1); self.add_counters(self.blor.counters)
            return
        if c in ("Finale of Devastation", "Green Sun's Zenith"):   # X=3: la mejor criatura de 3 o menos de la biblioteca
            cs = [x for x in self.library if x in C and C[x]["t"] == "cre" and sum(C[x]["cost"]) <= 3]
            if cs:
                best = max(cs, key=lambda x: (x == "Bugenhagen, Wise Elder", C[x].get("mana", 0), sum(C[x]["cost"])))
                self.library.remove(best); self.put_creature(best); self.cast_stat("(Finale) " + best)
            return
        if d.get("fetch"):
            nbf, nhand, tapped = d["fetch"]
            for _ in range(nbf):
                if "Forest" in self.library:
                    self.library.remove("Forest"); self.put_land("Forest", tapped=tapped)
            for _ in range(nhand):
                if "Forest" in self.library:
                    self.library.remove("Forest"); self.hand.append("Forest")
            if c == "Far Wanderings" and len(self.gy) >= 7:
                for _ in range(2):
                    if "Forest" in self.library:
                        self.library.remove("Forest"); self.put_land("Forest", tapped=True)
            self.rng.shuffle(self.library)
            return
        if c == "Explore":
            self.draw(1); self.extra_land += 1
            return
        if d.get("draw"):
            self.draw(d["draw"])
            return
        if c == "Rishkar's Expertise":
            self.draw(self.greatest_power())
            free = [x for x in self.hand if not is_land(x) and sum(C[x]["cost"]) <= 5 and self.dev_ok(x)
                    and C[x]["t"] not in ("inst",)]
            if free:
                best = max(free, key=self.card_value)
                self.cast(best, free=True)
            return
        if c == "Adventurous Impulse":
            top = self.library[-3:]
            pick = [x for x in top if is_land(x) or C[x]["t"] == "cre"]
            if pick:
                self.library.remove(pick[-1]); self.hand.append(pick[-1])
            return
        if c == "Harmonize":
            self.draw(3)
            return
        if c == "Saproling Migration":
            n = 4 if self.can_pay(4, 0) and self.turn >= 6 else 2
            if n == 4:
                self.pay(4, 0)
            for _ in range(n):
                self.make_token("Saproling token")
            return
        if c == "Natural Order":
            return
        if d.get("sans"):
            self.preempt_kind_with(c)
            return

    def greatest_power(self):
        ps = [self.power()] + [q.p + q.counters for q in self.cres]
        return max(ps) if ps else 0

    def best_gy_card(self):
        cs = [c for c in self.gy if not is_land(c) and c in C]
        return max(cs, key=self.card_value) if cs else None

    def best_in_library(self, pred):
        cs = [c for c in self.library if c in C and not is_land(c) and pred(c)]
        return max(cs, key=self.card_value) if cs else None

    def card_value(self, c):
        """Rough value of a card for discards / tutors (higher is better)."""
        if c == B:
            return 100
        if is_land(c):
            return 3 if len(self.lands) < 6 else 0
        v = {"Colossification": 10, "Unnatural Growth": 9, "Genji Glove": 9, "Hydra's Growth": 9, "Strong Back": 8,
             "Blanchwood Armor": 8, "Blackblade Reforged": 8, "Fireshrieker": 8, "Inquisitor's Flail": 8,
             "Grafted Exoskeleton": 8, "Level Up": 7, "Bear Umbra": 7, "Ancestral Mask": 7, "Berserk": 6,
             "Snake Umbra": 6, "Lion Umbra": 6, "Staff of Titania": 7, "Crystalline Armor": 7, "Leyline Axe": 8,
             "Commander's Plate": 6, "World War Hulk": 6, "Heroic Intervention": 6, "Rishkar's Expertise": 6, "Pariah's Shield": 5}
        return v.get(c, 3 if C[c]["t"] in ("aura", "equip") else 2)

    # ------------------------------------------------------------ attachments
    def attach_equip(self, e, free=False):
        if not self.blor or e["on"]:
            return False
        if self.equip_on_blor("Whispersilk Cloak") and e["name"] != "Whispersilk Cloak":
            return False                    # shroud: no se puede equipar otra cosa a Blor
        if e["name"] == "Whispersilk Cloak" and not free and self.cloak_waits():
            return False
        n = e["name"]
        cost = self.equip_cost(n)
        sq = [q for q in self.cres if q.name == "Brass Squire" and not q.tapped and not q.sick]
        if not free and sq and cost > 0:
            sq[0].tapped = True
            free = True
            self.cast_stat("(act) Brass Squire")
        if not free:
            if not self.can_pay(cost, 0):
                return False
            self.pay(cost, 0)
        wb = self.seen_all() if self.cfg.bracket else None
        e["on"] = True
        if wb is not None and self.instant_response(wb) and e not in self.equips:
            return True
        if e.pop("germ", False):
            g = [q for q in self.cres if q.name == "Germ token"]
            if g:
                self.cres.remove(g[0])
        self.cast_stat("(equip) " + n)
        if n in HASTE_E:
            self.blor.sick = False
        self.log("equip", n, "-> power", self.power())
        return True

    def cloak_waits(self):
        """Whispersilk Cloak va al final: espera si hay auras en mano o equipos sueltos que poner antes"""
        return any(C[x]["t"] == "aura" and not C[x].get("rival_aura") for x in self.hand) or \
            any(not x["on"] and x["name"] != "Whispersilk Cloak" for x in self.equips)

    def equip_cost(self, n):
        d = C[n]
        cost = d.get("leq", d["eq"])
        if n == "Belt of Giant Strength":
            cost = max(0, 10 - self.power(temp=False))
        if "Strong Back" in self.auras:
            cost = max(0, cost - 3)
        return cost

    def attach_gain(self, n, kind):
        """Estimated value (in 'power points') of attaching n to Blor now."""
        p0 = self.power(temp=False)
        ds = self.double_strike()
        mult = (2 if ds else 1) * (2 if self.equip_on_blor("Inquisitor's Flail") else 1)
        if kind == "aura":
            gain = {"Blanchwood Armor": self.forests(), "Crystalline Armor": self.n_lands(),
                    "Strong Back": 2 * (len(self.attached()) + 1) + 2 * len(self.attached()) * 0,
                    "Ancestral Mask": 2 * (self.our_enchantments() + min(4, 1 + self.turn // 4)),
                    "Level Up": 1 + (self.blor.counters + 1) * 1, "Hydra's Growth": 1 + (self.blor.counters + 1),
                    "Keen Sense": 1.5, "Sixth Sense": 1.5, "Indomitable Might": 4,
                    "Lure": 4 if self.deathtouch() else -1}.get(n, AURA_FLAT.get(n, 0))
            gain += {"Super State": (0 if self.equip_on_blor("Belt of Giant Strength") else 6) + 0.8 * p0,
                     "Well Rested": 4, "Seismic Tutelage": 1 + (self.blor.counters + 1), "Predatory Hunger": 2,
                     "Forced Adaptation": 2, "Instill Energy": 3 if self.blor.sick else 1.5, "Mark of Sakiko": 1.5,
                     "One with Nature": 1.5, "Meltstrider's Resolve": 1, "Druid's Call": 0.3}.get(n, 0)
            if n in ("Snake Umbra",):
                gain += 1.5
            if n == "Bear Umbra":
                gain += 2
            if n == "Verdant Embrace":
                gain += 1
            if n == "Lion Umbra" and not self.attached() and self.blor.counters == 0:
                return -1     # needs a modified creature
            if n == "Lion Umbra":
                gain += 1.5   # vigilance
            if "Strong Back" in self.auras:
                gain += 2
            if self.equip_on_blor("Thran Power Suit"):
                gain += 1
            return gain * mult
        # equipment
        gain = {"Blackblade Reforged": self.n_lands(), "Staff of Titania": self.forests() + 1,
                "Thran Power Suit": len(self.attached()) + 1, "Fireshrieker": p0 * (1 if not ds else 0),
                "Genji Glove": p0 * (3 if not ds else 2), "Leyline Axe": 1 + (p0 + 1) * (0 if ds else 1),
                "Inquisitor's Flail": p0 * (2 if ds else 1), "Basilisk Collar": 2.5, "Power Fist": 3,
                "Whispersilk Cloak": 0.45 * p0, "Tanuki Transplanter": 1 + 0.3 * p0, "Quietus Spike": 2.5 + 0.3 * p0,
                "Gorgon's Head": 2, "Hunter's Blowgun": 2.5, "Conqueror's Flail": 1.5, "Hammer of Nazahn": 3, "Darksteel Plate": 0.3,
                "Bone Sabres": 5, "Gavel of the Righteous": self._gavel_gain(p0, ds), "Grafted Exoskeleton": 2 + p0 * 1.1, "Pariah's Shield": 3,
                "Swiftfoot Boots": 3 if self.blor.sick else 0.5, "Lightning Greaves": 3 if self.blor.sick else 0.5,
                "Mask of Memory": 2, "Umezawa's Jitte": 4, "Tarrian's Soulcleaver": 2,
                "Belt of Giant Strength": 7, "Trailblazer's Boots": 1.5, "Sword of Feast and Famine": 4,
                "Sword of Fire and Ice": 5, "Sword of Truth and Justice": 4, "Sword of Hearth and Home": 3.5,
                "Avarice Amulet": 4, "Assault Suit": 3, "Aettir and Priwen": max(0, self.life - 3 - (7 if self.equip_on_blor("Belt of Giant Strength") else 0)),
                "Strata Scythe": sum(1 for l in self.lands if l["name"] == "Forest"), "Sword of Vengeance": 3.5,
                "Haunted Cloak": 3 if self.blor.sick else 1.5, "Captain America's Shield": 1.5 + 0.3 * p0,
                "Brotherhood Regalia": 1 + 0.45 * p0, "Vibranium Strike Gauntlets": 5, "The Aetherspark": 3,
                "Excalibur, Sword of Eden": 11, "Batterskull": 7, "Flayer Husk": 1, "Nettlecyst": self.n_art_ench() + 1, "Short Bow": 2.5, "Long-Lost Lances": 3.5}.get(n, EQUIP_FLAT.get(n, 0))
        if n in ("Fireshrieker", "Genji Glove", "Leyline Axe", "Inquisitor's Flail", "Grafted Exoskeleton"):
            return gain
        if "Strong Back" in self.auras:
            gain += 2
        if self.equip_on_blor("Thran Power Suit"):
            gain += 1
        return gain * mult

    # ------------------------------------------------------------ development
    def dev_ok(self, c):
        d = C[c]
        t = d["t"]
        if c == "Blank":
            return False
        if d.get("ans") or d.get("prot") or d.get("fog"):
            return False
        if d.get("pump") and t == "inst":
            return False
        if c in ("Epic Fight", "Triumph of the Hordes", "Primal Might", "Hunter's Insight", "Worldly Tutor",
                 "Crop Rotation", "Natural Order", "Return of the Wildspeaker", "Harrow", "Sprout Swarm"):
            return False
        if d.get("sans"):
            return False                    # used by preempt
        if t == "aura":
            if not self.blor:
                return False
            if self.equip_on_blor("Whispersilk Cloak") and not C[c].get("rival_aura"):
                return False                # shroud: tus auras tampoco pueden apuntar a Blor
            if c == "Lion Umbra" and not self.attached() and self.blor.counters == 0:
                return False
            if c == "Colossification" and not self.vigilance() and not self.blor.sick and self._precombat:
                return False                # taps Blor: cast after combat
            return True
        if c == "Elvish Spirit Guide":
            return self.blor_zone == "bf"
        if c == "Rishkar's Expertise":
            return self.greatest_power() >= 5 or (len(self.hand) <= 2 and self.greatest_power() >= 3)
        if c in ("Exponential Growth", "Hunter's Prowess", "Emergent Growth", "Lifestream's Blessing", "Legolas's Quick Reflexes"):
            return False                    # antes del combate / al final del turno / no modelada
        if c == "Traverse the Outlands":
            return self.greatest_power() >= 4
        if c in ("Soul's Majesty", "Season of Gathering"):
            return self.greatest_power() >= 5 or (len(self.hand) <= 1 and self.greatest_power() >= 4)
        if c in ("Thickest in the Thicket", "Fangs of Kalonia", "Wild Onslaught"):
            return bool(self.blor)
        if c == "Garruk, Primal Hunter":
            return True
        if c == "Curse of Predation":
            return bool(self.alive())
        if c == "Mox Diamond":
            return sum(1 for x in self.hand if is_land(x)) >= 2
        if c == "Chrome Mox":
            return any(not is_land(x) and C[x]["t"] not in ("art", "equip") and C[x]["cost"][1] > 0
                       and self.card_value(x) <= 3 for x in self.hand)
        return True

    def dev_priority(self, c):
        d = C[c]
        t = d["t"]
        if c in ("Sol Ring", "Mana Vault", "Chrome Mox", "Mox Diamond", "Lotus Petal", "Lotus Bloom"):
            return 0
        if c in self.RAMP1 or d.get("rock") or d.get("landaura") or d.get("fetch") or \
                c in ("Entish Restoration", "Traverse the Outlands"):
            return 1
        if c == "Emerald Medallion" or c == "The Earth Crystal":
            return 2
        if c == "Unnatural Growth" and self.blor:
            return 2                       # Juan: apenas se pueda, con Blor en mesa
        if t == "aura":
            return 5
        if t == "equip":
            return 6
        if c in ("Unnatural Growth", "Hardened Scales", "Branching Evolution"):
            return 6
        if t == "cre":
            return 7
        if t == "ench" or t == "art" or t == "pw":
            return 8
        return 9

    def blor_cost(self):
        g, w = self.cost_of(B)
        return g, w

    def try_cast_blor(self, reserve=0):
        if self.blor_zone not in ("cmd", "hand"):
            return False
        g, w = self.blor_cost()
        if self.can_pay(g, w, extra=0, creature=True, legend=True):
            return self.cast(B)
        if "Elvish Spirit Guide" in self.hand:
            self.W += 1
            if self.can_pay(g, w, extra=0, creature=True, legend=True):
                self.hand.remove("Elvish Spirit Guide"); self.exiled.append("Elvish Spirit Guide")
                self.cast_stat("(exile) Elvish Spirit Guide")
                return self.cast(B)
            self.W -= 1
        return False

    def develop(self, reserve=0, precombat=True):
        self._precombat = precombat
        guard = 0
        while guard < 60 and not self.won:
            guard += 1
            # 1) cheap ramp first if it doesn't stop Blor this turn
            ramp = sorted([c for c in set(self.hand) if not is_land(c) and self.dev_priority(c) <= 2 and self.dev_ok(c)],
                          key=lambda c: (self.dev_priority(c), sum(self.cost_of(c))))
            done = False
            if self.blor_zone in ("cmd", "hand"):
                g, w = self.blor_cost()
                if self.can_pay(g, w, creature=True, legend=True):
                    # free / net-positive ramp first (Sol Ring, rocks that tap right away), then Blor
                    for c in ramp:
                        cg, cw = self.cost_of(c)
                        if cg + cw == 0 or c in ("Sol Ring",):
                            if self.cast(c):
                                done = True
                                break
                    if done:
                        continue
                    if self.try_cast_blor():
                        continue
            for c in ramp:
                cg, cw = self.cost_of(c)
                if self.can_pay(cg, cw, extra=reserve, creature=C[c]["t"] == "cre"):
                    if self.cast(c):
                        done = True
                        break
            if done:
                continue
            if self.blor_zone in ("cmd", "hand") and self.try_cast_blor():
                continue
            # 2) attachments: best gain per mana
            best = None
            if self.blor:
                opts = []
                for c in set(self.hand):
                    if C[c]["t"] == "aura" and not C[c].get("rival_aura") and self.dev_ok(c):
                        cg, cw = self.cost_of(c)
                        if self.can_pay(cg, cw, extra=reserve):
                            gain = self.attach_gain(c, "aura")
                            if gain > 0:
                                opts.append((gain / max(1, cg + cw), "cast", c))
                    if C[c]["t"] == "equip":
                        cg, cw = self.cost_of(c)
                        if self.can_pay(cg, cw, extra=reserve):
                            gain = self.attach_gain(c, "equip")
                            eq = self.equip_cost(c) if c != "Lightning Greaves" else 0
                            opts.append((gain / max(1, cg + cw + eq) + 0.01, "cast", c))
                squire = any(q.name == "Brass Squire" and not q.tapped and not q.sick for q in self.cres)
                for e in self.equips:
                    if not e["on"]:
                        cost = 0 if squire else self.equip_cost(e["name"])
                        if self.can_pay(cost, 0, extra=reserve):
                            if e["name"] in ("Swiftfoot Boots", "Lightning Greaves") and not self.blor.sick and \
                                    any(x["on"] for x in self.equips if x["name"] in HASTE_E):
                                continue
                            if self.equip_on_blor("Whispersilk Cloak") or \
                                    (e["name"] == "Whispersilk Cloak" and self.cloak_waits()):
                                continue
                            gain = self.attach_gain(e["name"], "equip")
                            if gain > 0:
                                opts.append((gain / max(1, cost) + 0.5, "equip", e))
                if opts:
                    opts.sort(key=lambda o: -o[0])
                    best = opts[0]
            if best:
                if best[1] == "cast":
                    self.cast(best[2])
                else:
                    self.attach_equip(best[2])
                continue
            # 3) the rest
            rest = sorted([c for c in set(self.hand) if not is_land(c) and self.dev_ok(c) and
                           C[c]["t"] not in ("aura",) and self.dev_priority(c) > 2],
                          key=lambda c: (self.dev_priority(c), -sum(self.cost_of(c))))
            for c in rest:
                if C[c]["t"] == "equip" and self.blor is None:
                    pass
                cg, cw = self.cost_of(c)
                if self.can_pay(cg, cw, extra=reserve, creature=C[c]["t"] == "cre"):
                    if self.cast(c):
                        done = True
                        break
            if done:
                continue
            if self.use_utilities(reserve):
                continue
            break

    def use_utilities(self, reserve):
        if self.utilities_edhrec(reserve):
            return True
        # Skullclamp (22/11): equipar {1} a una ficha o dork de 1 de resistencia -> muere -> roba 2.
        # Se deja siempre al menos otra criatura (fodder contra edictos) salvo que la mano este vacia.
        if any(e["name"] == "Skullclamp" for e in self.equips) and len(self.library) > 8 \
                and self.can_pay(1, 0, extra=reserve):
            fod = [q for q in self.cres if q.x <= 1 and q.name not in ("Toski, Bearer of Secrets",)
                   and (q.token or CLAMP_AGGRO or getattr(self, "_clamp_t", -1) != self.turn)]
            if fod and (CLAMP_AGGRO or len(self.cres) >= 2 or len(self.hand) <= 1):
                q = min(fod, key=lambda q: (not q.token, q.name in ("Birds of Paradise", "Delighted Halfling")))
                self.pay(1, 0)
                if not q.token:
                    self._clamp_t = self.turn          # como mucho un dork por turno
                self.cres.remove(q)
                if not q.token:
                    self.gy.append(q.name)
                for e in self.equips:
                    if e["name"] == "Skullclamp":
                        e["on"] = False
                self.draw(2)
                self.cast_stat("(act) Skullclamp")
                return True
        # Crystal Chimes: {3}, T, sacrificar: vuelven a la mano los encantamientos del cementerio (con 2+ que valgan)
        ench_gy = [x for x in self.gy if x in C and (C[x]["t"] in ("aura", "ench") or C[x].get("ench"))]
        if self.art_on("Crystal Chimes") and len(ench_gy) >= 2 and self.can_pay(3, 0, extra=reserve):
            self.pay(3, 0)
            ch = next(a for a in self.arts if a["name"] == "Crystal Chimes")
            self.arts.remove(ch); self.gy.append("Crystal Chimes")
            for x in ench_gy:
                self.gy.remove(x); self.hand.append(x)
            self.cast_stat("(act) Crystal Chimes")
        # The Earth Crystal: {4}{G}{G}, {T}: dos contadores +1/+1 en Blor (se duplican con su propia habilidad)
        if self.blor and self.art_on("The Earth Crystal") and not getattr(self, "_crystal", False) \
                and self.can_pay(4, 2, extra=reserve):
            self._crystal = True
            self.pay(4, 2)
            self.add_counters(2)
            self.cast_stat("(act) The Earth Crystal")
            return True
        if self.ench_on("Exploration") and not getattr(self, "_explo", False):
            self._explo = True
            if self.play_land():
                return True
        for q in self.cres:
            if q.name == "Sakura-Tribe Scout" and not q.tapped and not q.sick and any(is_land(c) for c in self.hand):
                q.tapped = True
                self.play_land()
                return True
        for a in list(self.arts):
            if a["name"] == "Wayfarer's Bauble" and self.can_pay(2, 0, extra=reserve) and "Forest" in self.library:
                self.pay(2, 0); self.arts.remove(a); self.gy.append(a["name"])
                self.library.remove("Forest"); self.put_land("Forest", tapped=True)
                return True
        if "Harrow" in self.hand and self.can_pay(2, 1, extra=reserve) and self.library.count("Forest") >= 2:
            fs = [l for l in self.lands if l["name"] == "Forest"]
            if fs:
                self.pay(2, 1); self.hand.remove("Harrow"); self.gy.append("Harrow"); self.cast_stat("Harrow")
                self.lands.remove(fs[0])
                for _ in range(2):
                    self.library.remove("Forest"); self.put_land("Forest", tapped=False)
                return True
        # The One Ring
        if self.ring_on and not getattr(self, "_ring_tapped", False) and self.life > 14 + 2 * (self.ring + 1):
            self._ring_tapped = True
            self.ring += 1
            self.draw(self.ring)
            self.cast_stat("(act) The One Ring")
            return True
        # Sakura-Tribe Elder: sac for a land (keep as edict fodder until Blor is out and we are on 4+ lands)
        for q in list(self.cres):
            if q.name == "Sakura-Tribe Elder" and (len(self.lands) < 5) and "Forest" in self.library:
                self.cres.remove(q); self.gy.append(q.name)
                self.library.remove("Forest"); self.put_land("Forest", tapped=True)
                return True
        # Myriad Landscape
        for rec in list(self.lands):
            if rec["name"] == "Myriad Landscape" and not rec.get("tapped_entry") and self.can_pay(2, 0, extra=reserve + 1):
                self.pay(2, 0)
                self.lands.remove(rec); self.gy.append("Myriad Landscape")
                for _ in range(2):
                    if "Forest" in self.library:
                        self.library.remove("Forest"); self.put_land("Forest", tapped=True)
                return True
        return False

    # ------------------------------------------------------------ candidatas de EDHREC (24/11)
    def begin_combat_counters(self):
        """Inicio del combate en tu turno: Ouroboroid, Innkeeper's Talent, The Aetherspark, Okina."""
        if not self.blor:
            return
        for q in list(self.cres):
            if q.name == "Ouroboroid":
                x = q.p + q.counters
                self.add_counters(x)
                q.counters += self.counters_mult(x)
        if self.ench_on("Innkeeper's Talent"):
            self.add_counters(1)
        for e in self.equips:
            if e["name"] == "The Aetherspark" and not getattr(self, "_spark_t", None) == self.turn:
                self._spark_t = self.turn                         # una activacion por turno (velocidad de conjuro)
                if e.get("loy", 4) >= 5 and len(self.library) > 8 and e["on"]:
                    e["loy"] -= 5; self.draw(2); self._st("spark_draw")
                else:
                    e["loy"] = e.get("loy", 4) + 1
                    if not e["on"]:
                        self.attach_equip(e, free=True)
                    self.add_counters(1)
        if any(l["name"] == "Okina, Temple to the Grandfathers" and not l.get("tapped_entry") for l in self.lands) \
                and self.can_pay(0, 1, extra=self.reserve + 1):
            self.pay(0, 1); self.temp += 1                      # (aproximacion: no se descuenta el verde de la propia Okina)

    def well_rested(self):
        if "Well Rested" in self.auras and getattr(self, "_rested_t", None) != (self.turn, self._our):
            self._rested_t = (self.turn, self._our)
            self.add_counters(2); self.life += 2; self.draw(1); self._st("rested")

    def urza_saga(self):
        for rec in list(self.lands):
            if rec["name"] == "Urza's Saga" and rec.get("lore", 1) >= 3:
                self.lands.remove(rec); self.gy.append("Urza's Saga")
                cs = [x for x in self.library if x in C and C[x]["t"] in ("art", "equip") and sum(C[x]["cost"]) <= 1
                      and C[x]["cost"][1] == 0 and x != "Lotus Bloom"]          # Lotus Bloom no tiene coste de mana
                if cs:
                    best = max(cs, key=lambda x: (x in ("Sol Ring", "Mana Vault"), x == "Lotus Petal", self.card_value(x)))
                    self.library.remove(best); self.rng.shuffle(self.library)
                    self.cast_stat("(Urza's Saga) " + best)
                    if C[best]["t"] == "equip":
                        self.equips.append(dict(name=best, on=False))
                    else:
                        self.put_artifact(best)

    def answer_extra(self, c, paid):
        """Lo que hace una respuesta ademas de parar la amenaza."""
        if c in ("Fight for the Throne", "Ancient Animus") and self.blor:
            self.add_counters(1)
        if c == "Prizefight":
            self.treas += 1
        if c == "Force of Vigor" and paid == 0:
            g = [x for x in self.hand if x != B and not is_land(x) and C[x]["cost"][1] > 0]
            if g:
                w = min(g, key=self.card_value)
                self.hand.remove(w); self.exiled.append(w)

    def utilities_edhrec(self, reserve):
        """Activaciones de las candidatas de EDHREC; True si hizo algo."""
        if self.blor and self.blor.counters >= 3 and self.cre_on("Bristly Bill, Spine Sower") and \
                self.can_pay(3, 2, extra=reserve) and self._precombat:
            self.pay(3, 2); self.add_counters(self.blor.counters); self.cast_stat("(act) Bristly Bill")
            return True
        for a in list(self.arts):
            if a["name"] == "Implement of Ferocity" and self.blor and self._precombat and self.can_pay(0, 1, extra=reserve):
                self.pay(0, 1); self.arts.remove(a); self.gy.append("Implement of Ferocity")
                self.add_counters(1); self.draw(1); self.cast_stat("(act) Implement of Ferocity")
                return True
        if self.ench_on("Innkeeper's Talent"):
            lvl = getattr(self, "inn_lvl", 1)
            if lvl == 1 and self.can_pay(0, 1, extra=reserve):
                self.pay(0, 1); self.inn_lvl = 2; return True
            if lvl == 2 and self.can_pay(3, 1, extra=reserve):
                self.pay(3, 1); self.inn_lvl = 3; self.cast_stat("(act) Innkeeper's Talent 3"); return True
        for a in self.arts:
            if a["name"] == "Ozolith, the Shattered Spire" and self.blor and getattr(self, "_ozo_t", -1) != self.turn \
                    and self.can_pay(1, 1, extra=reserve):
                self._ozo_t = self.turn
                self.pay(1, 1); self.add_counters(1); return True
        if self.blor_zone == "cmd" and self.tax >= 2:
            for rec in list(self.lands):
                if rec["name"] == "Command Beacon":
                    self.lands.remove(rec); self.gy.append("Command Beacon")
                    self.blor_zone = "hand"; self.hand.append(B); self._beacon = True
                    self.cast_stat("(act) Command Beacon")
                    return True
        for rec in list(self.lands):
            if rec["name"] == "Urza's Cave" and len(self.lands) < 8 and self.can_pay(3, 0, extra=reserve + 1) \
                    and "Forest" in self.library:
                self.pay(3, 0); self.lands.remove(rec); self.gy.append("Urza's Cave")
                self.library.remove("Forest"); self.put_land("Forest", tapped=True); return True
            if rec["name"] == "Blighted Woodland" and len(self.lands) < 9 and self.can_pay(3, 1, extra=reserve + 1):
                self.pay(3, 1); self.lands.remove(rec); self.gy.append("Blighted Woodland")
                for _ in range(2):
                    if "Forest" in self.library:
                        self.library.remove("Forest"); self.put_land("Forest", tapped=True)
                return True
        return False

    def end_step_edhrec(self, reserve):
        if "Lifestream's Blessing" in self.hand and self.greatest_power() >= 5 and self.can_pay(4, 2, extra=reserve):
            self.pay(4, 2); self.hand.remove("Lifestream's Blessing"); self.gy.append("Lifestream's Blessing")
            self.cast_stat("Lifestream's Blessing"); self.draw(self.greatest_power())
        if any(l["name"] == "Bonders' Enclave" for l in self.lands) and self.greatest_power() >= 4 \
                and self.can_pay(3, 0, extra=reserve):
            self.pay(3, 0); self.draw(1); self.cast_stat("(act) Bonders' Enclave")
        if self.art_on("Bow of Nylea") and self.blor and self.can_pay(1, 1, extra=reserve):
            self.pay(1, 1); self.add_counters(1)
        if getattr(self, "monarch", False) and self.ench_on("Court of Garenbrig"):
            self.draw(1); self._st("monarch_draw")
        if self.ench_on("Thickest in the Thicket") and self.blor and \
                self.power(temp=False) >= min(8, 3 + self.turn // 3):
            self.draw(2); self._st("thickest_draw")

    def end_step_draws(self, reserve):
        self.end_step_edhrec(reserve)
        if "Return of the Wildspeaker" in self.hand and self.greatest_power() >= 5 and self.can_pay(4, 1, extra=reserve):
            self.pay(4, 1); self.hand.remove("Return of the Wildspeaker"); self.gy.append("Return of the Wildspeaker")
            self.cast_stat("Return of the Wildspeaker (draw)")
            self.draw(self.greatest_power())
        if any(l["name"] == "War Room" for l in self.lands) and self.can_pay(4, 0, extra=reserve) and self.life > 15:
            self.pay(4, 0); self.life -= 1; self.draw(1); self.cast_stat("(act) War Room")
        if self.art_on("Expedition Map") and "Talon Gates of Madara" in self.library and self.can_pay(2, 0, extra=reserve):
            self.pay(2, 0)
            m = next(a for a in self.arts if a["name"] == "Expedition Map")
            self.arts.remove(m); self.gy.append("Expedition Map")
            self.library.remove("Talon Gates of Madara"); self.hand.append("Talon Gates of Madara")
            self.rng.shuffle(self.library); self.cast_stat("(act) Expedition Map")

    # ------------------------------------------------------------ combat
    def focus_target(self):
        al = self.alive()
        if not al:
            return None
        def need(i):
            if self.infect() or self.cre_on("Fynn, the Fangbearer"):
                return min(21 - self.cmd[i], (10 - self.poison[i]) * 2.1, self.opp[i])
            return min(21 - self.cmd[i], self.opp[i])
        if self.cfg.focus == "threat":
            return min(al, key=lambda i: (self.rival_next[i], need(i)))
        return min(al, key=lambda i: (need(i), self.rival_next[i]))

    def blocker(self, i, lethal):
        """Toughness of the rival blocker, 0 if no block."""
        self._nblock = 1
        self._lure = None
        if self.mode != "table" or self.turn < 3:
            return 0
        cfg = self.cfg
        if self.indomitable_turn or "Indomitable Might" in self.auras or self.passage or self.equip_on_blor("Whispersilk Cloak") \
                or (self.art_on("Akroma's Memorial") and self.rng.random() < 0.8) \
                or ("Super State" in self.auras and self.rng.random() < 0.8) \
                or self.equip_on_blor("Brotherhood Regalia"):     # vuela: casi nadie lo bloquea
            return 0
        if self.equip_on_blor("Captain America's Shield") and self.rng.random() < 0.7:
            return 0                                              # gira al bloqueador probable al atacar
        if self.equip_on_blor("Trailblazer's Boots") and self.rng.random() < cfg.p_nonbasic:
            return 0
        if self.rng.random() > (0.9 if lethal else cfg.p_block):
            return 0
        if self.equip_on_blor("Commander's Plate") and self.rng.random() > cfg.p_green_blocker:
            return 0
        if self.board_reset[i] >= self.turn - 1:
            return 0
        if "Lure" in self.auras:                  # todas las criaturas que pueden bloquear lo hacen
            n = min(4, 1 + self.turn // 3)
            self._nblock = n
            self._lure = (i, n)
            return sum(min(8, 2 + self.turn // 3 + self.rng.randint(0, 2)) for _ in range(n))
        if cfg.p_big and self.turn >= 6 and self.rng.random() < cfg.p_big:
            self._big = True
            return 11 + self.rng.randint(0, 2)     # indestructible: el toque mortal no lo mata, pero absorbe 1
        return min(8, 2 + self.turn // 3 + self.rng.randint(0, 2))

    def step_damage(self, P_, block):
        """(damage to player, blocker toughness left) for one combat damage step."""
        if block <= 0:
            return P_, 0
        absorb = getattr(self, "_nblock", 1) if self.deathtouch() else block
        if P_ >= absorb:
            return P_ - absorb, 0
        return 0, block - P_

    def hit_damage(self, P_, block, ds, mult):
        """Total damage to the player for one combat (no pump decisions)."""
        tot = 0
        if ds:
            d, block = self.step_damage(P_, block)
            tot += d * mult
            d2, _ = self.step_damage(P_, block)
            tot += d2 * mult
        else:
            d, _ = self.step_damage(P_, block)
            tot += d * mult
        return tot

    def pumps_in_hand(self):
        return [c for c in self.hand if C[c].get("pump") and C[c]["t"] == "inst"]

    def pump_effect(self, c, P_):
        """(add, double) for a trick given current power."""
        if c in ("Berserk", "Tifa's Limit Break"):
            return 0, True
        if c == "Invigorating Surge":
            m = self.counters_mult(1)
            return m + self.counters_mult(self.blor.counters + m) if self.blor else 0, False
        return {"Become Immense": 6, "Primal Bellow": self.forests(), "Giant Growth": 3, "Invigorate": 4,
                "Might of Old Krosa": 2, "Gift of the Viper": self.counters_mult(1), "Tyvar's Stand": 0,
                "Overprotect": 3, "Vines of Vastwood": 4, "Blossoming Defense": 2,
                "Snakeskin Veil": self.counters_mult(1), "Stony Strength": self.counters_mult(1),
                "Return of the Wildspeaker": 3, "Inscription of Abundance": self.counters_mult(2), "Tower Above": 4, "Bestow Greatness": 4, "Grow Extra Arms": 4, "Mammoth Growth": 4, "Flourishing Strike": 3, "Efflorescence": self.counters_mult(2)}.get(c, 0), False

    def pump_cost(self, c):
        if c == "Invigorate" and self.forests() > 0:
            return 0, 0
        if c == "Vines of Vastwood":
            return 0, 2
        return self.cost_of(c)

    def plan_pumps(self, P_, block, ds, mult, need, budget):
        """Cheapest set of tricks that reaches `need` damage; Tyvar's Stand takes the leftover mana."""
        ps = self.pumps_in_hand()
        if not ps:
            return None
        ps = ps[:7]
        best = None
        for k in range(1, len(ps) + 1):
            for combo in combinations(ps, k):
                cost = sum(sum(self.pump_cost(c)) for c in combo)
                if cost > budget:
                    continue
                add, dbl = 0, False
                for c in combo:
                    a, d = self.pump_effect(c, P_)
                    add += a
                    dbl = dbl or d
                if "Tyvar's Stand" in combo:
                    add += max(0, budget - cost)
                newP = P_ + add
                if dbl:
                    newP *= 2
                dmg = self.hit_damage(newP, block, ds, mult)
                if dmg >= need and (best is None or cost < best[0]):
                    best = (cost, combo, newP)
            if best:
                break
        return best

    def apply_pumps(self, combo, budget):
        P_ = self.power()
        spent = 0
        order = sorted(combo, key=lambda c: c in ("Berserk", "Tifa's Limit Break"))
        for c in order:
            g, w = self.pump_cost(c)
            if c == "Tyvar's Stand":
                x = max(0, budget - spent - sum(sum(self.pump_cost(o)) for o in order if o != c))
                if not self.pay(x, 1):
                    continue
                self.temp += x
            else:
                if not self.pay(g, w):
                    continue
                if c in ("Berserk", "Tifa's Limit Break"):
                    self.temp += self.power()
                elif c == "Invigorating Surge":
                    self.add_counters(1); self.add_counters(self.blor.counters)
                elif c in ("Gift of the Viper", "Snakeskin Veil", "Stony Strength"):
                    self.add_counters(1)
                    if c == "Gift of the Viper":
                        self.deathtouch_ctr = True
                    if c in ("Gift of the Viper", "Stony Strength"):
                        self._untap_after = True
                elif c == "Inscription of Abundance":
                    self.add_counters(2)
                else:
                    a, _ = self.pump_effect(c, P_)
                    self.temp += a
            spent += g + w
            self.hand.remove(c)
            self.gy.append(c)
            self.cast_stat(c)
            self.on_cast_green(c)

    def precombat_sorceries(self, tgt):
        """Epic Fight (double), Triumph of the Hordes (infect), Primal Might (X) and Hunter's Insight before attacking."""
        if not self.blor:
            return
        P_ = self.power()
        need = self.need(tgt)
        ds = self.double_strike()
        mult = 2 if self.equip_on_blor("Inquisitor's Flail") else 1
        if "Triumph of the Hordes" in self.hand and not self.infect():
            g, w = self.cost_of("Triumph of the Hordes")
            pois_need = 10 - self.poison[tgt]
            if self.can_pay(g, w) and self.hit_damage(P_ + 1, 0, ds, mult) >= pois_need:
                self.pay(g, w); self.hand.remove("Triumph of the Hordes"); self.gy.append("Triumph of the Hordes")
                self.cast_stat("Triumph of the Hordes")
                self.infect_turn = True; self.temp += 1
                return
        if "Epic Fight" in self.hand:
            g, w = self.cost_of("Epic Fight")
            if self.can_pay(g, w) and (self.hit_damage(P_ * 2, 0, ds, mult) >= need or P_ >= 8):
                self.pay(g, w); self.hand.remove("Epic Fight"); self.gy.append("Epic Fight")
                self.cast_stat("Epic Fight"); self.on_cast_green("Epic Fight")
                self.temp += self.power()
        if "Primal Might" in self.hand:
            x = self.avail() - 1 - self.reserve
            if x >= 3 and self.hit_damage(P_ + x, 0, ds, mult) >= need:
                self.pay(x, 1); self.hand.remove("Primal Might"); self.gy.append("Primal Might")
                self.cast_stat("Primal Might"); self.temp += x
        if "Might of Old Krosa" in self.hand and self.can_pay(0, 1):
            if self.hit_damage(self.power() + 4, 0, ds, mult) >= need:
                self.pay(0, 1); self.hand.remove("Might of Old Krosa"); self.gy.append("Might of Old Krosa")
                self.cast_stat("Might of Old Krosa"); self.temp += 4
        if "Exponential Growth" in self.hand:
            x = (self.avail() - self.reserve - 2) // 2
            while x >= 1 and not self.can_pay(2 * x, 2):
                x -= 1
            if x >= 1 and (self.hit_damage(self.power() * 2 ** x, 0, ds, mult) >= need or x >= 2 and self.power() >= 6):
                self.pay(2 * x, 2); self.hand.remove("Exponential Growth"); self.gy.append("Exponential Growth")
                self.cast_stat("Exponential Growth"); self.on_cast_green("Exponential Growth")
                self.temp += self.power() * (2 ** x - 1)
        if "Emergent Growth" in self.hand and self.can_pay(3, 1, extra=self.reserve) and self.power() >= 4:
            self.pay(3, 1); self.hand.remove("Emergent Growth"); self.gy.append("Emergent Growth")
            self.cast_stat("Emergent Growth"); self.on_cast_green("Emergent Growth")
            self.temp += 5
        if "Hunter's Prowess" in self.hand and self.can_pay(4, 1, extra=self.reserve) and self.power() >= 4:
            self.pay(4, 1); self.hand.remove("Hunter's Prowess"); self.gy.append("Hunter's Prowess")
            self.cast_stat("Hunter's Prowess"); self.on_cast_green("Hunter's Prowess")
            self.temp += 3; self.hunters = True
        if "Hunter's Insight" in self.hand and self.can_pay(2, 1, extra=self.reserve) and self.power() >= 4:
            self.pay(2, 1); self.hand.remove("Hunter's Insight"); self.gy.append("Hunter's Insight")
            self.cast_stat("Hunter's Insight"); self.hunters = True

    def expected_swing(self):
        cfg = self.cfg
        if not cfg.combat:
            return 0
        return sum(self.rival_dmg(i, self.turn + 1) for i in self.alive()
                   if not cfg.kinds or cfg.kinds[i] == "combat")

    def need(self, i):
        n = min(21 - self.cmd[i], self.opp[i])
        if self.infect():
            n = min(n, 10 - self.poison[i])
        return n

    def combat(self, extra=False):
        b = self.blor
        if not b or b.tapped or not self.alive():
            return
        if b.sick and not self.haste():
            return
        tgt = self.focus_target()
        cfg = self.cfg
        if not extra and self.mode == "table" and cfg.attack_policy != "always" and not self.vigilance():
            ds0 = self.double_strike()
            m0 = 2 if self.equip_on_blor("Inquisitor's Flail") else 1
            lethal0 = self.hit_damage(self.power() * (2 if self.ench_on("Unnatural Growth") else 1), 0, ds0, m0) >= self.need(tgt)
            if not lethal0:
                pol = cfg.attack_policy
                if pol.startswith("big:") and self.power() < int(pol[4:]):
                    self.stats["held"] = self.stats.get("held", 0) + 1
                    return
                if pol == "safe" and self.expected_swing() >= self.life * 0.35:
                    self.stats["held"] = self.stats.get("held", 0) + 1
                    return
        if not extra:
            self.hunters = False
            self.precombat_sorceries(tgt)
        self.begin_combat_counters()
        if self.ench_on("Unnatural Growth"):
            self.temp += self.power()
        if self.cre_on("Zopandrel, Hunger Dominus"):
            self.temp += self.power()
        if getattr(self, "_hulk_double", False):
            self.temp += self.power(); self._hulk_double = False
        # Rogue's Passage
        self.passage = False
        if self.mode == "table" and any(l["name"] == "Rogue's Passage" for l in self.lands) and \
                self.can_pay(4, 0, extra=self.reserve + 1) and self.power() >= 6:
            self.pay(4, 0); self.Cl = max(0, self.Cl - 1); self.passage = True
            self.cast_stat("(act) Rogue's Passage")
        if not extra and self.ench_on("Glorious Sunrise") and self.blor and self.power() >= 3:
            self.draw(1); self._st("sunrise_draw")      # Juan: el modo de robar casi siempre
        for e in self.equips:                      # Gavel of the Righteous: contador al inicio del combate (equipado o no)
            if e["name"] == "Gavel of the Righteous":
                e["ctr"] = e.get("ctr", 0) + 1
        # declare attack
        if not self.vigilance():
            b.tapped = True
        self._untap_after = False
        for a in list(self.auras):
            if a == "Level Up":
                self.add_counters(b.counters)
                if self.power() >= 10:
                    self.draw(1)
            elif a == "Seismic Tutelage":
                self.add_counters(b.counters)
        for e in self.equips:
            if not e["on"]:
                continue
            n = e["name"]
            if n == "Bone Sabres":
                self.add_counters(4)
            elif n == "Staff of Titania":
                self.dryads += 1
            elif n == "Tanuki Transplanter":
                self.W += self.power()                 # verde que dura todo el turno: se usa despues del combate
            elif n == "Sword of the Animist" and "Forest" in self.library:
                self.library.remove("Forest"); self.put_land("Forest", tapped=True)
        if self.curse == tgt:
            self.add_counters(1)
        if "Bear Umbra" in self.auras:
            self._bear = True
        for q in self.cres:
            if q.name == "Toski, Bearer of Secrets" and not q.sick:
                q.tapped = True
        if self.mode == "table" and self.rng.random() < cfg.p_fog and self.power() >= 8:
            self.log("rival fogs")
            self.after_combat()
            return
        ds = self.double_strike()
        mult = 2 if self.equip_on_blor("Inquisitor's Flail") else 1
        lethal = self.hit_damage(self.power(), 0, ds, mult) >= self.need(tgt)
        block = self.blocker(tgt, lethal)
        # tricks after blocks
        need = self.need(tgt)
        cur = self.hit_damage(self.power(), block, ds, mult)
        budget = self.avail()
        if cur < need:
            plan = self.plan_pumps(self.power(), block, ds, mult, need, budget)
            if plan:
                self.apply_pumps(plan[1], budget)
        elif cfg.pump == "greedy":
            pass
        if cfg.pump == "greedy" or len(self.pumps_in_hand()) >= 3:
            spare = self.avail() - self.reserve
            for c in sorted(self.pumps_in_hand(), key=lambda c: sum(self.pump_cost(c))):
                if c in ("Berserk",) and self.power() < 6:
                    continue
                g, w = self.pump_cost(c)
                if g + w <= spare and c not in ("Tyvar's Stand",):
                    self.apply_pumps((c,), spare)
                    spare -= g + w
        # damage steps
        self.resolve_hits(tgt, block, ds, mult)
        lu = getattr(self, "_lure", None)
        if lu and self.blor and (self.deathtouch() or self.power() * (2 if ds else 1) >= block):
            i, n = lu                                  # Lure: se comieron a toda su mesa
            self.board_reset[i] = self.turn
            self._st("lure_wipes")
            if self.cfg.mus and self.wtype[i] == "combat" and self.opp[i] > 0:
                self.ready_t[i] = max(self.ready_t[i] or 0, self.turn + self.cfg.delay)
        self._lure = None
        self.after_combat()
        # Genji Glove: extra combat (first combat only)
        if not extra and self.equip_on_blor("Genji Glove") and self.alive() and self.blor:
            self.blor.tapped = False
            self.combat(extra=True)

    def resolve_hits(self, tgt, block, ds, mult):
        steps = 2 if ds else 1
        for s in range(steps):
            if self.opp[tgt] <= 0:
                # first strike killed the target: the regular damage has nobody to hit (attack was declared)
                break
            P_ = self.power()
            if self.jitte > 0 and self.equip_on_blor("Umezawa's Jitte"):
                P_ += 2 * self.jitte
                self.temp += 2 * self.jitte
                self.jitte = 0
            d, block = self.step_damage(P_, block)
            d *= mult
            if d <= 0:
                continue
            self._combat_hit = True
            self.deal_player(tgt, d)
            self._combat_hit = False
            if "Super State" in self.auras:
                for j in self.alive():
                    if j != tgt:
                        self.opp[j] -= d                   # no es dano de combate: no suma dano de comandante
                self.check_win()

    def deal_player(self, tgt, d):
        self.cmd[tgt] += d
        if self.infect():
            self.poison[tgt] += d
        else:
            self.opp[tgt] -= d
        if self.deathtouch() and self.cre_on("Fynn, the Fangbearer"):
            self.poison[tgt] += 2
        if self.lifelink():
            self.life += d
        self.log("hit rival", tgt, "for", d, "cmd", self.cmd, "poison", self.poison)
        self.stats["dmg"] = self.stats.get("dmg", 0) + d
        # damage triggers
        draws = 0
        for a in self.auras:
            draws += DRAW_ON_HIT_A.get(a, 0)
        for e in self.equips:
            if not e["on"]:
                continue
            n = e["name"]
            if n == "Power Fist":
                self.add_counters(d)
            elif n == "Quietus Spike" and self.opp[tgt] > 0:
                self.opp[tgt] -= (self.opp[tgt] + 1) // 2
            elif n == "Umezawa's Jitte":
                self.jitte += 2
            elif n == "Sword of Fire and Ice":
                draws += 1
                self.opp[tgt] -= 2
            elif n == "Sword of Feast and Famine":
                self._ff = True
            elif n == "Sword of Truth and Justice":
                self.add_counters(1); self.proliferate()
            elif n == "Sword of Hearth and Home":
                if "Forest" in self.library:
                    self.library.remove("Forest"); self.put_land("Forest", tapped=False)
            elif n == "Mask of Memory":
                draws += 1
            elif n == "Buster Sword":
                draws += 1
                self._buster = d
            elif n == "Vibranium Strike Gauntlets":
                draws += 1
            elif n == "The Aetherspark" and self._our:
                e["loy"] = e.get("loy", 4) + d
        if getattr(self, "_combat_hit", False):
            if "Mark of Sakiko" in self.auras:
                self.W += d
            if "One with Nature" in self.auras and "Forest" in self.library:
                self.library.remove("Forest"); self.put_land("Forest", tapped=True)
            if self.ench_on("Court of Garenbrig"):
                self.monarch = True
        for q in self.cres:
            if q.name in ("Toski, Bearer of Secrets", "Ohran Frostfang"):
                draws += 1
            if q.name == "Kodama of the West Tree" and (self.attached() or self.blor.counters > 0) \
                    and "Forest" in self.library:
                self.library.remove("Forest"); self.put_land("Forest", tapped=True)
        if any(a["name"] == "Herd Heirloom" and a.get("draw_mode") for a in self.arts):
            draws += 1
        if getattr(self, "hunters", False):
            draws += d
            self.hunters = False
        self.draw(draws)
        self.check_win()

    def after_combat(self):
        if "Instill Energy" in self.auras and self.blor and self.blor.tapped:
            self._untap_after = True
        if getattr(self, "_untap_after", False) and self.blor:
            if self.blor.tapped:
                self.well_rested()
            self.blor.tapped = False
        if getattr(self, "_bear", False) or getattr(self, "_ff", False):
            for rec in list(self.lands):
                self.add_land_mana(rec)
            self._bear = self._ff = False
        if getattr(self, "_buster", 0):
            d = self._buster
            self._buster = 0
            opts = [c for c in self.hand if not is_land(c) and sum(C[c]["cost"]) <= d and self.dev_ok(c)
                    and C[c]["t"] != "inst"]
            if opts and self.blor:
                self.cast(max(opts, key=self.card_value), free=True)

    # ------------------------------------------------------------ turns
    def our_turn(self):
        self._our = True
        self.turn += 1
        self.temp = 0
        self.infect_turn = False
        self.deathtouch_ctr = False
        self.extra_land = 0
        self._ring_tapped = False
        self._explo = False
        self._crystal = False
        self._instant_used = False
        self.counter_up = None
        self._cnt_up = {}
        if self.cfg.mus and self.mode == "table":
            self.roll_attempts()
        self.phased = False                   # Talon Gates: vuelve en tu paso de enderezar
        self.ring_prot = False
        for c in self.cres:
            c.tapped = False
            c.sick = False
        if self.blor:
            if self.blor.tapped:
                self.well_rested()
            self.blor.tapped = False
            self.blor.sick = False
        for rec in self.lands:
            if rec["name"] == "Urza's Saga":
                rec["lore"] = rec.get("lore", 1) + 1
        self.urza_saga()
        self.upkeep()
        if self.won or self.lost:
            return
        if not (self.turn == 1 and self.on_play):
            self.draw(1)
            if self.art_on("Mana Vault") and self.vault_used:
                self.life -= 1
        self._hulk_double = False
        if "World War Hulk" in self.enchs:     # saga: contador de lore despues del robo
            self.hulk_lore = getattr(self, "hulk_lore", 1) + 1
            if self.hulk_lore == 2 and self.blor:
                self.add_counters(3)
            elif self.hulk_lore >= 3:
                self._hulk_double = bool(self.blor)
                self.enchs.remove("World War Hulk"); self.gy.append("World War Hulk")
        if self.ench_on("Sylvan Library") and self.life > 24:
            self.draw(1); self.life -= 4
        self._pool_open = False
        for rec in self.lands:
            rec["tapped_entry"] = False
        self.play_land()
        self.compute_pool()
        self.reserve = self.hold_amount()
        self.develop(self.reserve, precombat=True)
        while self.extra_land > 0 and self.play_land():
            self.extra_land -= 1
        if self.mode == "table":
            self.preempt()
            if self.cfg.bracket:
                self.kill_hate()
        self.combat()
        self.check_win()
        if self.won:
            return
        self.develop(self.reserve, precombat=False)
        self.end_step_draws(self.reserve)
        self.reserve = self.W + self.Cl + self.treas + self.vault_mana()
        if self.cre_on("Seedborn Muse"):
            self.reserve += len(self.lands)
        self._our = False

    def tendershoot(self, ours=False):
        for q in list(self.cres):
            if q.name == "Tendershoot Dryad":
                self.make_token("Saproling token")
        if self.blor and "Verdant Embrace" in self.auras:
            self.make_token("Saproling token")
        if ours:
            for n, nm in (("Awakening Zone", "Eldrazi Spawn token"), ("From Beyond", "Eldrazi Scion token")):
                if self.ench_on(n):
                    self.make_token(nm, 0 if n == "Awakening Zone" else 1, 1)

    def upkeep(self):
        self.tendershoot(ours=True)
        if getattr(self, "bloom", None):
            self.bloom = [b - 1 for b in self.bloom]
            for b in [b for b in self.bloom if b <= 0]:
                self.treas += 3; self.cast_stat("(act) Lotus Bloom")
            self.bloom = [b for b in self.bloom if b > 0]
        if self.blor:
            if "Hydra's Growth" in self.auras:
                self.blor.counters += self.blor.counters * (2 ** sum(1 for a in self.auras if a == "Hydra's Growth")) \
                    - self.blor.counters
            if self.cre_on("Forgotten Ancient") and self.ancient > 0:
                self.blor.counters += self.counters_mult(self.ancient)
                self.ancient = 0
            if self.ench_on("Colossal Majesty") and self.power() >= 4:
                self.draw(1)
            if self.cre_on("Bugenhagen, Wise Elder") and self.power() >= 7:
                self.draw(1)
            if self.equip_on_blor("Avarice Amulet"):
                self.draw(1)
            if "Forced Adaptation" in self.auras:
                self.add_counters(1)
            if "Predatory Hunger" in self.auras:
                for i in self.alive():
                    if self.rng.random() < 0.6:
                        self.add_counters(1)
            if self.ench_on("Court of Garenbrig"):
                self.add_counters(2)
                if getattr(self, "monarch", False):
                    self.add_counters(self.blor.counters)
        if self.cre_on("Verdant Kraken"):
            self.dryads += len(self.alive()) + 1             # Forest Tentacle: una por mantenimiento de cada jugador
        if self.ring_on and self.ring > 0:
            self.life -= self.ring
            if self.life <= 0:
                self.lost = True; self.loss = "self"

    def hold_amount(self):
        if self.mode != "table" or self.turn < self.cfg.hold_from_turn:
            return 0
        best = 99
        for c in self.hand:
            d = C.get(c, {})
            if d.get("ans") or d.get("prot") or d.get("fog"):
                g, w = self.cost_of(c)
                if c == "Force of Vigor" and \
                        sum(1 for x in self.hand if x not in (c, B) and not is_land(x) and C[x]["cost"][1] > 0) >= 1:
                    g = w = 0                      # se paga exiliando una carta verde: no hace falta guardar mana
                best = min(best, g + w)
        return 0 if best == 99 else best

    # ------------------------------------------------------------ rivals
    def p_us(self):
        t = self.cfg.target
        if t == "always":
            return 1.0
        if t == "spread":
            return 1 / 3
        return 0.75 if self.threatening() else 0.25

    def rival_dmg(self, i, turn):
        cfg = self.cfg
        start = max(cfg.combat_start, self.board_reset[i] + 1)
        if turn < start:
            return 0
        return int(round(cfg.combat_k * (turn - start + 1)))

    def use_fog(self):
        for c in list(self.hand):
            if c in FOGS:
                g, w = self.cost_of(c)
                if self.reserve >= g + w:
                    self.reserve -= g + w
                    self.hand.remove(c)
                    if c == "Constant Mists" and len(self.lands) > 6:
                        self.lands.pop()
                        self.hand.append(c)
                    elif c == "Moment's Peace" and not getattr(self, "_mp_fb", False):
                        self._mp_fb = True
                        self.gy.append(c)
                    else:
                        self.gy.append(c)
                    self.cast_stat(c)
                    return True
        if "Moment's Peace" in self.gy and getattr(self, "_mp_fb", False) and self.reserve >= 3:
            self.gy.remove("Moment's Peace"); self.exiled.append("Moment's Peace"); self.reserve -= 3
            self._mp_fb = False
            self.cast_stat("Moment's Peace (fb)")
            return True
        for q in list(self.cres):
            if q.name == "Spore Frog":
                self.cres.remove(q); self.gy.append(q.name); self.cast_stat("(act) Spore Frog")
                return True
        return False

    def rival_combat(self, i):
        cfg = self.cfg
        if not cfg.combat or self.turn < cfg.combat_start or self.opp[i] <= 0:
            return
        if cfg.mus:
            if self.wtype[i] != "combat":                # regla 10: atacan los rivales de combate
                return
        elif cfg.kinds and cfg.kinds[i] != "combat":
            return
        if self.ring_prot:
            return
        if self.rng.random() >= self.p_us():
            return
        b0 = self.blor
        if cfg.deterrence > 0 and b0 and (not b0.tapped or self.cre_on("Seedborn Muse")) and self.power(False) >= 8 \
                and self.rng.random() < cfg.deterrence:
            return
        dmg = self.rival_dmg(i, self.turn)
        if dmg <= 0:
            return
        n_att = max(1, min(4, 1 + (self.turn - cfg.combat_start) // 2))
        if self.cre_on("Silent Arbiter"):
            dmg = dmg * min(1.0, 1.5 / n_att)
            n_att = 1
        elif self.art_on("Crawlspace") and n_att > 2:
            dmg = dmg * 2 / n_att
            n_att = 2
        a = dmg / n_att
        left = dmg
        b = self.blor
        if b and (not b.tapped or self.cre_on("Seedborn Muse")):
            left -= a                       # Blor eats the biggest attacker (indestructible)
        for q in self.cres:
            if left <= 0:
                break
            if not q.tapped and (q.x > a or q.name == "Toski, Bearer of Secrets"):
                left -= a
        if b and self.equip_on_blor("Pariah's Shield"):
            left = 0
        left = max(0, int(round(left)))
        if left >= self.life * 0.5 or left >= self.life:
            if self.use_fog():
                return
        if left >= self.life:
            # chump with dorks
            for q in sorted(self.cres, key=lambda q: q.p):
                if left < self.life:
                    break
                if not q.tapped:
                    left -= a
                    self.cres.remove(q); self.gy.append(q.name)
        left = max(0, int(round(left)))
        if left > 0:
            self.life -= left
            self.monarch = False                          # el rival que nos pega se lleva la corona
            self.stats["taken"] = self.stats.get("taken", 0) + left
            self.log("rival", i, "hits us for", left, "life", self.life)
        if self.life <= 0:
            self.lost = True
            self.loss = "combat"

    def roll_threat(self, i):
        if self.cfg.mus:
            return self.roll_threat_v2(i)
        r = self.rng.random()
        if self.cfg.kinds:
            kind = "cre" if self.cfg.kinds[i] == "combat" else ("ae" if r < 0.5 else "other")
        else:
            kind = "cre" if r < 0.5 else ("ae" if r < 0.75 else "other")
        self.threat[i] = dict(kind=kind, stoppable=self.rng.random() < self.cfg.p_stoppable,
                              visible=self.rng.random() < self.cfg.p_visible, stopped=False, t=self.turn,
                              combat=self.cfg.kinds[i] == "combat" if self.cfg.kinds else kind == "cre")

    def preempt_kind_with(self, c):
        kinds = (C[c].get("sans") or "").split()
        for i in self.alive():
            if self.rival_next[i] in (self.turn, self.turn + 1):
                th = self.threat.get(i)
                if th is None or th["t"] < self.turn - 1:
                    self.roll_threat(i); th = self.threat[i]
                if th["stoppable"] and th["visible"] and not th["stopped"] and th["kind"] in kinds:
                    th["stopped"] = True
                    self.log("pre-empted rival", i, "with", c)
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
            for c in list(self.hand):
                d = C.get(c, {})
                kinds = (d.get("sans") or "").split()
                if (c in ("Spinning Wheel Kick", "Epic Fight", "Primal Might", "Bridgeworks Battle") or c in FIGHT) and not self.blor:
                    continue
                if th["kind"] in kinds:
                    g, w = self.cost_of(c)
                    if self.can_pay(g, w):
                        self.pay(g, w)
                        self.hand.remove(c)
                        self.cast_stat(c)
                        if c == "Kenrith's Transformation":
                            self.draw(1)
                        if c == "Epic Fight" and self.blor:
                            pass
                        self.gy.append(c)
                        th["stopped"] = True
                        self.log("pre-empt", i, "with", c)
                        break

    def _st(self, k):
        self.stats[k] = self.stats.get(k, 0) + 1

    def removal_on_us(self, kind=None):
        if kind is None:
            mix = self.cfg.removal_mix
            r = self.rng.random()
            kind = "ae" if r < mix[0] else ("edict" if r < mix[0] + mix[1] else "cre")
        if self.ring_prot:
            return
        if kind == "edict":
            if self.cre_on("Tajuru Preserver"):
                self._st("edict_tajuru"); return
            if not self.blor and not self.cres:
                return
            self.stats["edicts"] = self.stats.get("edicts", 0) + 1
            others = [q for q in self.cres]
            if not others and self.dryads > 0:
                self.dryads -= 1
                self.log("edict takes a Forest Dryad token")
                self._st("edict_took_dryad"); return
            if not others:
                arb = [l for l in self.lands if l["name"] == "Dryad Arbor"]
                if arb:
                    self.lands.remove(arb[0]); self.gy.append("Dryad Arbor")
                    self._st("edict_took_arbor"); return
            if not others:
                ml = [l for l in self.lands if LANDS[l["name"]].get("manland")
                      and self.reserve >= LANDS[l["name"]]["manland"]]
                if ml:
                    self.reserve -= LANDS[ml[0]["name"]]["manland"]
                    self.lands.remove(ml[0]); self.gy.append(ml[0]["name"])
                    self.cast_stat("(edict) " + ml[0]["name"])
                    self._st("edict_took_manland"); return
            if not others and "Sprout Swarm" in self.hand and self.reserve >= 2:
                self.reserve -= 2
                self.cast_stat("Sprout Swarm")
                if self.reserve >= 3:
                    self.reserve -= 3          # buyback: back to hand
                else:
                    self.hand.remove("Sprout Swarm"); self.gy.append("Sprout Swarm")
                self._st("edict_took_sprout"); return
            if others:
                q = min(others, key=lambda q: (q.name not in DORK_NAMES and not q.token, q.p))
                self.cres.remove(q)
                if not q.token:
                    self.gy.append(q.name)
                self.log("edict takes", q.name)
                self._st("edict_took_" + ("dork" if (q.name in DORK_NAMES or q.token) else "cre")); return
            if self.blor and self.equip_on_blor("Assault Suit"):
                self._st("edict_took_suit"); return
            if self.try_phase("edict"):
                return
            self.stats["edict_blor"] = self.stats.get("edict_blor", 0) + 1
            self.log("EDICT takes Blor")
            self.blor_leaves("cmd")
            return
        if kind == "ae":
            # most valuable attachment, else a rock / global enchantment
            targets = []
            if self.blor:
                for a in self.auras:
                    targets.append((self.attach_value(a, True), "aura", a))
                for e in self.equips:
                    if e["on"]:
                        targets.append((self.attach_value(e["name"], False), "equip", e))
            if not targets or not self.threatening():
                for a in self.arts:
                    targets.append((1.5, "art", a))
                for e in self.enchs:
                    targets.append((2, "ench", e))
            if not targets:
                return
            targets.sort(key=lambda t: -t[0])
            val, typ, obj = targets[0]
            if val >= 5 and "Heroic Intervention" in self.hand and self.reserve >= 2:
                self.hand.remove("Heroic Intervention"); self.gy.append("Heroic Intervention")
                self.reserve -= 2; self.cast_stat("Heroic Intervention")
                return
            self.stats["attach_lost"] += 1 if typ in ("aura", "equip") else 0
            if typ == "aura":
                self.auras.remove(obj)
                self.to_gy_aura(obj)
            elif typ == "equip":
                self.equips.remove(obj); self.gy.append(obj["name"])
                if obj["name"] == "Grafted Exoskeleton":
                    self.log("Exoskeleton destroyed: sacrifice Blor")
                    self.blor_leaves("cmd", sac=True)
            elif typ == "art":
                self.arts.remove(obj); self.gy.append(obj["name"])
                if obj["name"] == "The One Ring":
                    pass
            elif typ == "ench":
                self.enchs.remove(obj)
                if obj in C:
                    self.gy.append(obj)
            self.log("removal on", obj if isinstance(obj, str) else obj["name"])
            return
        # creature-only removal: Blor can't be targeted
        cs = [q for q in self.cres if q.name != "Toski, Bearer of Secrets"]
        if cs:
            q = max(cs, key=lambda q: (q.name in ("Silent Arbiter", "Ohran Frostfang", "Tajuru Preserver",
                                                   "Forgotten Ancient", "Fynn, the Fangbearer", "Seedborn Muse"), q.p))
            self.cres.remove(q)
            if not q.token:
                self.gy.append(q.name)
            self.log("creature removal on", q.name)

    def attach_value(self, n, aura):
        if aura:
            v = {"Colossification": 20, "Blanchwood Armor": self.forests(), "Crystalline Armor": self.n_lands(),
                 "Strong Back": 2 * len(self.attached()), "Hydra's Growth": 4 + self.blor.counters / 2,
                 "Level Up": 3 + self.blor.counters / 2}.get(n, AURA_FLAT.get(n, 1.5))
            if n == "Ancestral Mask":
                v = 2 * self.our_enchantments()
            return v
        v = {"Blackblade Reforged": self.n_lands(), "Staff of Titania": self.forests(),
             "Fireshrieker": self.power(False), "Genji Glove": self.power(False) * 2, "Leyline Axe": self.power(False),
             "Inquisitor's Flail": self.power(False), "Grafted Exoskeleton": 8, "Pariah's Shield": 4}.get(n, EQUIP_FLAT.get(n, 1.5))
        return v

    def to_gy_aura(self, a):
        if a == "Rancor":
            self.hand.append(a)
        else:
            self.gy.append(a)

    def blor_leaves(self, where, sac=False):
        """Blor leaves the battlefield: 'cmd' (tax +2) or 'hand' (bounce)."""
        if not self.blor:
            return
        self.stats["blor_left"] += 1
        for a in self.auras:
            self.to_gy_aura(a)
        self.auras = []
        for e in self.equips:
            if e["on"] and e["name"] == "Grafted Exoskeleton" and not sac:
                pass
            e["on"] = False
        self.blor = None
        self.temp = 0
        if where == "hand":
            self.blor_zone = "hand"
            self.hand.append(B)
        else:
            self.blor_zone = "cmd"
            self.tax += 2

    def wipe(self, sub=None):
        cfg = self.cfg
        if sub is None:
            mix = cfg.wipe_mix
            r = self.rng.random()
            kind = "destroy" if r < mix[0] else ("minus" if r < mix[0] + mix[1] else
                                                 ("exile" if r < mix[0] + mix[1] + mix[2] else "bounce"))
            if self.ring_prot:
                return
            ae = None                                        # mesa vieja: se tira solo en destroy (mismo azar que antes)
        else:
            kind = {"destroy_ae": "destroy", "exile_ae": "exile", "rift": "bounce"}.get(sub, sub)
            ae = sub in ("destroy_ae", "exile_ae", "rift") and not cfg.ceil_attach
        self.log("RIVAL WIPE", kind)
        for i in self.alive():
            self.board_reset[i] = self.turn
        if kind == "destroy":
            if ae is None:
                ae = self.rng.random() < cfg.p_wipe_ae
            if "Heroic Intervention" in self.hand and self.reserve >= 2:
                self.hand.remove("Heroic Intervention"); self.gy.append("Heroic Intervention")
                self.reserve -= 2; self.cast_stat("Heroic Intervention")
                return
            self.lands = [l for l in self.lands if l["name"] != "Dryad Arbor"]
            for q in list(self.cres):
                if q.name != "Toski, Bearer of Secrets":
                    self.cres.remove(q)
                    if not q.token:
                        self.gy.append(q.name)
            self.dryads = 0
            if ae:
                for a in list(self.auras):
                    if a in ("Bear Umbra", "Lion Umbra", "Snake Umbra", "Spider Umbra"):
                        pass
                    self.auras.remove(a); self.to_gy_aura(a)
                for e in list(self.equips):
                    if e["name"] == "Darksteel Plate":
                        continue
                    self.equips.remove(e); self.gy.append(e["name"])
                    if e["on"] and e["name"] == "Grafted Exoskeleton":
                        self.blor_leaves("cmd", sac=True)
                for a in list(self.arts):
                    if a["name"] != "The One Ring":
                        self.arts.remove(a); self.gy.append(a["name"])
                for e in list(self.enchs):
                    self.enchs.remove(e)
                    if e in C:
                        self.gy.append(e)
            return
        if kind == "minus":
            for q in list(self.cres):
                self.cres.remove(q)
                if not q.token:
                    self.gy.append(q.name)
            self.dryads = 0
            if self.blor and self.tough() <= 12:
                self.blor_leaves("cmd")
            return
        if kind == "exile":
            for q in list(self.cres):
                self.cres.remove(q)
                if not q.token:
                    self.exiled.append(q.name)
            self.dryads = 0
            if self.blor:
                self.blor_leaves("cmd")
            if (self.rng.random() < 0.5) if sub is None else ae:      # Farewell: artifacts and enchantments too
                for e in list(self.equips):
                    self.equips.remove(e); self.exiled.append(e["name"])
                for a in list(self.arts):
                    self.arts.remove(a); self.exiled.append(a["name"])
                for e in list(self.enchs):
                    self.enchs.remove(e)
            return
        # bounce
        rift = (self.rng.random() < 0.5) if sub is None else ae
        for q in list(self.cres):
            self.cres.remove(q)
            if not q.token:
                self.hand.append(q.name)
        self.dryads = 0
        if self.blor:
            if rift:
                for a in self.auras:
                    self.hand.append(a)
                self.auras = []
            self.blor_leaves("hand")
        if rift:
            for e in list(self.equips):
                self.equips.remove(e); self.hand.append(e["name"])
            for a in list(self.arts):
                self.arts.remove(a); self.hand.append(a["name"])
            for e in list(self.enchs):
                self.enchs.remove(e)
                if e in C:
                    self.hand.append(e)

    def wipe_type(self):
        r = self.rng.random()
        for k, p in self.cfg.wipe_types:
            r -= p
            if r < 0:
                return k
        return self.cfg.wipe_types[-1][0]

    def w_naked(self):
        """peso de Blor sin adjuntos (lo que queda tras perder auras y equipos)"""
        au, on = self.auras, [e for e in self.equips if e["on"]]
        self.auras = []
        for e in on: e["on"] = False
        try:
            return self.w_blor()
        finally:
            self.auras = au
            for e in on: e["on"] = True

    def wipe_value_us(self, sub, i):
        """regla 7: lo que el rival i ve que nos quita esa barrida (solo lo que de verdad muere / se va)"""
        cres = sum(self.w_perm(q.name) for q in self.cres
                   if not (sub.startswith("destroy") and q.name == "Toski, Bearer of Secrets"))
        cres += self.W_DORK * (self.dryads + sum(l["name"] == "Dryad Arbor" for l in self.lands))
        perms = sum(self.w_perm(a["name"]) for a in self.arts if a["name"] != "The One Ring") + \
                sum(self.w_perm(x) for x in self.enchs)
        blor = self.w_seen(i) if self.blor else 0.0
        if sub == "destroy":
            return cres                                    # Blor es indestructible
        if sub == "destroy_ae":
            return cres + (max(0.0, blor - self.w_naked()) if self.blor else 0.0) + perms
        if sub == "minus":
            return cres + (blor if self.blor and self.tough() <= 12 else 0.0)
        if sub in ("exile", "bounce"):
            return cres + blor
        return cres + blor + perms * (1.0 if sub == "exile_ae" else 0.5)   # Farewell / Rift

    pick_r = staticmethod(M.pick)

    def pick(self, table):
        return M.pick(self.rng, table)

    AEM_OWN = {"art": 0.0, "both": 0.2, "ench": 0.2}    # Vandalblast con overload es solo de los oponentes

    def aem_hits(self, t):
        """que se lleva un odio masivo de tipo t: (auras, equipos, artefactos, encantamientos)"""
        if self.cfg.ceil_attach:
            return [], [], [], []
        A = t in ("art", "both"); E = t in ("ench", "both")
        return (list(self.auras) if E else [], [x for x in self.equips if x["name"] != "Darksteel Plate"] if A else [],
                [a for a in self.arts if a["name"] != "The One Ring"] if A else [], list(self.enchs) if E else [])

    def aem_value_us(self, t, i):
        au, eq, ar, en = self.aem_hits(t)
        v = sum(self.w_perm(a["name"]) for a in ar) + sum(self.w_perm(x) for x in en) + 0.15 * sum(not e["on"] for e in eq)
        if self.blor and (au or any(e["on"] for e in eq)):
            keep_a = self.auras; on = [e for e in eq if e["on"]]
            full = self.w_blor()
            self.auras = [a for a in self.auras if a not in au]
            for e in on: e["on"] = False
            try:
                naked = self.w_blor()
            finally:
                self.auras = keep_a
                for e in on: e["on"] = True
            drop = max(0.0, full - naked)
            v += max(drop, self.w_seen(i)) if drop >= 0.2 else drop   # regla 1-B: dejarlo desnudo es lo que pueden hacer
        return v

    def rival_aem(self, i):
        """regla 8: el rival i usa su odio masivo si lo que nos quita (y a la mesa) supera su propio costo + REM_THR"""
        stock = self.aem_stock[i]
        if not stock or self.turn < 3:
            return False
        t = max(sorted(set(stock)), key=lambda k: self.aem_value_us(k, i) - self.AEM_OWN[k])
        v = self.aem_value_us(t, i)
        if v < self.REM_THR + self.AEM_OWN[t]:
            return False
        stock.remove(t)
        self._st("aem"); self._st("aem_" + t)
        self.stats["aem_turn_sum"] = self.stats.get("aem_turn_sum", 0) + self.turn
        if "Heroic Intervention" in self.hand and self.reserve >= 2:
            self.hand.remove("Heroic Intervention"); self.gy.append("Heroic Intervention")
            self.reserve -= 2; self.cast_stat("Heroic Intervention"); self._st("aem_heroic")
            return True
        if v >= self.REM_THR + 0.2:
            self.try_phase("aem")
        ph = self.stash_phased()
        au, eq, ar, en = self.aem_hits(t)
        self.stats["aem_attach_lost"] = self.stats.get("aem_attach_lost", 0) + len(au) + sum(e["on"] for e in eq)
        self.stats["aem_perms_lost"] = self.stats.get("aem_perms_lost", 0) + len(ar) + len(en) + sum(not e["on"] for e in eq)
        for a in au:
            self.auras.remove(a); self.to_gy_aura(a)
        for e in eq:
            self.equips.remove(e); self.gy.append(e["name"])
            if e["on"] and e["name"] == "Grafted Exoskeleton":
                self.blor_leaves("cmd", sac=True)
        for a in ar:
            self.arts.remove(a); self.gy.append(a["name"])
        for x in en:
            self.enchs.remove(x)
            if x in C:
                self.gy.append(x)
        self.unstash(ph)
        return True

    # ---------------- 15/11: fase (Talon Gates of Madara) y piezas que quitan antimaleficio
    def can_phase(self):
        if not self.blor or self.phased:
            return None
        if "Talon Gates of Madara" in self.hand and self.reserve >= 4:
            return "hand"
        if "Talon Gates of Madara" in self.library:
            if "Archdruid's Charm" in self.hand and self.reserve >= 3:
                return "charm"
            if "Crop Rotation" in self.hand and self.reserve >= 1 and len(self.lands) >= 4:
                return "crop"
        return None

    def try_phase(self, why):
        """en respuesta a algo que saca a Blor o a sus adjuntos: Talon Gates entra y Blor se va de fase con todo lo puesto"""
        how = self.can_phase()
        if not how:
            return False
        if how == "hand":
            self.reserve -= 4; self.hand.remove("Talon Gates of Madara")
        elif how == "charm":
            self.reserve -= 3; self.hand.remove("Archdruid's Charm"); self.gy.append("Archdruid's Charm")
            self.library.remove("Talon Gates of Madara"); self.rng.shuffle(self.library); self.cast_stat("Archdruid's Charm (Talon)")
        else:
            self.reserve -= 1; self.hand.remove("Crop Rotation"); self.gy.append("Crop Rotation")
            fs = [l for l in self.lands if l["name"] == "Forest"] or self.lands
            self.lands.remove(fs[0]); self.gy.append(fs[0]["name"])
            self.library.remove("Talon Gates of Madara"); self.rng.shuffle(self.library); self.cast_stat("Crop Rotation (Talon)")
        self.put_land("Talon Gates of Madara", tapped=True)
        self.phased = True
        self.cast_stat("(fase) " + why)
        self._st("phase_" + why)
        return True

    def stash_phased(self):
        """lo que esta en fase no existe: se saca del estado y se devuelve despues"""
        if not self.phased:
            return None
        st = (self.blor, self.auras, [e for e in self.equips if e["on"]])
        self.blor, self.auras = None, []
        self.equips = [e for e in self.equips if not e["on"]]
        return st

    def unstash(self, st):
        if st:
            self.blor, self.auras = st[0], st[1]
            self.equips += st[2]

    def hate_kills_blor(self, i):
        """regla 15/11: el rival i tiene Shadowspear / Arcane Lighthouse en mesa y una remocion: va a Blor si lo vale"""
        if not (self.cfg.bracket and self.hate_on[i] and self.blor and not self.phased):
            return False
        ks = [k for k in self.rem[i] if k in ("cre", "any")]
        if not ks or (self.w_seen(i) or 0) < self.REM_THR:
            return False
        self.rem[i].remove(ks[0])
        self._st("hate_used")
        if "Heroic Intervention" in self.hand and self.reserve >= 2:   # timestamp posterior: vuelve a tener ambas
            self.hand.remove("Heroic Intervention"); self.gy.append("Heroic Intervention")
            self.reserve -= 2; self.cast_stat("Heroic Intervention"); self._st("hate_heroic")
            return True
        for c in ("Snakeskin Veil", "Vines of Vastwood", "Blossoming Defense", "Tamiyo's Safekeeping"):
            if c in self.hand and self.reserve >= sum(C[c]["cost"]) and C[c]["cost"][1] <= self.reserve:
                self.hand.remove(c); self.gy.append(c); self.reserve -= sum(C[c]["cost"]); self.cast_stat(c)
                self._st("hate_trick"); return True
        if self.try_phase("hate"):
            return True
        self._st("hate_blor")
        self.blor_leaves("cmd")
        return True

    def kill_hate(self):
        """en tu turno, con una respuesta de artefactos a mano y maná, rompes la pieza (Juan: guardar interaccion para esto)"""
        for i in self.alive():
            if not self.hate_on[i]:
                continue
            for c in ("Nature's Claim", "Krosan Grip", "Return to Nature", "Slice in Twain", "Beast Within", "Archdruid's Charm"):
                if c in self.hand:
                    g, w = self.cost_of(c)
                    if self.can_pay(g, w):
                        if c == "Archdruid's Charm" and self.rng.random() < 0.3:
                            continue                     # su modo de daño no rompe artefactos; Lighthouse (tierra) solo Beast Within
                        if c != "Beast Within" and self.rng.random() < 0.3:
                            continue                     # ~30% de las piezas son tierras (Arcane Lighthouse)
                        self.pay(g, w); self.hand.remove(c); self.gy.append(c); self.cast_stat(c + " (hate)")
                        self.hate_on[i] = False; self._st("hate_killed")
                        break

    def rival_wipes(self, i):
        """regla 7: el rival i barre (en su turno) si lo que pierden los demas supera lo suyo por wipe_margin
        (Forge DestroyAllAi; igual que Gandalf). Elige, de las que tiene, la que mas nos quita."""
        stock = self.wipe_stock[i]
        if not stock or self.turn < 3:
            return False
        sub = max(sorted(set(stock)), key=lambda k: self.wipe_value_us(k, i))
        us = self.wipe_value_us(sub, i)
        others = sum(self.opp_best_value() * 1.5 for j in self.alive() if j != i)
        own = self.opp_best_value() * 1.5
        if us + others < own + self.cfg.wipe_margin:
            return False
        stock.remove(sub)
        if self.blor and (self.wipe_value_us(sub, i) - self.wipe_value_us("destroy", i)) >= self.REM_THR:
            self.try_phase("wipe")                   # Farewell, Rift, -X/-X...: Blor se va de fase con todo
        if others < own + self.cfg.wipe_margin:
            self._st("wipe_due_us")                       # sin nosotros no habria barrido
        self.opp_wiped_t = self.turn
        b0, att0 = self.blor is not None, len(self.auras) + sum(e["on"] for e in self.equips)
        self._st("wipes"); self._st("wipe_" + sub)
        ph = self.stash_phased()
        self.wipe(sub)
        self.unstash(ph)
        if b0 and not self.blor:
            self._st("wipe_blor_left")
        att1 = len(self.auras) + sum(e["on"] for e in self.equips) if self.blor else 0
        if b0:
            self.stats["wipe_attach_lost"] = self.stats.get("wipe_attach_lost", 0) + max(0, att0 - att1)
        self.stats["wipe_turn_sum"] = self.stats.get("wipe_turn_sum", 0) + self.turn
        return True

    MU_SHIFT = {"combat": 0.4, "dmg": -0.5, "loss": -0.5, "combo": -1.5}   # Playgroup: combo gana ~2 rondas antes

    _F = staticmethod(M.F)

    def attempt_p(self, t, mu):
        return M.attempt_p(t, mu, self.cfg.spread)

    P_REM_STOP = M.P_REM_STOP

    def others_stop(self, i):
        """regla 11 (como Gandalf): antes que tus respuestas, los OTROS rivales frenan el intento de i con lo que guardaron.
        El azul primero (counter si dejo mana arriba); los demas con una remocion guardada (sirve el 40% de las veces)."""
        oth = [j for j in self.alive() if j != i]
        oth = sorted(self.rng.sample(oth, len(oth)), key=lambda j: j not in self.blue)
        for j in oth:
            if self.rem[j] and self.rng.random() < self.P_REM_STOP:
                self.rem[j].pop(self.rng.randrange(len(self.rem[j])))
                self._st("others_stop"); self._st("others_stop_rem")
                return True
            if j in self.blue and self.cnt_stock[j] > 0 and self.rng.random() < self.cfg.cnt_up:
                self.cnt_stock[j] -= 1
                self._st("others_stop"); self._st("others_stop_cnt")
                return True
        return False

    def dly(self, i):
        """regla 2 de la Mazmorra: el turbo rearma en 1 turno"""
        return self.cfg.mz_turbo[0] if (self.cfg.mz and i == self.turbo) else self.cfg.delay

    def win_other(self):
        """reparto de los rivales no azules para que la mesa entera quede en win_types"""
        c = self.cfg
        if not c.win_blue:
            return c.win_types
        nb = len(self.blue)
        blue = dict(c.win_blue)
        out = tuple((k, max(0.0, (3 * p - nb * blue.get(k, 0.0)) / (3 - nb))) for k, p in c.win_types)
        s = sum(p for _, p in out)
        return tuple((k, p / s) for k, p in out)

    def roll_attempts(self):
        """regla 10: al empezar tu turno se decide que rivales intentan ganar en su proximo turno (logistica por turno;
        si ya los frenaron, se rearman 'delay' turnos y reintentan con 'retry'). Helm of Awakening: mu - 1."""
        helm = 1 if self.art_on("Helm of Awakening") else 0
        for i in range(3):
            if self.opp[i] <= 0:
                continue
            if self.ready_t[i] is None:
                p = self.attempt_p(self.turn, self.mu[i] - helm)
            elif self.turn >= self.ready_t[i]:
                p = self.cfg.mz_turbo[1] if (self.cfg.mz and i == self.turbo) else self.cfg.retry
            else:
                p = 0.0
            self.rival_next[i] = self.turn if self.rng.random() < p else -1

    def roll_threat_v2(self, i):
        wt = self.wtype[i]
        r = self.rng.random()
        kind = "cre" if wt == "combat" else ("ae" if r < 0.5 else "other")
        self.threat[i] = dict(kind=kind, stoppable=self.rng.random() < self.cfg.p_stoppable,
                              visible=self.rng.random() < self.cfg.p_visible, stopped=False, t=self.turn,
                              combat=wt == "combat", wtype=wt)

    def burgeoning(self):
        if self.ench_on("Burgeoning") and self.turn <= 10:
            ls = [c for c in self.hand if is_land(c) and not LANDS[c].get("tapped") and LANDS[c]["col"] != "fetch"]
            if ls:
                self.hand.remove(ls[0])
                self.put_land(ls[0], tapped=False)

    def table_events(self, i):
        cfg = self.cfg
        self.rival_combat(i)
        if self.lost:
            return
        if cfg.bracket:
            self.rival_wipes(i)
            self.rival_aem(i)
            self.rival_removal_phase(i)
        elif not self.wipe_done and self.turn >= self.wipe_turn and self.rng.random() < 0.5:
            self.wipe_done = True
            self.wipe()
        if not cfg.bracket and self.rng.random() < cfg.p_removal and self.rng.random() < self.p_us():
            self.removal_on_us()
        # Forgotten Ancient grows with rival spells
        if self.cre_on("Forgotten Ancient"):
            k = int(cfg.rival_spells) + (1 if self.rng.random() < cfg.rival_spells % 1 else 0)
            self.ancient += k
        # Tarrian's Soulcleaver: creatures die all the time in a 4-player game
        if self.equip_on_blor("Tarrian's Soulcleaver") and self.rng.random() < 0.4:
            self.add_counters(1)
        # kill attempt
        if self.opp[i] > 0 and self.rival_next[i] == self.turn:
            th = self.threat.get(i)
            if th is None or th["t"] < self.turn - 1:
                self.roll_threat(i); th = self.threat[i]
            self.threat.pop(i, None)
            if cfg.mus:
                self.ready_t[i] = self.turn + self.dly(i)          # regla 10: si no gana, se rearma
                self._st("att"); self._st("att_" + th.get("wtype", "?"))
                self.stats.setdefault("att1", self.turn)
            if cfg.mz and self.slowed[i]:                         # regla 4: la remocion de otro rival lo retraso
                self.slowed[i] = False
                self._st("mz_slowed"); self._st("others_stop")
                self.rival_next[i] = self.turn + self.dly(i)
                return
            if th["stopped"]:
                self.rival_next[i] = self.turn + self.dly(i)
                return
            if self.ring_prot and th["combat"]:
                self.rival_next[i] = self.turn + 1
                return
            if cfg.mus and th.get("wtype") in ("combat", "dmg") and self.blor and self.equip_on_blor("Pariah's Shield"):
                self._st("pariah_saves")                         # todo el dano va a Blor (indestructible)
                self.rival_next[i] = self.turn + self.dly(i)
                return
            if th["combat"]:
                if self.cre_on("Silent Arbiter") and self.rng.random() < 0.6:
                    self.rival_next[i] = self.turn + self.dly(i)
                    self.log("Silent Arbiter stops rival", i)
                    return
                if self.art_on("Crawlspace") and self.rng.random() < 0.3:
                    self.rival_next[i] = self.turn + self.dly(i)
                    return
            if cfg.mus and self.others_stop(i):
                self.rival_next[i] = self.turn + self.dly(i)
                return
            if cfg.mus and th["combat"] and self.rng.random() >= cfg.p_combat_us:
                self._st("combat_elsewhere")                    # SENSIBILIDAD: el ataque letal fue a otro jugador
                self.rival_next[i] = self.turn + self.dly(i)
                return
            if th["stoppable"]:
                for c in sorted(self.hand, key=lambda c: sum(self.cost_of(c)) if c in C else 99):
                    d = C.get(c, {})
                    ok = th["kind"] in (d.get("ans") or "").split()
                    if d.get("fog") and th["combat"]:
                        ok = True
                    if c in FIGHT and not self.blor:
                        ok = False
                    if not ok:
                        continue
                    g, w = self.cost_of(c)
                    if self.reserve >= g + w:
                        self.reserve -= g + w
                        self.hand.remove(c)
                        self.gy.append(c)
                        self.cast_stat(c)
                        self.answer_extra(c, g + w)
                        self.rival_next[i] = self.turn + self.dly(i)
                        self.log("answered rival", i, "with", c)
                        self._st("we_stop")
                        return
                if th["kind"] == "ae":
                    for rec in self.lands:
                        if rec["name"] == "Boseiju, Who Endures" and self.reserve >= 1:
                            self.lands.remove(rec); self.gy.append(rec["name"]); self.reserve -= 1
                            self.cast_stat("(act) Boseiju")
                            self.rival_next[i] = self.turn + self.dly(i)
                            return
                if th["combat"] and any(q.name == "Spore Frog" for q in self.cres):
                    q = next(q for q in self.cres if q.name == "Spore Frog")
                    self.cres.remove(q); self.gy.append(q.name); self.cast_stat("(act) Spore Frog")
                    self.rival_next[i] = self.turn + self.dly(i)
                    return
            if not cfg.mus and cfg.p_others > 0 and self.rng.random() < cfg.p_others:
                self.rival_next[i] = self.turn + self.dly(i)
                self.log("another rival stops rival", i)
                return
            if cfg.mz and self.rng.random() < cfg.mz_partial:      # regla 5: golpe parcial, mata a un solo jugador
                vict = ["us"] + [j for j in self.alive() if j != i]
                w_us = cfg.mz_partial_us_w if sum(self.cmd) >= 21 else 1.0
                ws = [w_us] + [1.0] * (len(vict) - 1)
                r = self.rng.random() * sum(ws)
                for v, w in zip(vict, ws):
                    r -= w
                    if r <= 0:
                        break
                if v != "us":
                    self.opp[v] = 0
                    self._st("mz_partial_opp")
                    self.ready_t[i] = self.turn + 1                # el atacante reintenta al turno siguiente
                    self.rival_next[i] = -1
                    return
                self._st("mz_partial_us")
            self.lost = True
            self.loss = "rival"
            self.log("LOSS: rival", i, "wins")

    @property
    def rem_stock(self):
        return [len(x) for x in self.rem]

    def rem_type(self):
        r = self.rng.random()
        for k, p in self.cfg.rem_types:
            r -= p
            if r < 0:
                return k
        return self.cfg.rem_types[-1][0]

    # ---------------- regla 4 (14/11): a quien va la remocion (estructura de Forge, pesos de Juan) ----------------
    REM_THR = M.REM_THR
    KEEP_LAST = M.KEEP_LAST

    def our_target(self, kind, i):
        """mejor blanco LEGAL nuestro para una remocion de este tipo, visto por el rival i: (peso, accion) o None"""
        if self.ring_prot and not self.cfg.bracket:     # The One Ring protege al JUGADOR, no a sus permanentes
            return None
        best = None
        def consider(w, act):
            nonlocal best
            if best is None or w > best[0]:
                best = (w, act)
        if kind in ("cre", "any"):
            for q in self.cres:
                if q.name != "Toski, Bearer of Secrets":           # Toski es indestructible
                    consider(self.w_perm(q.name), ("cre", q))
        if kind in ("ae", "any") and not self.phased:
            t = self.w_attach_target()
            if t is not None:
                drop, typ, obj = t
                consider(max(drop, self.w_seen(i) or 0), (typ, obj))   # regla 1-B: rival frustrado
            for a in self.arts:
                consider(self.w_perm(a["name"]), ("art", a))
            for x in self.enchs:
                consider(self.w_perm(x), ("ench", x))
            for x in self.equips:
                if not x["on"]:
                    consider(0.15, ("equip", x))
        if kind == "edict":
            if self.cre_on("Tajuru Preserver") or (not self.blor and not self.cres):
                return None
            fodder = self.cres or self.dryads > 0 or any(l["name"] == "Dryad Arbor" for l in self.lands)
            if fodder or (self.blor and self.equip_on_blor("Assault Suit")):
                consider(self.W_DORK, ("edict", None))
            elif self.blor:
                consider(self.w_seen(i), ("edict", None))
        return best

    def rival_uses_removal(self, i, forced_us=False, kinds=None):
        """el rival i decide si usa una remocion guardada y contra quien. Devuelve True si la uso."""
        import math
        stock = self.rem[i]
        if not stock:
            return False
        thr = self.REM_THR if len(stock) == 1 else self.REM_THR - 0.1
        cands = []
        for k in sorted(set(stock)):
            if kinds and k not in kinds:
                continue
            t = self.our_target(k, i)
            if t and t[0] >= thr:
                cands.append(("us", t[0], k, t[1]))
        if not forced_us:
            for j in self.alive():
                if j != i:
                    o = self.opp_best_value()
                    if o >= thr:
                        cands.append(("opp", o, max(set(stock), key=lambda k: (k != "edict", k == "cre")), None))
        if not cands:
            return False
        if len(stock) == 1 and max(c[1] for c in cands) < 0.8 and self.rng.random() < self.KEEP_LAST:
            self.stats["rem_kept"] = self.stats.get("rem_kept", 0) + 1
            return False
        ws = [math.exp(c[1] / 0.3) for c in cands]
        r = self.rng.random() * sum(ws)
        for c, w in zip(cands, ws):
            r -= w
            if r <= 0:
                break
        who, val, k, act = c
        stock.remove(k)
        if who == "opp":
            self.stats["rem_opp"] = self.stats.get("rem_opp", 0) + 1
            if self.cfg.mz and self.rng.random() < self.cfg.mz_rem_slows:   # regla 4: va al mas rapido vivo
                fast = [j for j in self.alive() if j != i]
                if fast:
                    j = min(fast, key=lambda j: self.mu[j])
                    self.slowed[j] = True
            if k == "edict" and self.rng.random() < self.cfg.p_edict_each:
                self._st("edict_each_hits_us")        # regla 6 PROPUESTA: edicto a cada oponente nos alcanza
                self.removal_on_us("edict")
            return True
        self.stats["rem_us"] = self.stats.get("rem_us", 0) + 1
        self.stats["rem_us_" + k] = self.stats.get("rem_us_" + k, 0) + 1
        self.execute_removal(act, val)
        return True

    def execute_removal(self, act, val):
        typ, obj = act
        if typ == "edict":
            self.removal_on_us("edict")
            return
        if val >= self.REM_THR and "Heroic Intervention" in self.hand and self.reserve >= 2:
            self.hand.remove("Heroic Intervention"); self.gy.append("Heroic Intervention")
            self.reserve -= 2; self.cast_stat("Heroic Intervention")
            self.stats["heroic_saves"] = self.stats.get("heroic_saves", 0) + 1
            return
        if typ in ("aura", "equip") and val >= 0.6 and self.art_on("Spellskite"):
            a = next(a for a in self.arts if a["name"] == "Spellskite")
            self.arts.remove(a); self.gy.append("Spellskite"); self.life -= 2
            self._st("spellskite_saves"); return
        if typ in ("aura", "equip") and val >= 0.6 and "Tamiyo's Safekeeping" in self.hand and self.reserve >= 1:
            self.hand.remove("Tamiyo's Safekeeping"); self.gy.append("Tamiyo's Safekeeping"); self.reserve -= 1
            self.cast_stat("Tamiyo's Safekeeping"); self._st("tamiyo_saves"); return
        if typ in ("aura", "equip") and val >= 0.6 and self.try_phase("removal"):
            return
        if typ == "cre":
            if obj in self.cres:
                self.cres.remove(obj)
                if not obj.token:
                    self.gy.append(obj.name)
            return
        if typ == "aura" and obj in self.auras:
            self.stats["attach_lost"] += 1
            self.auras.remove(obj); self.to_gy_aura(obj)
        elif typ == "equip" and obj in self.equips:
            self.stats["attach_lost"] += 1 if obj["on"] else 0
            self.equips.remove(obj); self.gy.append(obj["name"])
            if obj["on"] and obj["name"] == "Grafted Exoskeleton":
                self.blor_leaves("cmd", sac=True)
        elif typ == "art" and obj in self.arts:
            self.arts.remove(obj); self.gy.append(obj["name"])
        elif typ == "ench" and obj in self.enchs:
            self.enchs.remove(obj)
            if obj in C:
                self.gy.append(obj)
        self.log("v2 removal on", obj if isinstance(obj, str) else obj.get("name", obj) if isinstance(obj, dict) else obj)

    def rival_removal_phase(self, i):
        if self.hate_kills_blor(i):
            return
        while self.rem[i]:
            if not self.rival_uses_removal(i):
                break
            if self.rem[i] and self.rng.random() < 0.5:
                break

    def instant_response(self, w_before):
        """regla 4 (Juan): si un adjunto dispara el peso de Blor, un rival con remocion de permanentes o de
        artefactos/encantamientos responde al instante (p_instant). Devuelve True si respondio."""
        if not self.cfg.bracket or not self.blor or self._our is False:
            return False
        if self.flail_locks():                            # Conqueror's Flail: no pueden lanzar hechizos en tu turno
            self._st("flail_blocks_instant")
            return False
        if getattr(self, "_instant_used", False):
            return False
        holders = [i for i in self.alive() if any(k in ("any", "ae") for k in self.rem[i])]
        for i in holders:
            after = self.w_seen(i)
            if after >= self.REM_THR and (w_before.get(i, 0) < self.REM_THR or after - w_before.get(i, 0) >= 0.2):
                if self.rng.random() < self.cfg.p_instant:
                    self._instant_used = True
                    if self.rival_uses_removal(i, forced_us=True, kinds=("any", "ae")):
                        self.stats["instant"] = self.stats.get("instant", 0) + 1
                        return True
                return False
        return False

    def seen_all(self):
        return {i: (self.w_seen(i) or 0) for i in self.alive()}

    def opp_draws(self, i):
        """regla 3: el rival i roba al empezar su turno; guarda remocion, barridas y (el azul) counters"""
        c = self.cfg
        n = int(c.cpt) + (self.rng.random() < c.cpt - int(c.cpt))
        for _ in range(n):
            if self.rng.random() < c.rem / 99:
                k_ = self.rem_type(); self.rem[i].append(k_); self.stats["rem_drawn"] += 1
                if k_ == "edict": self._st("rem_drawn_edict")
            if self.rng.random() < c.wipes / 99:
                self.wipe_stock[i].append(self.wipe_type())
            if self.rng.random() < c.aem / 99:
                self.aem_stock[i].append(self.pick(c.aem_types)); self._st("aem_drawn")
            if c.hate and not self.hate_on[i] and self.rng.random() < c.hate / 99:
                self.hate_on[i] = True; self._st("hate_drawn")
            if i in self.blue and self.rng.random() < c.cnt / 99:
                self.cnt_stock[i] += 1

    def mz_events(self, i):
        """Mazmorra reglas 6-7: edicto de Sephiroth y Strip Mine en bucle de Tifa (desde T3)"""
        c = self.cfg
        if self.turn < 3:
            return
        if i == self.mz_edictor and self.rng.random() < c.mz_edict_p:
            self._st("mz_edict")
            b0 = self.blor is not None
            self.removal_on_us("edict")
            if b0 and not self.blor:
                self._st("mz_edict_blor")
        if i == self.mz_strip and self.lands and self.rng.random() < c.mz_strip_p:
            basics = [l for l in self.lands if LANDS[l["name"]].get("basic")]
            pool = sorted(basics or self.lands, key=lambda l: l.get("aura", 0))
            l = pool[0]
            self.lands.remove(l); self.gy.append(l["name"])
            self._st("mz_strip")

    def opp_turns(self):
        self._our = False
        for i in range(3):
            if self.won or self.lost:
                return
            if self.cfg.bracket and self.opp[i] > 0:
                self.opp_draws(i)
            if self.opp[i] > 0:
                self.burgeoning()
                self.tendershoot()
            if self.mode == "table" and self.opp[i] > 0:
                if self.cfg.mz:
                    self.mz_events(i)
                    if self.lost:
                        return
                self.table_events(i)

    def run(self, max_turns=20):
        while self.turn < max_turns and not self.won and not self.lost:
            self.our_turn()
            if self.won or self.lost:
                break
            self.opp_turns()
            if self.turn == 8 and not self.won and not self.lost:
                self.stats["t8"] = dict(power=self.power(False), blor=self.blor is not None,
                                        attached=len(self.attached()), lands=len(self.lands),
                                        hand=sum(1 for c in self.hand if not is_land(c)),
                                        cmd=sorted(self.cmd), kills=len(self.stats["kills"]), life=self.life)
        return self


def play(deck, seed, **kw):
    rng = random.Random(seed)
    g = Game(deck, rng, **kw)
    g.run()
    return g
