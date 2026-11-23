import random, copy
from cards import C, VALUE
from engine import State, Lose
import ai
from ai import (mulligan, try_land, run_main, end_step, total_mana, DEV_EXCL_C, DEV_EXCL_B)

ANSWERS = [("Thunderclap", "sac1"), ("Fireblast", "sac2"), ("Fiery Impulse", None), ("Shock", None), ("Magma Spray", None),
           ("Lightning Bolt", None), ("Burst Lightning", None), ("Abrade", None), ("Lightning Strike", None),
           ("Searing Spear", None), ("Play with Fire", None), ("Unholy Heat", None), ("Chaos Warp", None), ("Delayed Blast Fireball", None), ("Demon Bolt", None),
           ("Mine Collapse", None)]
PROACTIVE = ["Fiery Confluence", "Blasphemous Act"]
AMPS = {"Ojer Axonil, Deepest Might", "Harmonic Prodigy", "Torbran, Thane of Red Fell", "Krark, the Thumbless",
        "Birgi, God of Storytelling", "Solphim, Mayhem Dominus", "Tomik, Izzet Sparkmage"}

def reserve(s, n):
    """reserve up to n answers for attempts after our turn; returns list"""
    out = []
    nm = sum(1 for l in s.lands if l.get("mtn"))
    used = set()
    for _ in range(n):
        got = None
        for name, alt in ANSWERS:
            if name in s.hand and s.hand.count(name) > sum(1 for x in out if x[0] == name):
                if alt == "sac1" and nm >= 1:
                    got = (name, alt); nm -= 1; break
                if alt == "sac2" and nm >= 2:
                    got = (name, alt); nm -= 2; break
                g, r = (3, 1) if name == "Mine Collapse" else (C[name]["g"], C[name]["r"])
                if s.can_pay(g, r):
                    s.pay(g, r); got = (name, None); break
        if not got:
            for name in PROACTIVE:
                if name in s.hand:
                    g, r = s.cost(name)
                    if s.can_pay(g, r, True):
                        s.cast(name, "hand"); got = (name, "done"); break
        if got:
            out.append(got)
    return out

# ---- mesas por bracket (13/11/2026) ----
# clocks: turnos en que cada rival intenta ganar (minimo de la tabla de brackets + ventana de 3)
# ix: remocion (p_rem), counters (p_counter + p_counter2 gratis), barrida, odio a cementerio (gyh) y artefactos (arth),
#     archienemigo (arch: la mesa te apunta mas cuanto mas vida les quitaste)
# amenaza de los rivales (14/11, criterio de Claude a pedido de Juan): lo mejor que tiene en mesa cada rival =
# min(v0 + dv*turno, vmax) + ruido, en la MISMA escala que nuestras piezas (0.6 = motor que la mesa tiene que matar,
# como Prodigy; 1.0 = bomba que gana sola). Ancla: el rival tipico llega a 0.6 en T7 (B1), T6 (B2), T5 (B3), T4 (B4), T3 (B5).
OPP_CURVE = {"B1": (-0.1, 0.1, 0.8), "B2": (0.0, 0.1, 0.9), "B3": (0.1, 0.1, 1.0), "B4": (0.2, 0.1, 1.1), "B5": (0.3, 0.1, 1.2)}
# interaccion de la mesa (14/11): cada rival ROBA remocion y la GUARDA hasta que algo valga la pena (estilo Forge).
#   rem = remocion puntual por mazo (mediana de 6532 mazos de Archidekt: 5 en B1-B4, 4 en B5)
#   cpt = cartas que ve cada rival por turno; blue = rivales azules (Juan: 1 por mesa, es el que mas frena);
#   cnt = counters en el mazo AZUL (la mediana de 1 de Archidekt promedia mazos sin azul; un azul de B3 lleva ~5)
#   cnt_up = prob. de que el azul tenga mana arriba en tu turno
def _ix(rem, cpt, blue, cnt, wipes, wlo, whi, gyh, gyh_perm, arth, arch=0.3, curve="B3", tau=0.3, noise=0.2, cnt_up=0.75):
    v0, dv, vmax = OPP_CURVE[curve]
    return dict(opp_v0=v0, opp_dv=dv, opp_vmax=vmax, opp_noise=noise, tau=tau,
                rem=rem, cpt=cpt, blue=blue, cnt=cnt, cnt_up=cnt_up, p_inst=0.5,
                wipes=wipes, wipe_lo=wlo, wipe_hi=whi, gyh=gyh, gyh_perm=gyh_perm, gyh_lo=wlo - 1, gyh_hi=whi + 1,
                arth=arth, arth_lo=wlo - 1, arth_hi=whi + 1, arch=arch)
BRACKETS = {
    "B1": (dict(mus=[10, 11, 12], spread=0.9, a=0.7, delay=2), _ix(5, 1.1, 1, 3, 2, 6, 10, 0.05, 0.0, 0.10, curve="B1")),
    "B2": (dict(mus=[9, 10, 11], spread=0.9, a=0.7, delay=2), _ix(5, 1.2, 1, 3, 2, 5, 9, 0.10, 0.2, 0.15, curve="B2")),
    "B3": (dict(mus=[7, 8, 9], spread=0.9, a=0.7, delay=2), _ix(5, 1.3, 1, 5, 2, 4, 8, 0.20, 0.3, 0.25, curve="B3")),
    "B4": (dict(mus=[5, 6, 7], spread=0.9, a=0.7, delay=2), _ix(5, 1.5, 1, 7, 2, 4, 7, 0.35, 0.4, 0.35, curve="B4")),
    "B5": (dict(mus=[3, 4, 4], spread=0.9, a=0.7, delay=2), _ix(4, 2.0, 2, 10, 1, 3, 6, 0.50, 0.5, 0.40, curve="B5")),
    "B3+B4": (dict(mus=[5, 8, 9], spread=0.9, a=0.7, delay=2), _ix(5, 1.4, 1, 6, 2, 4, 8, 0.25, 0.3, 0.30, curve="B3")),
}
# ---- Mazmorra B3 (16/11/2026): torneo B3 de La Mazmorra TCG, calibrado con 8 partidas del 15/11 (4 de Juan con Gandalf, 4 de Juma) ----
# Lo observado: mazos cEDH ajustados al bracket. Un turbo por mesa casi siempre (Tifa mato a un jugador en T3, Vivi iba a
# stormear en T4, Mikey bajo en T4 y pego en T5); partidas que terminan en T5-T7 (mediana ~T6). Los rivales se frenan mucho
# entre si (todos le tiran remocion al Vivi; el azul contrarresta al Mikey dos turnos seguidos) y el turbo reintenta al turno
# siguiente. Daño colateral: edictos de un Sephiroth (2 de 4 mesas), Strip Mine en bucle de la Tifa (1 de 4).
#   mus/spread: turno tipico de cada rival (el turbo en 4) -> se eligio con diag_mazmorra.py contra lo observado
#   delay/retry: tras un freno, el turbo rearma en 1 turno y reintenta el 85% de las veces (antes 2 turnos y 70%)
#   p_partial: si nadie lo frena, a veces el golpe solo mata a UN jugador (Tifa a Ureni en T3): elige victima al azar
#   ix extra: edict (prob. de un rival con edictos "cada oponente sacrifica"), edict_rate (por vuelta, desde T3);
#             ld (prob. de un rival que destruye tierras en bucle), ld_rate (por vuelta contra ti, desde T3)
#   rem_slows: la remocion que un rival tira contra OTRO rival va al mas rapido y, con esta prob., le tumba su proximo intento
#             (sin esto la remocion entre rivales se gastaba sin retrasar a nadie y la mesa frenaba la mitad de lo observado)
#   rem_stop: prob. de que una remocion guardada frene un intento en curso (B1-B5: 0,4)
#   rem/cnt/cpt: 7 remociones y 8 counters en el azul, 1,5 cartas por turno (mazos optimizados); amenazas con la curva de B4
TIME_TURNS = [(6, 0.2), (7, 0.4), (8, 0.4)]   # turno del corte por tiempo (Juan 16/11: la de la Vivi termino en T6 justo a la hora)
def _mz(mus, spread=1.0, delay=2, retry=0.7, delay_turbo=1, retry_turbo=0.85, p_partial=0.4, rem=7, cnt=8, cpt=1.5,
        edict=3 / 11, edict_rate=0.35, ld=3 / 11, ld_rate=0.5, rem_stop=0.4, rem_slows=0.0,
        time_turns=TIME_TURNS, me_life=(25, 38), opp_other_dmg=(0, 15)):
    ix = _ix(rem, cpt, 1, cnt, 2, 4, 7, 0.30, 0.4, 0.35, curve="B4")
    ix.update(edict=edict, edict_rate=edict_rate, ld=ld, ld_rate=ld_rate, rem_slows=rem_slows)
    return (dict(mus=list(mus), spread=spread, a=0.7, delay=delay, retry=retry, delay_turbo=delay_turbo, retry_turbo=retry_turbo,
                 p_partial=p_partial, rem_stop=rem_stop, time_turns=time_turns, me_life=me_life, opp_other_dmg=opp_other_dmg), ix)
BRACKETS["Mazmorra"] = _mz([4, 5, 6], rem_slows=0.5)
# variantes para ver cuanto depende el resultado de cada supuesto (diag_mazmorra.py). Calibracion v2 del 16/11 con Juan
# (4000 partidas, Gandalf 1.6): 4/5/6 ("todos van lo mas rapido que pueden"), solo el turbo reintenta rapido, edictos y
# Strip Mine como UN rival concreto entre 11 (3/11 de las mesas) -> fin <=T5 53%, <=T6 72%, <=T7 84%; 1er intento <=T4 80%;
# 1,6 frenos (observado ~45 / ~75 / ~100%, ~75%, ~1,5). Falta el limite de 45 min (cerraria las partidas largas).
MZ_VARIANTS = {
    "Mazmorra": BRACKETS["Mazmorra"],
    "Mz optimista (4/5/7)": _mz([4, 5, 7], rem_slows=0.5),
    "Mz pesimista (3/5/6)": _mz([3, 5, 6], rem_slows=0.5),
    "Mz sin edictos ni Strip Mine": _mz([4, 5, 6], rem_slows=0.5, edict=0, ld=0),
    "Mz sin golpes parciales": _mz([4, 5, 6], rem_slows=0.5, p_partial=0),
    "Mz rivales se frenan como en B3": _mz([4, 5, 6], delay_turbo=2, retry_turbo=0.7, rem=5, cnt=5, cpt=1.3),
    "Mz sin limite de tiempo": _mz([4, 5, 6], rem_slows=0.5, time_turns=None),
    "Mz tiempo corto (T6/T7)": _mz([4, 5, 6], rem_slows=0.5, time_turns=[(6, 0.5), (7, 0.5)]),
    "Mz tiempo largo (T8/T9)": _mz([4, 5, 6], rem_slows=0.5, time_turns=[(8, 0.5), (9, 0.5)]),
    "Mz llegas con menos vida (15-30)": _mz([4, 5, 6], rem_slows=0.5, me_life=(15, 30)),
}
# relojes (14/11, Juan): un rival no espera a un turno fijo: intenta ganar APENAS puede. Cada rival tiene un turno tipico
# (mu) y cada turno lo intenta con la prob. que sale de una logistica (spread): a veces lo tiene muy temprano, a veces tarde.
# Si lo frenan, rearma (delay turnos) y vuelve a intentarlo apenas puede (RETRY).
# Frenos: primero los OTROS rivales con remocion (sirve P_REM_STOP de las veces) o counter guardado (si dejo mana arriba);
# despues tus respuestas. Reemplaza el 67% inventado de la columna "calibrada".
import math
P_REM_STOP = 0.4
RETRY = 0.7
def _F(t, mu, sp):
    return 1 / (1 + math.exp(-(t + 0.5 - mu) / sp))
def attempt_p(t, mu, sp):
    f0 = _F(t - 1, mu, sp)
    return (_F(t, mu, sp) - f0) / max(1e-9, 1 - f0)

def calibrated(name, p_others=0.67):
    """OBSOLETO desde el 14/11: los rivales ya se frenan entre si con sus propias reservas. Devuelve la mesa normal."""
    return BRACKETS[name]

def _calibrated_old(name, p_others=0.67):
    t, ix = BRACKETS[name]
    t = dict(t); t["p_others"] = p_others
    return t, ix

SEARCH_KILL = [8]   # cuantos ordenes alternativos probar cuando el voraz no mata (0 = apagado)

def loss_cause(s):
    """por que no mato: se mira el estado al perder"""
    acc = set(s.hand) | {p["name"] for p in s.perms}
    amp = bool(acc & {"Ojer Axonil, Deepest Might", "Fiery Emancipation", "Harmonic Prodigy", "Tomik, Izzet Sparkmage"}) or s.artist >= 3
    cards = len(s.hand) + sum(1 for e in s.exile_play if e[1] >= s.turn)
    mana = total_mana(s)
    if min([x for x in s.opp if x > 0] or [0]) <= 12: return "cerca (un rival a 12 o menos)"
    if not amp: return "sin multiplicador"
    if cards <= 2: return "sin cartas"
    if mana < 6: return "sin mana"
    return "le falto dano"

def play_table(deck, strat, seed, table, ix=None, max_turn=18, log=False):
    rng = random.Random(seed)
    s = State(deck, rng, strat)
    s.diag = []; s.cf = []
    if log: s.log = []
    if ix:
        s.ix = dict(ix)
        if "p_wipe" in ix:   # mesa vieja: barrida en turno fijo
            s.ix["wipe_turn"] = rng.randint(ix["wipe_lo"], ix["wipe_hi"]) if rng.random() < ix["p_wipe"] else None
        if ix.get("gyh", 0) > 0:   # solo consume azar si el parametro esta activo (mesas viejas comparables)
            s.ix["gyh_turn"] = rng.randint(ix["gyh_lo"], ix["gyh_hi"]) if rng.random() < ix["gyh"] else None
            s.ix["gyh_perm"] = rng.random() < ix["gyh_perm"]
        if "rem" in ix:   # reservas de los rivales: mano inicial de 7
            s.rem_stock = [sum(rng.random() < ix["rem"] / 99 for _ in range(7)) for _ in range(3)]
            s.blue = rng.sample(range(3), ix["blue"])
            s.wipe_stock = [sum(rng.random() < ix["wipes"] / 99 for _ in range(7)) for _ in range(3)]
            s.cnt_stock = [sum(rng.random() < ix["cnt"] / 99 for _ in range(7)) if i in s.blue else 0 for i in range(3)]
        if ix.get("arth", 0) > 0:
            s.ix["arth_turn"] = rng.randint(ix["arth_lo"], ix["arth_hi"]) if rng.random() < ix["arth"] else None
        # Mazmorra (16/11): rivales con edictos y con destruccion de tierras en bucle (solo consume azar si estan activos)
        if ix.get("edict", 0) > 0:
            s.edict_on = rng.random() < ix["edict"]
        if ix.get("ld", 0) > 0:
            s.ld_on = rng.random() < ix["ld"]
    hz = "mus" in table
    retry_p = table.get("retry", RETRY)
    turbo = min(range(3), key=lambda i: table["mus"][i]) if hz else None
    def rp(i):   # prob. de reintento tras un freno (Mazmorra 16/11: el turbo tiene la suya)
        return table.get("retry_turbo", retry_p) if i == turbo else retry_p
    def dl(i):   # turnos para rearmar tras un freno
        return table.get("delay_turbo", table["delay"]) if i == turbo else table["delay"]
    s.first_att = None; s.n_att = 0; s.partial_kills = 0
    s.slow = [0, 0, 0]
    if hz: s.mz_order = sorted(range(3), key=lambda i: table["mus"][i])
    # limite de tiempo (Mazmorra 16/11): la ronda se corta al final de la vuelta t_lim y gana el que tiene mas vida
    s.t_lim = None; s.by_time = None
    if table.get("time_turns"):
        r = rng.random(); acc = 0.0
        for tt, pr in table["time_turns"]:
            acc += pr
            if r < acc: s.t_lim = tt; break
        s.me_life = rng.uniform(*table["me_life"])
        s.opp_other = [rng.uniform(*table["opp_other_dmg"]) for _ in range(3)]
    if hz:
        mus = list(table["mus"]); ready = [1, 1, 1]; retry = [False] * 3; K = [99, 99, 99]
    else:
        K = [rng.randint(lo, hi) for lo, hi in table["clocks"]]
    s.K = K
    mulligan(s)
    excl = DEV_EXCL_C | (AMPS if "M" in strat else set())
    if "B" in strat:
        excl = DEV_EXCL_B | {"ArtistL3"}
    early = "E" in strat
    try:
        for t in range(1, max_turn + 1):
            s.turn = t
            for l in s.lands: l["tapped"] = False
            for p in s.perms:
                if not p.get("nountap"): p["tapped"] = False
            s.pool = {"R": s.pool["R"] if s.keeps_red() else 0, "C": 0}
            s.spells = 0; s.dmg_turn = 0; s.molten = False; s.dcast = 0; s.ash_res = 0
            s.land_played = False; s.pif = False; s.casts_guard = 0; s.inst_used = False; s.breach_cleanup()
            s.focus_idx = None
            if s.ix:
                s.opp_draws()     # los rivales roban remocion/counters; fija los counters disponibles este turno
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
            try_land(s)
            if s.has("The One Ring"):
                s.ring += 1; s.draw(s.ring)
            s.isis_turn = 0; s.pif_any = False
            s.urabrask_upkeep(); s.keld_upkeep()
            for st in s.sagas:
                if t - st in (2, 3): s.pool["R"] += 1
            try_land(s)
            alive = s.alive()
            if hz:   # quien intenta ganar en esta vuelta de mesa
                for i in range(3):
                    p = rp(i) if retry[i] else attempt_p(t, mus[i], table["spread"])
                    K[i] = t if (i in alive and t >= ready[i] and rng.random() < p) else 99
                n_now = sum(1 for i in range(3) if K[i] == t)
                for i in range(3):
                    if K[i] == t and s.slow[i] > 0:      # Mazmorra: le removieron la pieza clave, el intento se cae
                        s.slow[i] -= 1; K[i] = 99; retry[i] = True; s.slow_used = getattr(s, "slow_used", 0) + 1
                if n_now:
                    s.n_att += n_now
                    if s.first_att is None: s.first_att = t
            imminent = [i for i in alive if K[i] <= t]
            # full kill check
            k = copy.deepcopy(s); k.ix = None; k.log = None
            try: run_main(k, "allin")
            except Lose: pass
            went = False
            if not k.dead() and SEARCH_KILL[0] and max(k.opp) <= 40:
                # busqueda: probar ordenes alternativos de lanzamiento en clones
                srng = random.Random(seed * 131 + t)
                for j in range(SEARCH_KILL[0]):
                    nz = {n: srng.uniform(-3, 3) for n in sorted(set(s.hand) | {e[0] for e in s.exile_play} | set(s.gy) | {"Gandalf", "Flameshape"})}
                    ai.PRIO_NOISE[0] = nz
                    k2 = copy.deepcopy(s); k2.ix = None; k2.log = None
                    try: run_main(k2, "allin")
                    except Lose: pass
                    if k2.dead():
                        s.search_found = getattr(s, "search_found", 0) + 1
                        s.L(f"T{t} busqueda encontro kill"); run_main(s, "allin"); went = True
                        break
                    ai.PRIO_NOISE[0] = None
                ai.PRIO_NOISE[0] = None
            if went:
                pass
            elif k.dead():
                s.L(f"T{t} all-in full kill"); run_main(s, "allin"); went = True
            elif early and imminent:
                tgt = min(imminent, key=lambda i: K[i])
                k2 = copy.deepcopy(s); k2.ix = None; k2.log = None; k2.focus_idx = tgt
                try: run_main(k2, "allin")
                except Lose: pass
                if k2.opp[tgt] <= 0:
                    s.L(f"T{t} all-in to kill opponent {tgt}"); s.focus_idx = tgt; run_main(s, "allin"); went = True
            if s.dead():
                return t, s, "win"
            if not went:
                n_att = sum(1 for i in s.alive() if K[i] == t)
                res = reserve(s, n_att) if n_att else []
                run_main(s, "dev", excl)
                # Grapeshot como remocion: en tu turno rompe la jugada de un rival que va a intentar ganar (sirve P_REM_STOP)
                if hz and ai.GS_REMOVAL[0] and "Grapeshot" in s.hand and s.can_pay(*s.cost("Grapeshot"), True):
                    att = [i for i in s.alive() if K[i] == t]
                    if att:
                        s.focus_idx = att[0]; s.cast("Grapeshot", "hand"); s.focus_idx = None
                        s.gs_removal = getattr(s, "gs_removal", 0) + 1
                        if rng.random() < P_REM_STOP:
                            K[att[0]] = 99; ready[att[0]] = t + dl(att[0]); retry[att[0]] = True
                            s.gs_stops = getattr(s, "gs_stops", 0) + 1
                        if s.dead():
                            return t, s, "win"
            else:
                res = []
            try_land(s)
            if s.dead():
                return t, s, "win"
            while len(s.hand) > 7: s.discard(1)
            s.bank_red()
            # Helm of Awakening es simetrico: abarata tambien a los rivales -> cada rival intenta ganar un turno antes (una vez)
            if s.has("Helm of Awakening") and not getattr(s, "_helm_rivals", False):
                s._helm_rivals = True
                for i in s.alive():
                    if hz: mus[i] -= 1
                    elif K[i] > t + 1: K[i] -= 1
            if s.ix:
                s.opp_phase()
            for i in s.alive():
                if K[i] == t:
                    if table.get("p_others", 0) > 0 and rng.random() < table["p_others"]:
                        K[i] += table["delay"]; s.others_stop = getattr(s, "others_stop", 0) + 1
                        continue
                    if hz and getattr(s, "rem_stock", None):
                        stopped = False
                        oth = [j for j in s.alive() if j != i]
                        oth = sorted(rng.sample(oth, len(oth)), key=lambda j: j not in s.blue)   # el azul responde primero
                        for j in oth:
                            if s.rem_stock[j] > 0 and rng.random() < table.get("rem_stop", P_REM_STOP):
                                s.rem_stock[j] -= 1; stopped = True; break
                            if j in s.blue and s.cnt_stock[j] > 0 and rng.random() < s.ix.get("cnt_up", 0.75):
                                s.cnt_stock[j] -= 1; stopped = True; break
                        if stopped:
                            ready[i] = t + dl(i); retry[i] = True
                            s.others_stop = getattr(s, "others_stop", 0) + 1
                            continue
                    if res and rng.random() < table["a"]:
                        name, alt = res.pop(0)
                        if alt != "done" and name in s.hand:
                            s.hand.remove(name); s.gy.append(name)
                            if alt in ("sac1", "sac2"):
                                for l in [l for l in s.lands if l.get("mtn")][: (1 if alt == "sac1" else 2)]:
                                    s.lands.remove(l)
                        K[i] += table["delay"]; s.ans_used = getattr(s,'ans_used',0)+1
                        if hz: ready[i] = t + dl(i); retry[i] = True
                    elif hz and table.get("p_partial", 0) and rng.random() < table["p_partial"]:
                        # golpe parcial (Mazmorra): mata a UN jugador al azar entre los demas (tu o un rival) y sigue atacando
                        victims = ["us"] + [j for j in s.alive() if j != i]
                        v = rng.choice(victims)
                        if v == "us":
                            s.lose_had = bool(res); s.cause = loss_cause(s); s.killed_by_partial = True
                            return t, s, "lose"
                        s.opp[v] = 0; s.partial_kills += 1; K[v] = 99
                        ready[i] = t + 1; retry[i] = True
                        s.L(f"T{t} el rival {i} elimina al rival {v}")
                        if s.dead():
                            return t, s, "lose"      # no deberia pasar: el atacante sigue vivo
                    else:
                        s.lose_had = bool(res)
                        s.cause = loss_cause(s)
                        return t, s, "lose"
            if s.t_lim is not None and t >= s.t_lim:
                if s.dead():
                    return t, s, "win"
                # se acabo el tiempo: gana el de mas vida (tus pings bajan la vida de todos los rivales; la tuya casi intacta)
                best = max(s.opp[i] - s.opp_other[i] for i in s.alive())
                s.by_time = s.me_life > best
                if s.by_time:
                    return t, s, "win"
                s.cause = "tiempo: un rival con mas vida"
                return t, s, "lose"
    except Lose:
        return 99, s, "lose"
    return 99, s, "timeout"
