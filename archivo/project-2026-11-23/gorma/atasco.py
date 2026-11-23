"""22/11: turnos en que el loop de Gorma se puede armar pero no cierra, separados por qué falta (maná vs robo)."""
import random, sys, collections, statistics
from multiprocessing import Pool
import engine
from engine import Game, CARDS
from scen import SCEN
from turnos import HOY, PLAN
ORIG_CO, ORIG_TW = Game.closer_ok, Game.try_win
def co(self, left, inf, tutor_left, tcost, hand, lib, sf, outlet_name):
    r = ORIG_CO(self, left, inf, tutor_left, tcost, hand, lib, sf, outlet_name)
    if r is None and not any(k in str(outlet_name) for k in ("+", "recur", "mazirek", "chatter", "hunters", "apprentice")):
        self._fails.append((inf, outlet_name, left))
    return r
def tw(self):
    self._fails = []
    r = ORIG_TW(self)
    if not r and self._fails:
        infs = [f for f in self._fails if f[0]]
        gg = [f for f in self._fails if f[1] == "Greater Good"]
        if infs:
            src = "Plunderer" if self.on_bf("Pitiless Plunderer") else ("Phyrexian Altar" if any(f[1] == "Phyrexian Altar" for f in infs) or self.on_bf("Phyrexian Altar") else ("Pawn" if self.on_bf("Pawn of Ulamog") else "otro"))
            k = "A) maná infinito, sin robo ni cierre (" + src + ")"
        elif gg and len(gg) == len(self._fails):
            k = "B) solo Greater Good: roba pero no alcanza el maná"
        else:
            hc = any(c in engine.DRAINERS or c == "Jarad, Golgari Lich Lord" for c in self.hand)
            tu = bool(getattr(self, "_tutors", None))
            k = "C) outlet gratis, nada más: " + ("cierre en mano, falta maná" if hc else ("tutor en mano, falta maná" if tu else "sin cierre en mano (falta robo y maná)"))
        self._stuck.setdefault(self.turn, k)
    return r
Game.closer_ok, Game.try_win = co, tw
def one(a):
    deck, mode, seed = a
    g = Game(deck, random.Random(seed), mode=mode, cfg=None if mode == "goldfish" else SCEN["B3"])
    g._stuck = {}; g._fails = []
    g.run()
    return g.won and bool(g.stats.get("closer")), g.win_turn, g._stuck
if __name__ == "__main__":
    N = 4000
    with Pool() as P:
        for dn, deck in (("HOY", HOY), ("PLAN", PLAN)):
            for mode in ("goldfish", "table"):
                res = P.map(one, [(deck, mode, 5_100_000 + i) for i in range(N)], chunksize=100)
                st = [r for r in res if r[2]]
                print(f"\n### {dn} / {'goldfish' if mode=='goldfish' else 'B3'}: {100*len(st)/N:.1f}% de partidas tienen al menos un turno con el loop armable y sin cierre")
                first = collections.Counter(); lost = collections.defaultdict(list); never = collections.Counter(); turns = collections.Counter()
                for won, wt, s in res:
                    if not s: continue
                    t0 = min(s); k = s[t0]; first[k] += 1
                    for kk in s.values(): turns[kk] += 1
                    if won and wt: lost[k].append(wt - t0)
                    else: never[k] += 1
                for k, n in first.most_common():
                    L = lost[k]
                    print(f"  {k:62s} {100*n/N:5.1f}% | turno de atasco medio T{statistics.mean([min(s) for _,_,s in res if s and s[min(s)]==k]):.1f} | luego gana {100*len(L)/n:4.0f}% con {statistics.mean(L) if L else 0:.1f} turnos de retraso | turnos-atasco totales {turns[k]}")
