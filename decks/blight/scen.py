from engine import TableCfg
from cards import PRECON_DECK

BASE = dict(clocks=((8, 10), (9, 11), (10, 12)), kinds=("combat", "combo", "combat"), p_removal=0.30,
            target="sometimes", p_counter=0.5, n_counters=1, combat=True, combat_start=5)


def C(**kw):
    d = dict(BASE)
    d.update(kw)
    return TableCfg(**d)


# Las mismas 18 mesas que Gorma; "combate" ahora es el tablero rival (crecimiento y tamaño de criaturas).
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
    "Combate fuerte": C(grow_combat=0.95, size=1.4, combat_start=4),
    "Mesa de combos (nadie ataca)": C(kinds=("combo", "combo", "combo")),
    "Amenazas difíciles de frenar (50%)": C(p_stoppable=0.5),
    "Amenazas fáciles de frenar (90%)": C(p_stoppable=0.9),
    "Pesimista": C(clocks=((7, 9), (8, 10), (9, 11)), p_removal=0.45, p_counter=0.7, n_counters=2, size=1.2),
    "Muy pesimista": C(clocks=((7, 9), (6, 8), (8, 10)), p_removal=0.5, target="always", p_counter=0.7,
                       n_counters=2, size=1.4, combat_start=4),
    "Optimista": C(clocks=((10, 12), (11, 13), (12, 14)), p_removal=0.15, target="spread", p_counter=0.3,
                   combat=False),
}
ACTUAL = PRECON_DECK
MESAS4 = ["Realista (base)", "Pesimista", "Rivales rápidos (6-10)", "Optimista"]


# Mesa v2 por bracket (16/11/2026, mesa2.py). Reemplaza a las mesas viejas y a la columna calibrada.
BRACKET_NAMES = ["B1", "B2", "B3", "B3+B4", "B4", "B5"]
for _b in BRACKET_NAMES:
    SCEN[_b] = C(v2=_b)
