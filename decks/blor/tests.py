"""Pruebas de reglas del simulador de Blor (mesa v2). Correr antes de cada lote: python3 tests.py"""
import random
from engine import Game, Perm, TableCfg, B
from scen import cfg

def g0(turn=6, mode="table", **kw):
    g = Game(["Forest"] * 99, random.Random(1), mode=mode, cfg=cfg("Realista", **kw))
    g.hand = []; g.turn = turn
    g.blor = Perm(name=B, p=3, x=3, sick=False); g.blor_zone = "bf"
    for _ in range(8):
        g.lands.append(dict(name="Forest", aura=0, dep=0, tapped_entry=False))
    return g

def eq(g, n):
    g.equips.append(dict(name=n, on=True)); return g.equips[-1]

T = []
def test(f): T.append(f); return f

@test
def peso_sin_escalon():
    """un Blor de 9 y uno de 10 pesan casi lo mismo (antes: 25% -> 75% de la remocion)"""
    g = g0(); g.blor.counters = 6; a = g.w_blor(); g.blor.counters = 7; b = g.w_blor()
    assert 0 < b - a < 0.06, (a, b)

@test
def peso_crece_con_dano():
    g = g0(mode="goldfish"); assert abs(g.w_blor() - (0.2 + 3 / 25)) < 1e-9
    g.blor.counters = 7; assert abs(g.w_blor() - 0.6) < 1e-9          # 10 de poder sin bloqueo = 0,6
    g.blor.counters = 50; assert g.w_blor() == 1.2                      # tope

@test
def doble_golpe_duplica():
    g = g0(mode="goldfish"); g.blor.counters = 5                        # 8 de poder
    a = g.blor_hit(); eq(g, "Fireshrieker"); b = g.blor_hit()
    assert b == 2 * a, (a, b)

@test
def doble_golpe_contra_bloqueador():
    """con doble golpe y arrollar, el primer paso mata al bloqueador y el segundo entra entero"""
    g = g0(turn=9); g.blor.counters = 7                                 # 10 de poder, bloqueador esperado 0,55*6=3,3
    a = g.blor_hit(); eq(g, "Fireshrieker"); b = g.blor_hit()
    assert abs(a - (10 - 3.3)) < 1e-6 and abs(b - (10 - 3.3 + 10)) < 1e-6, (a, b)

@test
def toque_mortal_reduce_lo_que_absorbe():
    g = g0(turn=9); g.blor.counters = 7
    a = g.blor_hit(); eq(g, "Basilisk Collar"); b = g.blor_hit()
    assert abs(b - (10 - 1)) < 1e-6 and b > a, (a, b)                  # Collar no da poder: el bloqueador absorbe 1 en vez de 3,3

@test
def imbloqueable_no_absorbe():
    g = g0(turn=9); g.blor.counters = 7; a = g.blor_hit()
    g.auras.append("Indomitable Might"); b = g.blor_hit()
    assert b == 13 and a < 10, (a, b)

@test
def genji_y_flail_multiplican():
    g = g0(mode="goldfish"); g.blor.counters = 2                        # 5
    eq(g, "Genji Glove"); assert g.blor_hit() == 2 * (2 * 5)            # Genji: doble golpe y un combate extra
    eq(g, "Inquisitor's Flail"); assert g.blor_hit() == 2 * 2 * (2 * 5)

@test
def unnatural_growth_duplica():
    g = g0(mode="goldfish"); g.blor.counters = 2; a = g.blor_hit()
    g.enchs.append("Unnatural Growth"); assert g.blor_hit() == 2 * a

@test
def peso_de_adjunto_es_lo_que_baja():
    g = g0(mode="goldfish"); g.blor.counters = 10                        # 13
    e = eq(g, "Leyline Axe")                                             # +1 y doble golpe: 14 x2 = 28 -> 1,2
    w = g.w_attach("equip", e)
    assert abs(w - (1.2 - (0.2 + 13 / 25))) < 1e-9, w
    assert e["on"] and g.w_blor() == 1.2                                 # no deja el estado cambiado

@test
def pisos():
    g = g0(mode="goldfish")
    g.enchs.append("Unnatural Growth")
    assert g.w_perm("The Earth Crystal") == 0.5 and g.w_perm("Unnatural Growth") == 0.5
    e = eq(g, "Genji Glove"); assert g.w_attach("equip", e) >= 0.4
    assert g.w_perm("Llanowar Elves") == 0.1 and g.w_perm("Silent Arbiter") == 0.4

@test
def earth_crystal_activa_y_duplica():
    g = g0(mode="goldfish"); g.arts.append(dict(name="The Earth Crystal", used=False))
    g.W, g.Cl = 6, 0
    assert g.use_utilities(0) and g.blor.counters == 4                  # 2 contadores, duplicados
    assert not g.use_utilities(0)                                        # una vez por turno ({T})

@test
def rival_frustrado_apunta_al_mejor_adjunto():
    """regla 1-B: contra Blor grande, su mejor adjunto vale lo que pesa Blor"""
    g = g0(mode="goldfish"); g.blor.counters = 7                         # 10
    g.auras.append("Blanchwood Armor"); g.auras.append("Rancor")         # +8 y +2 -> 20
    w, kind, obj = g.w_attach_target()
    assert obj == "Blanchwood Armor" and abs(w - g.w_blor()) < 1e-9, (w, obj)

@test
def sin_adjuntos_no_hay_blanco():
    g = g0(mode="goldfish"); assert g.w_attach_target() is None

@test
def regla2_plan_visible_y_archienemigo():
    g = g0(mode="goldfish")                                               # 3/3 sin dano hecho
    assert abs(g.w_seen(0) - (g.w_blor() + 0.1)) < 1e-9
    g.cmd = [21, 0, 0]; g.opp = [19, 40, 40]                              # 21 de comandante a un rival
    lost = 21 / 120
    assert abs(g.w_seen(0) - (g.w_blor() + 0.1 + 0.3 * lost + 0.5)) < 1e-9
    assert abs(g.w_seen(1) - (g.w_blor() + 0.1 + 0.3 * lost)) < 1e-9      # cada rival lo ve distinto (D)

@test
def regla2_sin_blor_no_hay_peso():
    g = g0(); g.blor = None; assert g.w_seen(0) is None

@test
def regla2_curva_rival():
    g = g0(turn=7, opp_curve=(0.1, 0.1, 1.0), opp_noise=0.0)
    assert abs(g.opp_best_value() - 0.8) < 1e-9
    g.opp_wiped_t = 5; assert abs(g.opp_best_value() - 0.3) < 1e-9      # tras una barrida reconstruye

@test
def regla3_reservas_al_ritmo_de_los_datos():
    """B3: cada rival ve 7 + 1,3 cartas por turno; al turno 8 robo ~0,88 remociones (5 de 99)"""
    import engine
    tot = 0; N = 3000
    for s in range(N):
        g = Game(["Forest"] * 99, random.Random(s), mode="table", cfg=cfg("B3"))
        for t in range(1, 9):
            g.turn = t
            for i in range(3): g.opp_draws(i)
        tot += sum(len(x) for x in g.rem)
    per = tot / N / 3
    assert 0.80 < per < 0.96, per

@test
def regla3_mesa_vieja_no_cambia():
    """sin bracket no hay reservas (y no se consume azar extra)"""
    g = Game(["Forest"] * 99, random.Random(1), mode="table", cfg=cfg("Realista"))
    assert not hasattr(g, "rem")

def gv2(turn=7, **kw):
    g = Game(["Forest"] * 99, random.Random(3), mode="table", cfg=cfg("B3", opp_noise=0.0, **kw))
    g.hand = []; g.turn = turn
    g.blor = Perm(name=B, p=3, x=3, sick=False); g.blor_zone = "bf"
    for _ in range(8):
        g.lands.append(dict(name="Forest", aura=0, dep=0, tapped_entry=False))
    g.rem = [[], [], []]
    return g

@test
def regla4_criaturas_no_tocan_a_blor():
    """remocion de criaturas: Blor es ilegal; contra solo elfos (0,1) no la gasta en nosotros"""
    g = gv2(turn=2); g.cres.append(Perm(name="Llanowar Elves", p=1, x=1, sick=False))
    g.rem[0] = ["cre"]
    g.rival_removal_phase(0)
    assert len(g.cres) == 1 and g.blor is not None

@test
def regla4_guarda_si_nada_vale():
    """turno 1: los rivales valen poco y Blor es un 3/3: nadie gasta"""
    g = gv2(turn=1); g.rem[0] = ["any"]
    g.rival_removal_phase(0)
    assert g.rem[0] == ["any"]

@test
def regla4_adjunto_de_blor_grande():
    """Blor grande y rivales chicos: la remocion de permanentes va a su mejor adjunto (regla 1-B)"""
    g = gv2(turn=2); g.blor.counters = 7
    g.auras += ["Blanchwood Armor", "Rancor"]
    g.rem[0] = ["any"]
    g.rival_removal_phase(0)
    assert "Blanchwood Armor" not in g.auras and "Rancor" in g.auras

@test
def regla4_edicto_con_fodder_no_va_a_blor():
    g = gv2(turn=2); g.blor.counters = 20; g.cres.append(Perm(name="Llanowar Elves", p=1, x=1, sick=False))
    g.rem[0] = ["edict"]
    g.rival_removal_phase(0)
    assert g.blor is not None and len(g.cres) == 1 and g.rem[0] == ["edict"]

@test
def regla4_edicto_contra_blor_solo():
    g = gv2(turn=2); g.blor.counters = 20; g.rem[0] = ["edict"]
    g.rival_removal_phase(0)
    assert g.blor is None and g.tax == 2

@test
def regla4_heroic_intervention_salva():
    g = gv2(turn=2); g.blor.counters = 7; g.auras.append("Blanchwood Armor")
    g.hand = ["Heroic Intervention"]; g.reserve = 2; g.rem[0] = ["ae"]
    g.rival_removal_phase(0)
    assert "Blanchwood Armor" in g.auras and "Heroic Intervention" in g.gy

@test
def regla4_respuesta_al_instante_al_equipar():
    """equipar algo que dispara a Blor: un rival con remocion de artefactos la usa en respuesta (p_instant=1)"""
    g = gv2(turn=2, p_instant=1.0); g.blor.counters = 2; g._our = True
    g.rem[1] = ["ae"]
    g.equips.append(dict(name="Genji Glove", on=False)); g.W = 10
    g.attach_equip(g.equips[0])
    assert not g.equips and "Genji Glove" in g.gy and g.stats.get("instant") == 1

@test
def regla6_edicto_a_cada_oponente_nos_alcanza():
    """un edicto 'cada oponente' gastado en otro rival tambien nos hace sacrificar: con un elfo, se va el elfo"""
    g = gv2(turn=9, p_edict_each=1.0); g.cres.append(Perm(name="Llanowar Elves", p=1, x=1, sick=False))
    g.rem[0] = ["edict"]
    g.rival_removal_phase(0)
    assert g.blor is not None and not g.cres and g.stats.get("edict_each_hits_us") == 1

@test
def regla6_edicto_dirigido_no_nos_alcanza():
    g = gv2(turn=9, p_edict_each=0.0); g.cres.append(Perm(name="Llanowar Elves", p=1, x=1, sick=False))
    g.rem[0] = ["edict"]
    g.rival_removal_phase(0)
    assert len(g.cres) == 1

@test
def regla6_tajuru_para_el_edicto():
    g = gv2(turn=2); g.blor.counters = 20
    g.cres.append(Perm(name="Tajuru Preserver", p=2, x=1, sick=False))
    g.removal_on_us("edict")
    assert g.blor is not None and len(g.cres) == 1

@test
def regla7_destruir_no_cuenta_a_blor():
    """Blor enorme y solo: una barrida de destruir no nos quita nada; una de exilio vale todo Blor"""
    g = gv2(turn=4); g.blor.counters = 10
    assert g.wipe_value_us("destroy", 0) == 0.0 and g.wipe_value_us("exile", 0) >= 0.6

@test
def regla7_elige_la_barrida_que_mas_quita():
    g = gv2(turn=4, opp_curve=(0.6, 0.0, 0.6)); g.blor.counters = 10
    g.wipe_stock[0] = ["destroy", "exile"]
    assert g.rival_wipes(0) and g.blor is None and g.wipe_stock[0] == ["destroy"]

@test
def regla7_no_barre_si_no_gana_nada():
    """mesa vacia de los rivales y Blor indestructible: con solo destruir en mano, no barre"""
    g = gv2(turn=4, opp_curve=(0.6, 0.0, 0.6)); g.blor.counters = 10
    g.wipe_stock[0] = ["destroy"]
    assert not g.rival_wipes(0) and g.wipe_stock[0] == ["destroy"]

@test
def regla7_menos_x_segun_resistencia():
    g = gv2(turn=4); g.blor.counters = 5      # 8/8
    assert g.wipe_value_us("minus", 0) > 0
    g.blor.counters = 12                      # 15/15
    assert g.wipe_value_us("minus", 0) == 0.0

@test
def regla7_destruir_con_art_ench_quita_adjuntos_no_a_blor():
    g = gv2(turn=4, opp_curve=(0.8, 0.0, 0.8)); g.blor.counters = 4
    g.auras += ["Blanchwood Armor", "Rancor"]
    g.wipe_stock[0] = ["destroy_ae"]
    assert g.rival_wipes(0) and g.blor is not None and not g.auras

@test
def regla7_one_ring_no_para_barridas():
    g = gv2(turn=4, opp_curve=(0.6, 0.0, 0.6)); g.blor.counters = 10; g.ring_prot = True
    g.wipe_stock[0] = ["exile"]
    assert g.rival_wipes(0) and g.blor is None

@test
def regla8_vandalblast_deja_las_auras():
    g = gv2(turn=6); g.blor.counters = 3
    g.auras.append("Blanchwood Armor"); g.equips.append(dict(name="Commander's Plate", on=True))
    g.aem_stock[0] = ["art"]
    assert g.rival_aem(0) and g.auras == ["Blanchwood Armor"] and not g.equips and "Commander's Plate" in g.gy

@test
def regla8_tranquility_deja_los_equipos():
    g = gv2(turn=6); g.blor.counters = 3
    g.auras.append("Blanchwood Armor"); g.equips.append(dict(name="Shadowspear", on=True))
    g.aem_stock[0] = ["ench"]
    assert g.rival_aem(0) and not g.auras and len(g.equips) == 1

@test
def regla8_no_la_gasta_en_poco():
    """Blor desnudo con una roca: no vale la pena"""
    g = gv2(turn=6); g.arts.append(dict(name="Mind Stone"))
    g.aem_stock[0] = ["both"]
    assert not g.rival_aem(0) and g.aem_stock[0] == ["both"]

@test
def regla8_heroic_intervention_la_frena():
    g = gv2(turn=6); g.blor.counters = 3; g.auras += ["Blanchwood Armor", "Ancestral Mask"]
    g.hand = ["Heroic Intervention"]; g.reserve = 2; g.aem_stock[0] = ["both"]
    assert g.rival_aem(0) and len(g.auras) == 2 and "Heroic Intervention" in g.gy

def gcnt(**kw):
    g = gv2(turn=6, **kw); g.blue = [0]; g.cnt_stock = [3, 0, 0]; g._cnt_up = {0: True}
    return g

@test
def regla9_clave_siempre():
    g = gcnt(); g.blor.counters = 3
    assert g.spell_threat("Unnatural Growth") >= 0.5 and g.countered("Unnatural Growth") and g.cnt_stock[0] == 2

@test
def regla9_sin_mana_arriba_no():
    g = gcnt(); g._cnt_up = {0: False}
    assert not g.countered("Unnatural Growth")

@test
def regla9_conquerors_flail_lo_impide():
    g = gcnt(); g.equips.append(dict(name="Conqueror's Flail", on=True))
    assert not g.countered("Unnatural Growth") and g.cnt_stock[0] == 3

@test
def regla9_allosaurus_shepherd_protege_lo_verde():
    g = gcnt(); g.cres.append(Perm(name="Allosaurus Shepherd", p=1, x=1, sick=False))
    assert not g.countered("Unnatural Growth")
    g.blor = None; g.blor_zone = "cmd"
    assert not g.countered(B)

@test
def regla9_destiny_spinner_protege_auras_no_equipos():
    g = gcnt(); g.blor.counters = 3; g.cres.append(Perm(name="Destiny Spinner", p=2, x=3, sick=False))
    assert not g.countered("Unnatural Growth")
    assert g.spell_threat("Genji Glove") >= 0.4

@test
def regla9_guarda_el_ultimo():
    """con un solo counter y algo de 0,5, lo guarda el 40% de las veces"""
    kept = 0
    for s in range(400):
        g = gcnt(); g.rng.seed(s); g.blor.counters = 3; g.cnt_stock = [1, 0, 0]
        kept += not g.countered("Unnatural Growth")
    assert 120 < kept < 200, kept

@test
def regla9_blor_con_su_ultimo_counter():
    """el azul gasta su ultimo counter en Blor al bajar (cnt_blor=1)"""
    g = gcnt(cnt_blor=1.0); g.blor = None; g.blor_zone = "cmd"; g.cnt_stock = [1, 0, 0]
    assert g.countered(B) and g.cnt_stock[0] == 0

@test
def regla9_power_fist_es_clave():
    g = gcnt()
    assert g.is_key("Power Fist")

@test
def regla9_lo_que_vuelve_letal_es_clave():
    """un rival a 21 de comandante menos 5: lo que hace que el golpe llegue es clave aunque el peso suba poco"""
    g = gcnt(); g.blor.counters = 9; g.cmd = [10, 0, 0]
    assert g.blor_hit() < g.lethal_need() and g.is_key("Blanchwood Armor")

@test
def reductores_costo():
    g = gv2(turn=5)
    assert g.cost_of("Genji Glove") == (5, 0)
    g.cres.append(Perm(name="Foundry Inspector", p=3, x=2, sick=False))
    assert g.cost_of("Genji Glove") == (4, 0)
    g.arts.append(dict(name="Semblance Anvil", imprint="art"))
    assert g.cost_of("Genji Glove") == (2, 0) and g.cost_of("Blanchwood Armor") == (2, 1)
    g.arts[-1]["imprint"] = "aura"
    assert g.cost_of("Blanchwood Armor") == (0, 1)

@test
def hammer_of_nazahn_equipa_gratis():
    g = gv2(turn=5); g.equips.append(dict(name="Hammer of Nazahn", on=True))
    g.hand = ["Genji Glove"]; g.W = 0; g.Cl = 10
    g.cast("Genji Glove")
    assert any(e["name"] == "Genji Glove" and e["on"] for e in g.equips)

@test
def regla10_logistica_acumula_bien():
    """con mu=7 y dispersion 0,9: igual que Gandalf (6% al T4, 36% al T6, 84% al T8)"""
    g = gv2(turn=1)
    surv = 1.0; acc = {}
    for t in range(1, 13):
        surv *= 1 - g.attempt_p(t, 7.0); acc[t] = 1 - surv
    assert abs(acc[4] - 0.06) < 0.01 and abs(acc[6] - 0.36) < 0.01 and abs(acc[8] - 0.84) < 0.01

def gatt(wt, **kw):
    g = gv2(turn=6, **kw); g.wtype = [wt, "combo", "combo"]; g.mu = [1.0, 99, 99]; g.ready_t = [None] * 3
    g.cfg.p_stoppable = 0.0; g.hand = []
    return g

@test
def regla10_pariah_frena_combate_y_dano():
    for wt, safe in [("combat", True), ("dmg", True), ("loss", False), ("combo", False)]:
        g = gatt(wt); g.equips.append(dict(name="Pariah's Shield", on=True))
        g.rival_next = [g.turn, -1, -1]
        g.table_events(0)
        assert g.lost != safe, wt

@test
def regla10_se_rearma_tras_frenarlo():
    g = gatt("combo"); g.equips.append(dict(name="Pariah's Shield", on=True)); g.wtype[0] = "combat"
    g.rival_next = [g.turn, -1, -1]; g.table_events(0)
    assert not g.lost and g.ready_t[0] == g.turn + g.cfg.delay

@test
def regla10_helm_adelanta_a_los_rivales():
    g = gv2(turn=1); g.mu = [7.0, 7.0, 7.0]; g.ready_t = [None] * 3
    p0 = g.attempt_p(5, 7.0); p1 = g.attempt_p(5, 6.0)
    assert p1 > p0

@test
def regla11_otro_rival_frena_con_counter():
    """el azul (rival 1) frena el intento del rival 0 con su counter si dejo mana arriba (cnt_up=1)"""
    g = gatt("combo", cnt_up=1.0); g.blue = [1]; g.cnt_stock = [0, 2, 0]; g.rem = [[], [], []]
    g.rival_next = [g.turn, -1, -1]; g.table_events(0)
    assert not g.lost and g.cnt_stock[1] == 1 and g.stats.get("others_stop_cnt") == 1

@test
def regla11_sin_reservas_nadie_frena():
    g = gatt("combo"); g.blue = [1]; g.cnt_stock = [0, 0, 0]; g.rem = [[], [], []]
    g.rival_next = [g.turn, -1, -1]; g.table_events(0)
    assert g.lost

@test
def regla10_el_azul_gana_distinto():
    import random as R
    from collections import Counter
    b = Counter(); o = Counter()
    for s in range(600):
        g = Game(["Forest"] * 99, R.Random(s), mode="table", cfg=cfg("B3"))
        for i in range(3):
            (b if i in g.blue else o)[g.wtype[i]] += 1
    assert b["combo"] / sum(b.values()) > 0.33 and o["combo"] / sum(o.values()) < 0.06

@test
def whispersilk_shroud():
    g = gv2(turn=6); g.equips.append(dict(name="Whispersilk Cloak", on=True))
    g.equips.append(dict(name="Shadowspear", on=False)); g.hand = ["Rancor"]
    assert g.unblockable() and not g.dev_ok("Rancor") and not g.attach_equip(g.equips[1], free=True)

@test
def whispersilk_va_al_final():
    g = gv2(turn=6); g.equips.append(dict(name="Whispersilk Cloak", on=False)); g.hand = ["Rancor"]
    assert g.cloak_waits() and not g.attach_equip(g.equips[0])

@test
def darksteel_plate_sobrevive_vandalblast():
    g = gv2(turn=6); g.blor.counters = 3
    g.equips += [dict(name="Darksteel Plate", on=True), dict(name="Commander's Plate", on=True)]
    g.aem_stock[0] = ["art"]
    assert g.rival_aem(0) and [x["name"] for x in g.equips] == ["Darksteel Plate"]

@test
def crystal_chimes_devuelve_auras():
    g = gv2(turn=6); g.arts.append(dict(name="Crystal Chimes")); g.gy += ["Blanchwood Armor", "Ancestral Mask"]
    g.W = 0; g.Cl = 5; g.use_utilities(0)
    assert "Blanchwood Armor" in g.hand and "Ancestral Mask" in g.hand and "Crystal Chimes" in g.gy

@test
def talon_gates_fase_contra_farewell():
    g = gv2(turn=6, opp_curve=(0.8, 0.0, 0.8)); g.blor.counters = 6
    g.auras.append("Blanchwood Armor"); g.equips.append(dict(name="Shadowspear", on=True))
    g.hand = ["Talon Gates of Madara"]; g.reserve = 4; g.wipe_stock[0] = ["exile_ae"]
    assert g.rival_wipes(0) and g.blor is not None and g.auras == ["Blanchwood Armor"] and g.phased
    assert any(l["name"] == "Talon Gates of Madara" for l in g.lands)

@test
def archdruids_charm_busca_talon_contra_edicto():
    g = gv2(turn=6); g.hand = ["Archdruid's Charm"]; g.reserve = 3; g.library.append("Talon Gates of Madara")
    g.removal_on_us("edict")
    assert g.blor is not None and g.phased and "Archdruid's Charm" in g.gy

@test
def en_fase_no_se_puede_apuntar_adjuntos():
    g = gv2(turn=6); g.blor.counters = 6; g.auras.append("Blanchwood Armor"); g.phased = True
    assert g.our_target("ae", 0) is None or g.our_target("ae", 0)[1][0] not in ("aura", "equip")

@test
def shadowspear_rival_y_heroic():
    g = gv2(turn=8); g.blor.counters = 8; g.hate_on = [True, False, False]; g.rem[0] = ["cre"]
    g.hand = ["Heroic Intervention"]; g.reserve = 2
    assert g.hate_kills_blor(0) and g.blor is not None and g.stats.get("hate_heroic") == 1
    g2 = gv2(turn=8); g2.blor.counters = 8; g2.hate_on = [True, False, False]; g2.rem[0] = ["any"]; g2.hand = []
    assert g2.hate_kills_blor(0) and g2.blor is None

@test
def nightshade_peddler_da_toque_mortal():
    g = gv2(turn=6); assert not g.deathtouch()
    g.cres.append(Perm(name="Nightshade Peddler", p=1, x=1, sick=False)); assert g.deathtouch()

@test
def lure_con_toque_mortal_se_come_la_mesa():
    g = gv2(turn=9); g.blor.counters = 10; g.auras.append("Lure"); g.equips.append(dict(name="Basilisk Collar", on=True))
    g.wtype = ["combat"] * 3; g.ready_t = [None] * 3
    g.combat()
    assert g.stats.get("lure_wipes") == 1 and g.board_reset[g.stats["kills"][0] if g.stats["kills"] else 0] >= 0

@test
def toque_mortal_contra_bloqueador_enorme():
    g = gv2(turn=8); g.blor.counters = 9          # 12/12
    assert g.step_damage(12, 12) == (0, 0)
    g.equips.append(dict(name="Basilisk Collar", on=True))
    assert g.step_damage(12, 12) == (11, 0)

@test
def blowgun_toque_mortal_solo_en_tu_turno():
    g = gv2(turn=6); g.equips.append(dict(name="Hunter's Blowgun", on=True))
    g._our = True; assert g.deathtouch()
    g._our = False; assert not g.deathtouch()

# ---- mesa Mazmorra (19/11) ----
def gmz(turn=5, **kw):
    g = Game(["Forest"] * 99, random.Random(5), mode="table", cfg=cfg("Mazmorra", opp_noise=0.0, **kw))
    g.hand = []; g.turn = turn
    g.blor = Perm(name=B, p=3, x=3, sick=False); g.blor_zone = "bf"
    for _ in range(8):
        g.lands.append(dict(name="Forest", aura=0, dep=0, tapped_entry=False))
    g.rem = [[], [], []]; g.wipe_stock = [[], [], []]; g.aem_stock = [[], [], []]
    return g

@test
def mz_edicto_se_lleva_la_ficha_antes_que_blor():
    g = gmz(); g.mz_edictor = 1; g.mz_strip = None
    g.cres.append(Perm(name="Beast token", p=3, x=3, token=True, sick=False))
    g.cfg.mz_edict_p = 1.0; g.mz_events(1)
    assert g.blor and not g.cres
    g.mz_events(1)                                       # ya no hay ficha: Blor vuelve a la zona de mando
    assert g.blor is None and g.stats.get("mz_edict_blor") == 1

@test
def mz_strip_mine_basica_primero():
    g = gmz(); g.mz_edictor = None; g.mz_strip = 0; g.cfg.mz_strip_p = 1.0
    g.lands[0]["aura"] = 1; g.lands.append(dict(name="Rogue's Passage", aura=0, dep=0, tapped_entry=False))
    n = len(g.lands); g.mz_events(0)
    assert len(g.lands) == n - 1 and any(l["name"] == "Rogue's Passage" for l in g.lands)
    assert sum(l["aura"] for l in g.lands) == 1          # se lleva un Forest sin aura

@test
def mz_remocion_entre_rivales_retrasa_al_mas_rapido():
    g = gmz(mz_rem_slows=1.0); g.mu = [6, 4, 5]
    g.rem[0] = ["cre"]; g.blor = None
    g.opp_best_value = lambda: 1.0
    assert g.rival_uses_removal(0)
    assert g.slowed[1] and not g.slowed[2]

@test
def mz_golpe_parcial_mata_a_un_rival():
    g = gmz(turn=6, mz_partial=1.0, p_stoppable=0.0)
    g.cmd = [0, 0, 0]; g.mz_edictor = g.mz_strip = None
    g.rival_next = [6, -1, -1]; g.slowed = [False] * 3
    random.seed(0)
    lost = 0
    for s in range(40):
        g2 = gmz(turn=6, mz_partial=1.0, p_stoppable=0.0); g2.rng = random.Random(s)
        g2.mz_edictor = g2.mz_strip = None; g2.rival_next = [6, -1, -1]; g2.ready_t = [None] * 3
        g2.cnt_stock = [0, 0, 0]; g2.wtype = ["combo"] * 3
        g2.table_events(0)
        if g2.lost: lost += 1
        else: assert sum(1 for x in g2.opp if x <= 0) == 1 and g2.ready_t[0] == 7
    assert 5 < lost < 25, lost                           # ~1/3 de las veces eres tu

@test
def mz_turbo_rearma_en_un_turno():
    g = gmz(); g.turbo = 2
    assert g.dly(2) == 1 and g.dly(0) == 2

@test
def skullclamp_roba_dos_con_una_ficha():
    g = g0(mode="goldfish"); g.equips.append(dict(name="Skullclamp", on=False))
    g.make_token("Saproling token"); g.make_token("Saproling token")
    g.W = 1; n = len(g.hand)
    assert g.use_utilities(0) and len(g.hand) == n + 2 and len(g.cres) == 1

@test
def skullclamp_deja_un_fodder():
    g = g0(mode="goldfish"); g.equips.append(dict(name="Skullclamp", on=False))
    g.make_token("Saproling token"); g.W = 3; g.hand += ["Forest", "Forest"]
    assert not g.use_utilities(0) or len(g.cres) == 1

@test
def lotus_bloom_llega_en_tres_mantenimientos():
    g = g0(mode="goldfish"); g.bloom = [3]; t0 = g.treas
    g.upkeep(); g.upkeep(); assert g.treas == t0
    g.upkeep(); assert g.treas == t0 + 3

if __name__ == "__main__":
    ok = 0
    for f in T:
        try:
            f(); ok += 1; print("ok  ", f.__name__)
        except AssertionError as ex:
            print("FALLA", f.__name__, ex)
    print(f"{ok}/{len(T)} pruebas")
