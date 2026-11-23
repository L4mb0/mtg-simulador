"""Línea base corta: cada simulador contra su número de referencia (checklist 56).

Uso (desde la raíz del repo):
    PYTHONHASHSEED=0 python3 linea_base.py [N] [mazo ...]

Corre con sim.py N partidas (2000 por defecto) de la lista vigente de cada mazo en un bracket de la mesa v2
y marca OK si la diferencia con la referencia cabe en 2,5 errores estándar.
"""
import os, sys, math, subprocess, json, time

ROOT = os.path.dirname(os.path.abspath(__file__))

# mazo: (bracket, referencia %, de dónde sale). La lista es la de por defecto de cada adaptador.
REF = {
    "gandalf": ("B3", 43.4, "Gandalf 1.6, mesa v2, 6.000 partidas (claude/mazo-gandalf.md)"),
    "gorma": ("B3", 8.7, "Gorma 1.0, 6.000 partidas, 22/11 (era 6,8% el 17/11; sube por las líneas de combo del 22/11)"),
    "giada": ("B2", 15.3, "Giada actual (con Lyra), mesa v2, 4.000 partidas (simulador-montecarlo.md, sección 8)"),
    "blight": ("B2", 6.6, "Blight precon, mesa v2, 4.000 partidas (simulador-montecarlo.md, sección 9)"),
    "blor": ("B3", 17.9, "Blor 1.6, mesa v2 con extensiones Mazmorra (simulador-montecarlo.md, 19/11)"),
}


def main():
    args = sys.argv[1:]
    n = int(args.pop(0)) if args and args[0].isdigit() else 2000
    names = args or list(REF)
    env = dict(os.environ, PYTHONHASHSEED="0")
    bad = 0
    for name in names:
        br, ref, src = REF[name]
        t = time.time()
        out = subprocess.run([sys.executable, os.path.join(ROOT, "sim.py"), name, "-m", br, "-n", str(n), "--json"],
                             env=env, capture_output=True, text=True)
        if out.returncode:
            print(f"{name:8} ERROR\n{out.stderr[-1500:]}"); bad += 1; continue
        got = json.loads(out.stdout.strip().splitlines()[-1])["base"][br]["win"]
        se = 100 * math.sqrt(ref / 100 * (1 - ref / 100) / n)
        ok = abs(got - ref) <= 2.5 * se
        bad += not ok
        print(f"{name:8} {br:3} {got:5.1f}%  ref {ref:5.1f}%  (±{2.5 * se:.1f})  {'OK' if ok else 'REVISAR'}  "
              f"{time.time() - t:4.0f}s  — {src}", flush=True)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
