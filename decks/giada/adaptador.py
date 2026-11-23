"""Adaptador de Giada para sim.py."""
from engine import play
from scen import SCEN, cfg
from cards import CARDS, LANDS, ACTUAL, PRECON

SEED0 = 12345
LISTAS = {"actual": lambda: list(ACTUAL), "precon": lambda: list(PRECON)}
DEFAULT = "actual"
MESAS = list(SCEN)
DEFAULT_MESAS = ["B2", "B3"]


def lista(nombre):
    return list(LISTAS[nombre]())


def conoce(carta):
    return carta in CARDS or carta in LANDS


def _one(a):
    deck, mesa, seed = a
    g = play(deck, seed, mode="goldfish" if mesa == "goldfish" else "table",
             cfg=None if mesa == "goldfish" else cfg(mesa), mull_policy="guide")
    return dict(win=bool(g.won), turn=g.win_turn if g.won else None)
