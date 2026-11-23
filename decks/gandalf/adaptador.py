"""Adaptador de Gandalf para sim.py: listas, mesas y una partida."""
import os, glob
import table, engine, ai, lab
from cards import C, OFF_COLOR

HERE = os.path.dirname(os.path.abspath(__file__))
SEED0 = 900_000
LISTAS = {os.path.basename(p)[len("gandalf_"):-4]: p for p in sorted(glob.glob(os.path.join(HERE, "gandalf_*.txt")))}
DEFAULT = "1.6"
MESAS = list(table.BRACKETS)
DEFAULT_MESAS = ["B3"]
DEV_TUTOR = ["Ojer Axonil, Deepest Might", "Harmonic Prodigy", "Ruby Medallion", "Past in Flames"]


def lista(nombre):
    return lab.load(LISTAS[nombre])


def conoce(carta):
    return carta in C and carta not in OFF_COLOR


def _one(a):
    deck, mesa, seed = a
    if mesa == "goldfish":
        t = ai.play_game(deck, "C", seed)[0]
        return dict(win=t < 99, turn=t if t < 99 else None)
    engine.DEV_TUTOR[:] = DEV_TUTOR
    tb, ix = table.BRACKETS[mesa]
    t, s, res = table.play_table(deck, "E", seed, tb, ix=ix)
    return dict(win=res == "win", turn=t if res == "win" else None)
