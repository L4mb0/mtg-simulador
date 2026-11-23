"""Ejemplos de uso del simulador de Blight Curse (Auntie Ool, contadores -1/-1).

Correr con la carpeta como directorio de trabajo:
    PYTHONHASHSEED=0 python3 blight_ejemplo.py base
    PYTHONHASHSEED=0 python3 blight_ejemplo.py candidata "Generous Patron" "Hoarder's Greed"
    PYTHONHASHSEED=0 python3 blight_ejemplo.py ruta "Hoarder's Greed,Painful Truths" "Generous Patron,Dawnhand Dissident"
    PYTHONHASHSEED=0 python3 blight_ejemplo.py log 123          (una partida con registro, semilla 123)

Para el análisis completo (ablación, candidatas, rutas, pilotaje): runs.py <fase>.
Toda carta nueva necesita: entrada en cards.CARDS (coste, tipo, poder/resistencia, etiquetas), su efecto en engine.py
(etb, enter_perm, put, die, opp_die, utilities o resolve_spell) y una prioridad en Game.PRIORITY si es un permanente.
"""
import sys
from multiprocessing import Pool
from cards import swap
from engine import play
from harness import run, summary, paired
from scen import SCEN, ACTUAL

NT = 4000
MESAS = ["Realista (base)", "Rivales lentos (10-14)", "Optimista", "Pesimista"]


def base(P):
    for s in MESAS:
        print(f"{s:26s} {summary(run(ACTUAL, NT, 'table', cfg=SCEN[s], pool=P))['win']:.1f} %")
    g = summary(run(ACTUAL, 2000, "goldfish", pool=P))
    print("goldfish: turno medio", round(g["mean_turn"], 2), "| kill en el t10 o antes", round(g["k10"], 1), "%")


def candidata(P, inn, out):
    for s in MESAS:
        b = run(ACTUAL, NT, "table", cfg=SCEN[s], pool=P)
        t = run(swap(ACTUAL, out, inn), NT, "table", cfg=SCEN[s], pool=P)
        d, ci = paired(b, t)
        print(f"{s:26s} {inn} por {out}: {d:+.1f} ± {ci:.1f} pts")


def ruta(P, outs, ins):
    d = ACTUAL
    for o, i in zip(outs, ins):
        d = swap(d, o, i)
    for s in MESAS:
        b = run(ACTUAL, NT, "table", cfg=SCEN[s], pool=P)
        t = run(d, NT, "table", cfg=SCEN[s], pool=P)
        print(f"{s:26s} {summary(b)['win']:.1f}% -> {summary(t)['win']:.1f}%  ({paired(b, t)[0]:+.1f} ± {paired(b, t)[1]:.1f})")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "base"
    if cmd == "log":
        g = play(ACTUAL, int(sys.argv[2]), mode="table", cfg=SCEN["Realista (base)"], log=True)
        print("ganó" if g.won else "perdió", g.win_how, "turno", g.turn)
        sys.exit()
    with Pool() as P:
        if cmd == "base":
            base(P)
        elif cmd == "candidata":
            candidata(P, sys.argv[2], sys.argv[3])
        elif cmd == "ruta":
            ruta(P, sys.argv[2].split(","), sys.argv[3].split(","))
