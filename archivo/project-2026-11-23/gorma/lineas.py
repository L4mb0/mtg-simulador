"""Lineas de combo de Gorma (fisica 22/11): que pieza cumple cada rol en las partidas ganadas."""
import random, sys, collections
from multiprocessing import Pool
from engine import Game, PERSIST_LOOP, OUTLETS, DRAINERS, ENABLERS
from cards import COMMANDER
from scen import SCEN, ACTUAL
from cards import physical_deck, target_deck
from verif import sw
SW22 = [("Bloodghast", "Blasting Station"), ("Nether Traitor", "Carrion Feeder"), ("Pest Rescuer", "Altar of Dementia")]
PHYS = sw(physical_deck(), SW22)          # fisica 22/11: Woodfall Primus, Twitching Doll y Blade of the Bloodchief
PHYS_LLEGAN = sw(target_deck(), SW22)     # cuando lleguen Insidious Fungus y Rendclaw Trow (Woodfall sigue)
CLOSE_NAMES = DRAINERS | {"Jarad, Golgari Lich Lord", "Altar of Dementia", "Blasting Station", "Feral Ghoul", "Defiling Daemogoth"}
orig = Game._finish_combo
def spy(self, closed, en, pe, oc):
    names = {p.name for p in self.bf}
    for x in (en, pe, oc):
        if x and x not in ("TUTOR",) and not str(x).startswith("GY:"): names.add(x)
    if pe and str(pe).startswith("GY:"): names.add(pe[3:])
    self._line = dict(closed=closed, eng=[e for e in [COMMANDER] + list(ENABLERS) if e in names] or ["(sin Gorma)"],
                      pers=sorted(n for n in names if n in PERSIST_LOOP) or ["(tutor)" if pe == "TUTOR" else "-"],
                      outl=sorted(n for n in names if n in OUTLETS or (n == "Aerie Ouphes")) or ["(tutor)" if oc == "TUTOR" else "-"],
                      clos=sorted(n for n in names if n in CLOSE_NAMES), turn=self.turn, used_tutor=("TUTOR" in (pe, oc)))
    return orig(self, closed, en, pe, oc)
Game._finish_combo = spy
def one(a):
    sc, seed, deck = a
    g = Game(deck, random.Random(seed), mode="goldfish" if sc == "goldfish" else "table", cfg=None if sc == "goldfish" else SCEN[sc])
    g.run()
    return (g.won, getattr(g, "_line", None) if g.won else None, g.stats.get("t8"))
if __name__ == "__main__":
    N = 4000
    with Pool() as P:
        for nm, deck in (("fisica hoy", PHYS), ("con Fungus y Rendclaw", PHYS_LLEGAN)):
          for sc in ("goldfish", "B3", "Mazmorra"):
            res = P.map(one, [(sc, 1_900_000 + i, deck) for i in range(N)], chunksize=100)
            wins = [r[1] for r in res if r[0] and r[1]]
            print(f"\n######## {nm} / {sc}: gana {100*sum(r[0] for r in res)/N:.1f}%  (por combo {100*len(wins)/N:.1f}%)")
            C = collections.Counter
            def show(t, c):
                print(f"  {t}: " + ", ".join(f"{k} {100*v/len(wins):.0f}%" for k, v in c.most_common(12)))
            show("cierre", C(w["closed"] for w in wins))
            show("motor", C("+".join(w["eng"]) for w in wins))
            show("persist en mesa", C(p for w in wins for p in w["pers"]))
            show("outlets en mesa", C(p for w in wins for p in w["outl"]))
            show("cierres en mesa", C(p for w in wins for p in w["clos"]))
            print(f"  usó tutor para una pieza: {100*sum(w['used_tutor'] for w in wins)/len(wins):.0f}%")
            t8 = [r[2] for r in res if r[2]]
            if t8:
                print("  T8 sin ganar, le faltaba: " + ", ".join(f"{k} {100*sum(1 for x in t8 if not x[k])/len(t8):.0f}%" for k in ("persist", "outlet", "closer", "tutor")))
