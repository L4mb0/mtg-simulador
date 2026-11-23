"""Pruebas del simulador de Gorma (mesa v2). Correr antes de cada lote: python3 tests.py"""
import random
from engine import Game, Perm, TableCfg
from scen import C
from cards import CARDS, COMMANDER

T = []
def test(f): T.append(f); return f

def gv2(turn=6, **kw):
    g = Game(["Forest"] * 99, random.Random(1), mode="table", cfg=C(rules=("rem",), bracket="B3", **kw))
    g.hand = []; g.turn = turn; g.bf = []; g.rem = [[], [], []]
    g._our = False
    return g

def put(g, name, counters=0):
    p = Perm(name=name, base=CARDS[name].get("p", 0), creature=CARDS[name]["t"] == "C", sick=False, counters=counters)
    g.bf.append(p); return p

def gorma(g, power=1):
    p = Perm(name=COMMANDER, base=1, creature=True, sick=False, counters=power - 1); g.bf.append(p); g.gorma_in_cmd = False
    return p

@test
def peso_gorma_sin_escalon():
    """Gorma de 5 y de 6 pesan casi lo mismo (antes: 25% -> 75% de la remocion al llegar a 6)"""
    g = gv2(); p = gorma(g, 5); a = g.w_perm(p); p.counters += 1; b = g.w_perm(p)
    assert abs((b - a) - 0.05) < 1e-9 and abs(b - 0.6) < 1e-9, (a, b)
    p.counters = 50; assert g.w_perm(p) == 0.9

@test
def pieza_menor_no_cambia_lo_que_ve_la_mesa():
    """agregar un Putrid Goblin (0,3) junto a Blood Artist (0,5) no cambia el valor que la mesa ve en nosotros"""
    g = gv2(); put(g, "Blood Artist"); a = g.us_value("cre")[0]
    put(g, "Putrid Goblin"); put(g, "Viscera Seer"); b = g.us_value("cre")[0]
    assert a == b, (a, b)

@test
def va_a_lo_mas_peligroso():
    g = gv2(turn=1); put(g, "Putrid Goblin"); put(g, "Blood Artist"); gorma(g, 2)
    assert g.best_ours("cre").name == "Blood Artist"
    gp = g.gorma(); gp.counters = 10          # Gorma de 11 = 0,85
    assert g.best_ours("cre").name == COMMANDER

@test
def guarda_si_solo_hay_fichas():
    g = gv2(turn=1, ); g.make_token("pest", 3); g.rem[0] = ["cre"]
    g.opp_best_value = lambda: 0.2
    assert g.rival_decides(0) is None

@test
def criaturas_no_tocan_altares():
    """con solo Phyrexian Altar (0,5) y fichas, la remocion de criaturas no tiene un blanco que valga"""
    g = gv2(turn=1); put(g, "Phyrexian Altar"); g.make_token("pest", 2)
    g.opp_best_value = lambda: 0.0
    assert g.us_value("cre")[0] < 0.5 and g.us_value("any")[1].name == "Phyrexian Altar"
    g.rem[0] = ["cre"]; assert g.rival_decides(0) is None
    g.rem[0] = ["ae", "ae"]; assert g.rival_decides(0)[1][1].name == "Phyrexian Altar"   # con 2 no se guarda la ultima

@test
def masticore_es_artefacto():
    g = gv2(); p = put(g, "Lesser Masticore"); assert g.legal(p, "ae") and g.legal(p, "cre")

@test
def edicto_cuesta_una_ficha():
    """edicto contra nosotros: sacrificamos la ficha, Gorma crece y Blood Artist drena"""
    g = gv2(); gp = gorma(g, 6); put(g, "Blood Artist"); g.make_token("pest")
    g.removal_on_us("edict", g.us_value("edict")[1])
    assert g.gorma() is not None and gp.counters == 6 and not g.tokens("pest") and sum(g.opp) == 119

@test
def edicto_contra_persist_vuelve():
    g = gv2(); put(g, "Putrid Goblin"); put(g, "Blood Artist")
    g.bf[1].counters = 0
    v, p = g.us_value("edict"); assert p.name == "Putrid Goblin"
    g.removal_on_us("edict", p)
    assert g.on_bf("Putrid Goblin") and next(q for q in g.bf if q.name == "Putrid Goblin").minus

@test
def reservas_al_ritmo_de_los_datos():
    """B3: cada rival ve 7 + 1,3 cartas por turno; al turno 8 robo ~0,88 remociones (5 de 99)"""
    tot = 0; N = 2000
    for s in range(N):
        g = Game(["Forest"] * 99, random.Random(s), mode="table", cfg=C(rules=("rem",), bracket="B3"))
        for t in range(1, 9):
            g.turn = t
            for i in range(3): g.v2_draws(i)
        tot += sum(len(x) for x in g.rem)
    per = tot / N / 3
    assert 0.80 < per < 0.96, per

@test
def mesa_vieja_no_cambia():
    g = Game(["Forest"] * 99, random.Random(1), mode="table", cfg=C())
    assert not hasattr(g, "rem")

@test
def heroic_intervention_salva():
    g = gv2(); gorma(g, 8); g.hand = ["Heroic Intervention"]; g.reserve = 2
    g.removal_on_us("cre", g.gorma())
    assert g.gorma() is not None and "Heroic Intervention" in g.gy

@test
def respuesta_al_instante_a_un_motor():
    g = gv2(p_inst=1.0); g._our = True; g.rem[1] = ["cre"]
    g.enter("Blood Artist")
    assert not g.on_bf("Blood Artist") and g.stats.get("rem_inst") == 1 and g.rem[1] == []

@test
def no_responde_a_lo_chico():
    g = gv2(p_inst=1.0); g._our = True; g.rem[1] = ["cre"]
    g.enter("Putrid Goblin")
    assert g.on_bf("Putrid Goblin") and g.rem[1] == ["cre"]

@test
def guarda_la_ultima_40():
    kept = 0
    for s in range(500):
        g = gv2(turn=1); g.rng.seed(s); put(g, "Blood Artist"); g.rem[0] = ["cre"]
        g.opp_best_value = lambda: 0.0
        kept += g.rival_decides(0) is None
    assert 160 < kept < 240, kept

@test
def altar_de_dementia_cierra():
    """Gorma + Putrid Goblin + Altar of Dementia, sin drenador ni Jarad: el loop muele y gana"""
    g = Game(["Forest"] * 99, random.Random(1), mode="goldfish")
    g.hand = []; g.bf = []; g.turn = 6
    gorma(g, 1); put(g, "Putrid Goblin"); put(g, "Altar of Dementia")
    assert g.try_win() and g.stats["closer"].endswith("mill")

@test
def sin_altar_no_cierra():
    g = Game(["Forest"] * 99, random.Random(1), mode="goldfish")
    g.hand = []; g.bf = []; g.turn = 6
    gorma(g, 1); put(g, "Putrid Goblin"); put(g, "Viscera Seer")
    assert not g.try_win()

def gcnt(stock=3, **kw):
    g = Game(["Forest"] * 99, random.Random(5), mode="table", cfg=C(rules=("rem", "cnt"), bracket="B3", **kw))
    g.hand = []; g.turn = 6; g.bf = []; g.rem = [[], [], []]
    g.blue = 1; g.cnt = [0, stock, 0]; g.cnt_ready = stock; g.blue_open = True; g._our = True
    return g

@test
def regla2_motor_siempre():
    g = gcnt(); assert g.counter_p("Blood Artist") == 1.0 and g.counter_try("Blood Artist") and g.cnt[1] == 2

@test
def regla2_lo_chico_casi_nunca():
    n = 0
    for s in range(1000):
        g = gcnt(); g.rng.seed(s); n += g.counter_try("Putrid Goblin")
    assert 20 < n < 90, n              # coste 2 -> 5%

@test
def regla2_la_pieza_que_cierra_es_clave():
    """con Gorma, Viscera Seer y Blood Artist en mesa, el Putrid Goblin que completa el combo es clave"""
    g = gcnt(); gorma(g, 1); put(g, "Viscera Seer"); put(g, "Blood Artist")
    assert g.completes_combo("Putrid Goblin") and g.counter_p("Putrid Goblin") == 1.0
    g2 = gcnt(); put(g2, "Viscera Seer")
    assert not g2.completes_combo("Putrid Goblin")

@test
def regla2_guarda_el_ultimo_para_la_victoria():
    kept = 0
    for s in range(400):
        g = gcnt(stock=1); g.rng.seed(s); kept += not g.counter_try("Blood Artist")
    assert 120 < kept < 200, kept
    g = gcnt(stock=1); assert g.counter_try("Putrid Goblin", win=True)   # en el turno del combo lo usa siempre

@test
def regla2_sin_mana_arriba_no():
    g = gcnt(); g.cnt_ready = 0; assert not g.counter_try("Blood Artist")

@test
def regla2_veil_salva_el_combo():
    g = gcnt(); g.hand = ["Veil of Summer"]; g.col = 1
    assert not g.counter_try("Putrid Goblin", win=True) and "Veil of Summer" in g.gy and g.cnt[1] == 3

@test
def regla2_counter_al_comandante_sube_impuesto():
    g = gcnt(); g.col = 10; g.gorma_in_cmd = True
    g.counter_p = lambda c: 1.0
    g.cast(COMMANDER)
    assert g.gorma() is None and g.gorma_in_cmd and g.tax == 2

@test
def regla2_contrarresta_en_el_turno_del_combo():
    g = gcnt(); gorma(g, 1); put(g, "Viscera Seer"); put(g, "Blood Artist")
    g.hand = ["Putrid Goblin"]; g.col = 2
    assert not g.try_win() and "Putrid Goblin" in g.gy and g.cnt[1] == 2

from scen import B as BR

def gfull(turn=6, **kw):
    g = Game(["Forest"] * 99, random.Random(7), mode="table", cfg=BR("B3", **kw))
    g.hand = []; g.turn = turn; g.bf = []; g.rem = [[], [], []]; g.cnt = [0, 0, 0]; g.wipe_stock = [0, 0, 0]
    g._our = False
    return g

@test
def regla3_no_barre_por_fichas():
    """tres fichas no justifican una barrida: los rivales la guardan"""
    g = gfull(turn=4); g.make_token("pest", 3); g.wipe_stock[0] = 1
    g.opp_best_value = lambda: 0.4
    g.v2_wipe_check(0); assert g.wipe_stock[0] == 1 and len(g.tokens("pest")) == 3

@test
def regla3_barre_mesa_grande_y_persist_vuelve():
    g = gfull(turn=7); gorma(g, 8); put(g, "Blood Artist"); put(g, "Putrid Goblin"); put(g, "Pitiless Plunderer")
    g.wipe_stock[0] = 1; g.opp_best_value = lambda: 0.3
    g.v2_wipe_check(0)
    assert g.wipe_stock[0] == 0 and g.gorma() is None and g.on_bf("Putrid Goblin") and not g.on_bf("Blood Artist")

@test
def regla3_heroic_frena_la_barrida():
    g = gfull(turn=7); gorma(g, 8); put(g, "Blood Artist"); g.wipe_stock[0] = 1; g.opp_best_value = lambda: 0.3
    g.hand = ["Heroic Intervention"]; g.reserve = 2
    g.v2_wipe_check(0); assert g.gorma() is not None and "Heroic Intervention" in g.gy

@test
def regla3_artefactos_sobreviven():
    g = gfull(turn=7); gorma(g, 8); put(g, "Phyrexian Altar"); put(g, "Blood Artist"); g.wipe_stock[0] = 1
    g.opp_best_value = lambda: 0.3
    g.v2_wipe_check(0); assert g.on_bf("Phyrexian Altar")

@test
def regla4_logistica_acumula_bien():
    g = gfull(turn=1); surv = 1.0; acc = {}
    for t in range(1, 13):
        surv *= 1 - g.attempt_p(t, 7.0); acc[t] = 1 - surv
    assert abs(acc[4] - 0.06) < 0.01 and abs(acc[6] - 0.36) < 0.01 and abs(acc[8] - 0.84) < 0.01

@test
def regla4_el_azul_frena_primero():
    g = gfull(); g.blue = 2; g.cnt = [0, 0, 1]; g.rem = [[], ["cre"], []]
    g.rng.random = lambda: 0.0
    assert g.v2_others_stop(0) and g.cnt[2] == 0 and g.rem[1] == ["cre"]

@test
def regla4_sin_reservas_nadie_frena():
    g = gfull(); g.blue = 2
    assert not g.v2_others_stop(0)

@test
def regla4_frenado_se_rearma():
    g = gfull(); g.rival_rearms(0)
    assert g.ready[0] == g.turn + 2 and g.retry[0] and g.rival_next[0] == 999

@test
def regla5_edictos_bajan_la_mesa_rival():
    g = gfull(turn=7, ); g.cfg.bracket = "B3"
    g.rng.gauss = lambda mu, s: mu
    a = g.opp_best_value()
    put(g, "Grave Pact"); g.make_token("pest", 4)
    for p in list(g.tokens("pest")): g.sacrifice(p)
    b = g.opp_best_value()
    assert abs((a - b) - 0.12) < 1e-9, (a, b)

@test
def regla6_rest_in_peace_corta_persist():
    g = gfull(); g.gy_locked = True; p = put(g, "Putrid Goblin"); g.sacrifice(p)
    assert not g.on_bf("Putrid Goblin") and "Putrid Goblin" not in g.gy

@test
def regla6_mite_quita_rest_in_peace():
    g = gfull(); g._our = True; g.gy_locked = True; put(g, "Haywire Mite"); g.cless = 1
    g.answer_gy_lock(); assert not g.gy_locked

@test
def regla6_vandalblast_y_persist_de_artefacto():
    g = gfull(); g.arth_turn = g.turn; g.gyh_turn = None
    put(g, "Phyrexian Altar"); put(g, "Lesser Masticore"); put(g, "Blood Artist")
    g.v2_hate()
    assert not g.on_bf("Phyrexian Altar") and g.on_bf("Lesser Masticore") and g.on_bf("Blood Artist")

@test
def regla7_sin_escalon_en_el_combate():
    """agregar una pieza menor no cambia a quien atacan"""
    g = gfull(turn=8); put(g, "Blood Artist"); a = g.best_ours("any")
    put(g, "Putrid Goblin"); assert g.best_ours("any") is a

def gmz(turn=5, **kw):
    g = Game(["Forest"] * 99, random.Random(11), mode="table", cfg=BR("Mazmorra", **kw))
    g.hand = []; g.turn = turn; g.bf = []; g.rem = [[], [], []]; g.cnt = [0, 0, 0]; g.wipe_stock = [0, 0, 0]
    g._our = False
    return g

@test
def mz_edicto_sacrifica_lo_que_menos_vale():
    """edicto de la Mazmorra: se va la ficha antes que Gorma o Blood Artist; con persist, la criatura vuelve"""
    g = gmz(); g.edict_rival = 1; gorma(g, 5); put(g, "Blood Artist"); g.make_token("pest")
    g.rng.random = lambda: 0.0
    g.mz_events(1)
    assert g.gorma() and g.on_bf("Blood Artist") and not g.tokens("pest")
    g2 = gmz(); g2.edict_rival = 1; gorma(g2, 5); put(g2, "Putrid Goblin"); g2.rng.random = lambda: 0.0
    g2.mz_events(1); assert g2.gorma() and g2.on_bf("Putrid Goblin")

@test
def mz_edicto_a_gorma_solo_va_a_la_zona_de_mando():
    g = gmz(); g.edict_rival = 1; gorma(g, 5); g.rng.random = lambda: 0.0
    g.mz_events(1); assert g.gorma() is None and g.gorma_in_cmd and g.tax == 2

@test
def mz_strip_mine_basica_primero():
    g = gmz(); g.strip_rival = 0; g.lands = ["Woodland Cemetery", "Forest", "Swamp"]; g.rng.random = lambda: 0.0
    g.mz_events(0); assert g.lands == ["Woodland Cemetery", "Forest"] and "Swamp" in g.gy

@test
def mz_remocion_entre_rivales_retrasa_al_mas_rapido():
    g = gmz(); g.mu = [6, 4, 5]; g.turbo = 1; g.rem = [["cre"], [], []]
    g.rival_decides = lambda i: ("cre", ("opp", 2))
    g.rng.random = lambda: 0.0
    g.v2_removal_phase(0)
    assert g.slowed[1] and not g.slowed[2]

@test
def mz_golpe_parcial_mata_a_un_rival():
    g = gmz(); g.rng.random = lambda: 0.0; g.rng.choice = lambda xs: xs[-1]
    assert g.mz_partial(0) and g.opp.count(0) == 1 and g.ready[0] == g.turn + 1

@test
def mz_corte_por_tiempo_gana_el_de_mas_vida():
    g = gmz(turn=7); g.life = 38; g.opp = [20, 25, 30]; g.rng.uniform = lambda a, b: 0.0
    g.mz_time(); assert g.won
    g2 = gmz(turn=7); g2.life = 20; g2.opp = [20, 25, 30]; g2.rng.uniform = lambda a, b: 0.0
    g2.mz_time(); assert g2.lost

@test
def mz_mesas_viejas_sin_claves():
    g = Game(["Forest"] * 99, random.Random(1), mode="table", cfg=BR("B3"))
    assert not g.mz

@test
def ballista_cierra_tras_el_loop():
    g = Game(["Forest"] * 99, random.Random(1), mode="goldfish"); g.hand = ["Walking Ballista"]; g.bf = []; g.turn = 6
    gorma(g, 1); put(g, "Putrid Goblin"); put(g, "Viscera Seer")
    assert g.try_win() and g.stats["closer"] == "ballista"

@test
def apprentice_y_chain_of_smog_ganan_sin_gorma():
    g = Game(["Forest"] * 99, random.Random(1), mode="goldfish"); g.hand = ["Chain of Smog"]; g.bf = []; g.turn = 4
    put(g, "Witherbloom Apprentice"); g.col = 2
    assert g.try_win() and g.stats["closer"] == "smog"

@test
def allosaurus_impide_counters_a_lo_verde():
    g = gcnt(); put(g, "Allosaurus Shepherd")
    assert not g.counter_try(COMMANDER, win=True) and g.counter_try("Putrid Goblin", win=True)

@test
def chord_cobra_x_mas_ggg_con_convoke():
    """Juan 17/11: Chord = X + GGG (X = valor de maná de la criatura); convoke paga 1 por criatura sin girar. Finale = XXGG"""
    g = gv2(); g.library = ["Putrid Goblin"]
    assert g.x_tutor_cost("Chord of Calling", "Putrid Goblin") == 5
    put(g, "Viscera Seer"); put(g, "Blood Artist")
    assert g.x_tutor_cost("Chord of Calling", "Putrid Goblin") == 3
    assert g.x_tutor_cost("Chord of Calling", "Aerie Ouphes") == 6
    assert g.x_tutor_cost("Chord of Calling", "Walking Ballista") == 1
    assert g.x_tutor_cost("Finale of Devastation", "Putrid Goblin") == 6

@test
def chord_en_desarrollo_paga_el_coste_real():
    """antes pagaba 3 fijos por cualquier criatura; ahora 3 de maná no alcanzan para Putrid Goblin sin criaturas"""
    g = gv2(); g.library = ["Putrid Goblin"]; g.hand = ["Chord of Calling"]; g.col, g.cless = 3, 0
    assert not g.dev_ok("Chord of Calling")
    g.col = 5; assert g.dev_ok("Chord of Calling") and g.cast("Chord of Calling")
    assert any(p.name == "Putrid Goblin" for p in g.bf) and g.col == 0

def gw(hand=(), bf=(), lib=("Forest",), gy=(), col=0, lands=()):
    g = Game(["Forest"] * 99, random.Random(1), mode="goldfish"); g.hand = list(hand); g.bf = []; g.turn = 6
    g.library = list(lib); g.gy = list(gy); g.col = col; g.cless = 0; g.lands = list(lands)
    gorma(g, 1)
    for c in bf: put(g, c)
    return g

@test
def pawn_da_mana_infinito():
    """22/11: Pawn of Ulamog + loop = Spawns infinitos; con 2 de color sobrante alcanza para devolver y activar a Jarad desde el cementerio"""
    g = gw(bf=("Putrid Goblin", "Viscera Seer", "Pawn of Ulamog"), gy=("Jarad, Golgari Lich Lord",), col=2, lands=("Swamp", "Forest"))
    assert g.try_win() and g.stats["closer"] == "inf+jaradgy"
    g = gw(bf=("Putrid Goblin", "Viscera Seer"), gy=("Jarad, Golgari Lich Lord",), col=2, lands=("Swamp", "Forest"))
    assert not g.try_win()

@test
def zealot_y_desperate_plea():
    """Zealot vigila hasta mandar a Zulaport al cementerio; Desperate Plea sacrifica la criatura enorme y lo devuelve al campo"""
    g = gw(hand=("Desperate Plea",), bf=("Putrid Goblin", "Umbral Collar Zealot"), lib=("Forest", "Zulaport Cutthroat"), col=2)
    assert g.try_win() and g.stats["closer"] == "plea"
    g = gw(hand=("Desperate Plea",), bf=("Putrid Goblin", "Umbral Collar Zealot"), lib=("Forest", "Zulaport Cutthroat"), col=1)
    assert not g.try_win()

@test
def zealot_y_morbid_lanzado_despues():
    """el drenador queda arriba con el vigilar; Morbid Opportunist lanzado después del loop lo roba (3 + 2 de maná)"""
    g = gw(hand=("Morbid Opportunist",), bf=("Putrid Goblin", "Umbral Collar Zealot"), lib=("Forest", "Blood Artist"), col=5)
    assert g.try_win() and g.stats["closer"] == "zealot-draw"
    g = gw(hand=("Morbid Opportunist",), bf=("Putrid Goblin", "Umbral Collar Zealot"), lib=("Forest", "Blood Artist"), col=4)
    assert not g.try_win()

@test
def greater_good_no_es_infinito():
    """con Greater Good como único outlet el loop no gana aunque haya drenador; cava hasta Altar of Dementia y lo baja"""
    g = gw(bf=("Putrid Goblin", "Greater Good", "Blood Artist"), lib=("Forest",), col=5)
    assert not g.try_win()
    g = gw(bf=("Putrid Goblin", "Greater Good"), lib=("Forest", "Altar of Dementia"), col=2)
    assert g.try_win() and g.stats["closer"] == "gg-dig"

@test
def garruks_uprising_cava_en_el_loop():
    """22/11: con Uprising en mesa, la criatura con persist vuelve con poder 4+ y roba en cada vuelta; 2 de maná para el drenador"""
    g = gw(bf=("Putrid Goblin", "Viscera Seer", "Garruk's Uprising"), lib=("Forest", "Zulaport Cutthroat"), col=2)
    assert g.try_win() and g.stats["closer"] == "uprising-dig"
    g = gw(bf=("Putrid Goblin", "Viscera Seer"), lib=("Forest", "Zulaport Cutthroat"), col=2)
    assert not g.try_win()

@test
def robo_por_muerte_cava_y_paga():
    """22/11b: Grim Haruspex + loop roba toda la biblioteca; hace falta maná para el drenador que aparezca"""
    g = gw(bf=("Putrid Goblin", "Viscera Seer", "Grim Haruspex"), lib=("Forest", "Zulaport Cutthroat"), col=2)
    assert g.try_win() and g.stats["closer"] == "deathdraw"
    g = gw(bf=("Putrid Goblin", "Viscera Seer", "Grim Haruspex"), lib=("Forest", "Zulaport Cutthroat"), col=1)
    assert not g.try_win()
    g = gw(hand=("Grim Haruspex",), bf=("Putrid Goblin", "Viscera Seer"), lib=("Forest", "Zulaport Cutthroat"), col=5)
    assert g.try_win() and g.stats["closer"] == "deathdraw"

@test
def skullclamp_con_altar_roba_infinito():
    """22/11b: Phyrexian Altar (maná por muerte) + Skullclamp (equipar 1, roba 2) = robo infinito; sin Clamp no hay cierre"""
    g = gw(bf=("Putrid Goblin", "Phyrexian Altar", "Skullclamp"), lib=("Forest", "Zulaport Cutthroat"), col=0)
    assert g.try_win() and g.stats["closer"] == "inf+deathdraw"
    g = gw(bf=("Putrid Goblin", "Phyrexian Altar"), lib=("Forest", "Zulaport Cutthroat"), col=0)
    assert not g.try_win()

if __name__ == "__main__":
    ok = 0
    for f in T:
        try:
            f(); ok += 1; print("ok   ", f.__name__)
        except Exception as ex:
            print("FALLA", f.__name__, repr(ex))
    print(f"{ok}/{len(T)} pruebas")
