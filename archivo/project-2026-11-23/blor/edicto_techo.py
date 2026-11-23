"""Ceiling: how much would we gain if no edict could ever take Blor?"""
from multiprocessing import Pool
import engine
from harness import _one, summary, paired
from decks import DECKS
from scen import cfg
N = 4000
D = DECKS["Blor 1.1 (vigilancia)"]
orig = engine.Game.removal_on_us
def immune(self):
    keep = self.blor
    r = self.rng.random  # same stream: call original, then restore Blor if an edict took him
    before = self.blor
    tax, zone, auras, eq = self.tax, self.blor_zone, list(self.auras), [dict(e) for e in self.equips]
    orig(self)
    if before is not None and self.blor is None and self.stats.get("edict_blor", 0) and getattr(self, "_last_eb", 0) != self.stats["edict_blor"]:
        self._last_eb = self.stats["edict_blor"]
        self.blor, self.blor_zone, self.tax, self.auras = before, zone, tax, auras
        for a in auras:
            if a in self.gy: self.gy.remove(a)
            if a in self.hand and a == "Rancor": self.hand.remove(a)
        for e in self.equips:
            for x in eq:
                if x["name"] == e["name"]: e["on"] = x["on"]
def job(a):
    flag, seed, sc = a
    engine.Game.removal_on_us = immune if flag else orig
    return _one((D, seed, "table", cfg(sc), "guide"))
if __name__ == "__main__":
    with Pool() as pool:
        for sc in ("Edictos castiga", "Forge edictos", "Realista castiga", "Forge"):
            a = pool.map(job, [(False, 12345 + i, sc) for i in range(N)], chunksize=200)
            b = pool.map(job, [(True, 12345 + i, sc) for i in range(N)], chunksize=200)
            print(f"{sc:18s} normal {summary(a)['win']:.1f}  Blor inmune a edictos {summary(b)['win']:.1f}  techo {paired(a, b)[0]:+.1f}", flush=True)
