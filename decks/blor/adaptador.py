"""Adaptador de Blor para sim.py."""
from engine import play
from scen import SCEN, cfg
from cards import C, LANDS
from decks import DECKS

SEED0 = 12345
LISTAS = DECKS
DEFAULT = "Blor 1.6"
MESAS = list(SCEN)
DEFAULT_MESAS = ["B3", "Mazmorra"]


def lista(nombre):
    return list(LISTAS[nombre])


def conoce(carta):
    return carta in C or carta in LANDS


def _one(a):
    deck, mesa, seed = a
    g = play(deck, seed, mode="goldfish" if mesa == "goldfish" else "table",
             cfg=None if mesa == "goldfish" else cfg(mesa), mull_policy="guide")
    return dict(win=bool(g.won), turn=g.win_turn if g.won else None)
