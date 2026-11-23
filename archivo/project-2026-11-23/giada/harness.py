"""Batch runner: same seeds for paired comparisons, IC 95%, multiprocessing (pattern from the Gorma simulator)."""
import math
from multiprocessing import Pool
from engine import play, TableCfg

SEED0 = 12345


def _one(args):
    deck, seed, mode, cfg, mull = args
    g = play(deck, seed, mode=mode, cfg=cfg, mull_policy=mull)
    return dict(win=g.won, turn=g.win_turn, lost=g.lost, loss=g.loss, gt=g.g_turn, mulls=g.stats["mulls"],
                cast=g.stats["cast"], t8=g.stats.get("t8"), life=g.life,
                ang={t: g.stats.get(f"ang{t}") for t in (4, 6, 8)})


def run(deck, N=4000, mode="table", cfg=None, mull="guide", seed0=SEED0, pool=None):
    args = [(deck, seed0 + i, mode, cfg, mull) for i in range(N)]
    if pool is None:
        return [_one(a) for a in args]
    return pool.map(_one, args, chunksize=200)


def summary(res):
    n = len(res)
    w = [r for r in res if r["win"]]
    p = len(w) / n
    turns = [r["turn"] for r in w]
    return dict(n=n, win=100 * p, ci=100 * 1.96 * math.sqrt(p * (1 - p) / n),
                mean_turn=sum(turns) / len(turns) if turns else None,
                k8=100 * sum(1 for t in turns if t <= 8) / n,
                k10=100 * sum(1 for t in turns if t <= 10) / n,
                lost_rival=100 * sum(1 for r in res if r["loss"] == "rival") / n,
                lost_combat=100 * sum(1 for r in res if r["loss"] == "combat") / n,
                giada_t=sum(r["gt"] for r in res if r["gt"]) / max(1, sum(1 for r in res if r["gt"])),
                mull=sum(r["mulls"] for r in res) / n)


def paired(a, b):
    """mean difference b-a in win points (pp), with 95% CI."""
    d = [(1 if y["win"] else 0) - (1 if x["win"] else 0) for x, y in zip(a, b)]
    n = len(d)
    m = sum(d) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in d) / (n - 1))
    return 100 * m, 100 * 1.96 * sd / math.sqrt(n)


def cast_rate(res, card):
    return 100 * sum(1 for r in res if r["cast"].get(card) or r["cast"].get("(Gateway) " + card)) / len(res)


def fmt(s):
    mt = f"{s['mean_turn']:.1f}" if s["mean_turn"] else "-"
    return (f"win {s['win']:5.1f}% ±{s['ci']:.1f}  turno {mt}  ≤T8 {s['k8']:4.1f}%  ≤T10 {s['k10']:4.1f}%  "
            f"pierde rival {s['lost_rival']:4.1f}% combate {s['lost_combat']:4.1f}%  Giada T{s['giada_t']:.1f}")
