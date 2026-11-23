"""Scenarios, same definitions as the Gorma simulator (BASE = mesa realista de la tienda de Juan)."""
from engine import TableCfg

BASE = dict(clocks=((8, 10), (9, 11), (10, 12)), p_removal=0.30, target="sometimes", combat=True,
            kinds=("combat", "combo", "combat"), combat_k=2.0, combat_start=5, p_counter=0.5, n_counters=1)

SCEN = {
    "Realista": dict(BASE),
    "Pesimista": dict(BASE, clocks=((7, 9), (8, 10), (9, 11)), p_removal=0.45, target="always", n_counters=2),
    "Rivales rápidos": dict(BASE, clocks=((6, 8), (7, 9), (8, 10))),
    "Rivales lentos": dict(BASE, clocks=((10, 12), (11, 13), (12, 14))),
    "Optimista": dict(BASE, clocks=((10, 12), (11, 13), (12, 14)), p_removal=0.15, n_counters=0),
    "Mucho removal": dict(BASE, p_removal=0.50),
    "Sin combate rival": dict(BASE, combat=False),
    "Combate fuerte": dict(BASE, combat_k=3.0),
    "Mesa de vuelo": dict(BASE, p_air=0.9, air_rate=0.6),
    "Sin vuelo rival": dict(BASE, p_air=0.0),
    "Nos apuntan": dict(BASE, target="always"),
    "Reparto parejo": dict(BASE, target="spread"),
    "Todo imparable": dict(BASE, p_stoppable=0.0),
    "Todo parable": dict(BASE, p_stoppable=1.0),
    "Dos counters": dict(BASE, n_counters=2),
    "Sin wipe": dict(BASE, wipe_window=(99, 99)),
    "Wipe temprano": dict(BASE, wipe_window=(5, 7)),
    "Todos combate": dict(BASE, kinds=("combat", "combat", "combat")),
}


def cfg(name, **over):
    d = dict(SCEN[name])
    d.update(over)
    return TableCfg(**d)

# ---- mesa v2 por bracket (16/11/2026, mesa.py): mismos parámetros que Gandalf y Blor ----
WT_CASUAL = (("combat", 0.66), ("dmg", 0.10), ("loss", 0.09), ("combo", 0.15))
WT_B4 = (("combat", 0.55), ("dmg", 0.10), ("loss", 0.10), ("combo", 0.25))
WT_B5 = (("combat", 0.25), ("dmg", 0.05), ("loss", 0.05), ("combo", 0.65))
WB_CASUAL = (("combat", 0.49), ("dmg", 0.05), ("loss", 0.05), ("combo", 0.41))
WB_B4 = (("combat", 0.40), ("dmg", 0.05), ("loss", 0.05), ("combo", 0.50))
WB_B5 = (("combat", 0.15), ("dmg", 0.03), ("loss", 0.02), ("combo", 0.80))
_V2 = dict(BASE, combat_k=2.0, combat_start=5)
BRACKETS = {
    "B1": dict(_V2, bracket="B1", mus=(10, 11, 12), win_types=WT_CASUAL, win_blue=WB_CASUAL, aem=0.2, opp_curve=(-0.1, 0.1, 0.8), rem=5, cpt=1.1, wipes=2, cnt=3),
    "B2": dict(_V2, bracket="B2", mus=(9, 10, 11), win_types=WT_CASUAL, win_blue=WB_CASUAL, aem=0.25, opp_curve=(0.0, 0.1, 0.9), rem=5, cpt=1.2, wipes=2, cnt=3),
    "B3": dict(_V2, bracket="B3", mus=(7, 8, 9), win_types=WT_CASUAL, win_blue=WB_CASUAL, aem=0.3, opp_curve=(0.1, 0.1, 1.0), rem=5, cpt=1.3, wipes=2, cnt=5),
    "B4": dict(_V2, bracket="B4", mus=(5, 6, 7), win_types=WT_B4, win_blue=WB_B4, aem=0.35, opp_curve=(0.2, 0.1, 1.1), rem=5, cpt=1.5, wipes=2, cnt=7),
    "B5": dict(_V2, bracket="B5", mus=(3, 4, 4), win_types=WT_B5, win_blue=WB_B5, aem=0.4, opp_curve=(0.3, 0.1, 1.2), rem=4, cpt=2.0, wipes=1, cnt=10, n_blue=2),
    "B3+B4": dict(_V2, bracket="B3+B4", mus=(5, 8, 9), win_types=WT_CASUAL, win_blue=WB_CASUAL, aem=0.3, opp_curve=(0.1, 0.1, 1.0), rem=5, cpt=1.4, wipes=2, cnt=6),
}
SCEN.update(BRACKETS)
