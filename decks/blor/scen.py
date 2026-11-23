"""Tables: the same realistic table as Gorma/Giada/Blight Curse, plus voltron stress tests."""
import engine
from engine import TableCfg

_p_us = engine.Game.p_us


def _p_us_open(self):
    """target="open": rivals pile onto us when Blor is tapped (what Juan saw in Forge, 13/11/2026)."""
    if self.cfg.target == "open":
        b = self.blor
        if not b or (b.tapped and not self.cre_on("Seedborn Muse")):
            return 1.0
        return 0.75 if self.threatening() else 0.25
    return _p_us(self)


engine.Game.p_us = _p_us_open

BASE = dict(clocks=((8, 10), (9, 11), (10, 12)), p_removal=0.30, target="sometimes", combat=True,
            kinds=("combat", "combo", "combat"), combat_k=2.0, combat_start=5, p_counter=0.5, n_counters=1)

SCEN = {
    "Realista": dict(BASE),
    "Rivales lentos": dict(BASE, clocks=((10, 12), (11, 13), (12, 14))),
    "Optimista": dict(BASE, clocks=((10, 12), (11, 13), (12, 14)), p_removal=0.15, n_counters=0),
    "Pesimista": dict(BASE, clocks=((7, 9), (8, 10), (9, 11)), p_removal=0.45, target="always", n_counters=2),
    "Calibrada": dict(BASE, p_others=0.67),
    # voltron stress tests
    "Mucho quitaencantamientos": dict(BASE, p_removal=0.45, removal_mix=(0.8, 0.1, 0.1)),
    "Edictos": dict(BASE, removal_mix=(0.35, 0.45, 0.20)),
    "Barrida de exilio": dict(BASE, wipe_mix=(0.1, 0.2, 0.5, 0.2)),
    "Sin barrida": dict(BASE, wipe_window=(99, 99)),
    "Bloquean siempre": dict(BASE, p_block=0.9),
    "Combate fuerte": dict(BASE, combat_k=3.0),
    "Nos apuntan": dict(BASE, target="always"),
    "Mesa agresiva": dict(BASE, kinds=("combat", "combat", "combat"), combat_k=3.0, combat_start=4),
    "Agresiva y nos apuntan": dict(BASE, kinds=("combat", "combat", "combat"), combat_k=3.0, combat_start=4,
                                   target="always"),
    # rivals punish a tapped Blor (what Juan saw in Forge, 13/11)
    "Realista castiga": dict(BASE, target="open", deterrence=0.7),
    "Lentos castiga": dict(BASE, clocks=((10, 12), (11, 13), (12, 14)), target="open", deterrence=0.7),
    "Calibrada castiga": dict(BASE, p_others=0.67, target="open", deterrence=0.7),
    # Forge AI (13/11, Juan): every rival attacks the player whose Blor is tapped
    "Forge": dict(BASE, kinds=("combat", "combat", "combat"), combat_k=2.5, combat_start=4, target="open",
                  deterrence=0.7),
    "Edictos castiga": dict(BASE, target="open", deterrence=0.7, p_removal=0.35, removal_mix=(0.35, 0.45, 0.20)),
    "Forge edictos": dict(BASE, kinds=("combat", "combat", "combat"), combat_k=2.5, combat_start=4, target="open",
                          deterrence=0.7, p_removal=0.40, removal_mix=(0.35, 0.45, 0.20)),
    "Forge dura": dict(BASE, kinds=("combat", "combat", "combat"), combat_k=3.0, combat_start=4, target="open",
                       deterrence=0.5),
}


# ---- mesa v2 por bracket (14/11, reglas aprobadas por Juan una por una) ----
# curva de amenaza rival: min(v0 + 0,1*turno, vmax) (igual que Gandalf); interaccion: datos de 6532 mazos de Archidekt
# combate: rivales que castigan a Blor girado (target="open", disuasion 0,7), como se acordo el 13/11 (Juan: se queda)
BASE = dict(BASE, target="open", deterrence=0.7)
# regla 10 (15/11): como ganan los rivales. Playgroup.gg (ene-sep 2026, ~25-40 mil partidas casuales por mes):
# combate ~55% + dano de comandante ~10% + veneno ~1% -> combat 0.66; dano no de combate ~19% -> dmg 0.10 / loss 0.09
# (Playgroup no separa dano directo de perdida de vida: mitad y mitad, estimado); combo ~7% + alternativa ~6% + mill ~2% -> 0.15.
# Playgroup no lo separa por bracket: B4 y B5 corridos hacia el combo (estimado).
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", ".."))
from core import mesa as M
WT_CASUAL, WT_B4, WT_B5, WB_CASUAL, WB_B4, WB_B5 = M.WT_CASUAL, M.WT_B4, M.WT_B5, M.WB_CASUAL, M.WB_B4, M.WB_B5
BRACKETS = {b: dict(BASE, **M.cfg_v2(b)) for b in M.BRACKET_NAMES}
# ---- mesa "Mazmorra" (torneo B3 de La Mazmorra TCG; portada 19/11) ----
# Receta única de core.mesa.MAZMORRA (23/11): base B4 + lo observado. Regla 8 (tiempo): apagada.
_Z = M.MAZMORRA
MZ = dict(BASE, **M.cfg_v2("Mazmorra"), mz=True, spread=_Z["spread"])
BRACKETS["Mazmorra"] = MZ
for _n, _v in M.MAZMORRA_VARIANTES.items():
    BRACKETS[_n] = dict(MZ, **_v)
SCEN.update(BRACKETS)


def cfg(name, **over):
    d = dict(SCEN[name])
    d.update(over)
    return TableCfg(**d)
