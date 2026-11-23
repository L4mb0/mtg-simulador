"""Línea base corta: cada simulador contra su número de referencia (checklist 56).

Uso (desde la raíz del repo):
    PYTHONHASHSEED=0 python3 linea_base.py [N] [mazo ...]

Corre N partidas (2000 por defecto) de la lista vigente de cada mazo en un bracket de la mesa v2
y marca OK si la diferencia con la referencia cabe en 2,5 errores estándar.
"""
import os, sys, math, subprocess, json, time

ROOT = os.path.dirname(os.path.abspath(__file__))

# mazo: (bracket, referencia %, de dónde sale, código que imprime el % de victorias)
REF = {
    "gandalf": ("B3", 43.4, "Gandalf 1.6, mesa v2, 6.000 partidas (claude/mazo-gandalf.md)", """
import lab
d = lab.load("gandalf_1.6.txt")
r = lab.run(d, N, 900_000, "B3")
print(json.dumps(100 * sum(r) / len(r)))
"""),
    "gorma": ("B3", 8.7, "Gorma 1.0, 6.000 partidas, 22/11 (era 6,8% el 17/11; sube por las líneas de combo del 22/11)", """
from multiprocessing import Pool
from harness import run, summary
from scen import SCEN, ACTUAL
with Pool() as P:
    print(json.dumps(summary(run(ACTUAL, N, "table", cfg=SCEN["B3"], pool=P))["win"]))
"""),
    "giada": ("B2", 15.3, "Giada actual (con Lyra), mesa v2, 4.000 partidas (simulador-montecarlo.md, sección 8)", """
from multiprocessing import Pool
from harness import run, summary
from scen import cfg
from cards import ACTUAL
with Pool() as P:
    print(json.dumps(summary(run(ACTUAL, N, cfg=cfg("B2"), pool=P))["win"]))
"""),
    "blight": ("B2", 6.6, "Blight precon, mesa v2, 4.000 partidas (simulador-montecarlo.md, sección 9)", """
from multiprocessing import Pool
from harness import run, summary
from scen import SCEN, ACTUAL
with Pool() as P:
    print(json.dumps(summary(run(ACTUAL, N, "table", cfg=SCEN["B2"], pool=P))["win"]))
"""),
    "blor": ("B3", 17.9, "Blor 1.6, mesa v2 con extensiones Mazmorra (simulador-montecarlo.md, 19/11)", """
from multiprocessing import Pool
from harness import run, summary
from scen import cfg
from decks import DECKS
with Pool() as P:
    print(json.dumps(summary(run(DECKS["Blor 1.6"], N, cfg=cfg("B3"), pool=P))["win"]))
"""),
}


def main():
    args = sys.argv[1:]
    n = int(args.pop(0)) if args and args[0].isdigit() else 2000
    names = args or list(REF)
    env = dict(os.environ, PYTHONHASHSEED="0")
    bad = 0
    for name in names:
        br, ref, src, code = REF[name]
        t = time.time()
        out = subprocess.run([sys.executable, "-c", f"import json\nN = {n}\n" + code],
                             cwd=os.path.join(ROOT, "decks", name), env=env, capture_output=True, text=True)
        if out.returncode:
            print(f"{name:8} ERROR\n{out.stderr[-1500:]}"); bad += 1; continue
        got = float(out.stdout.strip().splitlines()[-1])
        se = 100 * math.sqrt(ref / 100 * (1 - ref / 100) / n)
        ok = abs(got - ref) <= 2.5 * se
        bad += not ok
        print(f"{name:8} {br:3} {got:5.1f}%  ref {ref:5.1f}%  (±{2.5 * se:.1f})  {'OK' if ok else 'REVISAR'}  "
              f"{time.time() - t:4.0f}s  — {src}", flush=True)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
