"""Pruebas de la mesa v2 de Blight Curse (16/11/2026). Correr antes de cada lote: PYTHONHASHSEED=0 python3 tests.py"""
import random
import mesa2
from mesa2 import Game2, attempt_p
from engine import Cr, COMMANDER, play, Game
from scen import SCEN, ACTUAL

FAILS = []


def check(name, cond, detail=""):
    print(("OK   " if cond else "FALLA") + " " + name + (f"  ({detail})" if detail else ""))
    if not cond:
        FAILS.append(name)


def blank(b="B2", seed=1):
    g = Game2(ACTUAL, random.Random(seed), mode="table", cfg=SCEN[b])
    g.cre, g.perms, g.loyal = [], {}, {}
    g.boards = [[], [], []]
    g.natural = [0.0, 0.0, 0.0]
    g.rem_stock = [[], [], []]
    g.wipe_stock = [0, 0, 0]
    g.cnt_stock = [0, 0, 0]
    g.turn = 6
    g.opp = [40, 40, 40]
    g.opp_engine = lambda i: 0.0
    return g


def ours(g, name, p=2, t=2):
    c = Cr(name, "us", p, t)
    g.cre.append(c)
    return c


def rival_cre(g, i, p):
    c = Cr("opp", i, p, p)
    g.boards[i].append(c)
    g.natural[i] += p
    return c


# 1. sin escalones: sumar piezas menores no cambia lo que la mesa ve de ti
g = blank()
ours(g, COMMANDER, 4, 4); rival_cre(g, 0, 2)
v1, _ = g.us_value("cre", 0)
ours(g, "Evolution Sage"); ours(g, "Skinrender")
v2, _ = g.us_value("cre", 0)
check("no hay escalón al sumar piezas menores", abs(v1 - v2) < 1e-9, f"{v1:.2f} vs {v2:.2f}")

# 2. la mesa guarda la remoción si solo hay algo chico
used = 0
for s in range(300):
    g = blank(seed=s)
    ours(g, "Evolution Sage")
    g.rem_stock[0] = ["cre"]
    used += g.rival_uses_removal(0)
check("la mesa guarda la remoción si solo hay algo chico", used == 0, f"usó {used}/300")

# 3. la remoción va a lo más peligroso
hit = 0
for s in range(200):
    g = blank(seed=s)
    k = ours(g, "Kulrath Knight", 3, 3); ours(g, "Evolution Sage")
    g.rem_stock[0] = ["cre", "cre"]
    g.rival_uses_removal(0)
    hit += k.dead
check("la remoción va a lo más peligroso (Kulrath antes que Evolution Sage)", hit == 200, f"{hit}/200")

# 4. ward—Blight 2: sin criaturas el rival no puede apuntar a Auntie; con criatura, se pone 2 contadores
g = blank()
ours(g, COMMANDER, 4, 4)
check("ward: un rival sin criaturas no puede apuntar a Auntie", g.our_pieces("cre", 0) == [])
g = blank()
a = ours(g, COMMANDER, 4, 4); b = rival_cre(g, 0, 5)
g.remove_ours(a, 0)
check("ward: el rival se pone 2 contadores y pierde 1 de vida por Auntie", b.m == 2 and g.opp[0] == 39 and a.dead,
      f"contadores {b.m}, vida {g.opp[0]}")

# 5. Blowfly y su motor suben juntos solo con el loop armado
g = blank()
g.perms["Blowfly Infestation"] = 1
w_solo = g.w("Blowfly Infestation")
ours(g, "Hapatra, Vizier of Poisons")
check("Blowfly pesa 0,3 sola y 0,7 con su motor", w_solo == 0.3 and g.w("Blowfly Infestation") == 0.7
      and g.w("Hapatra, Vizier of Poisons") == 0.7)

# 6. counters: Auntie siempre; el azul guarda su último counter
g = blank(); g.cnt_stock[g.blue[0]] = 2; g.counter_ready = 2
check("counter: Auntie siempre", g.countered(COMMANDER))
n = 0
for s in range(300):
    g = blank(seed=s); g.cnt_stock[g.blue[0]] = 1; g.counter_ready = 1
    n += g.countered("Night's Whisper")
check("counter: guarda el último para frenar victorias", n == 0, f"{n}/300")
n = 0
for s in range(1000):
    g = blank(seed=s); g.cnt_stock[g.blue[0]] = 3; g.counter_ready = 3
    n += g.countered("Night's Whisper")
check("counter: lo chico casi nunca (Night's Whisper ~5%)", n < 100, f"{n}/1000")

# 7. barridas: nadie barre con la mesa vacía; barre cuando la mesa de los demás supera la suya
g = blank(); g.wipe_stock[0] = 1
check("barrida: no con las mesas vacías", not g.rival_wipes(0))
g = blank(); g.wipe_stock[0] = 1
for n_ in ("Kulrath Knight", "Midnight Banshee", COMMANDER, "Hapatra, Vizier of Poisons"):
    ours(g, n_)
rival_cre(g, 1, 6); rival_cre(g, 2, 6)
check("barrida: sí cuando lo de los demás supera lo suyo por 1,5", g.rival_wipes(0))

# 8. relojes: logística alrededor del turno típico
cum, alive = 0.0, 1.0
for t in range(1, 12):
    p = attempt_p(t, 9)
    if t == 9:
        at_mu = cum + alive * p
    cum += alive * p; alive *= 1 - p
check("relojes: ~50–65% ya lo intentó en su turno típico", 0.5 <= at_mu <= 0.65, f"{at_mu:.2f}")
check("relojes: >90% lo intentó 2 turnos después", cum > 0.9, f"{cum:.2f}")

# 9. el control solo frena intentos de combate
for wt, expect in (("combat", True), ("combo", False)):
    g = blank()
    g.wtype = [wt, "combo", "combo"]
    g.turn = 9; g.rival_next = [9, 99, 99]
    rival_cre(g, 0, 6); g.boards[0][0].m = 5          # tu control dejó su mesa en 1/6 de lo normal
    g._threat[0] = dict(t=9, kind="cre" if wt == "combat" else "ae", stoppable=False, visible=False, stopped=False)
    g.table_events(0)
    check(f"control: frena intentos de {wt}" if expect else "control: no frena intentos de combo",
          (not g.lost) == expect)

# 10. otro rival frena con lo que guardó
stops = 0
for s in range(400):
    g = blank(seed=s)
    g.wtype = ["combo", "combo", "combo"]
    g.turn = 9; g.rival_next = [9, 99, 99]
    j = [k for k in (1, 2) if k not in g.blue][0] if any(k not in g.blue for k in (1, 2)) else 1
    g.rem_stock[j] = ["cre"]
    g._threat[0] = dict(t=9, kind="ae", stoppable=False, visible=False, stopped=False)
    g.table_events(0)
    stops += not g.lost
check("frenos: otro rival con remoción frena ~40%", 0.3 < stops / 400 < 0.5, f"{stops/400:.2f}")

# 11. tu control no baja la mesa "natural"; la remoción entre rivales sí
g = blank()
c = rival_cre(g, 0, 4)
g.put(c, 4)
nat_after_us = g.natural[0]
c2 = rival_cre(g, 0, 3)
g.rival_kill(0, c2)
check("natural: tu control no la baja, la remoción rival sí", nat_after_us == 4 and g.natural[0] == 4,
      f"{nat_after_us} y {g.natural[0]}")

# 12. archienemigo
g = blank()
ours(g, "Kulrath Knight"); rival_cre(g, 0, 2)
v0, _ = g.us_value("cre", 0)
g.opp = [20, 20, 20]
v1, _ = g.us_value("cre", 0)
check("archienemigo: drenar la mesa te vuelve más blanco", v1 > v0, f"{v0:.2f} -> {v1:.2f}")

# 13. los ataques rivales no dependen de tus motores (el escalón viejo filtraba a otro subsistema)
g = blank()
p0 = g.p_us()
for n_ in ("Kulrath Knight", "Midnight Banshee", "Hapatra, Vizier of Poisons", "Grave Venerations"):
    ours(g, n_)
check("ataques: el blanco no cambia por tener motores", g.p_us() == p0)

# 14. la mesa vieja no cambió (mismo resultado que antes de la mesa v2)
w = sum(play(ACTUAL, 900000 + s, mode="table", cfg=SCEN["Realista (base)"]).won for s in range(400))
check("mesa vieja intacta (400 partidas, Realista; referencia 16/11)", w == 7, f"{w} victorias")

print()
print("TODAS OK" if not FAILS else f"{len(FAILS)} FALLAS: {FAILS}")
