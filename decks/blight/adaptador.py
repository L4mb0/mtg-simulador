"""Adaptador de Blight Curse para sim.py."""
from engine import play
from scen import SCEN, ACTUAL
from cards import CARDS, LANDS

SEED0 = 700_000
LISTAS = {"precon": lambda: list(ACTUAL)}
DEFAULT = "precon"
MESAS = list(SCEN)
DEFAULT_MESAS = ["B2", "B3"]


def lista(nombre):
    return list(LISTAS[nombre]())


def conoce(carta):
    return carta in CARDS or carta in LANDS


def _one(a):
    deck, mesa, seed = a
    g = play(deck, seed, mode="goldfish" if mesa == "goldfish" else "table",
             cfg=None if mesa == "goldfish" else SCEN[mesa], policy=None)
    return dict(win=bool(g.won), turn=g.win_turn if g.won else None)
