"""Mesa v2 para Blight Curse (16/11/2026), con la estructura de la sección 13 de simulador-montecarlo.md.

Reglas (aprobadas por Juan):
 1. Pesos de amenaza por carta (THREAT_W); Blowfly y su motor pesan 0.7 cuando el loop está armado. Sin escalones.
 2. Auntie compite por peso (ya no es blanco fijo). Ward—Blight 2: el rival necesita una criatura (le pone 2 contadores)
    y para él Auntie pesa 0.1 menos.
 3. Valor de amenaza de cada rival: su mejor criatura (poder/10, +0.1 si vuela) o, si es mayor, un motor que no es
    criatura (curva del bracket; 0.2 menos para los rivales de combate). Las mesas rivales crecen por bracket.
 4. Reservas: cada rival roba remoción (tipada), barridas y (el azul) counters, y las guarda.
 5. Remoción a lo más peligroso de TODA la mesa (softmax), umbral 0.5 (0.4 con 2+), guarda la última el 40% salvo
    bombas (>= 0.8), respuesta al instante (50%) cuando bajas una pieza de peso >= 0.5.
 6. Counters: siempre a Auntie y a las piezas de peso >= 0.5 (o que arman el loop); al resto según el coste.
    El azul guarda su último counter para frenar victorias.
 7. Barridas: un rival barre si la mesa de los demás supera la suya por 1.5.
 8. Relojes: cada rival intenta ganar apenas puede (logística alrededor de su turno típico); si lo frenan, se rearma
    2 turnos y reintenta al 70% por turno.
 9. Tipos de victoria rival (Playgroup): combate / daño directo / pérdida de vida / combo-alternativa. El control de la
    mesa (Kulrath, mesa rival por debajo de la mitad) solo frena intentos de combate.
10. Frenos: primero los otros rivales con lo que guardaron (el azul primero), después tu control y tus respuestas.
11. Ataques rivales: blanco propio, 1/3 + archienemigo (sin depender de tus motores).
12. Archienemigo: +0.3 x fracción de vida que ya les quitaste, sobre el peso de tu mejor pieza.
13. Odio a cementerio: un evento por partida según el bracket.
14. Los rivales de combate que no te atacan pegan a otro rival con la mitad de su poder (los rivales se dañan entre sí;
    sin esto un mazo de drenaje tenía que quitar 120 de vida él solo).
"""
import math
from dataclasses import replace
from engine import Game, Cr, COMMANDER, ENGINES, CARDS, mv

# ---------------------------------------------------------------- pesos (regla 1)
THREAT_W = {
    "Kulrath Knight": 0.6, "Midnight Banshee": 0.6, "All Will Be One": 0.6,
    COMMANDER: 0.5, "Hapatra, Vizier of Poisons": 0.5, "Grave Venerations": 0.5, "Massacre Girl, Known Killer": 0.5,
    "Carnifex Demon": 0.5, "Persistent Constrictor": 0.5, "Tree of Perdition": 0.5, "Vraska, Betrayal's Sting": 0.5,
    "Massacre Wurm": 0.5, "Yawgmoth, Thran Physician": 0.5, "The Meathook Massacre": 0.5,
    "Lasting Tarfire": 0.4, "The Scorpion God": 0.4, "Obelisk Spider": 0.4, "Necroskitter": 0.4,
    "Nest of Scarabs": 0.4, "Flourishing Defenses": 0.4, "Bastion of Remembrance": 0.4, "Zulaport Cutthroat": 0.4,
    "Cauldron of Essence": 0.4, "Blood Artist": 0.4, "Glissa Sunslayer": 0.4, "The Reaper, King No More": 0.4,
    "Crumbling Ashes": 0.4, "Contagion Engine": 0.4, "Liliana, Death Wielder": 0.4, "Archfiend of Sorrows": 0.4,
    "Blowfly Infestation": 0.3, "Everlasting Torment": 0.3, "Village Pillagers": 0.3, "Skinrender": 0.3,
    "Sinister Gnarlbark": 0.3, "Evolution Sage": 0.3, "Soul Snuffers": 0.3, "Dread Tiller": 0.3, "Ammit Eternal": 0.3,
}
W_DEFAULT = 0.2
W_TOKEN = 0.05          # una ficha suelta: solo cuenta para las barridas
W_COMBO = 0.7           # Blowfly + motor en mesa
WARD_COST = 0.1
ARCH = 0.3

# ---------------------------------------------------------------- brackets
# curve = (v0, dv, vmax): motor no-criatura de cada rival (misma escala que tus piezas)
# size/grow: tamaño y ritmo de las criaturas rivales; rem/wipes/cnt por mazo (Archidekt por bracket, guía 5.1)
MIX13 = (0.66, 0.10, 0.09, 0.15)      # combate, daño directo, pérdida de vida, combo/alternativa (Playgroup 2026)
MIX4 = (0.55, 0.10, 0.10, 0.25)
MIX5 = (0.25, 0.05, 0.05, 0.65)
BLUE13, BLUE4, BLUE5 = (0.49, 0.05, 0.05, 0.41), (0.40, 0.05, 0.05, 0.50), (0.15, 0.03, 0.02, 0.80)
BRACKETS = {
    "B1": dict(mus=(10, 11, 12), cpt=1.1, rem=5, blue=1, cnt=3, wipes=2, gyh=0.05, size=0.85, grow=0.70,
               curve=(-0.1, 0.1, 0.8), mix=MIX13, bmix=BLUE13),
    "B2": dict(mus=(9, 10, 11), cpt=1.2, rem=5, blue=1, cnt=3, wipes=2, gyh=0.10, size=1.00, grow=0.75,
               curve=(0.0, 0.1, 0.9), mix=MIX13, bmix=BLUE13),
    "B3": dict(mus=(7, 8, 9), cpt=1.3, rem=5, blue=1, cnt=5, wipes=2, gyh=0.20, size=1.15, grow=0.80,
               curve=(0.1, 0.1, 1.0), mix=MIX13, bmix=BLUE13),
    "B4": dict(mus=(5, 6, 7), cpt=1.5, rem=5, blue=1, cnt=7, wipes=2, gyh=0.35, size=1.30, grow=0.85,
               curve=(0.2, 0.1, 1.1), mix=MIX4, bmix=BLUE4),
    "B5": dict(mus=(3, 4, 4), cpt=2.0, rem=4, blue=2, cnt=10, wipes=1, gyh=0.50, size=1.30, grow=0.85,
               curve=(0.3, 0.1, 1.2), mix=MIX5, bmix=BLUE5),
    "B3+B4": dict(mus=(5, 8, 9), cpt=1.4, rem=5, blue=1, cnt=6, wipes=2, gyh=0.25, size=1.20, grow=0.80,
                  curve=(0.1, 0.1, 1.0), mix=MIX13, bmix=BLUE13, fast_mix=MIX4),
}
SPREAD, RETRY, DELAY = 0.9, 0.7, 2
REM_THR, KEEP_LAST, BOMB, TAU, P_INST = 0.5, 0.4, 0.8, 0.3, 0.5
P_REM_STOP, CNT_UP = 0.4, 0.75
WIPE_MARGIN = 1.5
REM_MIX = (("cre", 0.55), ("any", 0.20), ("ae", 0.20), ("edict", 0.05))
COUNTER_BY_MV = {0: 0.02, 1: 0.02, 2: 0.05, 3: 0.15}
COUNTER_HI = 0.30
TRADE = 0.05            # cada criatura rival muere en combate entre rivales con esta prob. por turno
RIVAL_DMG = [0.5]       # (regla 14) fracción del poder de un rival de combate que llega a OTRO rival cuando no te ataca a ti


def _F(t, mu, sp):
    return 1 / (1 + math.exp(-(t + 0.5 - mu) / sp))


def attempt_p(t, mu, sp=SPREAD):
    f0 = _F(t - 1, mu, sp)
    return (_F(t, mu, sp) - f0) / max(1e-9, 1 - f0)


class Game2(Game):
    def __init__(self, deck, rng, mode="table", cfg=None, log=False, policy=None):
        super().__init__(deck, rng, mode=mode, cfg=cfg, log=log, policy=policy)
        self.br = BRACKETS[self.cfg.v2]
        br = self.br
        self.v2 = True
        self.blue = sorted(rng.sample(range(3), br["blue"]))
        self.wtype = []
        for i in range(3):
            mix = br["bmix"] if i in self.blue else (br.get("fast_mix") if (i == 0 and "fast_mix" in br) else br["mix"])
            x, acc, k = rng.random(), 0.0, 0
            for k, p in enumerate(mix):
                acc += p
                if x <= acc:
                    break
            self.wtype.append(("combat", "direct", "life", "combo")[k])
        self.cfg = replace(self.cfg, kinds=tuple("combat" if w == "combat" else "combo" for w in self.wtype))
        self.rem_stock = [[] for _ in range(3)]
        self.wipe_stock = [0, 0, 0]
        self.cnt_stock = [0, 0, 0]
        for i in range(3):
            for _ in range(7):
                self._draw_one(i)
        self.mus = list(br["mus"])
        self.ready = [1, 1, 1]
        self.retry = [False] * 3
        self.rival_next = [99, 99, 99]
        self.eng_t0 = [0, 0, 0]
        self.counter_ready = 0
        self.counters_left = 0
        self.inst_used = False
        self.gyh_turn = rng.randint(4, 10) if rng.random() < br["gyh"] else None
        self.D = dict(rem_used=0, rem_us=0, rem_auntie=0, rem_names={}, cnt_us={}, wipes=[], attempts=0, others=0,
                      controlled=0, answered=0, ward_paid=0, inst=0)

    # ---------------------------------------------------------------- reservas (regla 4)
    def _draw_one(self, i):
        br, r = self.br, self.rng
        if r.random() < br["rem"] / 99:
            x, acc = r.random(), 0.0
            for typ, p in REM_MIX:
                acc += p
                if x <= acc:
                    break
            self.rem_stock[i].append(typ)
        if r.random() < br["wipes"] / 99:
            self.wipe_stock[i] += 1
        if i in self.blue and r.random() < br["cnt"] / 99:
            self.cnt_stock[i] += 1

    def opp_draws(self):
        cpt = self.br["cpt"]
        for i in self.alive():
            n = int(cpt) + (self.rng.random() < cpt - int(cpt))
            for _ in range(n):
                self._draw_one(i)
        self.counter_ready = sum(self.cnt_stock[i] for i in self.blue if i in self.alive() and self.rng.random() < CNT_UP)
        self.counters_left = self.counter_ready

    # ---------------------------------------------------------------- pesos (reglas 1, 2, 12)
    def combo_on(self):
        return self.on("Blowfly Infestation") and any(self.on(e) for e in ENGINES)

    def w(self, name):
        if self.combo_on() and (name == "Blowfly Infestation" or name in ENGINES):
            return W_COMBO
        return THREAT_W.get(name, W_DEFAULT)

    def our_pieces(self, typ, rival=None):
        """(peso, objeto) de lo tuyo que esa remoción puede quitar"""
        out = []
        if typ in ("cre", "any", "edict"):
            for c in self.cre:
                if c.dead or c.kind != "card" or c.eq == "boots":
                    continue
                v = self.w(c.name)
                if c.name == COMMANDER:
                    if rival is not None and not self.boards[rival]:
                        continue          # ward—Blight 2: sin criaturas no puede pagarlo
                    v -= WARD_COST
                out.append((v, c))
        if typ in ("any", "ae"):
            for n in self.perms:
                if CARDS.get(n, {}).get("t") in ("E", "A"):
                    out.append((self.w(n), n))
            if typ == "any":
                for n in self.loyal:
                    out.append((self.w(n), ("walker", n)))
        return out

    def lost_frac(self):
        return 1 - sum(max(x, 0) for x in self.opp) / 120

    def us_value(self, typ="any", rival=None):
        ps = self.our_pieces(typ, rival)
        if not ps:
            return None, None
        v, obj = max(ps, key=lambda x: x[0])
        return v + ARCH * self.lost_frac(), obj

    # ---------------------------------------------------------------- mesas rivales (regla 3)
    def cre_value(self, c):
        return self.eff_pw(c) / 10 + (0.1 if c.flying else 0)

    def opp_best_cre(self, i):
        b = [c for c in self.boards[i] if not c.dead]
        return max(b, key=self.cre_value) if b else None

    def opp_engine(self, i):
        v0, dv, vmax = self.br["curve"]
        t = self.turn - self.eng_t0[i]
        mu = min(v0 + dv * t, vmax) - (0.2 if self.wtype[i] == "combat" else 0)
        return max(0.0, self.rng.gauss(mu, 0.2))

    def opp_value(self, i, typ="any"):
        """(valor, que) del mejor blanco del rival i para esa remoción"""
        c = self.opp_best_cre(i)
        cv = self.cre_value(c) if c else 0.0
        ev = self.opp_engine(i)
        if typ == "cre":
            return cv, ("cre", c)
        if typ == "ae":
            return ev, ("eng", None)
        if typ == "edict":
            return (cv if len(self.boards[i]) == 1 else 0.1), ("cre", c)
        return (cv, ("cre", c)) if cv >= ev else (ev, ("eng", None))

    def board_w(self):
        return sum(self.w(c.name) if c.kind == "card" else W_TOKEN for c in self.cre if not c.dead)

    def opp_board_w(self, i):
        return sum(self.cre_value(c) for c in self.boards[i] if not c.dead)

    def rival_develop(self, i):
        if self.mode != "table":
            return
        br = self.br
        for b in list(self.boards[i]):          # combate entre rivales
            if self.rng.random() < TRADE:
                self.rival_kill(i, b)
        p = br["grow"] if self.wtype[i] == "combat" else br["grow"] * 0.5
        if self.turn >= 2 and self.rng.random() < p:
            if self.rng.random() < 0.15:
                for _ in range(2):
                    self.boards[i].append(Cr("tok", i, 1, 1, kind="token"))
                self.natural[i] += 2
            else:
                s = max(1, int(round(self.rng.gauss(1.0 + 0.35 * self.turn, 1.0) * br["size"])))
                c = Cr("opp", i, s, s, black=self.rng.random() < 0.2, flying=self.rng.random() < self.cfg.flyer_p)
                self.boards[i].append(c)
                self.natural[i] += s

    def rival_kill(self, i, c):
        """muerte causada por los rivales (no cuenta como control tuyo)"""
        if c is None or c.dead or c not in self.boards[i]:
            return
        self.natural[i] = max(0.0, self.natural[i] - c.pw)
        c.dead = True
        self.sba()

    # ---------------------------------------------------------------- remoción (regla 5)
    def remove_ours(self, obj, rival):
        if isinstance(obj, Cr):
            if "Heroic Intervention" in self.hand and self.reserve_ok(2):
                self.hand.remove("Heroic Intervention"); self.gy.append("Heroic Intervention")
                return
            if obj.name == COMMANDER:
                b = max(self.boards[rival], key=self.eff_tg)
                self.put(b, 2, by_us=False)          # el rival paga ward—Blight 2
                self.D["ward_paid"] += 1
                if obj.dead:
                    return
                self.D["rem_auntie"] += 1
            name = obj.name
            obj.dead = True
            self.sba()
        elif isinstance(obj, tuple):
            name = obj[1]
            self.loyal.pop(name, None)
            if name in self.perms:
                self.perms[name] -= 1
                if self.perms[name] <= 0:
                    del self.perms[name]
            self.gy.append(name)
        else:
            if "Heroic Intervention" in self.hand and self.reserve_ok(2):
                self.hand.remove("Heroic Intervention"); self.gy.append("Heroic Intervention")
                return
            name = obj
            self.perms[name] -= 1
            if self.perms[name] <= 0:
                del self.perms[name]
            self.gy.append(name)
        self.D["rem_us"] += 1
        self.D["rem_names"][name] = self.D["rem_names"].get(name, 0) + 1
        self.log("REMOCIÓN contra", name)

    def edict_us(self):
        cs = [c for c in self.cre if not c.dead]
        if not cs:
            return
        c = min(cs, key=lambda c: (c.kind == "card", self.w(c.name) if c.kind == "card" else 0))
        c.dead = True
        self.sba()

    def rival_uses_removal(self, i, forced_us=False):
        st = self.rem_stock[i]
        if not st:
            return False
        thr = REM_THR if len(st) == 1 else REM_THR - 0.1
        best = None
        for k, typ in enumerate(st):        # elige la remoción guardada que mejor le sirve
            cands = []
            v, obj = self.us_value(typ, i)
            if v is not None and v >= thr:
                cands.append((v, "us", obj))
            if not forced_us:
                for j in self.alive():
                    if j != i:
                        ov, what = self.opp_value(j, typ)
                        if ov >= thr and (what[0] == "eng" or what[1] is not None):
                            cands.append((ov, j, what))
            if cands and (best is None or max(x[0] for x in cands) > max(x[0] for x in best[1])):
                best = (k, cands)
        if best is None:
            return False
        k, cands = best
        if len(st) == 1 and max(x[0] for x in cands) < BOMB and self.rng.random() < KEEP_LAST:
            return False
        ws = [math.exp(x[0] / TAU) for x in cands]
        r = self.rng.random() * sum(ws)
        for c, wgt in zip(cands, ws):
            r -= wgt
            if r <= 0:
                break
        typ = st.pop(k)
        self.D["rem_used"] += 1
        v, who, obj = c
        if who == "us":
            if typ == "edict":
                self.edict_us()
            else:
                self.remove_ours(obj, i)
        else:
            if obj[0] == "cre":
                self.rival_kill(who, obj[1])
            else:
                self.eng_t0[who] = self.turn
            if typ == "edict" and self.rng.random() < 0.5:     # "cada oponente sacrifica": también te alcanza
                self.edict_us()
        return True

    def cast(self, n):
        ok = super().cast(n)
        if ok and self.mode == "table" and not self.our is False and not self.inst_used:
            on_bf = any(c.name == n for c in self.cre) or n in self.perms or n == COMMANDER and self.auntie()
            if on_bf and self.w(n) >= REM_THR:
                hold = [i for i in self.alive() if self.rem_stock[i]]
                if hold and self.rng.random() < P_INST:
                    if self.rival_uses_removal(hold[0], forced_us=True):
                        self.inst_used = True
                        self.D["inst"] += 1
        return ok

    # ---------------------------------------------------------------- counters (regla 6)
    def counter_p(self, n):
        if n == COMMANDER or self.w(n) >= REM_THR:
            return 1.0
        if (n == "Blowfly Infestation" and any(self.on(e) for e in ENGINES)) or \
                (n in ENGINES and self.on("Blowfly Infestation")):
            return 1.0
        if n in CARDS and CARDS[n]["t"] == "L":
            return 0.0
        return COUNTER_BY_MV.get(mv(n) if n in CARDS else 4, COUNTER_HI)

    def countered(self, n):
        if self.mode != "table" or self.counter_ready <= 0:
            return False
        p = self.counter_p(n)
        if sum(self.cnt_stock) == 1 and p < 1.0:
            return False                     # guarda el último para frenar victorias
        if self.rng.random() < p:
            self.counter_ready -= 1
            self.counters_left = self.counter_ready
            for i in self.blue:
                if self.cnt_stock[i] > 0:
                    self.cnt_stock[i] -= 1
                    break
            self.D["cnt_us"][n] = self.D["cnt_us"].get(n, 0) + 1
            self.log("COUNTER a", n)
            return True
        return False

    def auntie_ok(self):
        if self.policy.get("auntie") == "wait_blue" and self.mode == "table" and not self.policy.get("no_auntie"):
            return not (self.counter_ready > 0 and self.turn < 9)
        return super().auntie_ok()

    # ---------------------------------------------------------------- turno: relojes (regla 8)
    def our_turn(self):
        if self.mode == "table":
            nt = self.turn + 1
            self.opp_draws()
            self.inst_used = False
            for i in range(3):
                if self.opp[i] > 0 and self.poison[i] < 10 and nt >= self.ready[i]:
                    p = RETRY if self.retry[i] else attempt_p(nt, self.mus[i])
                    self.rival_next[i] = nt if self.rng.random() < p else 99
                else:
                    self.rival_next[i] = 99
        super().our_turn()

    def roll_threat(self, i):
        th = self._threat.get(i)
        if th and th["t"] == self.rival_next[i]:
            return th
        wt = self.wtype[i]
        kind = "cre" if wt == "combat" else (("ae" if self.rng.random() < 0.5 else "other") if wt == "combo" else "other")
        th = dict(t=self.rival_next[i], kind=kind, stoppable=self.rng.random() < self.cfg.p_stoppable,
                  visible=self.rng.random() < self.cfg.p_visible, stopped=False)
        self._threat[i] = th
        return th

    # ---------------------------------------------------------------- ataques (reglas 11, 12)
    def p_us(self):
        return min(0.7, 1 / 3 + ARCH * self.lost_frac())

    def rival_attack(self, i):
        before = self.life
        super().rival_attack(i)
        # si no te atacó a ti, ataca a otro rival (los rivales también se dañan entre sí)
        if RIVAL_DMG[0] > 0 and self.life == before and self.wtype[i] == "combat" and self.turn >= self.cfg.combat_start:
            tg = [j for j in self.alive() if j != i]
            if tg:
                j = self.rng.choice(tg)
                dmg = int(RIVAL_DMG[0] * sum(self.eff_pw(b) for b in self.boards[i]))
                if dmg > 0:
                    self.opp[j] = max(self.opp[j] - dmg, 0) if self.opp[j] - dmg > 0 else 0
                    self.D["rival_dmg"] = self.D.get("rival_dmg", 0) + dmg
                    if self.opp[j] <= 0:
                        self.boards[j] = []
                        self.D["rival_killed"] = self.D.get("rival_killed", 0) + 1
                    self.check_win()

    # ---------------------------------------------------------------- barridas (regla 7)
    def rival_wipes(self, i):
        if self.wipe_stock[i] <= 0 or self.turn < 3:
            return False
        others = self.board_w() + sum(self.opp_board_w(j) for j in self.alive() if j != i)
        if others >= self.opp_board_w(i) + WIPE_MARGIN:
            self.wipe_stock[i] -= 1
            return True
        return False

    def do_wipe(self):
        self.D["wipes"].append(self.turn)
        if self.cre and "Heroic Intervention" in self.hand and self.reserve_ok(2):
            self.hand.remove("Heroic Intervention"); self.gy.append("Heroic Intervention")
        else:
            self.log("BARRIDA")
            for c in self.cre:
                c.dead = True
            if self.goat:
                self.goat_dies()
        for k in range(3):
            for b in self.boards[k]:
                b.dead = True
            self.natural[k] = 0.0
        self.sba()

    # ---------------------------------------------------------------- eventos del turno rival (regla 10)
    def table_events(self, i):
        cfg = self.cfg
        self.rival_attack(i)
        if self.lost or self.won:
            return
        if self.rival_wipes(i):
            self.do_wipe()
            if self.won or self.lost:
                return
        for _ in range(2):
            if not self.rem_stock[i] or not self.rival_uses_removal(i):
                break
            if self.won or self.lost or self.rng.random() < 0.5:
                break
        if self.won or self.lost:
            return
        if self.gyh_turn == self.turn and i == 0:
            self.gy = []
        if self.opp[i] > 0 and self.rival_next[i] == self.turn:
            self.D["attempts"] += 1
            th = self.roll_threat(i)
            stop = th["stopped"]
            if not stop:
                oth = [j for j in self.alive() if j != i]
                oth = sorted(self.rng.sample(oth, len(oth)), key=lambda j: j not in self.blue)
                for j in oth:
                    if j in self.blue and self.cnt_stock[j] > 0 and self.rng.random() < CNT_UP:
                        self.cnt_stock[j] -= 1; stop = True; break
                    if self.rem_stock[j] and self.rng.random() < P_REM_STOP:
                        self.rem_stock[j].pop(0); stop = True; break
                if stop:
                    self.D["others"] += 1
            if not stop and self.wtype[i] == "combat":
                locked = self.on("Kulrath Knight")
                power = sum(self.eff_pw(b) for b in self.boards[i] if not (locked and b.m > 0))
                if self.natural[i] >= 4 and power < cfg.control_ratio * self.natural[i]:
                    stop = True
                    self.D["controlled"] += 1
                    self.stats["controlled"] = self.stats.get("controlled", 0) + 1
            if not stop and th["stoppable"]:
                for ans in self.answers(th["kind"] if th["kind"] != "other" else "any"):
                    if self.reserve_ok(ans[0]):
                        self.use_answer(ans, i)
                        stop = True
                        self.D["answered"] += 1
                        break
            if stop:
                self.ready[i] = self.turn + DELAY
                self.retry[i] = True
                return
            self.lost = True
            self.log("DERROTA: gana el rival", i, self.wtype[i])
