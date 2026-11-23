import random, copy, math
from cards import C, VALUE
from engine import State, Lose
import ai
from ai import (mulligan, try_land, run_main, end_step, total_mana, DEV_EXCL_C, DEV_EXCL_B)

ANSWERS = [("Thunderclap", "sac1"), ("Fireblast", "sac2"), ("Fiery Impulse", None), ("Shock", None), ("Magma Spray", None),
           ("Lightning Bolt", None), ("Burst Lightning", None), ("Abrade", None), ("Lightning Strike", None),
           ("Searing Spear", None), ("Play with Fire", None), ("Unholy Heat", None), ("Chaos Warp", None), ("Delayed Blast Fireball", None), ("Demon Bolt", None),
           ("Mine Collapse", None), ("Frost Bite", None)]
PROACTIVE = ["Fiery Confluence", "Blasphemous Act"]
AMPS = {"Ojer Axonil, Deepest Might", "Harmonic Prodigy", "Torbran, Thane of Red Fell", "Krark, the Thumbless",
        "Birgi, God of Storytelling", "Solphim, Mayhem Dominus", "Tomik, Izzet Sparkmage"}

def reserve(s, n):
    out = []
    nm = sum(1 for l in s.lands if l.get("mtn"))
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

# Parámetros por bracket: fuente única en core/mesa.py (aquí se arman las tablas con el formato de Gandalf)
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", ".."))
from core import mesa as M
OPP_CURVE = {b: v["curve"] for b, v in M.BRACKETS.items()}
# nb (22/11): fraccion de tierras no basicas de los rivales, para Price of Progress (supuesto de Claude)
NB = {b: v["nb"] for b, v in M.BRACKETS.items()}
def _ix(rem, cpt, blue, cnt, wipes, wlo, whi, gyh, gyh_perm, arth, arch=M.ARCH, curve="B3", tau=M.TAU, noise=M.NOISE, cnt_up=M.CNT_UP):
    v0, dv, vmax = OPP_CURVE[curve]
    return dict(opp_v0=v0, opp_dv=dv, opp_vmax=vmax, opp_noise=noise, tau=tau,
                rem=rem, cpt=cpt, blue=blue, cnt=cnt, cnt_up=cnt_up, p_inst=M.P_INST,
                wipes=wipes, wipe_lo=wlo, wipe_hi=whi, gyh=gyh, gyh_perm=gyh_perm, gyh_lo=wlo - 1, gyh_hi=whi + 1,
                arth=arth, arth_lo=wlo - 1, arth_hi=whi + 1, arch=arch, nb=NB[curve])
def _br(b):
    v = M.BRACKETS[b]
    return (dict(mus=list(v["mus"]), spread=M.SPREAD, a=0.7, delay=M.DELAY),
            _ix(v["rem"], v["cpt"], v["blue"], v["cnt"], v["wipes"], v["wipe_lo"], v["wipe_hi"], v["gyh"], v["gyh_perm"],
                v["arth"], curve=b))
BRACKETS = {b: _br(b) for b in M.BRACKETS}
_Z = M.MAZMORRA
TIME_TURNS = [tuple(x) for x in _Z["time_turns"]]
def _mz(mus, spread=_Z["spread"], delay=_Z["delay"], retry=_Z["retry"], delay_turbo=_Z["delay_turbo"],
        retry_turbo=_Z["retry_turbo"], p_partial=_Z["p_partial"], rem=_Z["rem"], cnt=_Z["cnt"], cpt=_Z["cpt"],
        edict=_Z["edict"][0], edict_rate=_Z["edict"][1], ld=_Z["strip"][0], ld_rate=_Z["strip"][1],
        rem_stop=_Z["rem_stop"], rem_slows=0.0, time_turns=TIME_TURNS, me_life=_Z["me_life"], opp_other_dmg=_Z["opp_other_dmg"]):
    ix = _ix(rem, cpt, 1, cnt, _Z["wipes"], _Z["wipe_lo"], _Z["wipe_hi"], _Z["gyh"], _Z["gyh_perm"], _Z["arth"], curve="B4")
    ix.update(edict=edict, edict_rate=edict_rate, ld=ld, ld_rate=ld_rate, rem_slows=rem_slows, nb=_Z["nb"])
    return (dict(mus=list(mus), spread=spread, a=0.7, delay=delay, retry=retry, delay_turbo=delay_turbo, retry_turbo=retry_turbo,
                 p_partial=p_partial, rem_stop=rem_stop, time_turns=time_turns, me_life=me_life, opp_other_dmg=opp_other_dmg), ix)
# regla 8 (desempate por vida) apagada salvo que se pida: "Mazmorra con tiempo" (Juan, 18/11)
BRACKETS["Mazmorra"] = _mz(_Z["mus"], rem_slows=_Z["rem_slows"], time_turns=None)
for _n, _v in M.MAZMORRA_VARIANTES.items():
    BRACKETS[_n] = _mz(_v["mus"], rem_slows=_Z["rem_slows"], time_turns=None)
BRACKETS["Mazmorra con tiempo"] = _mz(_Z["mus"], rem_slows=_Z["rem_slows"])

P_REM_STOP = M.P_REM_STOP
RETRY = M.RETRY
_F = M.F
attempt_p = M.attempt_p

SEARCH_KILL = [8]
KRARK_VOTES = [5]   # 17/11 (rehecho 22/11): con Krark el piloto decide el all-in con 5 tiradas nuevas, no con las monedas reales

def loss_cause(s):
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
        if ix.get("gyh", 0) > 0:
            s.ix["gyh_turn"] = rng.randint(ix["gyh_lo"], ix["gyh_hi"]) if rng.random() < ix["gyh"] else None
            s.ix["gyh_perm"] = rng.random() < ix["gyh_perm"]
        if "rem" in ix:
            s.rem_stock = [sum(rng.random() < ix["rem"] / 99 for _ in range(7)) for _ in range(3)]
            s.blue = rng.sample(range(3), ix["blue"])
            s.wipe_stock = [sum(rng.random() < ix["wipes"] / 99 for _ in range(7)) for _ in range(3)]
            s.cnt_stock = [sum(rng.random() < ix["cnt"] / 99 for _ in range(7)) if i in s.blue else 0 for i in range(3)]
        if ix.get("arth", 0) > 0:
            s.ix["arth_turn"] = rng.randint(ix["arth_lo"], ix["arth_hi"]) if rng.random() < ix["arth"] else None
        if ix.get("edict", 0) > 0:
            s.edict_on = rng.random() < ix["edict"]
        if ix.get("ld", 0) > 0:
            s.ld_on = rng.random() < ix["ld"]
    hz = "mus" in table
    retry_p = table.get("retry", RETRY)
    turbo = min(range(3), key=lambda i: table["mus"][i]) if hz else None
    def rp(i):
        return table.get("retry_turbo", retry_p) if i == turbo else retry_p
    def dl(i):
        return table.get("delay_turbo", table["delay"]) if i == turbo else table["delay"]
    s.first_att = None; s.n_att = 0; s.partial_kills = 0
    s.slow = [0, 0, 0]
    if hz: s.mz_order = sorted(range(3), key=lambda i: table["mus"][i])
    s.t_lim = None; s.by_time = None
    if table.get("time_turns"):
        r = rng.random(); acc = 0.0
        for tt, pr in table["time_turns"]:
            acc += pr
            if r < acc: s.t_lim = tt; break
        s.me_life = rng.uniform(*table["me_life"])
        s.opp_other = [rng.uniform(*table["opp_other_dmg"]) for _ in range(3)]
    mus = list(table["mus"]); ready = [1, 1, 1]; retry = [False] * 3; K = [99, 99, 99]
    s.K = K
    mulligan(s)
    excl = DEV_EXCL_C
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
                s.opp_draws()
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
            if s.blooms: s.bloom_upkeep()
            try_land(s)
            if s.has("The One Ring"):
                s.ring += 1; s.draw(s.ring)
            s.isis_turn = 0; s.pif_any = False
            s.urabrask_upkeep(); s.keld_upkeep()
            for st in s.sagas:
                if t - st in (2, 3): s.pool["R"] += 1
            try_land(s)
            alive = s.alive()
            for i in range(3):
                p = rp(i) if retry[i] else attempt_p(t, mus[i], table["spread"])
                K[i] = t if (i in alive and t >= ready[i] and rng.random() < p) else 99
            n_now = sum(1 for i in range(3) if K[i] == t)
            for i in range(3):
                if K[i] == t and s.slow[i] > 0:
                    s.slow[i] -= 1; K[i] = 99; retry[i] = True; s.slow_used = getattr(s, "slow_used", 0) + 1
            if n_now:
                s.n_att += n_now
                if s.first_att is None: s.first_att = t
            imminent = [i for i in alive if K[i] <= t]
            k = copy.deepcopy(s); k.ix = None; k.log = None
            try: run_main(k, "allin")
            except Lose: pass
            krark = s.has("Krark, the Thumbless") or "Krark, the Thumbless" in s.hand
            if krark:
                votes = 0
                for j in range(KRARK_VOTES[0]):
                    kj = copy.deepcopy(s); kj.ix = None; kj.log = None; kj.rng = random.Random(seed * 7919 + t * 13 + j)
                    try: run_main(kj, "allin")
                    except Lose: pass
                    votes += kj.dead()
                k_dead = votes * 2 > KRARK_VOTES[0]
            else:
                k_dead = k.dead()
            went = False
            if not k_dead and not krark and SEARCH_KILL[0] and max(k.opp) <= 40:
                srng = random.Random(seed * 131 + t)
                for j in range(SEARCH_KILL[0]):
                    nz = {n: srng.uniform(-3, 3) for n in sorted(set(s.hand) | {e[0] for e in s.exile_play} | set(s.gy) | {"Gandalf", "Flameshape"})}
                    ai.PRIO_NOISE[0] = nz
                    k2 = copy.deepcopy(s); k2.ix = None; k2.log = None
                    try: run_main(k2, "allin")
                    except Lose: pass
                    if k2.dead():
                        s.search_found = getattr(s, "search_found", 0) + 1
                        run_main(s, "allin"); went = True
                        break
                    ai.PRIO_NOISE[0] = None
                ai.PRIO_NOISE[0] = None
            if went:
                pass
            elif k_dead:
                run_main(s, "allin"); went = True
            elif early and imminent:
                tgt = min(imminent, key=lambda i: K[i])
                k2 = copy.deepcopy(s); k2.ix = None; k2.log = None; k2.focus_idx = tgt
                try: run_main(k2, "allin")
                except Lose: pass
                if k2.opp[tgt] <= 0:
                    s.focus_idx = tgt; run_main(s, "allin"); went = True
            if s.dead():
                return t, s, "win"
            if not went:
                n_att = sum(1 for i in s.alive() if K[i] == t)
                res = reserve(s, n_att) if n_att else []
                run_main(s, "dev", excl)
                if ai.GS_REMOVAL[0] and "Grapeshot" in s.hand and s.can_pay(*s.cost("Grapeshot"), True):
                    att = [i for i in s.alive() if K[i] == t]
                    if att:
                        s.focus_idx = att[0]; s.cast("Grapeshot", "hand"); s.focus_idx = None
                        if rng.random() < P_REM_STOP:
                            K[att[0]] = 99; ready[att[0]] = t + dl(att[0]); retry[att[0]] = True
                        if s.dead():
                            return t, s, "win"
            else:
                res = []
            try_land(s)
            if s.dead():
                return t, s, "win"
            while len(s.hand) > 7: s.discard(1)
            s.bank_red()
            if s.has("Helm of Awakening") and not getattr(s, "_helm_rivals", False):
                s._helm_rivals = True
                for i in s.alive():
                    mus[i] -= 1
            if s.ix:
                s.opp_phase()
            for i in s.alive():
                if K[i] == t:
                    if getattr(s, "rem_stock", None):
                        stopped = False
                        oth = [j for j in s.alive() if j != i]
                        oth = sorted(rng.sample(oth, len(oth)), key=lambda j: j not in s.blue)
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
                        K[i] += table["delay"]; s.ans_used = getattr(s, 'ans_used', 0) + 1
                        ready[i] = t + dl(i); retry[i] = True
                    elif table.get("p_partial", 0) and rng.random() < table["p_partial"]:
                        victims = ["us"] + [j for j in s.alive() if j != i]
                        v = rng.choice(victims)
                        if v == "us":
                            s.cause = loss_cause(s); s.killed_by_partial = True
                            return t, s, "lose"
                        s.opp[v] = 0; s.partial_kills += 1; K[v] = 99
                        ready[i] = t + 1; retry[i] = True
                        if s.dead():
                            return t, s, "lose"
                    else:
                        s.cause = loss_cause(s)
                        return t, s, "lose"
            if s.t_lim is not None and t >= s.t_lim:
                if s.dead():
                    return t, s, "win"
                best = max(s.opp[i] - s.opp_other[i] for i in s.alive())
                s.by_time = s.me_life > best
                if s.by_time:
                    return t, s, "win"
                s.cause = "tiempo: un rival con mas vida"
                return t, s, "lose"
    except Lose:
        return 99, s, "lose"
    return 99, s, "timeout"
