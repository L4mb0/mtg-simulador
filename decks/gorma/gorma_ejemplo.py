"""Ejemplos de uso del simulador de Gorma (aristócratas + persist).

Correr con la carpeta como directorio de trabajo:
    PYTHONHASHSEED=0 python3 gorma_ejemplo.py base
    PYTHONHASHSEED=0 python3 gorma_ejemplo.py candidata "Dina's Guidance" "Merchant of Venom"
    PYTHONHASHSEED=0 python3 gorma_ejemplo.py ablacion
    PYTHONHASHSEED=0 python3 gorma_ejemplo.py ruta "Merchant of Venom,Gyre Sage" "Dina's Guidance,Aerie Ouphes,Carrion Feeder"

PYTHONHASHSEED=0 hace que las iteraciones sobre sets sean iguales en todos los procesos (pareado más limpio).
Toda carta nueva necesita: entrada en cards.CARDS (coste, tipo, poder, etiquetas), su efecto en engine.py
y una prioridad en Game.PRIORITY si es un permanente (si no, el modelo nunca la baja antes del combo).
"""
import sys
from multiprocessing import Pool
from cards import CARDS, swap
from harness import run, summary, paired
from scen import SCEN, ACTUAL

NT = 4000
MESAS = ["Realista (base)", "Pesimista", "Rivales rápidos (6-10)", "Optimista"]


def base(P):
    for s in MESAS:
        print(s, round(summary(run(ACTUAL, NT, "table", cfg=SCEN[s], pool=P))["win"], 1), "%")
    g = summary(run(ACTUAL, 2000, "goldfish", pool=P))
    print("goldfish: turno medio", round(g["mean_turn"], 2), "| kill antes del t8", round(g["k8"], 1), "%")


def candidata(P, inn, out):
    for s in MESAS:
        b = run(ACTUAL, NT, "table", cfg=SCEN[s], pool=P)
        t = run(swap(ACTUAL, out, inn), NT, "table", cfg=SCEN[s], pool=P)
        d, ci = paired(b, t)
        print(f"{s:24s} {inn} por {out}: {d:+.1f} ± {ci:.1f} pts")


def ablacion(P, mesa="Realista (base)"):
    b = run(ACTUAL, NT, "table", cfg=SCEN[mesa], pool=P)
    res = []
    for c in dict.fromkeys(ACTUAL):
        if c in CARDS:
            res.append((paired(b, run(swap(ACTUAL, c, "Blank"), NT, "table", cfg=SCEN[mesa], pool=P)), c))
    for (d, ci), c in sorted(res):
        print(f"{c:34s} {d:+.1f} ± {ci:.1f}")


def ruta(P, outs, ins):
    d = ACTUAL
    for o, i in zip(outs, ins):
        d = swap(d, o, i)
    for s in MESAS:
        b = run(ACTUAL, NT, "table", cfg=SCEN[s], pool=P); t = run(d, NT, "table", cfg=SCEN[s], pool=P)
        print(f"{s:24s} {summary(b)['win']:.1f}% -> {summary(t)['win']:.1f}%  ({paired(b, t)[0]:+.1f} ± {paired(b, t)[1]:.1f})")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "base"
    with Pool() as P:
        if cmd == "base":
            base(P)
        elif cmd == "candidata":
            candidata(P, sys.argv[2], sys.argv[3])
        elif cmd == "ablacion":
            ablacion(P)
        elif cmd == "ruta":
            ruta(P, sys.argv[2].split(","), sys.argv[3].split(","))
