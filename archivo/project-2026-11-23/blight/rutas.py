"""Rutas de cambios (greedy) para Blight Curse. PYTHONHASHSEED=0 python3 rutas.py barata|completa"""
import sys, json, time
from multiprocessing import Pool
from cards import PRECON_DECK, CARDS, LANDS
from runs import ruta, OUT

COMMANDER = "Auntie Ool, Cursewretch"
# interacción que no se saca aunque el modelo la valore ~0 (checklist 7: respuestas y barridas solo frenan intentos)
PROTEGIDAS = {"Assassin's Trophy", "Fire Covenant", "Infernal Grasp", "Putrefy", "Terminate", "Cathartic Pyre",
              "Chain Reaction", "Black Sun's Zenith", "Incremental Blight"}
OUTS = sorted({c for c in PRECON_DECK if c not in LANDS and c != COMMANDER and c not in PROTEGIDAS})

cand = json.load(open(f"{OUT}/candidatas.json"))
GC = {"Demonic Tutor", "Vampiric Tutor", "Worldly Tutor"}
ok = lambda c: not c.startswith("_") and c not in GC and cand[c]["avg"] > 0.25 and c not in LANDS
rank = sorted([c for c in cand if ok(c)], key=lambda c: -cand[c]["avg"])
INS = {
    "barata": [c for c in rank if cand[c]["price"] is not None and cand[c]["price"] <= 5],
    "completa": rank,
}

if __name__ == "__main__":
    name = sys.argv[1]
    t = time.time()
    print(name, INS[name], flush=True)
    with Pool(2) as P:
        ruta(P, INS[name], OUTS, name)
    print("tiempo", round(time.time() - t), "s")
