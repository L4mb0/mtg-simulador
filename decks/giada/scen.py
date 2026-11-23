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
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", ".."))
from core import mesa as M
WT_CASUAL, WT_B4, WT_B5, WB_CASUAL, WB_B4, WB_B5 = M.WT_CASUAL, M.WT_B4, M.WT_B5, M.WB_CASUAL, M.WB_B4, M.WB_B5
_V2 = dict(BASE, combat_k=2.0, combat_start=5)
BRACKETS = {b: dict(_V2, **M.cfg_v2(b)) for b in M.BRACKET_NAMES}
SCEN.update(BRACKETS)
