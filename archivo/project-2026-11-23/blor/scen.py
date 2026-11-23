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
WT_CASUAL = (("combat", 0.66), ("dmg", 0.10), ("loss", 0.09), ("combo", 0.15))
WT_B4 = (("combat", 0.55), ("dmg", 0.10), ("loss", 0.10), ("combo", 0.25))
WT_B5 = (("combat", 0.25), ("dmg", 0.05), ("loss", 0.05), ("combo", 0.65))
# el azul (Juan 15/11): comandantes azules en Playgroup (180 dias, 9.344 partidas): combate 41,0 + comandante 6,4 + veneno 1,8
# -> 0.49; dano no de combate 10,1 -> 0.05 / 0.05; alternativa 17,5 + combo 12,0 + mill 11,2 -> 0.41. B4/B5 corridos al combo.
WB_CASUAL = (("combat", 0.49), ("dmg", 0.05), ("loss", 0.05), ("combo", 0.41))
WB_B4 = (("combat", 0.40), ("dmg", 0.05), ("loss", 0.05), ("combo", 0.50))
WB_B5 = (("combat", 0.15), ("dmg", 0.03), ("loss", 0.02), ("combo", 0.80))
BRACKETS = {
    "B1": dict(BASE, bracket="B1", win_blue=WB_CASUAL, mus=(10, 11, 12), win_types=WT_CASUAL, aem=0.2, opp_curve=(-0.1, 0.1, 0.8), rem=5, cpt=1.1, wipes=2, cnt=3),
    "B2": dict(BASE, bracket="B2", win_blue=WB_CASUAL, mus=(9, 10, 11), win_types=WT_CASUAL, aem=0.25, opp_curve=(0.0, 0.1, 0.9), rem=5, cpt=1.2, wipes=2, cnt=3),
    "B3": dict(BASE, bracket="B3", win_blue=WB_CASUAL, mus=(7, 8, 9), win_types=WT_CASUAL, aem=0.3, opp_curve=(0.1, 0.1, 1.0), rem=5, cpt=1.3, wipes=2, cnt=5),
    "B4": dict(BASE, bracket="B4", win_blue=WB_B4, mus=(5, 6, 7), win_types=WT_B4, aem=0.35, opp_curve=(0.2, 0.1, 1.1), rem=5, cpt=1.5, wipes=2, cnt=7),
    "B5": dict(BASE, bracket="B5", win_blue=WB_B5, mus=(3, 4, 4), win_types=WT_B5, aem=0.4, opp_curve=(0.3, 0.1, 1.2), rem=4, cpt=2.0, wipes=1, cnt=10, n_blue=2),
    "B3+B4": dict(BASE, bracket="B3+B4", win_blue=WB_CASUAL, mus=(5, 8, 9), win_types=WT_CASUAL, aem=0.3, opp_curve=(0.1, 0.1, 1.0), rem=5, cpt=1.4, wipes=2, cnt=6),
}
# ---- mesa "Mazmorra" (torneo B3 de La Mazmorra TCG; claude/mesa-mazmorra.md, receta del 16/11; portada 19/11) ----
# reglas 1-3: relojes 4/5/6 (dispersion 1,0), 7 remociones, azul con 8 counters, 1,5 cartas por turno, curva de B4.
# Tipo de victoria: el reparto de B4 (mas combo que B3; los mazos son cEDH ajustados al bracket). Regla 8 (tiempo): apagada.
MZ = dict(BRACKETS["B3"], bracket="Mazmorra", mz=True, mus=(4, 5, 6), spread=1.0, rem=7, cnt=8, cpt=1.5,
          opp_curve=(0.2, 0.1, 1.1), wipes=2, aem=0.35, win_types=WT_B4, win_blue=WB_B4)
BRACKETS["Mazmorra"] = MZ
BRACKETS["Mazmorra optimista"] = dict(MZ, mus=(4, 5, 7))
BRACKETS["Mazmorra pesimista"] = dict(MZ, mus=(3, 5, 6))
SCEN.update(BRACKETS)


def cfg(name, **over):
    d = dict(SCEN[name])
    d.update(over)
    return TableCfg(**d)
