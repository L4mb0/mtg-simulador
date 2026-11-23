"""Speed bottlenecks for Blor 1.0: goldfish turn distribution and counterfactuals."""
import sys
from collections import Counter
from multiprocessing import Pool
import engine
from harness import run, summary, paired_turn, paired
from decks import DECKS
from scen import cfg

N = 4000
D = DECKS["Blor 1.0"]

def dist(res):
    c = Counter(r["turn"] if r["win"] else 21 for r in res)
    return " ".join(f"T{t}:{100*c[t]/len(res):.0f}" for t in range(5, 14)) + f" >T13:{100*sum(v for k,v in c.items() if k>13)/len(res):.0f}"

# counterfactual patches
orig_compute = engine.Game.compute_pool
orig_power = engine.Game.power
orig_haste = engine.Game.haste
orig_draw_turn = engine.Game.our_turn

def p_mana(self):
    orig_compute(self); self.W += 2
def p_mana1(self):
    orig_compute(self); self.W += 1
def p_power(self, temp=True):
    v = orig_power(self, temp); return v + 5 if self.blor else v
def p_haste(self):
    return True
def p_cards(self):
    self.draw(1); orig_draw_turn(self)

CF = {"+1 maná por turno": ("compute_pool", p_mana1), "+2 maná por turno": ("compute_pool", p_mana),
      "+5 de poder fijo": ("power", p_power), "Prisa siempre": ("haste", p_haste), "+1 carta por turno": ("our_turn", p_cards)}

def job(args):
    name, seed, mode = args
    engine.Game.compute_pool = orig_compute; engine.Game.power = orig_power
    engine.Game.haste = orig_haste; engine.Game.our_turn = orig_draw_turn
    if name:
        attr, fn = CF[name]
        setattr(engine.Game, attr, fn)
    from harness import _one
    return _one((D, seed, mode, None if mode == "goldfish" else cfg("Realista"), "guide"))

if __name__ == "__main__":
    with Pool() as pool:
        g = pool.map(job, [(None, 12345 + i, "goldfish") for i in range(N)], chunksize=200)
        s = summary(g)
        print("goldfish", f"T{s['mean_turn']:.2f}", dist(g), "Blor T", round(s["blor_t"], 2))
        t = run(D, N, cfg=cfg("Realista"), pool=pool)
        st = summary(t)
        print("realista", f"win {st['win']:.1f} turno {st['mean_turn']:.2f} 1ª muerte {st['first_kill']:.2f}", dist(t))
        for name in CF:
            r = pool.map(job, [(name, 12345 + i, "goldfish") for i in range(N)], chunksize=200)
            m, ci = paired_turn(g, r)
            print(f"{name:22s} goldfish {m:+.2f} ±{ci:.2f}")
