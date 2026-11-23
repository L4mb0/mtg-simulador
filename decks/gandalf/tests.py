"""Pruebas de reglas y sinergias del simulador de Gandalf. Correr antes de cada lote: python3 tests.py"""
import random, ai
from engine import State
from cards import C
FAILS = []
def new(hand=(), perms=(), lands=3, lib_extra=60):
    s = State(["Mountain"] * lib_extra, random.Random(7), "E")
    s.turn = 5; s.hand = list(hand); s.log = []
    for _ in range(lands): s.lands.append(dict(name="Mountain", prod="R", tapped=False, mtn=True))
    for p in perms:
        d = dict(name=p, tapped=False, wiz=C.get(p, {}).get("wiz", False), shaman=C.get(p, {}).get("shaman", False))
        if p == "Gandalf": d["wiz"] = True; s.gandalf = "bf"
        s.perms.append(d)
    return s
def check(name, cond, info=""):
    print(("OK   " if cond else "FAIL ") + name + ("" if cond else f"  -> {info}"))
    if not cond: FAILS.append(name)

# 1 Birgi da R por cualquier hechizo (tambien Lotus Petal) y Gandalf pinguea con artefactos
s = new(["Lotus Petal"], ["Birgi, God of Storytelling", "Gandalf"]); s.cast("Lotus Petal", "hand")
check("Birgi + Lotus Petal: +R de Birgi, Treasure del Petal, ping de Gandalf", s.pool["R"] == 1 and s.treasures == 1 and s.opp == [39, 39, 39], (s.pool, s.treasures, s.opp))
# 2 Birgi tambien con criaturas; Gandalf no
s = new(["Coruscation Mage"], ["Birgi, God of Storytelling", "Gandalf"]); s.cast("Coruscation Mage", "hand")
check("Birgi con criatura: +R; Gandalf no pinguea", s.pool["R"] == 1 and s.opp == [40, 40, 40], (s.pool, s.opp))
# 3 Mox Amber: maná solo con leyenda (Birgi es leyenda)
s = new([], ["Mox Amber"], lands=0); r0 = s.avail()[0]
s2 = new([], ["Mox Amber", "Birgi, God of Storytelling"], lands=0); r1 = s2.avail()[0]
check("Mox Amber sin leyenda 0, con Birgi 1", r0 == 0 and r1 == 1, (r0, r1))
# 4 Guttersnipe: no con artefactos, si con instantaneos
s = new(["Sol Ring", "Shock"], ["Guttersnipe"]); s.cast("Sol Ring", "hand"); a = list(s.opp); s.cast("Shock", "hand")
check("Guttersnipe ignora artefactos y dispara con Shock", a == [40, 40, 40] and sum(40 - x for x in s.opp) == 2 + 6, (a, s.opp))
# 5 Harmonic Prodigy duplica a Gandalf (Wizard)
s = new(["Sol Ring"], ["Gandalf", "Harmonic Prodigy"]); s.cast("Sol Ring", "hand")
check("Prodigy duplica el ping de Gandalf", s.opp == [38, 38, 38], s.opp)
# 6 reemplazos ordenados por el rival (616.1): Ojer + Emancipation + Tomik sobre 1 de dano = 4
s = new([], ["Ojer Axonil, Deepest Might", "Fiery Emancipation", "Tomik, Izzet Sparkmage"])
check("Ojer+Emancipation+Tomik: un ping de 1 hace 4", s.mod(1, True) == 4, s.mod(1, True))
# 7 la ficha de Lindblum es negra: Ojer no la sube
s = new(["Sol Ring"], ["Ojer Axonil, Deepest Might"]); s.perms.append(dict(name="Wizard token", tapped=False, wiz=True, red=False)); s.cast("Sol Ring", "hand")
check("Ficha de Mage Siege (negra) no recibe a Ojer", s.opp == [39, 39, 39], s.opp)
# 8 Electro guarda el maná rojo (tambien el de Birgi) entre turnos
s = new(["Sol Ring"], ["Electro, Assaulting Battery", "Birgi, God of Storytelling"], lands=2); s.cast("Sol Ring", "hand"); s.bank_red()
check("Electro: guarda maná de tierras y de Birgi", s.pool["R"] == 1 + 1 + 0 or s.pool["R"] >= 2, s.pool)
# 9 Bonus Round copia los hechizos lanzados con Mizzix
s = new([], []); s.bonus_round = True; s.gy = ["Lightning Bolt"]; s._mz_over = False
s.mizzix(overload=False)
check("Bonus Round copia el Bolt lanzado por Mizzix (3+3)", sum(40 - x for x in s.opp) == 6, s.opp)
# 10 Embereth Blaze: 2 de dano y Virtue queda en el exilio para lanzarla despues
s = new(["Virtue of Courage"], [], lands=7); s.hand.remove("Virtue of Courage"); s._adventure = True; s.cast("Embereth Blaze", "none")
ok = sum(40 - x for x in s.opp) == 2 and any(e[0] == "Virtue of Courage" for e in s.exile_play) and "Embereth Blaze" not in s.gy
s.cast("Virtue of Courage", "exile")
check("Embereth Blaze -> Virtue desde el exilio", ok and s.has("Virtue of Courage"), (s.opp, s.exile_play))
# 11 Virtue: exilia tantas cartas como dano
s = new([], ["Virtue of Courage"]); s.lib = ["Mountain"] * 60; s.dmg_each(2)
check("Virtue: 2 de dano a 3 rivales = 6 cartas", len(s.exile_play) == 6, len(s.exile_play))
# 12 Harnfel: descarta tierra sobrante y exilia 2
s = new(["Mountain", "Shock"], ["Harnfel, Horn of Bounty"], lands=6); s.land_played = True
check("Harnfel descarta la tierra y exilia 2", s.harnfel("dev") and len(s.exile_play) == 2 and "Mountain" in s.gy, (s.hand, s.exile_play))
# 13 Linea de apertura: Mountain, Sol Ring, Signet, Petal -> Flameshape en el turno 1
s = State(["Mountain"] * 60, random.Random(1), "E"); s.turn = 1; s.hand = ["Mountain", "Sol Ring", "Arcane Signet", "Lotus Petal", "Lightning Bolt"]
ai.try_land(s); ai.run_main(s, "dev", ai.DEV_EXCL_C)
check("T1: Sol Ring + Signet + Petal -> Flameshape", s.gandalf == "exile", s.gandalf)
# 14 Counters: dos counters frenan dos hechizos clave
s = new(["Past in Flames", "Mizzix's Mastery"], [], lands=10); s.ix = dict(p_inst=0); s.counter_ready = 2; s.gy = ["Shock", "Lightning Bolt"]
a = s.cast("Past in Flames", "hand"); b = s.cast("Mizzix's Mastery", "hand")
check("Dos counters frenan dos cierres", a is False and b is False and s.counter_ready == 0, (a, b, s.counter_ready))
# 15 Rest in Peace: sin recursion del cementerio
s = new([], [], lands=8); s.gy = ["Lightning Bolt", "Shock", "Past in Flames"]; s.gy_locked = True
cands = ai.candidates(s)
ai.act_once(s, "allin", frozenset())
check("Cementerio bloqueado: no hay candidatos del cementerio", not any(z == "gy" for _, z, _ in cands) and not s.gy, (cands, s.gy))
# 16 Gandalf: Flameshape desde la zona de mando paga impuesto; Gandalf desde el exilio no
s = new([], [], lands=0); s.cmd_casts = 1
check("Impuesto: Flameshape 4, Gandalf desde el exilio 3", sum(s.cost("Flameshape")) == 4 and (setattr(s, "gandalf", "exile") or sum(s.cost("Gandalf")) == 3), (s.cost("Flameshape"),))
# 17 Mox Amber cuenta como hechizo no criatura (Gandalf) y para Birgi
s = new(["Mox Amber"], ["Gandalf", "Birgi, God of Storytelling"]); s.cast("Mox Amber", "hand")
check("Mox Amber: ping de Gandalf y +R de Birgi; luego da maná", s.opp == [39, 39, 39] and s.pool["R"] == 1 and s.avail()[0] >= 4, (s.opp, s.pool))
# 18 Copias de Grapeshot (Bonus Round) hacen 1, no storm
s = new(["Grapeshot"], [], lands=4); s.spells = 3; s.bonus_round = True; s.cast("Grapeshot", "hand")
check("Grapeshot con 3 previos + copia de Bonus Round = 4 + 1", sum(40 - x for x in s.opp) == 5, s.opp)
# 19 Ashling: magecraft tambien con copias
s = new(["Shock"], ["Ashling, Flame Dancer"], lands=4); s.hand += ["Mountain"] * 3; s.bonus_round = True; s.cast("Shock", "hand")
check("Ashling se dispara con lanzar y con copiar (2 veces: 2 de dano a cada uno)", s.ash_res == 2, s.ash_res)
# 20 Remocion estilo Forge: cada rival guarda su remocion y la usa en lo mas peligroso de TODA la mesa
from table import BRACKETS
def p_target(perms, stock=1, n=4000):
    hits = 0
    for k in range(n):
        s = new([], perms); s.ix = dict(BRACKETS["B3"][1]); s.rng = random.Random(k); s.turn = 5
        s.rem_stock = [stock, 0, 0]; s.blue = [1]; s.cnt_stock = [0, 0, 0]
        hits += s.rival_uses_removal(0)
    return hits / n
s = new([], ["Gandalf", "Harmonic Prodigy"]); s.ix = dict(BRACKETS["B3"][1]); s.remove_best()
check("La remocion elige a Prodigy (motor) antes que a Gandalf (pinger)", s.gandalf == "bf" and not any(p["name"] == "Harmonic Prodigy" for p in s.perms), [p["name"] for p in s.perms])
a, b = p_target(["Harmonic Prodigy"]), p_target(["Harmonic Prodigy", "Tomik, Izzet Sparkmage", "Guttersnipe", "Gandalf"])
check("Sin escalon: Prodigy solo vs Prodigy+Tomik+Guttersnipe+Gandalf da la misma prob.", abs(a - b) < 0.03 and a > 0.2, (a, b))
s = new([], ["Tomik, Izzet Sparkmage"]); s.ix = dict(BRACKETS["B3"][1]); s.turn = 3; s.rem_stock = [1, 0, 0]; s.blue = [1]; s.cnt_stock = [0, 0, 0]
s.opp_best_value = lambda: 0.0
check("Con 1 remocion y solo un pinger (0.4) en mesa, el rival la guarda", s.rival_uses_removal(0) is False and s.rem_stock[0] == 1, s.rem_stock)
s.rem_stock = [2, 0, 0]
check("Con 2 remociones guardadas, ya la gasta en un pinger (umbral 0.4)", s.rival_uses_removal(0) is True and s.rem_stock[0] == 1, s.rem_stock)
# 21 Counters: motores y piezas de storm siempre; Gandalf y hechizos chicos rara vez
s = new([], []); s.ix = dict(BRACKETS["B3"][1])
check("Counter: Past in Flames, Mana Geyser y Prodigy 100%; Gandalf y Shock bajos",
      s.counter_p("Past in Flames") == 1 and s.counter_p("Mana Geyser") == 1 and s.counter_p("Harmonic Prodigy") == 1
      and s.counter_p("Gandalf") <= 0.15 and s.counter_p("Shock") == 0.02,
      [s.counter_p(x) for x in ("Past in Flames", "Mana Geyser", "Harmonic Prodigy", "Gandalf", "Shock")])
# 22 Barridas: el rival barre cuando la mesa de los demas supera la suya; no barre una mesa vacia temprano
s = new([], ["Harmonic Prodigy", "Ojer Axonil, Deepest Might", "Gandalf", "Tomik, Izzet Sparkmage"]); s.ix = dict(BRACKETS["B3"][1]); s.turn = 4
s.wipe_stock = [1, 0, 0]; s.opp_best_value = lambda: 0.3
check("Barre tu mesa grande (2.0) cuando los rivales tienen poco", s.rival_wipes(0) is True and s.wipe_stock[0] == 0, s.wipe_stock)
s = new([], ["Gandalf"]); s.ix = dict(BRACKETS["B3"][1]); s.turn = 4; s.wipe_stock = [1, 0, 0]; s.opp_best_value = lambda: 0.3
check("No barre por un Gandalf solo con mesas chicas", s.rival_wipes(0) is False and s.wipe_stock[0] == 1, s.wipe_stock)
# 23 Artist's Talent: entra en nivel 1 (filtra), {2}{R} para nivel 2 (-1 a no criaturas) y otro {2}{R} para nivel 3 (+2 de dano)
s = new(["Artist's Talent"], [], lands=8); s.cast("Artist's Talent", "hand")
l1 = s.artist; s.gandalf = "bf"; left = s.avail()[0] + s.avail()[1]
while ai.act_once(s, "allin", frozenset()): pass
check("Artist's Talent: nivel 1 gratis al entrar; con 6 de mana sube a 3 (+2 de dano) y gasta exactamente 6",
      l1 == 1 and s.artist == 3 and s.mod(1, True) == 3 and left - (s.avail()[0] + s.avail()[1]) == 6, (l1, s.artist, s.mod(1, True), left, s.avail()))
# 24 Ojer: removido vuelve como Temple of Power; con 4+ de dano rojo en el turno y {2}{R} vuelve a ser Ojer
s = new([], ["Ojer Axonil, Deepest Might"], lands=4); s.kill_perm(s.perms[0]); s.lands[-1]["tapped"] = False
s.dmg_turn = 0; a0 = s.temple_flip(); s.dmg_turn = 6; a1 = s.temple_flip()
check("Ojer vuelve desde Temple of Power solo con 4+ de dano en el turno", a0 is False and a1 is True and s.has("Ojer Axonil, Deepest Might") and not any(l["name"] == "Temple of Power" for l in s.lands), (a0, a1))
# 25 The Fire Crystal copia a Prodigy: Gandalf pinguea x3; la copia muere al final del turno
s = new(["Sol Ring"], ["Gandalf", "Harmonic Prodigy", "The Fire Crystal"], lands=7); f = s.fire_crystal(); s.cast("Sol Ring", "hand")
hit3 = s.opp == [37, 37, 37]; s.breach_cleanup()
check("Fire Crystal copia Prodigy: ping x3 y la copia se va al final del turno", f and hit3 and s.count("Harmonic Prodigy") == 1, (f, s.opp, s.count("Harmonic Prodigy")))
# 26 Grapeshot temprano: si con el storm actual mata a un rival (el que esta por ganar), se lanza ya
s = new(["Grapeshot", "Shock"], [], lands=4); s.opp = [40, 3, 40]; s.spells = 2; s.K = [99, 5, 99]
ok = ai.grapeshot_early(s)
check("Grapeshot temprano mata al rival a 3 de vida con storm 2", ok and s.opp[1] <= 0, s.opp)
# 27 Descartes situacionales: Blasphemous se guarda si la mesa rival es peligrosa; Redirect si hay un motor que proteger
s = new(["Blasphemous Act", "Redirect Lightning", "Mountain"], [], lands=7); s.ix = dict(BRACKETS["B3"][1]); s.turn = 7; s.K = [7, 99, 99]
keep_bl = s.card_value("Blasphemous Act"); s2 = new(["Blasphemous Act"], [], lands=7)
check("Blasphemous Act: se guarda con la mesa peligrosa (6), se descarta en goldfish (0)", keep_bl == 6 and s2.card_value("Blasphemous Act") == 0, (keep_bl, s2.card_value("Blasphemous Act")))
s3 = new([], ["Harmonic Prodigy"]); s4 = new([], ["Gandalf"])
check("Redirect: se guarda con Prodigy en mesa, descartable con solo Gandalf", s3.card_value("Redirect Lightning") == 6 and s4.card_value("Redirect Lightning") == 1)
# 28 Blasphemous Act cuesta 1 menos por criatura (tuyas + estimado rival) y reinicia las mesas rivales
s = new([], ["Gandalf"], lands=4); s.ix = dict(BRACKETS["B3"][1]); s.turn = 6
c6 = sum(s.cost("Blasphemous Act")); s2 = new([], [], lands=4)
check("Blasphemous Act: T6 en B3 cuesta 1 (1 tuya + 9 rivales); en goldfish sin criaturas cuesta 9", c6 == 1 and sum(s2.cost("Blasphemous Act")) == 9, (c6, s2.cost("Blasphemous Act")))
# 29 Underworld Breach: Lotus Petal se relanza desde el cementerio (ping de Gandalf + Treasure) quemando solo relleno
s = new([], ["Gandalf"], lands=2); s.breach = True; s.mode = "allin"
s.gy = ["Lotus Petal", "Mountain", "Mountain", "Ojer Axonil, Deepest Might", "Coruscation Mage", "Mountain", "Seething Song", "Grapeshot"]
n = 0
while any(x[0] == "Lotus Petal" and x[1] == "gy" for x in ai.candidates(s)) and n < 10:
    s.cast("Lotus Petal", "gy", alt="escape"); n += 1
check("Breach + Lotus Petal: 1 vuelta por cada 3 cartas de relleno, sin exiliar Seething Song ni Grapeshot",
      n == 1 and s.opp == [39, 39, 39] and "Seething Song" in s.gy and "Grapeshot" in s.gy, (n, s.opp, s.gy))

# ---- 30-34 Mazmorra (16/11): edictos, Strip Mine, remocion entre rivales que retrasa, golpes parciales, mesas viejas intactas ----
import table as T
from table import BRACKETS as BR
s = new([], ["Gandalf", "Coruscation Mage"]); s.ix = dict(BR["Mazmorra"][1]); s.perms.append(dict(name="Wizard token", tapped=False, wiz=True, red=False))
s.edict(); a = [p["name"] for p in s.perms]; s.edict(); b = [p["name"] for p in s.perms]; s.edict()
check("Edicto: sacrificas primero la ficha, luego Coruscation, y Gandalf al final (vuelve a la zona de mando)",
      "Wizard token" not in a and "Coruscation Mage" in a and b == ["Gandalf"] and s.gandalf == "cmd" and s.gandalf_edicted == 1, (a, b, s.gandalf))
s = new([], [], lands=4); s.lands.append(dict(name="Temple of Power", prod="R", tapped=False)); s.lose_land()
check("Strip Mine: destruye una Mountain (no el Temple of Power) y va al cementerio", len(s.lands) == 4 and "Mountain" in s.gy and any(l["name"] == "Temple of Power" for l in s.lands), s.lands)
s = new([], []); s.ix = dict(BR["Mazmorra"][1]); s.ix["rem_slows"] = 1.0; s.slow = [0, 0, 0]; s.mz_order = [0, 1, 2]
s.slow_rival(0); s.slow_rival(1)
check("Remocion entre rivales: va al mas rapido que no sea quien la tira (0 -> retrasa a 1; 1 -> retrasa a 0)", s.slow == [1, 1, 0], s.slow)
d16 = ["Mountain"] * 99
r_old = [T.play_table(d16, "E", 5000 + i, *BR["B3"])[0] for i in range(30)]
check("Mesas B1-B5 sin cambios: las claves nuevas no existen fuera de la Mazmorra", all(k not in BR["B3"][0] for k in ("p_partial", "retry", "rem_stop"))
      and all(k not in BR["B3"][1] for k in ("edict", "ld", "rem_slows")), BR["B3"])
part = sum(getattr(T.play_table(d16, "E", 7000 + i, *BR["Mazmorra"])[1], "partial_kills", 0) > 0 for i in range(200))
check("Golpes parciales: un mazo que no hace nada ve rivales eliminados por otro rival en algunas partidas", 10 < part < 150, part)
print(f"\n{len(FAILS)} fallas" + (": " + ", ".join(FAILS) if FAILS else ""))
