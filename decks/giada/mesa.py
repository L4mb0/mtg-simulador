"""Mesa v2 para Giada (16/11/2026): estructura de la sección 13 de simulador-montecarlo.md (la de Gandalf y Blor).

Solo se activa con cfg.bracket (\"B1\"..\"B5\", \"B3+B4\"). Las mesas viejas (Realista, Optimista...) no consumen azar nuevo
y dan exactamente las mismas partidas que antes.

Reglas (aprobadas por Juan el 16/11, una tabla en la respuesta del chat):
 1  Pesos de amenaza por carta (escala v2: 0,6 motor que hay que matar, 1,0 bomba) + tamaño (0,2 + poder/15), sin escalones.
 2  Atención: +0,3 x fracción de la vida rival que ya quitaste (archienemigo); no hay \"te apuntan 25%/75%\".
 3  Reservas: cada rival roba y guarda remoción (5/99), barridas (2/99) y odio masivo a artefactos/encantamientos;
    el azul, counters (3/3/5/7/10).
 4  Remoción: a lo más peligroso de toda la mesa (umbral 0,5; 0,4 con 2+), guarda la última el 40% salvo bombas,
    respuesta al instante (50%) cuando bajas algo de peso >= 0,5.
 5  Tipos: destruir criatura, exiliar criatura, cualquier permanente, artefacto/encantamiento, edicto.
 6  Barridas tipadas; el rival barre si lo tuyo + lo de los otros supera lo suyo por 1,5 y elige la que más te quita.
 7  Counters por hechizo: siempre a motores y cierres (peso >= 0,5), el resto por costo; guarda el último.
 8  Relojes logísticos por bracket con tipos de victoria (Playgroup).
 9  Frenos entre rivales antes que tus respuestas.
 10 Herald of Eternal Dawn: mientras está en mesa nadie gana (los rivales la quitan: pesa 1,0).
 11 Odio masivo a artefactos y encantamientos.
 12 Combate rival: a quién ataca sale de tu poder aéreo de forma continua (sin el escalón de 15 de poder).
"""
import math
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", ".."))
from core import mesa as M

# ---- regla 1: pesos (propuestos el 16/11; Juan pre-aprobó) ----
W_CARD = {
    "Giada, Font of Hope": 0.35, "Lyra Dawnbringer": 0.6, "Court of Grace": 0.6,
    "Herald's Horn": 0.3, "Starnheim Aspirant": 0.3, "Urza's Incubator": 0.4, "Pearl Medallion": 0.2,
    "Thraben Watcher": 0.4, "Always Watching": 0.4, "Angelic Field Marshal": 0.4,
    "Vanquisher's Banner": 0.3, "Patchwork Banner": 0.3, "Heraldic Banner": 0.2,
    "Lyra, Archangel of Dawn": 0.5, "Resplendent Angel": 0.5, "Valkyrie Harbinger": 0.5, "Exemplar of Light": 0.4,
    "Norn's Choirmaster": 0.5, "Youthful Valkyrie": 0.3, "Firemane Commando": 0.4,
    "Sephara, Sky's Blade": 0.7, "Avacyn, Angel of Hope": 1.0, "Herald of Eternal Dawn": 1.0,
    "Archangel of Thune": 0.5, "Angelic Destiny": 0.4, "Leader's Talent": 0.3, "Herald of the Host": 0.4,
    "Ob Nixilis, the Ascended": 0.4, "Bishop of Wings": 0.3, "Archangel of Tithes": 0.4, "Reya Dawnbringer": 0.5,
    "Linvala, the Preserver": 0.3, "Smothering Tithe": 0.5, "Tome of Legends": 0.2,
    "Swiftfoot Boots": 0.1, "Lightning Greaves": 0.1, "Grasp of Fate": 0.1, "Search the Premises": 0.2,
}
W_ROCK = 0.1
W_NONCRE = 0.15
CLOSERS = {"Felidar Sovereign", "Emeria's Call", "Akroma's Will", "Avacyn, Angel of Hope", "Sephara, Sky's Blade",
           "Starnheim Unleashed"}
REM_THR, KEEP_LAST, TAU, P_REM_STOP = M.REM_THR, M.KEEP_LAST, M.TAU, M.P_REM_STOP
CNT_BY_CMC, CNT_HI = M.COUNTER_BY_MV, M.COUNTER_HI
MU_SHIFT = {"combat": 0.4, "dmg": -0.5, "loss": -0.5, "combo": -1.5}
MINUS_X = 5            # -X/-X típico (Toxic Deluge, Crux of Fate no): mata resistencia <= 5


pick = M.pick


class MesaV2:
    # ------------------------------------------------------------ init
    def v2_init(self):
        c, rng = self.cfg, self.rng
        self.rem = [[pick(rng, c.rem_types) for _ in range(7) if rng.random() < c.rem / 99] for _ in range(3)]
        self.wipe_stock = [[pick(rng, c.wipe_types) for _ in range(7) if rng.random() < c.wipes / 99] for _ in range(3)]
        self.aem_stock = [[pick(rng, c.aem_types) for _ in range(7) if rng.random() < c.aem / 99] for _ in range(3)]
        self.blue = rng.sample(range(3), c.n_blue)
        self.cnt_stock = [sum(rng.random() < c.cnt / 99 for _ in range(7)) if i in self.blue else 0 for i in range(3)]
        self.wtype = [pick(rng, c.win_blue if (i in self.blue and c.win_blue) else self.win_other()) for i in range(3)]
        avg = sum(p * MU_SHIFT[k] for k, p in c.win_types)
        self.mu = [m + MU_SHIFT[w] - avg for m, w in zip(c.mus, self.wtype)]
        self.ready_t = [None, None, None]
        self.rival_next = [-1, -1, -1]
        self.opp_wiped_t = 0
        self._cnt_up = {}
        self._instant_used = False
        for k in ("rem_drawn", "rem_us", "rem_opp", "rem_giada", "wipes", "wipe_saved", "cnt_us", "att",
                  "others_stop", "we_stop", "herald_stop", "aem", "instant", "edict_us"):
            self.stats[k] = 0
        self.stats["rem_drawn"] = sum(len(x) for x in self.rem)
        self.stats["rem_tgt"] = {}
        self.stats["wipe_t"] = []
        self.stats["cnt_on"] = {}

    def win_other(self):
        c = self.cfg
        if not c.win_blue:
            return c.win_types
        nb = len(self.blue)
        blue = dict(c.win_blue)
        out = tuple((k, max(0.0, (3 * p - nb * blue.get(k, 0.0)) / (3 - nb))) for k, p in c.win_types)
        s = sum(p for _, p in out)
        return tuple((k, p / s) for k, p in out)

    def is_combat_rival(self, i):
        if self.cfg.bracket:
            return self.wtype[i] == "combat"
        return bool(self.cfg.kinds) and self.cfg.kinds[i] == "combat"

    def _st(self, k, n=1):
        self.stats[k] = self.stats.get(k, 0) + n

    # ------------------------------------------------------------ regla 1: pesos
    def w_perm(self, p):
        n = p.name
        if p.creature:
            size = self.power(p) / 15 + (0.0 if p.token else 0.2)
            if n == "Giada, Font of Hope":
                # motor: pesa mas cuantos mas angeles hay (cada uno que entra trae mas contadores); sola es un 2/2
                angels = sum(1 for q in self.creatures() if q.angel and q is not p)
                role = min(0.65, 0.35 + 0.03 * angels)
            elif n == "Righteous Valkyrie":
                role = 0.5 + 0.2 * min(1.0, max(0.0, (self.life - 40) / 7))
            elif n == "Felidar Sovereign":
                role = 1.0 if self.life >= 40 else 0.5
            elif n == "Herald of War":
                role = 0.4 + 0.05 * p.counters
            else:
                role = W_CARD.get(n, 0.0)
            w = max(role, size)
            if p.destiny:
                w += 0.2
            return min(1.2, w)
        if n in W_CARD:
            return W_CARD[n]
        from cards import CARDS
        return W_ROCK if CARDS.get(n, {}).get("rock") else W_NONCRE

    def w_spell(self, c):
        """peso de lo que hace un hechizo al resolverse (para counters)"""
        from cards import CARDS
        if c in CLOSERS:
            return 1.0
        if c in W_CARD:
            return W_CARD[c]
        info = CARDS[c]
        if info["t"] == "C":
            pw = info["p"] + (sum(1 for q in self.creatures() if q.angel) if info.get("angel") and self.giada() else 0)
            return 0.2 + pw / 15
        return W_ROCK if info.get("rock") else W_NONCRE

    def arch(self):
        lost = 1 - sum(max(x, 0) for x in self.opp) / 120
        return self.cfg.w_arch * lost

    def opp_best_value(self):
        v0, dv, vmax = self.cfg.opp_curve
        t = self.turn - self.opp_wiped_t
        return max(0.0, self.rng.gauss(min(v0 + dv * t, vmax), self.cfg.opp_noise))

    def targetable(self, p):
        return not (p.name == "Giada, Font of Hope" and p.boots)

    # ------------------------------------------------------------ regla 3: robo de los rivales
    def opp_draws(self, i):
        c = self.cfg
        n = int(c.cpt) + (self.rng.random() < c.cpt - int(c.cpt))
        for _ in range(n):
            if self.rng.random() < c.rem / 99:
                self.rem[i].append(pick(self.rng, c.rem_types)); self.stats["rem_drawn"] += 1
            if self.rng.random() < c.wipes / 99:
                self.wipe_stock[i].append(pick(self.rng, c.wipe_types))
            if self.rng.random() < c.aem / 99:
                self.aem_stock[i].append(pick(self.rng, c.aem_types))
            if i in self.blue and self.rng.random() < c.cnt / 99:
                self.cnt_stock[i] += 1

    # ------------------------------------------------------------ regla 4/5: remoción
    def kills(self, kind, p):
        """la remoción de este tipo saca a p? (indestructible frena las de destruir)"""
        if not self.targetable(p):
            return False
        destroy = kind in ("cre", "any", "ae")
        if destroy and self.indestructible(p):
            return False
        if kind in ("cre", "cre_x"):
            return p.creature
        if kind == "ae":
            return not p.creature
        return True          # any

    def our_target(self, kind):
        if kind == "edict":
            cs = self.creatures()
            if not cs:
                return None
            v = min(self.w_perm(p) for p in cs)      # sacrificamos la que menos vale
            return (v + self.arch(), None)
        best = None
        for p in self.bf:
            if p.name in ("Blank",) or not self.kills(kind, p):
                continue
            w = self.w_perm(p)
            if best is None or w > best[0]:
                best = (w, p)
        if best is None:
            return None
        return (best[0] + self.arch(), best[1])

    def rival_uses_removal(self, i, forced_us=False, kinds=None):
        stock = self.rem[i]
        if not stock:
            return False
        thr = REM_THR if len(stock) == 1 else REM_THR - 0.1
        cands = []
        for k in sorted(set(stock)):
            if kinds and k not in kinds:
                continue
            t = self.our_target(k)
            if t and t[0] >= thr:
                cands.append(("us", t[0], k, t[1]))
        if not forced_us:
            for j in self.alive():
                if j != i:
                    o = self.opp_best_value()
                    if o >= thr:
                        cands.append(("opp", o, max(sorted(set(stock)), key=lambda k: (k != "edict", k)), None))
        if not cands:
            return False
        if len(stock) == 1 and max(c[1] for c in cands) < 0.8 and self.rng.random() < KEEP_LAST:
            return False
        ws = [math.exp(c[1] / TAU) for c in cands]
        r = self.rng.random() * sum(ws)
        for c, w in zip(cands, ws):
            r -= w
            if r <= 0:
                break
        who, val, k, tgt = c
        stock.remove(k)
        if who == "opp":
            self._st("rem_opp")
            if k == "edict" and self.rng.random() < self.cfg.p_edict_each:
                self.do_edict()
            return True
        self._st("rem_us")
        if k == "edict":
            self.do_edict()
        else:
            self.do_removal(k, tgt, val)
        return True

    def do_edict(self):
        cs = self.creatures()
        if not cs:
            return
        self._st("edict_us")
        p = min(cs, key=lambda q: (self.w_perm(q), self.power(q)))
        self.destroy(p)
        self.stats["rem_tgt"]["(edicto) " + ("ficha" if p.token else p.name)] = \
            self.stats["rem_tgt"].get("(edicto) " + ("ficha" if p.token else p.name), 0) + 1

    def do_removal(self, kind, p, val):
        if p not in self.bf:
            return
        destroy = kind in ("cre", "any", "ae")
        if p.creature and destroy:
            if "Valorous Stance" in self.hand and self.reserve >= 2:
                self.hand.remove("Valorous Stance"); self.gy.append("Valorous Stance"); self.reserve -= 2
                self.stats["cast"]["Valorous Stance"] = self.stats["cast"].get("Valorous Stance", 0) + 1
                self._st("saved_stance")
                return
            if "Flawless Maneuver" in self.hand and self.giada() and val >= 0.8 + self.arch():
                self.hand.remove("Flawless Maneuver"); self.gy.append("Flawless Maneuver")
                self.stats["cast"]["Flawless Maneuver"] = self.stats["cast"].get("Flawless Maneuver", 0) + 1
                self._st("saved_flawless_rem")
                return
        nm = "ficha" if p.token else p.name
        self.stats["rem_tgt"][nm] = self.stats["rem_tgt"].get(nm, 0) + 1
        if p.name == "Giada, Font of Hope":
            self._st("rem_giada")
        self.log("v2 removal on", p.name, kind)
        self.destroy(p, exile=(kind == "cre_x"))

    def rival_removal_phase(self, i):
        while self.rem[i]:
            if not self.rival_uses_removal(i):
                break
            if self.rem[i] and self.rng.random() < 0.5:
                break

    def instant_response(self, p):
        """regla 4: bajas algo de peso >= 0,5 -> un rival con remoción que lo alcanza responde al instante (50%)"""
        if not self.cfg.bracket or self._instant_used or not self._our or p not in self.bf:
            return
        if self.w_perm(p) < REM_THR:
            return
        for i in self.alive():
            ks = [k for k in self.rem[i] if k != "edict" and self.kills(k, p)]
            if not ks:
                continue
            self._instant_used = True
            if self.rng.random() < self.cfg.p_instant:
                self.rem[i].remove(ks[0])
                self._st("instant"); self._st("rem_us")
                self.do_removal(ks[0], p, self.w_perm(p) + self.arch())
            return

    # ------------------------------------------------------------ regla 6: barridas
    def wipe_hits(self, sub):
        """(criaturas que mueren o se van, permanentes no criatura que se van)"""
        av = self.on_bf("Avacyn, Angel of Hope")
        cre, other = [], []
        for p in self.bf:
            if p.creature:
                if sub in ("destroy", "destroy_ae"):
                    if not self.indestructible(p) and not av:
                        cre.append(p)
                elif sub == "minus":
                    if self.tough(p) <= MINUS_X:
                        cre.append(p)
                else:
                    cre.append(p)
            else:
                if sub == "destroy_ae" and not av:
                    other.append(p)
                elif sub in ("exile_ae", "rift"):
                    other.append(p)
        return cre, other

    def wipe_value_us(self, sub):
        cre, other = self.wipe_hits(sub)
        v = sum(self.w_perm(p) for p in cre) + sum(self.w_perm(p) for p in other) * (0.5 if sub == "rift" else 1.0)
        if sub in ("bounce", "rift"):
            v -= 0.5 * sum(self.w_perm(p) for p in cre if not p.token)     # las cartas vuelven a la mano
        return max(0.0, v + (self.arch() if cre else 0.0))

    def rival_wipes(self, i):
        stock = self.wipe_stock[i]
        if not stock or self.turn < 3:
            return False
        sub = max(sorted(set(stock)), key=self.wipe_value_us)
        us = self.wipe_value_us(sub)
        others = sum(self.opp_best_value() * 1.5 for j in self.alive() if j != i)
        own = self.opp_best_value() * 1.5
        if us + others < own + self.cfg.wipe_margin:
            return False
        stock.remove(sub)
        self._st("wipes"); self.stats["wipe_t"].append(self.turn)
        self.opp_wiped_t = self.turn
        for j in self.alive():
            self.board_reset[j] = self.turn
            self.air[j] = 0
        if sub in ("destroy", "destroy_ae") and "Flawless Maneuver" in self.hand and self.giada():
            self.hand.remove("Flawless Maneuver"); self.gy.append("Flawless Maneuver")
            self.stats["cast"]["Flawless Maneuver"] = self.stats["cast"].get("Flawless Maneuver", 0) + 1
            self._st("wipe_saved")
            if sub == "destroy_ae":
                for p in self.wipe_hits(sub)[1]:
                    self.destroy(p)
            self.log("Flawless Maneuver saves the board from", sub)
            return True
        cre, other = self.wipe_hits(sub)
        self.log("RIVAL WIPE", sub, len(cre), "creatures")
        for p in cre:
            if p not in self.bf:
                continue
            if sub in ("bounce", "rift"):
                self.bf.remove(p); self.leaves(p)
                if p.name == "Giada, Font of Hope":
                    self.g_in_cmd = True
                elif not p.token:
                    self.hand.append(p.name)
                if p.destiny:
                    self.hand.append("Angelic Destiny")
                    for q in list(self.bf):
                        if q.name == "Angelic Destiny":
                            self.bf.remove(q)
            else:
                self.destroy(p, exile=sub.startswith("exile"))
        for p in other:
            if p in self.bf:
                if sub == "rift":
                    self.bf.remove(p); self.hand.append(p.name)
                else:
                    self.destroy(p, exile=sub == "exile_ae")
        return True

    # ------------------------------------------------------------ regla 11: odio masivo a artefactos/encantamientos
    AEM_OWN = {"art": 0.0, "both": 0.2, "ench": 0.2}

    def aem_hits(self, t):
        from cards import CARDS
        out = []
        for p in self.bf:
            if p.creature:
                if CARDS.get(p.name, {}).get("artifact") and t in ("art", "both"):
                    out.append(p)
                continue
            typ = CARDS.get(p.name, {}).get("t")
            if (typ == "A" and t in ("art", "both")) or (typ == "E" and t in ("ench", "both")):
                out.append(p)
        return out

    def rival_aem(self, i):
        stock = self.aem_stock[i]
        if not stock or self.turn < 3:
            return False
        t = max(sorted(set(stock)), key=lambda k: sum(self.w_perm(p) for p in self.aem_hits(k)) - self.AEM_OWN[k])
        hits = self.aem_hits(t)
        v = sum(self.w_perm(p) for p in hits)
        if v < REM_THR + self.AEM_OWN[t]:
            return False
        stock.remove(t)
        self._st("aem")
        for p in hits:
            self.destroy(p)
        return True

    # ------------------------------------------------------------ regla 7: counters
    def countered_v2(self, c):
        for i in self.blue:
            if self.opp[i] <= 0 or self.cnt_stock[i] <= 0:
                continue
            if i not in self._cnt_up:
                self._cnt_up[i] = self.rng.random() < self.cfg.cnt_up
            if not self._cnt_up[i]:
                continue
            v = self.w_spell(c)
            key = v >= REM_THR
            from cards import CARDS
            cmc = sum(self.cost_of(c)) if c in CARDS else 3
            p = 1.0 if key else CNT_BY_CMC.get(cmc, CNT_HI)
            if self.rng.random() >= p:
                continue
            if self.cnt_stock[i] == 1 and v < 0.8 and self.rng.random() < KEEP_LAST:
                continue
            self.cnt_stock[i] -= 1
            self._cnt_up[i] = False
            self._st("cnt_us")
            self.stats["cnt_on"][c] = self.stats["cnt_on"].get(c, 0) + 1
            self.log("COUNTERED", c)
            return True
        return False

    # ------------------------------------------------------------ regla 8/9: relojes y frenos
    _F = staticmethod(M.F)

    def attempt_p(self, t, mu):
        return M.attempt_p(t, mu, self.cfg.spread)

    def roll_attempts(self):
        for i in range(3):
            if self.opp[i] <= 0:
                continue
            if self.ready_t[i] is None:
                p = self.attempt_p(self.turn, self.mu[i])
            elif self.turn >= self.ready_t[i]:
                p = self.cfg.retry
            else:
                p = 0.0
            self.rival_next[i] = self.turn if self.rng.random() < p else -1

    def roll_threat_v2(self, i):
        wt = self.wtype[i]
        r = self.rng.random()
        kind = "cre" if wt == "combat" else ("ae" if r < 0.5 else "other")
        self.threat[i] = dict(kind=kind, stoppable=self.rng.random() < self.cfg.p_stoppable,
                              visible=self.rng.random() < self.cfg.p_visible, stopped=False, t=self.turn, wtype=wt)

    def others_stop(self, i):
        oth = [j for j in self.alive() if j != i]
        oth = sorted(self.rng.sample(oth, len(oth)), key=lambda j: j not in self.blue)
        for j in oth:
            if self.rem[j] and self.rng.random() < P_REM_STOP:
                self.rem[j].pop(self.rng.randrange(len(self.rem[j])))
                self._st("others_stop")
                return True
            if j in self.blue and self.cnt_stock[j] > 0 and self.rng.random() < self.cfg.cnt_up:
                self.cnt_stock[j] -= 1
                self._st("others_stop")
                return True
        return False

    # ------------------------------------------------------------ regla 12: a quién ataca el combate rival
    def p_us_combat(self):
        air = sum(self.power(p) for p in self.creatures() if self.has_kw(p, "flying"))
        return 0.25 + 0.5 * min(1.0, air / 30)
