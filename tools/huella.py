"""Huella partida por partida de cada simulador, para refactorizar sin cambiar resultados.

    PYTHONHASHSEED=0 python3 tools/huella.py guardar     # escribe tools/huella.json
    PYTHONHASHSEED=0 python3 tools/huella.py comparar    # falla si alguna partida cambió

Juega N partidas por mazo y bracket (B2, B3, B4, Mazmorra y goldfish) y guarda (gana, turno) de cada una.
"""
import os, sys, json, subprocess, hashlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
N = 150
MESAS = ["B2", "B3", "B4", "Mazmorra"]

CODE = {
    "gandalf": """
import lab, table
d = lab.load("gandalf_1.6.txt")
out = {}
for m in MESAS:
    tb, ix = table.BRACKETS[m]
    import engine
    engine.DEV_TUTOR[:] = ["Ojer Axonil, Deepest Might", "Harmonic Prodigy", "Ruby Medallion", "Past in Flames"]
    out[m] = [[(r := table.play_table(d, "E", 900_000 + i, tb, ix=ix))[2] == "win", r[0]] for i in range(N)]
import ai
out["goldfish"] = [[True, ai.play_game(d, "C", 700000 + i)[0]] for i in range(N)]
""",
    "gorma": """
from harness import run
from scen import SCEN, ACTUAL
out = {m: [list(r[:2]) for r in run(ACTUAL, N, "table", cfg=SCEN[m])] for m in MESAS}
out["goldfish"] = [list(r[:2]) for r in run(ACTUAL, N, "goldfish")]
""",
    "giada": """
from harness import run
from scen import cfg
from cards import ACTUAL
out = {m: [[r["win"], r["turn"], r["loss"]] for r in run(ACTUAL, N, cfg=cfg(m))] for m in MESAS if m != "Mazmorra"}
out["goldfish"] = [[r["win"], r["turn"]] for r in run(ACTUAL, N, mode="goldfish")]
""",
    "blight": """
from harness import run
from scen import SCEN, ACTUAL
out = {m: [[r["win"], r["wt"], r["lost"]] for r in run(ACTUAL, N, "table", cfg=SCEN[m])] for m in MESAS if m in SCEN}
out["goldfish"] = [[r["win"], r["wt"]] for r in run(ACTUAL, N, "goldfish")]
""",
    "blor": """
from harness import run
from scen import cfg
from decks import DECKS
d = DECKS["Blor 1.6"]
out = {m: [[r["win"], r["turn"], r["loss"], r["kills"]] for r in run(d, N, cfg=cfg(m))] for m in MESAS}
out["goldfish"] = [[r["win"], r["turn"]] for r in run(d, N, mode="goldfish")]
""",
}


def take(name):
    code = f"import json\nN = {N}\nMESAS = {MESAS!r}\n" + CODE[name] + "\nprint(json.dumps(out, default=str))"
    env = dict(os.environ, PYTHONHASHSEED="0")
    r = subprocess.run([sys.executable, "-c", code], cwd=os.path.join(ROOT, "decks", name), env=env,
                       capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"{name}: {r.stderr[-2000:]}")
    return json.loads(r.stdout.strip().splitlines()[-1])


def main():
    path = os.path.join(ROOT, "tools", "huella.json")
    names = sys.argv[2:] or list(CODE)
    now = {n: take(n) for n in names}
    if sys.argv[1] == "guardar":
        old = json.load(open(path)) if os.path.exists(path) else {}
        old.update(now)
        json.dump(old, open(path, "w"), indent=0)
        for n in names:
            print(n, {m: sum(1 for x in v if x[0] in (1, True, "win")) for m, v in now[n].items()})
        return
    old = json.load(open(path))
    bad = 0
    for n in names:
        mine = 0
        for m, v in now[n].items():
            diff = [i for i, (a, b) in enumerate(zip(old[n][m], v)) if a != b]
            if diff or len(v) != len(old[n][m]):
                mine += 1
                print(f"{n:8} {m:9} CAMBIÓ en {len(diff)} de {len(v)} partidas (primera: {diff[:1]})")
        bad += mine
        h = hashlib.sha1(json.dumps(now[n], sort_keys=True).encode()).hexdigest()[:10]
        print(f"{n:8} {'idéntico' if not mine else 'cambió'} {h}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
