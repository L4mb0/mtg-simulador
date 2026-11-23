"""Por que Gorma gana poco en la Mazmorra: velocidad vs rivales y techos (contrafactuales)."""
import math
from multiprocessing import Pool
import engine, mesa
from mz_runs import cfg
from verif import OWN
from scen import CONS
from cards import swap
from harness import run, summary
N = 3000
def sw(d, pairs):
    for o, i in pairs: d = swap(d, o, i)
    return d
RUTA = sw(OWN, [("Jadar, Ghoulcaller of Nephalia", "Walking Ballista"), ("Greater Good", "Carpet of Flowers"),
                ("Morbid Opportunist", "Chord of Calling"), ("Find // Finality", "Blasting Station")])
ORIG = dict(cp=engine.Game.compute_pool, us=mesa.MesaV2.us_value, inst=mesa.MesaV2.v2_instant,
            ctry=mesa.MesaV2.counter_try, part=mesa.MZ_PARTIAL, draw=engine.Game.draw)
def apply(flag):
    engine.Game.compute_pool = ORIG["cp"]; mesa.MesaV2.us_value = ORIG["us"]; mesa.MesaV2.v2_instant = ORIG["inst"]
    mesa.MesaV2.counter_try = ORIG["ctry"]; mesa.MZ_PARTIAL = ORIG["part"]
    if flag == "sin golpes parciales": mesa.MZ_PARTIAL = 0.0
    if flag == "sin counters": mesa.MesaV2.counter_try = lambda self, c, win=False: False
    if flag == "sin remocion contra ti":
        mesa.MesaV2.us_value = lambda self, kind: (None, None); mesa.MesaV2.v2_instant = lambda self, p: None
    if flag == "+1 mana por turno":
        def cp(self):
            ORIG["cp"](self); self.col += 1
        engine.Game.compute_pool = cp
def job(a):
    deck, sc, s, flag, kw = a
    apply(flag)
    g = engine.play(deck, 3_300_000 + s, mode="table", cfg=cfg(sc, **kw))
    have = set(g.hand) | {p.name for p in g.bf}
    roles = sum([any(c in engine.PERSIST_LOOP for c in have), any(c in engine.OUTLETS for c in have),
                 any(c in engine.DRAINERS or c in ("Jarad, Golgari Lich Lord", "Altar of Dementia", "Walking Ballista") for c in have)])
    return g.won, g.turn, roles, g.stats.get("first_att_any", 99)
def gold(deck, P):
    r = run(deck, N, "goldfish", seed0=3_300_000, pool=P)
    return {t: 100 * sum(1 for x in r if x[2] and x[1] <= t) / N for t in (4, 5, 6, 7, 8)}
if __name__ == "__main__":
    with Pool() as P:
        print("== 1) carrera: % de partidas con combo armado (goldfish) vs rival que ya intento ganar (Mazmorra) ==")
        for nm, d in (("1.1", CONS), ("1.1 + tuyas", OWN), ("ruta Ballista/Carpet/Chord/Blasting", RUTA)):
            g = gold(d, P)
            print(f"{nm:38s} combo <=T4 {g[4]:.0f}%  <=T5 {g[5]:.0f}%  <=T6 {g[6]:.0f}%  <=T7 {g[7]:.0f}%  <=T8 {g[8]:.0f}%")
        sp = 1.0
        F = lambda t, mu: 1 / (1 + math.exp(-(t + 0.5 - mu) / sp))
        for t in (3, 4, 5, 6):
            p = 1 - (1 - F(t, 4)) * (1 - F(t, 5)) * (1 - F(t, 6))
            print(f"  algún rival ya intentó ganar al T{t}: {100*p:.0f}%")
        print("\n== 2) cómo pierdes (1.1 + tuyas, Mazmorra) ==")
        r = P.map(job, [(OWN, "Mazmorra", s, None, {}) for s in range(N)], chunksize=100)
        lost = [x for x in r if not x[0]]
        from collections import Counter
        c = Counter(x[2] for x in lost); tl = Counter(min(x[1], 8) for x in lost)
        print("  piezas del combo que tenías (persist / outlet / cierre) al perder:", ", ".join(f"{k} de 3: {100*v/len(lost):.0f}%" for k, v in sorted(c.items())))
        print("  turno en que pierdes:", ", ".join(f"T{k}{'+' if k == 8 else ''}: {100*v/len(lost):.0f}%" for k, v in sorted(tl.items())))
        print("\n== 3) techos: cuánto ganarías si desapareciera cada problema (1.1 + tuyas) ==")
        base = sum(x[0] for x in r) / N * 100
        print(f"  base Mazmorra {base:.1f}%")
        for flag, kw in (("sin golpes parciales", {}), ("sin counters", {}), ("sin remocion contra ti", {}),
                         ("+1 mana por turno", {}), ("rivales 1 turno más lentos (5/6/7)", dict(mz_mus=(5, 6, 7))),
                         ("rivales 2 turnos más lentos (6/7/8)", dict(mz_mus=(6, 7, 8)))):
            fl = flag if not kw else None
            rr = P.map(job, [(OWN, "Mazmorra", s, fl, kw) for s in range(N)], chunksize=100)
            print(f"  {flag:38s} {100*sum(x[0] for x in rr)/N:.1f}%")
        apply(None)
