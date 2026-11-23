"""Mesa v2 para el simulador de Gorma (16/11/2026), portada de claude/simulador (Gandalf, 14/11).

Regla 1 ("rem"): pesos de amenaza por carta + remocion robada y guardada por cada rival.
- Cada rival ROBA remocion (5 de 99 cartas; 4 en B5): mano inicial de 7 y cpt cartas por turno.
- Tipos: solo criaturas / cualquier permanente / artefacto-encantamiento / edicto (cfg.rem_mix).
- La usa cuando algo de la mesa pesa >= 0,5 (>= 0,4 si guarda 2+), contra lo mas peligroso de TODA la mesa
  (softmax tau 0,3). Guarda la ultima el 40% de las veces (salvo bombas >= 0,8).
- Si bajas algo de peso >= 0,5, un rival con remocion que lo pueda tocar responde al instante el 50% de las veces.
- Archienemigo: +0,3 x fraccion de vida que ya les quitaste.
- Sin escalones: el peso de cada pieza es suyo; agregar piezas menores no cambia el de la mejor.
"""
import math

COMMANDER = "Gorma, the Gullet"

# Pesos de amenaza (propuesta del 15/11, por acordar con Juan). Escala de la mesa v2: el rival tipico de B3 llega a 0,6 en T5.
W = {}
for _n in ("Yawgmoth, Thran Physician", "Mazirek, Kraul Death Priest", "Jarad, Golgari Lich Lord", "Defiling Daemogoth",
           "Grave Pact", "Dictate of Erebos"):
    W[_n] = 0.6
for _n in ("Blood Artist", "Zulaport Cutthroat", "Cauldron of Essence", "Pitiless Plunderer", "Moldervine Reclamation",
           "Phyrexian Altar", "Ashnod's Altar", "Blasting Station", "Butcher of Malakir", "The Meathook Massacre",
           "Sephiroth, Fabled SOLDIER", "Ygra, Eater of All", "Witherbloom Apprentice"):
    W[_n] = 0.5
for _n in ("Viscera Seer", "Carrion Feeder", "Umbral Collar Zealot", "Yahenni, Undying Partisan", "Warren Soultrader",
           "Altar of Dementia", "Bastion of Remembrance", "Vengeful Bloodwitch", "Morbid Opportunist",
           "Dina, Essence Brewer", "Aerie Ouphes", "Puppeteer Clique", "Vengeance Mission", "Emeritus of Woe",
           "Fauna Shaman", "Veinwitch Coven", "Greater Good", "The Gitrog, Ravenous Ride", "Sylvan Library",
           "Walking Ballista"):
    W[_n] = 0.4
for _n in ("Putrid Goblin", "Rendclaw Trow", "Lesser Masticore", "Wingrattle Scarecrow", "Lingering Tormentor",
           "Woe Strider", "Bloodthrone Vampire", "Spawning Pit", "Feral Ghoul", "Jenova, Ancient Calamity",
           "Merchant of Venom", "Rampant Rejuvenator", "Priest of Forgotten Gods", "Wight of the Reliquary",
           "Selvala, Heart of the Wilds", "Pest Rescuer", "Blight Mound", "Jadar, Ghoulcaller of Nephalia",
           "Pawn of Ulamog", "Garruk's Uprising", "Foot Chopper", "Eccentric Pestfinder", "Fanatic of Rhonas",
           "Sol Ring", "Woodfall Primus", "Smothering Abomination"):
    W[_n] = 0.3
W_TOKEN = 0.05
W_DEFAULT = 0.2          # ramp, Haywire Mite, Fungus, Bloodghast, Gyre Sage y el resto

# Parámetros por bracket: fuente única en core/mesa.py (aquí solo se arman las tablas que usa Gorma)
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", ".."))
from core import mesa as M
_B = M.BRACKETS
OPP_CURVE = {b: v["curve"] for b, v in _B.items()}
STOCK = {b: (v["rem"], v["cpt"]) for b, v in _B.items()}
REM_THR, KEEP_LAST, TAU, ARCH, NOISE = M.REM_THR, M.KEEP_LAST, M.TAU, M.ARCH, M.NOISE
KINDS = ("cre", "any", "ae", "edict")
# Regla 2 ("cnt"): counters del jugador azul
CNT = {b: v["cnt"] for b, v in _B.items()}
CNT_UP = M.CNT_UP
COUNTER_BY_CMC, COUNTER_HI = M.COUNTER_BY_MV, M.COUNTER_HI
# Regla 3 ("wipe"): barridas robadas; barre si la mesa de los demas supera la suya por 1,5
WIPES = {b: v["wipes"] for b, v in _B.items()}
WIPE_MARGIN = M.WIPE_MARGIN
# Regla 4 ("clock"): turno tipico de cada rival; frenado, rearma 2 turnos y reintenta al 70%
MUS = {b: v["mus"] for b, v in _B.items()}
SPREAD, RETRY, P_REM_STOP = M.SPREAD, M.RETRY, M.P_REM_STOP
# Regla 6 ("hate"): odio a cementerio (prob., fraccion permanente) y a artefactos, con su ventana
HATE = {b: (v["gyh"], v["gyh_perm"], v["arth"], v["wipe_lo"], v["wipe_hi"]) for b, v in _B.items()}
# Regla 7 ("combat"): desde que turno atacan los rivales de combate
COMBAT_START = {b: v["combat_start"] for b, v in _B.items()}
# Regla 5 ("edict"): cada edicto de Butcher/Grave Pact/Dictate baja 0,03 la mejor pieza de cada rival (max 0,3; dura 2 turnos)
PACT_HIT = 0.03
# Mesa "Mazmorra" (core.mesa.MAZMORRA, receta única desde el 23/11: base B4 + lo observado)
MZ = "Mazmorra"
_Z = M.MAZMORRA
OPP_CURVE[MZ] = _Z["curve"]; STOCK[MZ] = (_Z["rem"], _Z["cpt"]); CNT[MZ] = _Z["cnt"]; WIPES[MZ] = _Z["wipes"]
MUS[MZ] = _Z["mus"]
HATE[MZ] = (_Z["gyh"], _Z["gyh_perm"], _Z["arth"], _Z["wipe_lo"], _Z["wipe_hi"]); COMBAT_START[MZ] = _Z["combat_start"]
MZ_SPREAD = _Z["spread"]
MZ_TURBO = (_Z["delay_turbo"], _Z["retry_turbo"])
MZ_REM_SLOWS = _Z["rem_slows"]
MZ_PARTIAL = _Z["p_partial"]
MZ_EDICT = _Z["edict"]
MZ_STRIP = _Z["strip"]
MZ_CUT = _Z["time_turns"]


class MesaV2:
    # ---------------- pesos ----------------
    def w_perm(self, p):
        if p.kind == "token":
            return W_TOKEN if p.creature else 0.0
        if p.name == COMMANDER:
            return min(0.3 + 0.05 * self.power(p), 0.9)
        return W.get(p.name, W_DEFAULT)

    def arch_bonus(self):
        lost = 1 - sum(max(x, 0) for x in self.opp) / 120
        return ARCH * lost

    def is_artifact(self, p):
        from cards import CARDS
        c = CARDS.get(p.name, {})
        return c.get("t") == "A" or "artifact" in c.get("tags", set())

    def legal(self, p, kind):
        if p.kind == "token" and not p.creature:
            return False                      # tesoros: nadie gasta remocion en eso
        if kind == "cre":
            return p.creature
        if kind == "ae":
            return (not p.creature) or self.is_artifact(p)
        return kind == "any"

    def best_ours(self, kind):
        c = [p for p in self.bf if self.legal(p, kind)]
        return max(c, key=self.w_perm) if c else None

    def us_value(self, kind):
        """(valor que la mesa ve en nosotros para esta remocion, objetivo)"""
        if kind == "edict":
            cres = self.creatures()
            if not cres:
                return None, None
            p = min(cres, key=self.w_perm)          # el edicto lo elegimos nosotros
            return self.w_perm(p) + self.arch_bonus(), p
        p = self.best_ours(kind)
        if p is None:
            return None, None
        return self.w_perm(p) + self.arch_bonus(), p

    def opp_best_value(self):
        v0, dv, vmax = OPP_CURVE[self.cfg.bracket]
        t = self.turn - self.opp_wiped_t
        mu = min(v0 + dv * t, vmax)
        if "edict" in self.cfg.rules:
            hits = sum(1 for x in getattr(self, "pact_t", []) if x >= self.turn - 1)
            mu -= min(0.3, PACT_HIT * hits)
        return max(0.0, self.rng.gauss(mu, NOISE))

    # ---------------- reservas ----------------
    def rem_type(self):
        r = self.rng.random(); acc = 0.0
        for k, m in zip(KINDS, self.cfg.rem_mix):
            acc += m
            if r < acc:
                return k
        return KINDS[-1]

    def v2_init(self):
        rem, _ = STOCK[self.cfg.bracket]
        self.blue = self.rng.randrange(3)
        self.cnt = [0, 0, 0]
        self.blue_open = False
        self.cnt_ready = 0
        b = self.cfg.bracket
        self.wipe_stock = [sum(self.rng.random() < WIPES[b] / 99 for _ in range(7)) if "wipe" in self.cfg.rules else 0
                           for _ in range(3)]
        if "clock" in self.cfg.rules:
            self.mu = list(MUS[b]); self.rng.shuffle(self.mu)
            self.ready = [1, 1, 1]; self.retry = [False] * 3
            self.rival_next = [999, 999, 999]
            # el azul es el rival de combo; los otros dos atacan
            self.kinds = ["combo" if i == self.blue else "combat" for i in range(3)]
        if "hate" in self.cfg.rules:
            gyh, gyp, arth, lo, hi = HATE[b]
            self.gyh_turn = self.rng.randint(lo - 1, hi + 1) if self.rng.random() < gyh else None
            self.gyh_perm = self.rng.random() < gyp
            self.arth_turn = self.rng.randint(lo - 1, hi + 1) if self.rng.random() < arth else None
        if "cnt" in self.cfg.rules:
            self.cnt[self.blue] = sum(self.rng.random() < CNT[self.cfg.bracket] / 99 for _ in range(7))
            self.stats["cnt_drawn"] = self.cnt[self.blue]
        self.rem = []
        for _ in range(3):
            n = sum(self.rng.random() < rem / 99 for _ in range(7))
            self.rem.append([self.rem_type() for _ in range(n)])
        self.stats["rem_drawn"] = sum(len(x) for x in self.rem)
        self.mz = b == MZ
        if self.mz:
            self.mz_init()

    def mz_init(self):
        cfg = self.cfg
        if cfg.mz_mus:
            self.mu = list(cfg.mz_mus); self.rng.shuffle(self.mu)
        self.turbo = min(range(3), key=lambda i: self.mu[i])
        self.slowed = [False] * 3
        self.edict_rival = None
        if self.rng.random() < cfg.mz_edict_p:
            self.edict_rival = self.rng.choice([i for i in range(3) if i != self.turbo])
        self.strip_rival = self.turbo if self.rng.random() < cfg.mz_strip_p else None
        r = self.rng.random(); acc = 0.0; self.cut_turn = MZ_CUT[-1][0]
        for t, p in MZ_CUT:
            acc += p
            if r < acc:
                self.cut_turn = t; break
        if not cfg.time_limit:
            self.cut_turn = None
        self.stats["mz_edict_table"] = int(self.edict_rival is not None)
        self.stats["mz_strip_table"] = int(self.strip_rival is not None)

    def v2_draws(self, i):
        rem, cpt = STOCK[self.cfg.bracket]
        n = int(cpt) + (self.rng.random() < cpt - int(cpt))
        for _ in range(n):
            if self.rng.random() < rem / 99:
                self.rem[i].append(self.rem_type())
                self.stats["rem_drawn"] = self.stats.get("rem_drawn", 0) + 1
            if "wipe" in self.cfg.rules and self.rng.random() < WIPES[self.cfg.bracket] / 99:
                self.wipe_stock[i] += 1
            if "cnt" in self.cfg.rules and i == self.blue and self.rng.random() < CNT[self.cfg.bracket] / 99:
                self.cnt[i] += 1
                self.stats["cnt_drawn"] = self.stats.get("cnt_drawn", 0) + 1

    # ---------------- decision estilo Forge ----------------
    def _engine_on_board(self):
        return any(self.w_perm(p) >= REM_THR for p in self.bf)

    def rival_decides(self, i):
        """el rival i elige (tipo, blanco) o None si se la guarda. blanco = ("us", perm) / ("opp", j)"""
        stock = self.rem[i]
        if not stock:
            return None
        thr = REM_THR if len(stock) == 1 else REM_THR - 0.1
        best_us = None
        for kind in dict.fromkeys(stock):
            v, p = self.us_value(kind)
            if v is not None and (best_us is None or v > best_us[0]):
                best_us = (v, kind, p)
        cands = []
        if best_us and best_us[0] >= thr:
            cands.append((best_us[0], best_us[1], ("us", best_us[2])))
        for j in self.alive():
            if j == i:
                continue
            o = self.opp_best_value()
            if o >= thr:
                kind = next((k for k in stock if k != "edict"), stock[0])
                cands.append((o, kind, ("opp", j)))
        if not cands:
            return None
        if len(stock) == 1 and max(c[0] for c in cands) < 0.8 and self.rng.random() < KEEP_LAST:
            return None                      # se la guarda por si alguien intenta ganar
        ws = [math.exp(c[0] / TAU) for c in cands]
        r = self.rng.random() * sum(ws)
        for c, w in zip(cands, ws):
            r -= w
            if r <= 0:
                return c[1], c[2]
        return cands[-1][1], cands[-1][2]

    def v2_removal_phase(self, i):
        self.v2_draws(i)
        while self.rem[i]:
            d = self.rival_decides(i)
            if d is None:
                break
            kind, (who, tgt) = d
            self.rem[i].remove(kind)
            eng = self._engine_on_board()
            self.stats["rem_used"] = self.stats.get("rem_used", 0) + 1
            if eng:
                self.stats["rem_used_eng"] = self.stats.get("rem_used_eng", 0) + 1
            if who == "us":
                if eng:
                    self.stats["rem_us_eng"] = self.stats.get("rem_us_eng", 0) + 1
                self.removal_on_us(kind, tgt)
            elif self.mz and self.rng.random() < MZ_REM_SLOWS:
                fast = [j for j in self.alive() if j != i]
                if fast:
                    f = min(fast, key=lambda j: self.mu[j]); self.slowed[f] = True
            elif kind == "edict" and self.rng.random() < self.cfg.p_edict_each:
                v, p = self.us_value("edict")
                if p is not None:
                    self.stats["edict_each_us"] = self.stats.get("edict_each_us", 0) + 1
                    self.removal_on_us("edict", p, count=False)
            if self.won or self.lost:
                return
            if self.rem[i] and self.rng.random() < 0.5:
                break                        # no siempre usa dos en el mismo turno

    def v2_instant(self, p):
        """bajamos algo de peso >= 0,5: un rival con remocion que lo toque responde al instante (p_inst)"""
        if self.inst_used or self.w_perm(p) < REM_THR or p not in self.bf:
            return
        holders = [(i, k) for i in self.alive() for k in dict.fromkeys(self.rem[i]) if k != "edict" and self.legal(p, k)]
        if not holders or self.rng.random() >= self.cfg.p_inst:
            return
        i, kind = holders[0]
        v = self.w_perm(p) + self.arch_bonus()
        if len(self.rem[i]) == 1 and v < 0.8 and self.rng.random() < KEEP_LAST:
            return
        self.inst_used = True
        self.rem[i].remove(kind)
        self.stats["rem_used"] = self.stats.get("rem_used", 0) + 1
        self.stats["rem_used_eng"] = self.stats.get("rem_used_eng", 0) + 1
        self.stats["rem_us_eng"] = self.stats.get("rem_us_eng", 0) + 1
        self.stats["rem_inst"] = self.stats.get("rem_inst", 0) + 1
        self.removal_on_us(kind, p)

    # ---------------- efecto sobre nosotros ----------------
    def stat_rem_us(self, p, kind="destroy"):
        self.stats["rem_us"] = self.stats.get("rem_us", 0) + 1
        nm = "Gorma" if p.name == COMMANDER else ("ficha" if p.kind == "token" else p.name)
        self.stats.setdefault("rem_names", {})
        self.stats["rem_names"][nm] = self.stats["rem_names"].get(nm, 0) + 1

    def _pay_prot(self, g, c):
        if self._our:
            if self.can_pay(g, c):
                return self.pay_now(g, c)
            return False
        if self.reserve >= g + c:
            self.reserve -= g + c
            return True
        return False

    def removal_on_us(self, kind, p, count=True):
        if p not in self.bf:
            return
        if count:
            self.stat_rem_us(p)
        if kind == "edict":
            self.stats["edict_us"] = self.stats.get("edict_us", 0) + 1
            self.log("edict: we sacrifice", p.name)
            self.sacrifice(p)
            return
        if p.creature:
            if self.on_bf("Dr. Joseph M'Benga") and p.name != "Dr. Joseph M'Benga" and p.counters > 0:
                self.stats["saved"] = self.stats.get("saved", 0) + 1
                return
            prot = next((x for x in ("Snakeskin Veil", "Tamiyo's Safekeeping") if x in self.hand), None)
            if prot and self._pay_prot(0, 1):
                self.hand.remove(prot); self.gy.append(prot)
                self.stats["saved"] = self.stats.get("saved", 0) + 1
                return
        if "Heroic Intervention" in self.hand and self._pay_prot(1, 1):
            self.hand.remove("Heroic Intervention"); self.gy.append("Heroic Intervention")
            self.stats["saved"] = self.stats.get("saved", 0) + 1
            self.stats["heroic_saves"] = self.stats.get("heroic_saves", 0) + 1
            return
        if "Veil of Summer" in self.hand and self.rng.random() < 0.4 and self._pay_prot(0, 1):
            self.hand.remove("Veil of Summer"); self.gy.append("Veil of Summer")
            self.stats["saved"] = self.stats.get("saved", 0) + 1
            return
        if p.name == "Yahenni, Undying Partisan" and self.pick_fodder():
            self.sacrifice(self.pick_fodder())
            self.stats["saved"] = self.stats.get("saved", 0) + 1
            return
        self.log("removal on", p.name, kind)
        self.destroy(p)

    # ---------------- regla 2: counters ----------------
    def attempt_p(self, t, mu):
        sp = MZ_SPREAD if getattr(self, "mz", False) else SPREAD
        return M.attempt_p(t, mu, sp)

    def v2_turn_start(self):
        """inicio de nuestro turno: quien intenta ganar en esta vuelta (regla 4) y el mana del azul (regla 2)"""
        if "clock" in self.cfg.rules:
            for i in range(3):
                self.rival_next[i] = 999
                if self.opp[i] > 0 and self.turn >= self.ready[i]:
                    rt = MZ_TURBO[1] if (getattr(self, "mz", False) and i == self.turbo) else RETRY
                    p = rt if self.retry[i] else self.attempt_p(self.turn, self.mu[i])
                    if self.rng.random() < p:
                        self.stats["att"] = self.stats.get("att", 0) + 1
                        if getattr(self, "mz", False) and self.slowed[i]:
                            self.slowed[i] = False          # la remocion de otro rival le tumbo este intento
                            self.stats["others_stop"] = self.stats.get("others_stop", 0) + 1
                            self.stats["mz_slowed"] = self.stats.get("mz_slowed", 0) + 1
                            self.rival_rearms(i)
                            continue
                        self.rival_next[i] = self.turn
                        if self.turn <= 4 and "first_att" not in self.stats:
                            self.stats["first_att"] = self.turn
                        self.stats.setdefault("first_att_any", self.turn)
        if "cnt" not in self.cfg.rules:
            return
        self.blue_open = self.opp[self.blue] > 0 and self.rng.random() < CNT_UP
        self.cnt_ready = self.cnt[self.blue] if self.blue_open else 0

    def roles_after(self, c=None):
        """que roles del combo quedan cubiertos en mesa si resolviera c"""
        from engine import PERSIST_LOOP, OUTLETS, DRAINERS, ENABLERS
        names = {p.name for p in self.bf} | ({c} if c else set())
        en = COMMANDER in names or any(x in names for x in ENABLERS)
        pe = any(x in names for x in PERSIST_LOOP)
        ou = any(x in names for x in OUTLETS) or ("Aerie Ouphes" in names and self.has_rival_flyer)
        cl = any(x in names for x in DRAINERS) or "Altar of Dementia" in names or "Jarad, Golgari Lich Lord" in names \
            or "Walking Ballista" in names
        return en, pe, ou, cl

    def completes_combo(self, c):
        """c es la pieza que deja el combo listo (los 4 roles en mesa y antes faltaba uno): un cierre"""
        return all(self.roles_after(c)) and not all(self.roles_after())

    def spell_threat(self, c):
        if c == COMMANDER:
            g = self.gorma()
            return 0.35
        return W.get(c, W_DEFAULT)

    def is_key(self, c):
        return self.spell_threat(c) >= REM_THR or self.completes_combo(c)

    def counter_p(self, c):
        from cards import CARDS
        if self.is_key(c):
            return 1.0
        if c in CARDS and CARDS[c]["t"] == "L":
            return 0.0
        g, p = CARDS[c]["cost"]
        if c == COMMANDER:
            g += self.tax
        return COUNTER_BY_CMC.get(g + p, COUNTER_HI)

    def counter_try(self, c, win=False):
        """el azul decide si contrarresta c (lanzado en nuestro turno). True = contrarrestado"""
        if self.cnt_ready <= 0:
            return False
        if self.on_bf("Allosaurus Shepherd") and c in __import__("cards").GREEN:
            return False                          # los hechizos verdes no se pueden contrarrestar
        if self.on_bf("Defense Grid") and self.rng.random() < 0.7:
            return False                          # +{3} fuera de su turno: casi nunca le alcanza
        key = win or self.is_key(c)
        if self.cnt[self.blue] == 1 and not win and self.rng.random() < KEEP_LAST:
            return False                          # guarda su ultimo counter para frenar una victoria
        if not win and self.rng.random() >= self.counter_p(c):
            return False
        if key and "Veil of Summer" in self.hand and self.can_pay(0, 1):
            self.pay_now(0, 1); self.hand.remove("Veil of Summer"); self.gy.append("Veil of Summer")
            self.stats["veil_saves"] = self.stats.get("veil_saves", 0) + 1
            return False
        self.cnt[self.blue] -= 1; self.cnt_ready -= 1
        self.stats["cnt_used"] = self.stats.get("cnt_used", 0) + 1
        k = "cnt_combo" if win else "cnt_dev"
        self.stats[k] = self.stats.get(k, 0) + 1
        nm = "Gorma" if c == COMMANDER else c
        self.stats.setdefault("cnt_names", {})
        self.stats["cnt_names"][nm] = self.stats["cnt_names"].get(nm, 0) + 1
        self.log("COUNTERED", c)
        return True

    # ---------------- regla 3: barridas ----------------
    def board_value(self):
        return sum(self.w_perm(p) for p in self.bf if p.creature)

    def v2_wipe_check(self, i):
        if self.wipe_stock[i] <= 0 or self.turn < 3 or getattr(self, "_wipe_round", None) == self.turn:
            return
        others = sum(self.opp_best_value() * 1.5 for j in self.alive() if j != i)
        own = self.opp_best_value() * 1.5
        if self.board_value() + others < own + WIPE_MARGIN:
            return
        self.wipe_stock[i] -= 1
        self._wipe_round = self.turn
        self.opp_wiped_t = self.turn
        self.stats["wipes"] = self.stats.get("wipes", 0) + 1
        self.stats.setdefault("wipe_turns", []).append(self.turn)
        if "Heroic Intervention" in self.hand and self._pay_prot(1, 1):
            self.hand.remove("Heroic Intervention"); self.gy.append("Heroic Intervention")
            self.stats["wipe_saved"] = self.stats.get("wipe_saved", 0) + 1
            return
        if "Golgari Charm" in self.hand and self.rng.random() < 0.7 and self._pay_prot(0, 2):
            self.hand.remove("Golgari Charm"); self.gy.append("Golgari Charm")
            self.stats["wipe_saved"] = self.stats.get("wipe_saved", 0) + 1
            return
        lost = [p for p in self.bf if p.creature and p.kind == "card"]
        self.stats["wipe_cards"] = self.stats.get("wipe_cards", 0) + len(lost)
        self.log("WIPE by rival", i)
        was = self._our; self._our = False
        yah = next((q for q in self.bf if q.name == "Yahenni, Undying Partisan"), None)
        for p in [q for q in self.bf if q.creature and q is not yah]:
            self.destroy(p)
        if yah and not self.creatures_except(yah):
            self.destroy(yah)
        self._our = was

    # ---------------- regla 4: frenos entre rivales ----------------
    def v2_others_stop(self, i):
        """antes que tus respuestas, los otros rivales frenan el intento de i con lo que guardaron (el azul primero)"""
        oth = [j for j in self.alive() if j != i]
        self.rng.shuffle(oth)
        oth.sort(key=lambda j: j != self.blue)
        for j in oth:
            if j == self.blue and self.cnt[j] > 0 and self.rng.random() < CNT_UP:
                self.cnt[j] -= 1
                self.stats["others_stop_cnt"] = self.stats.get("others_stop_cnt", 0) + 1
                return True
            if self.rem[j] and self.rng.random() < P_REM_STOP:
                k = next((x for x in self.rem[j] if x != "edict"), self.rem[j][0])
                self.rem[j].remove(k)
                self.stats["others_stop_rem"] = self.stats.get("others_stop_rem", 0) + 1
                return True
        return False

    def rival_rearms(self, i):
        d = MZ_TURBO[0] if (getattr(self, "mz", False) and i == self.turbo) else self.cfg.delay
        self.ready[i] = self.turn + d
        self.retry[i] = True
        self.rival_next[i] = 999

    # ---------------- regla 6: odio ----------------
    def v2_hate(self):
        if getattr(self, "_hate_t", None) == self.turn:
            return
        self._hate_t = self.turn
        if self.turn == self.gyh_turn:
            self.stats["gy_hate"] = 1
            self.gy = []
            if self.gyh_perm:
                self.gy_locked = True
                self.stats["gy_lock"] = 1
            self.log("GRAVEYARD HATE", "permanent" if self.gyh_perm else "")
        if self.turn == self.arth_turn:
            arts = [p for p in self.bf if p.kind == "card" and self.is_artifact(p)]
            if arts and "Heroic Intervention" in self.hand and self._pay_prot(1, 1):
                self.hand.remove("Heroic Intervention"); self.gy.append("Heroic Intervention")
                return
            self.stats["art_hate"] = len(arts)
            was = self._our; self._our = False
            for p in arts:
                self.destroy(p)
            self._our = was
            self.log("ARTIFACT HATE", [p.name for p in arts])

    def answer_gy_lock(self):
        """en nuestro turno: quitar el Rest in Peace rival con una respuesta a artefacto/encantamiento"""
        if not getattr(self, "gy_locked", False):
            return
        for ans in self.threat_answers("ae", instant_only=False):
            if self.avail() >= ans[0]:
                if ans[0] > 0:
                    self.pay_now(ans[0], 0)
                cost, where, ref = ans
                if where == "hand":
                    self.hand.remove(ref); self.gy.append(ref)
                else:
                    self.sacrifice(ref)
                self.gy_locked = False
                self.stats["gy_lock_answered"] = 1
                return

    # ---------------- regla 7: combate sin escalon ----------------
    def v2_combat(self, i):
        b = self.cfg.bracket
        kinds = getattr(self, "kinds", None) or self.cfg.kinds
        if not kinds or kinds[i] != "combat" or self.opp[i] <= 0:
            return
        t_eff = self.turn - self.opp_wiped_t if self.opp_wiped_t else self.turn
        start = COMBAT_START[b]
        if t_eff < start:
            return
        # atacan a lo mas peligroso de la mesa (mismo criterio que la remocion)
        best = self.best_ours("any")
        us = (self.w_perm(best) if best else 0.1) + self.arch_bonus()
        cands = [("us", us)] + [("opp", self.opp_best_value()) for j in self.alive() if j != i]
        ws = [math.exp(x / TAU) for _, x in cands]
        r = self.rng.random() * sum(ws)
        who = cands[-1][0]
        for (w, _), x in zip(cands, ws):
            r -= x
            if r <= 0:
                who = w; break
        if who != "us":
            return
        self.stats["attacked"] = self.stats.get("attacked", 0) + 1
        self._combat_hit(i, int(round(self.cfg.combat_k * (t_eff - start + 1))))

    # ---------------- Mazmorra ----------------
    def mz_events(self, i):
        """reglas 6-7: el rival de edictos y el Strip Mine en bucle actuan en su turno, desde el T3"""
        if self.turn < 3 or self.opp[i] <= 0:
            return
        if i == self.edict_rival and self.rng.random() < MZ_EDICT[1]:
            cres = self.creatures()
            if cres:
                p = min(cres, key=self.w_perm)
                self.stats["mz_edicts"] = self.stats.get("mz_edicts", 0) + 1
                if p.name == COMMANDER:
                    self.stats["mz_edict_gorma"] = self.stats.get("mz_edict_gorma", 0) + 1
                self.removal_on_us("edict", p, count=False)
        if i == self.strip_rival and self.rng.random() < MZ_STRIP[1] and self.lands:
            basics = [l for l in self.lands if l in ("Forest", "Swamp")]
            l = basics[-1] if basics else self.lands[-1]
            self.lands.remove(l); self.gy.append(l)
            self.stats["mz_strip"] = self.stats.get("mz_strip", 0) + 1

    def mz_partial(self, i):
        """regla 5: un intento que nadie freno mata solo a un jugador al azar el 40% de las veces. True = sigues vivo"""
        if self.rng.random() >= MZ_PARTIAL:
            return False
        vict = ["us"] + [j for j in self.alive() if j != i]
        v = self.rng.choice(vict)
        self.stats["mz_partial"] = self.stats.get("mz_partial", 0) + 1
        if v == "us":
            self.stats["mz_partial_us"] = 1
            return False
        self.opp[v] = 0
        self.stats["mz_partial_kill"] = self.stats.get("mz_partial_kill", 0) + 1
        self.ready[i] = self.turn + 1; self.retry[i] = True; self.rival_next[i] = 999
        return True

    def mz_time(self):
        """regla 8: al final de la vuelta del corte gana el de mas vida"""
        al = self.alive()
        me = self.life if not self.cfg.time_life else self.rng.uniform(*self.cfg.time_life)
        rivals = [self.opp[i] - self.rng.uniform(0, 15) for i in al]
        self.stats["time_cut"] = 1
        self.stats["life_at_cut"] = self.life
        if not rivals or me > max(rivals):
            self.won = True; self.win_turn = self.turn; self.stats["time_win"] = 1
        else:
            self.lost = True; self.stats["time_loss"] = 1
