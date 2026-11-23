import math, statistics, sys
from multiprocessing import Pool
from engine import play, TableCfg

SEED0 = 500_000


def _one(args):
    deck, seed, mode, cfg, mull = args
    g = play(deck, seed, mode=mode, cfg=cfg, mull_policy=mull)
    t8 = g.stats.get("t8")
    return (1 if g.won else 0, g.win_turn or 21, 1 if g.stats["combo_turn"] else 0, g.gorma_turn or 21,
            g.stats["mulls"], t8)


def run(deck, N, mode="table", cfg=None, mull="guide", seed0=SEED0, pool=None):
    args = [(deck, seed0 + i, mode, cfg, mull) for i in range(N)]
    if pool:
        return pool.map(_one, args, chunksize=200)
    return [_one(a) for a in args]


def summary(res):
    N = len(res)
    w = [r[0] for r in res]
    wt = [r[1] for r in res]
    return dict(win=100 * sum(w) / N, mean_turn=statistics.mean(wt),
                k8=100 * sum(1 for t in wt if t <= 8) / N, k10=100 * sum(1 for t in wt if t <= 10) / N,
                combo=100 * sum(r[2] for r in res) / N, gorma=statistics.mean(r[3] for r in res),
                mulls=statistics.mean(r[4] for r in res))


def paired(a, b, idx=0):
    """mean difference b-a (pts) with 95% CI half-width"""
    d = [(y[idx] - x[idx]) for x, y in zip(a, b)]
    m = statistics.mean(d)
    sd = statistics.pstdev(d)
    return 100 * m, 100 * 1.96 * sd / math.sqrt(len(d))


def paired_turn(a, b):
    d = [(y[1] - x[1]) for x, y in zip(a, b)]
    m = statistics.mean(d)
    sd = statistics.pstdev(d)
    return m, 1.96 * sd / math.sqrt(len(d))
