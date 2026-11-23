"""Pruebas de los datos compartidos: python3 core/tests.py"""
import os, sys, subprocess, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from core import efectos as EF, mapeo as MP

fails = 0
def ok(cond, msg):
    global fails
    print(("ok    " if cond else "FALLA ") + msg)
    fails += not cond

ok(not EF.check(), f"data/efectos.yaml bien formado ({len(EF.db())} cartas) {EF.check()[:3]}")
for n, e in EF.db().items():
    for m in ("gandalf", "gorma", "giada", "blight", "blor"):
        for x in e.get(m, {}).get("no", ()):
            if x not in e.get("tags", ()) and x not in e:
                ok(False, f"{n}: '{m}.no' nombra '{x}', que la carta no tiene")
# cada mazo: sus cartas salen del YAML igual que si se rearmaran ahora, y lo que usa existe
CODE = """
import json, cards as m
D = m.C if isinstance(getattr(m, "C", None), dict) else m.CARDS
from core import mapeo as MP
bad = [n for n, v in D.items() if MP.importar(DECK, n, {k: x for k, x in v.items() if k in MP.STATS[DECK]}) != v]
print(json.dumps(dict(n=len(D), bad=bad, names=list(D))))
"""
known = set()
for deck in ("gandalf", "gorma", "giada", "blight", "blor"):
    r = subprocess.run([sys.executable, "-c", f"import sys; sys.path.insert(0, {ROOT!r}); DECK = {deck!r}\n" + CODE],
                       cwd=os.path.join(ROOT, "decks", deck), capture_output=True, text=True,
                       env=dict(os.environ, PYTHONHASHSEED="0"))
    if r.returncode:
        ok(False, f"{deck}: {r.stderr[-300:]}"); continue
    out = json.loads(r.stdout.strip().splitlines()[-1]); known |= set(out["names"])
    ok(not out["bad"], f"{deck}: {out['n']} cartas rearmadas desde el YAML {out['bad'][:3]}")
huerfanas = [n for n in EF.db() if n not in known]
ok(not huerfanas, f"todas las entradas del YAML son cartas de algún mazo {huerfanas[:5]}")
print("TODO OK" if not fails else f"{fails} fallas")
sys.exit(1 if fails else 0)
