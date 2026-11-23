"""Pruebas de la mesa v2 de Giada (16/11/2026). Correr antes de cada lote: PYTHONHASHSEED=0 python3 tests.py"""
import json, os, random
import engine
from engine import Game, play
from cards import ACTUAL
from scen import cfg

OK = []


def check(name, cond):
    OK.append((name, bool(cond)))
    print(("OK   " if cond else "FAIL ") + name)


def game(br="B3", turn=6, life=40):
    g = Game(list(ACTUAL), random.Random(1), mode="table", cfg=cfg(br))
    g.bf, g.hand, g.gy = [], [], []
    g.turn, g.life = turn, life
    g.rem = [[], [], []]
    g.wipe_stock = [[], [], []]
    g.aem_stock = [[], [], []]
    g.cnt_stock = [0, 0, 0]
    g.reserve = 0
    return g


def put(g, name, counters=0, token=None):
    if token:
        p = g.new_perm(token[0], token=True, p=token[1], x=token[2], angel=token[3], kw=("flying",))
    else:
        p = g.new_perm(name)
    p.counters = counters
    p.sick = False
    g.bf.append(p)
    return p


# 1. las mesas viejas no cambian (el código nuevo no consume azar sin bracket)
base = os.path.join(os.path.dirname(__file__), "v1_backup", "seeds.json")
if os.path.exists(base):
    old = json.load(open(base))
    r = [[x.won, x.turn, x.life] for x in (play(ACTUAL, s, mode="table", cfg=cfg("Realista")) for s in range(300))]
    check("mesa vieja: mismas 300 partidas que antes de la v2", r == old[0])

# 2. pesos (regla 1)
g = game()
gi = put(g, "Giada, Font of Hope")
check("Giada sola pesa 0,35", abs(g.w_perm(gi) - 0.35) < 1e-9)
for _ in range(5):
    put(g, None, token=("Angel token", 4, 4, True))
check("Giada con 5 ángeles pesa 0,50", abs(g.w_perm(gi) - 0.50) < 1e-9)
g = game()
tok = put(g, None, token=("Angel token", 4, 4, True))
w_tok = g.w_perm(tok)
ly = put(g, "Lyra Dawnbringer")
check("Lyra Dawnbringer 0,6; ficha 4/4 ~0,27 (sin anthem)", abs(g.w_perm(ly) - 0.6) < 0.05 and abs(w_tok - 4 / 15) < 0.01)
rv = put(g, "Righteous Valkyrie")
ws = []
for life in range(40, 49):
    g.life = life
    ws.append(g.w_perm(rv))
check("Righteous Valkyrie sube de forma continua (sin escalón en 47)", max(b - a for a, b in zip(ws, ws[1:])) <= 0.06)

# 3. sin escalón al sumar piezas menores
g = game()
put(g, "Serra Avenger")
v0 = g.our_target("cre")[0]
for k in range(4):
    put(g, None, token=("Spirit token", 1, 1, False))
v1 = g.our_target("cre")[0]
check("sumar fichas 1/1 no cambia lo que la remoción ve de ti", abs(v1 - v0) < 1e-9)

# 4. la mesa guarda la remoción si solo hay algo chico
g = game(turn=3)
put(g, "Segovian Angel")
g.rem[1] = ["cre"]
g.opp_best_value = lambda: 0.2
check("con un 1/1 y rivales flojos, la remoción se guarda", g.rival_uses_removal(1) is False and g.rem[1] == ["cre"])

# 5. va a lo más peligroso
g = game()
put(g, "Serra Avenger"); ly = put(g, "Lyra Dawnbringer")
g.rem[1] = ["cre", "cre"]; g.opp_best_value = lambda: 0.0
g.rival_uses_removal(1)
check("la remoción elige a Lyra Dawnbringer antes que a Serra Avenger", ly not in g.bf)

# 6. botas
g = game()
gi = put(g, "Giada, Font of Hope"); gi.boots = True
check("Giada con Swiftfoot Boots no es blanco", g.our_target("cre") is None)

# 7. indestructible
g = game()
put(g, "Sephara, Sky's Blade"); sv = put(g, "Serra Avenger")
check("con Sephara, destruir no saca a un volador pero exiliar sí", not g.kills("cre", sv) and g.kills("cre_x", sv))

# 8. counters por hechizo
g = game(); g.cnt_stock = [5, 5, 5]; g.blue = [1]; g._cnt_up = {1: True}
hits = sum(1 for _ in range(200) if (g.cnt_stock.__setitem__(1, 5), g._cnt_up.__setitem__(1, True), g.countered_v2("Felidar Sovereign"))[2])
check("Felidar Sovereign siempre se contrarresta (cierre)", hits == 200)
hits = sum(1 for _ in range(500) if (g.cnt_stock.__setitem__(1, 5), g._cnt_up.__setitem__(1, True), g.countered_v2("Segovian Angel"))[2])
check("Segovian Angel casi nunca (2%)", hits < 30)
g.cnt_stock = [0, 1, 0]; g._cnt_up = {1: True}
kept = sum(1 for _ in range(400) if not (g.cnt_stock.__setitem__(1, 1), g._cnt_up.__setitem__(1, True), g.countered_v2("Lyra Dawnbringer"))[2])
check("el azul guarda su último counter ~40% ante algo que no es bomba", 100 < kept < 220)

# 9. barridas según la mesa
g = game(); g.wipe_stock[0] = ["destroy"]; g.opp_best_value = lambda: 0.6
for _ in range(5):
    put(g, None, token=("Angel token", 4, 4, True))
put(g, "Lyra Dawnbringer")
check("con mesa grande, el rival barre", g.rival_wipes(0) and not g.creatures())
g = game(); g.wipe_stock[0] = ["destroy"]
put(g, None, token=("Spirit token", 1, 1, False))
vals = iter([0.1, 0.1, 1.0])
g.opp_best_value = lambda: next(vals)
check("con mesa chica y la suya fuerte, no barre", not g.rival_wipes(0))

# 10. Flawless Maneuver frena destruir pero no exiliar
for sub, expect in (("destroy", True), ("exile", False)):
    g = game(); g.wipe_stock[0] = [sub]; g.opp_best_value = lambda: 0.6
    put(g, "Giada, Font of Hope")
    for _ in range(4):
        put(g, None, token=("Angel token", 4, 4, True))
    g.hand = ["Flawless Maneuver"]
    g.rival_wipes(0)
    check(f"Flawless Maneuver {'salva' if expect else 'no salva'} ante barrida de {sub}", (len(g.creatures()) == 5) == expect)

# 11. -X/-X
g = game(); g.wipe_stock[0] = ["minus"]; g.opp_best_value = lambda: 0.6
small = [put(g, None, token=("Angel token", 4, 4, True)) for _ in range(4)]
big = put(g, "Serra Avenger", counters=4)
g.rival_wipes(0)
check("-X/-X (X=5) mata a los 4/4 y deja al 7/7", big in g.bf and not any(p in g.bf for p in small))

# 12. rebote
g = game(); g.wipe_stock[0] = ["bounce"]; g.opp_best_value = lambda: 0.6
gi = put(g, "Giada, Font of Hope"); g.g_in_cmd = False; tax0 = g.tax
for _ in range(4):
    put(g, None, token=("Angel token", 4, 4, True))
put(g, "Lyra Dawnbringer")
g.rival_wipes(0)
check("rebote: fichas desaparecen, Lyra a la mano, Giada a la zona de mando sin impuesto extra",
      not g.creatures() and "Lyra Dawnbringer" in g.hand and g.g_in_cmd and g.tax == tax0)

# 13. edicto
g = game()
ly = put(g, "Lyra Dawnbringer"); t = put(g, None, token=("Spirit token", 1, 1, False))
g.do_edict()
check("el edicto se lleva la ficha, no a Lyra", ly in g.bf and t not in g.bf)

# 14. Herald of Eternal Dawn frena intentos
g = game(); put(g, "Herald of Eternal Dawn")
g.rival_next = [g.turn, -1, -1]; g.ready_t = [None] * 3
g.threat = {}
g.table_events_v2(0)
check("con Herald of Eternal Dawn en mesa nadie gana", not g.lost and g.stats["herald_stop"] == 1)

# 15. frenos entre rivales
g = game(); g.blue = [1]; g.cnt_stock = [0, 3, 0]
stops = 0
for _ in range(300):
    g.cnt_stock[1] = 3; g.rem = [[], [], []]
    stops += g.others_stop(0)
check("el azul con counter frena ~75% de los intentos de otro", 180 < stops < 270)

# 16. combate rival sin escalón
g = game()
ps = []
for pw in range(10, 21):
    g.bf = []
    put(g, None, token=("Angel token", pw, pw, True))
    ps.append(g.p_us_combat())
check("a quién ataca el combate rival cambia de forma continua con tu poder aéreo", max(b - a for a, b in zip(ps, ps[1:])) < 0.03)

# 17. respuesta al instante
g = game(); g._our = True; g.rem[2] = ["cre"]
cfg_hits = 0
for s in range(200):
    g.rng = random.Random(s); g._instant_used = False; g.rem[2] = ["cre"]
    g.bf = []; p = put(g, "Lyra Dawnbringer"); g.instant_response(p)
    cfg_hits += p not in g.bf
check("bajar Lyra Dawnbringer provoca respuesta al instante ~50%", 70 < cfg_hits < 130)
g.bf = []; tk = put(g, None, token=("Spirit token", 1, 1, False)); g._instant_used = False; g.rem[2] = ["cre"]
g.instant_response(tk)
check("una ficha 1/1 no provoca respuesta", tk in g.bf)

# 18. odio masivo a artefactos y encantamientos
g = game(); g.aem_stock[0] = ["both"]
for n in ("Court of Grace", "Patchwork Banner", "Always Watching"):
    put(g, n)
check("con Court, banner y Always Watching, el rival usa su odio masivo", g.rival_aem(0) and not g.bf)
g = game(); g.aem_stock[0] = ["art"]; put(g, "Sol Ring")
check("con solo Sol Ring, no lo usa", not g.rival_aem(0))

# 19. regla de juego: un intento rival exitoso termina la partida
g = game(); g.rival_next = [g.turn, -1, -1]; g.ready_t = [None] * 3; g.blue = [1]; g.threat = {}
g.threat[0] = dict(kind="other", stoppable=False, visible=False, stopped=False, t=g.turn, wtype="combo")
g.table_events_v2(0)
check("intento rival sin frenos = derrota", g.lost)

print(f"\n{sum(o for _, o in OK)}/{len(OK)} pruebas OK")
