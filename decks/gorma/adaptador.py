"""Adaptador de Gorma para sim.py."""
from engine import play
from scen import SCEN, ACTUAL, SWAPS_11
from cards import CARDS, LANDS, target_deck, physical_deck

SEED0 = 500_000
# Mazo de Juan al 22/11 (cambios físicos de ese día) y el plan aprobado (1.1 + A + B), como en el chat de Gorma.
_SW22 = [("Bloodghast", "Blasting Station"), ("Nether Traitor", "Carrion Feeder"), ("Pest Rescuer", "Altar of Dementia")]
_A, _B = ("Pest Rescuer", "Altar of Dementia"), ("Mazirek, Kraul Death Priest", "Archdruid's Charm")


def _sw(deck, pares):
    d = list(deck)
    for o, i in pares:
        d[d.index(o)] = i
    return d


LISTAS = {"1.0": lambda: list(ACTUAL), "objetivo": target_deck, "física": physical_deck,
          "física 22/11": lambda: _sw(physical_deck(), _SW22),       # Twitching Doll, Blade y Woodfall todavía
          "hoy": lambda: _sw(target_deck(), _SW22),                  # con Insidious Fungus y Rendclaw Trow recogidas
          "plan": lambda: _sw(target_deck(), SWAPS_11 + [_A, _B])}   # 1.1 aprobada + Altar of Dementia + Archdruid's Charm
DEFAULT = "1.0"
MESAS = list(SCEN)
DEFAULT_MESAS = ["B3"]


def lista(nombre):
    return list(LISTAS[nombre]())


def conoce(carta):
    return carta in CARDS or carta in LANDS


def _one(a):
    deck, mesa, seed = a
    g = play(deck, seed, mode="goldfish" if mesa == "goldfish" else "table",
             cfg=None if mesa == "goldfish" else SCEN[mesa], mull_policy="guide")
    return dict(win=bool(g.won), turn=g.win_turn if g.won else None)
