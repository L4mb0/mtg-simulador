"""Punto de entrada único de los simuladores.

    python3 sim.py <mazo> [opciones]

Ejemplos:
    python3 sim.py blor                                    # lista por defecto en sus mesas por defecto
    python3 sim.py gorma -m B2,B3,B4 -n 6000 -g            # varias mesas y goldfish
    python3 sim.py blor -c "Rancor>Ohran Frostfang"        # la lista con ese cambio, pareada contra la base
    python3 sim.py gandalf -k "Shock>Lava Dart" "Gut Shot>Fireblast"   # cada candidata por separado
    python3 sim.py giada -l precon                         # otra lista guardada (-L las muestra)
    python3 sim.py blight -l mi_lista.txt                  # o un archivo "1 Nombre" por línea
    python3 sim.py gorma --nuevas                          # semillas nuevas, para verificar un hallazgo

Por pantalla sale un resumen corto; el detalle (cada partida, cada comparación) va a resultados/.
Mazos: gandalf, gorma, giada, blight, blor. Mesas: B1–B5, B3+B4, Mazmorra (según el mazo), goldfish.
"""
import os, sys, json, time, argparse, datetime, importlib
from multiprocessing import Pool

ROOT = os.path.dirname(os.path.abspath(__file__))
if os.environ.get("PYTHONHASHSEED") != "0":   # los resultados dependen del orden de los sets: siempre con 0
    os.execve(sys.executable, [sys.executable] + sys.argv, dict(os.environ, PYTHONHASHSEED="0"))
sys.path.insert(0, ROOT)
from core import harness as H

MAZOS = ["gandalf", "gorma", "giada", "blight", "blor"]
BASICAS = {"Plains", "Island", "Swamp", "Mountain", "Forest", "Wastes",
           "Snow-Covered Plains", "Snow-Covered Island", "Snow-Covered Swamp", "Snow-Covered Mountain", "Snow-Covered Forest"}
NUEVAS = 10_000_000   # desplazamiento de semillas para verificar con partidas que no se usaron al buscar


def cargar(mazo):
    """Importa el adaptador del mazo (cada mazo en su propio proceso: sus módulos se llaman igual)."""
    d = os.path.join(ROOT, "decks", mazo)
    sys.path.insert(0, d)
    os.chdir(d)
    return importlib.import_module("adaptador")


def leer_lista(A, nombre):
    if nombre.endswith(".txt"):
        path = nombre if os.path.isabs(nombre) else os.path.join(_cwd0, nombre)
        deck = []
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#"):
                n, name = line.split(" ", 1)
                deck += [name] * int(n)
        return deck
    return A.lista(nombre)


def aplicar(A, deck, cambios):
    d = list(deck)
    for c in cambios:
        out, inn = [x.strip() for x in c.split(">")]
        if out not in d:
            sys.exit(f"'{out}' no está en la lista")
        if inn in d and inn not in BASICAS:
            sys.exit(f"'{inn}' ya está en la lista (Commander es singleton)")
        if not A.conoce(inn):
            sys.exit(f"el simulador no conoce '{inn}' (agregarla a cards.py y a su motor)")
        d[d.index(out)] = inn
    return d


def jugar(A, deck, mesa, n, seed0, pool):
    return H.run_batch(A._one, [(deck, mesa, seed0 + i) for i in range(n)], pool, chunksize=max(1, n // 64))


def resumen(res):
    n = len(res)
    w = sum(1 for r in res if r["win"])
    turns = sorted(r["turn"] for r in res if r["win"] and r["turn"])
    p, ci = H.win_ci(w, n)
    return dict(n=n, win=round(p, 4), ci=round(ci, 4),
                turno=round(sum(turns) / len(turns), 2) if turns else None,
                mediana=turns[len(turns) // 2] if turns else None)


def main():
    global _cwd0
    _cwd0 = os.getcwd()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mazo", choices=MAZOS)
    ap.add_argument("-l", "--lista", help="nombre de una lista guardada o archivo .txt")
    ap.add_argument("-m", "--mesas", help="mesas separadas por coma (por defecto, las del mazo)")
    ap.add_argument("-n", type=int, default=4000, help="partidas por mesa (4000)")
    ap.add_argument("-g", "--goldfish", action="store_true", help="agrega goldfish (turno de la victoria sin rivales)")
    ap.add_argument("-c", "--cambio", nargs="+", default=[], help='cambios "Sale>Entra" aplicados juntos')
    ap.add_argument("-k", "--candidatas", nargs="+", default=[], help='cambios "Sale>Entra", cada uno por separado')
    ap.add_argument("--semilla", type=int, help="primera semilla (por defecto, la del mazo)")
    ap.add_argument("--nuevas", action="store_true", help=f"semillas nuevas (+{NUEVAS:,})")
    ap.add_argument("-L", "--listas", action="store_true", help="muestra listas y mesas del mazo y sale")
    ap.add_argument("--json", action="store_true", help="imprime el resumen como JSON (para otros scripts)")
    ap.add_argument("-p", "--procesos", type=int, default=os.cpu_count())
    a = ap.parse_args()

    A = cargar(a.mazo)
    if a.listas:
        print("Listas:", ", ".join(A.LISTAS), f"(por defecto: {A.DEFAULT})")
        print("Mesas:", ", ".join(A.MESAS), f"(por defecto: {', '.join(A.DEFAULT_MESAS)})")
        return
    nombre = a.lista or A.DEFAULT
    base = leer_lista(A, nombre)
    mesas = a.mesas.split(",") if a.mesas else list(A.DEFAULT_MESAS)
    for m in mesas:
        if m not in A.MESAS:
            sys.exit(f"mesa '{m}' no existe para {a.mazo}; hay: {', '.join(A.MESAS)}")
    if a.goldfish:
        mesas.append("goldfish")
    seed0 = (a.semilla if a.semilla is not None else A.SEED0) + (NUEVAS if a.nuevas else 0)

    variantes = []
    if a.cambio:
        variantes.append((" + ".join(a.cambio), aplicar(A, base, a.cambio)))
    for c in a.candidatas:
        variantes.append((c, aplicar(A, base, [c])))

    t0 = time.time()
    out = dict(mazo=a.mazo, lista=nombre, n=a.n, semilla=seed0, fecha=datetime.datetime.now().isoformat(timespec="seconds"),
               base={}, variantes={}, partidas={})
    with Pool(a.procesos) as pool:
        base_res = {}
        for m in mesas:
            r = jugar(A, base, m, a.n, seed0, pool)
            base_res[m] = r
            out["base"][m] = resumen(r)
            out["partidas"][f"base|{m}"] = [[int(x["win"]), x["turn"]] for x in r]
        for etiqueta, deck in variantes:
            out["variantes"][etiqueta] = {}
            for m in mesas:
                r = jugar(A, deck, m, a.n, seed0, pool)
                s = resumen(r)
                if m == "goldfish":
                    cap = 99
                    d, h = H.paired(base_res[m], r, lambda x: x["turn"] if x["win"] else cap, scale=1)
                else:
                    d, h = H.paired(base_res[m], r, "win")
                s.update(dif=round(d, 2), dif_ci=round(h, 2))
                out["variantes"][etiqueta][m] = s
                out["partidas"][f"{etiqueta}|{m}"] = [[int(x["win"]), x["turn"]] for x in r]
    out["segundos"] = round(time.time() - t0, 1)

    os.makedirs(os.path.join(ROOT, "resultados"), exist_ok=True)
    fn = os.path.join(ROOT, "resultados", f"{out['fecha'].replace(':', '')}_{a.mazo}.json")
    json.dump(out, open(fn, "w", encoding="utf-8"), ensure_ascii=False)

    if a.json:
        print(json.dumps({k: v for k, v in out.items() if k != "partidas"}, ensure_ascii=False))
        return
    def fmt(m, s):
        if m == "goldfish":
            return f"turno {s['turno']} (mediana {s['mediana']})"
        return f"{s['win']:5.1f}% ±{s['ci']:.1f}"
    print(f"{a.mazo} · {nombre} · {a.n} partidas por mesa · semilla {seed0}")
    print("  " + " · ".join(f"{m} {fmt(m, s)}" for m, s in out["base"].items()))
    for etiqueta, res in out["variantes"].items():
        cols = []
        for m, s in res.items():
            unit = " turnos" if m == "goldfish" else ""
            cols.append(f"{m} {s['dif']:+.1f}{unit} ±{s['dif_ci']:.1f}")
        print(f"  {etiqueta}: " + " · ".join(cols))
    print(f"  ({out['segundos']} s; detalle en resultados/{os.path.basename(fn)})")


if __name__ == "__main__":
    main()
