"""Adaptador de Gorma para sim.py."""
from engine import play
from scen import SCEN, ACTUAL
from cards import CARDS, LANDS, target_deck, physical_deck

SEED0 = 500_000
LISTAS = {"1.0": lambda: list(ACTUAL), "objetivo": target_deck, "física": physical_deck}
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
