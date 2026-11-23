import math, statistics
from engine import play, TableCfg

SEED0 = 700_000


def _one(args):
    deck, seed, mode, cfg, policy = args
    g = play(deck, seed, mode=mode, cfg=cfg, policy=policy)
    return dict(win=1 if g.won else 0, wt=g.win_turn or 21, combo=1 if g.stats["combo"] else 0,
                at=g.auntie_turn or 21, mulls=g.stats["mulls"], how=g.win_how if g.won else None,
                cast=dict(g.cast_count), t8=g.stats.get("t8"), lost=1 if g.lost else 0,
                ctrl=g.stats.get("controlled", 0), okills=g.stats.get("okills", 0), okus=g.stats.get("okills_us", 0), lost_t=g.turn if g.lost else None, draws=g.stats["draws"],
                dmg={k[4:]: v for k, v in g.stats.items() if k.startswith("dmg_")})


def run(deck, N, mode="table", cfg=None, policy=None, seed0=SEED0, pool=None):
    args = [(deck, seed0 + i, mode, cfg, policy) for i in range(N)]
    if pool:
        return pool.map(_one, args, chunksize=100)
    return [_one(a) for a in args]


def summary(res):
    N = len(res)
    wt = [r["wt"] for r in res]
    hows = {}
    for r in res:
        if r["how"]:
            hows[r["how"]] = hows.get(r["how"], 0) + 1
    return dict(win=100 * sum(r["win"] for r in res) / N, mean_turn=statistics.mean(wt),
                k8=100 * sum(1 for t in wt if t <= 8) / N, k10=100 * sum(1 for t in wt if t <= 10) / N,
                combo=100 * sum(r["combo"] for r in res) / N, auntie=statistics.mean(r["at"] for r in res),
                mulls=statistics.mean(r["mulls"] for r in res), how={k: 100 * v / N for k, v in hows.items()},
                draws=statistics.mean(r["draws"] for r in res))


def paired(a, b, key="win"):
    d = [(y[key] - x[key]) for x, y in zip(a, b)]
    m = statistics.mean(d)
    sd = statistics.pstdev(d)
    return 100 * m, 100 * 1.96 * sd / math.sqrt(len(d))


def paired_turn(a, b):
    d = [(y["wt"] - x["wt"]) for x, y in zip(a, b)]
    return statistics.mean(d), 1.96 * statistics.pstdev(d) / math.sqrt(len(d))
