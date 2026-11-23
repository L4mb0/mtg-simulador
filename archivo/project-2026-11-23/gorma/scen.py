from engine import TableCfg
from cards import target_deck, swap
BASE = dict(clocks=((8, 10), (9, 11), (10, 12)), p_removal=0.30, target="sometimes", combat=True,
            kinds=("combat", "combo", "combat"), combat_k=2.0, combat_start=5, p_counter=0.5, n_counters=1)
def C(**kw):
    d = dict(BASE); d.update(kw); return TableCfg(**d)
SCEN = {
 "Realista (base)": C(),
 "Rivales rápidos (6-10)": C(clocks=((6, 8), (7, 9), (8, 10))),
 "Rivales lentos (10-14)": C(clocks=((10, 12), (11, 13), (12, 14))),
 "Un rival de combo al turno 6-8": C(clocks=((9, 11), (6, 8), (10, 12))),
 "Remoción baja": C(p_removal=0.15),
 "Remoción alta": C(p_removal=0.50),
 "Siempre eres el blanco": C(target="always"),
 "Blanco repartido": C(target="spread"),
 "Azul débil (30%, 1 counter)": C(p_counter=0.3, n_counters=1),
 "Azul fuerte (70%, 2 counters)": C(p_counter=0.7, n_counters=2),
 "Sin combate contra ti": C(combat=False),
 "Combate fuerte": C(combat_k=3.0, combat_start=4),
 "Mesa de combos (nadie ataca)": C(kinds=("combo", "combo", "combo")),
 "Amenazas difíciles de frenar (50%)": C(p_stoppable=0.5),
 "Amenazas fáciles de frenar (90%)": C(p_stoppable=0.9),
 "Pesimista": C(clocks=((7, 9), (8, 10), (9, 11)), p_removal=0.45, target="sometimes", p_counter=0.7, n_counters=2, combat_k=2.5),
 "Muy pesimista": C(clocks=((7, 9), (6, 8), (8, 10)), p_removal=0.5, target="always", p_counter=0.7, n_counters=2, combat_k=3.0, combat_start=4),
 "Optimista": C(clocks=((10, 12), (11, 13), (12, 14)), p_removal=0.15, target="spread", p_counter=0.3, combat=False),
}
# mesa v2 por reglas (16/11): por ahora solo la regla 1 ("rem") sobre la realista
SCEN["Realista + regla 1 (B3)"] = C(rules=("rem",), bracket="B3")
SCEN["Realista + reglas 1-2 (B3)"] = C(rules=("rem", "cnt"), bracket="B3")
ACTUAL = swap(target_deck(), "Woodfall Primus", "Woe Strider")  # Gorma 1.0 (lista objetivo del 10/11)
SWAPS_11 = [("Merchant of Venom", "Dina's Guidance"), ("Gyre Sage", "Aerie Ouphes"),
            ("Wight of the Reliquary", "Wingrattle Scarecrow"), ("Bloodghast", "Lesser Masticore"),
            ("Blight Mound", "Spawning Pit"), ("Nether Traitor", "Carrion Feeder"),
            ("Dina, Essence Brewer", "Bloodthrone Vampire"), ("Ophiomancer", "Lingering Tormentor"),
            ("Eccentric Pestfinder", "Bastion of Remembrance"), ("Pawn of Ulamog", "Vengeful Bloodwitch")]
CONS = ACTUAL
for _o, _i in SWAPS_11:
    CONS = swap(CONS, _o, _i)

# mesa v2 completa (16/11): las 7 reglas, por bracket
V2 = ("rem", "cnt", "wipe", "clock", "edict", "hate", "combat")
def B(br, **kw):
    return C(rules=V2, bracket=br, **kw)
for _b in ("B1", "B2", "B3", "B4", "B5", "B3+B4"):
    SCEN[_b] = B(_b)

# Mesa Mazmorra (torneo B3 de la tienda; claude/mesa-mazmorra.md) y sus variantes
# Juan (17/11): sin limite de tiempo en ningun caso; toda partida termina en victoria de alguien
SCEN["Mazmorra"] = B("Mazmorra", time_limit=False)
SCEN["Mazmorra optimista"] = B("Mazmorra", time_limit=False, mz_mus=(4, 5, 7))
SCEN["Mazmorra pesimista"] = B("Mazmorra", time_limit=False, mz_mus=(3, 5, 6))
SCEN["Mazmorra con tiempo"] = B("Mazmorra")
