"""Batch runner: same seeds for paired comparisons, IC 95%, multiprocessing (pattern from the Gorma simulator)."""
import math
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", ".."))
from core import harness as H
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
    return H.run_batch(_one, args, pool, chunksize=200)


def summary(res):
    n = len(res)
    w = [r for r in res if r["win"]]
    p = len(w) / n
    turns = [r["turn"] for r in w]
    return dict(n=n, win=100 * p, ci=H.win_ci(len(w), n)[1],
                mean_turn=sum(turns) / len(turns) if turns else None,
                k8=100 * sum(1 for t in turns if t <= 8) / n,
                k10=100 * sum(1 for t in turns if t <= 10) / n,
                lost_rival=100 * sum(1 for r in res if r["loss"] == "rival") / n,
                lost_combat=100 * sum(1 for r in res if r["loss"] == "combat") / n,
                giada_t=sum(r["gt"] for r in res if r["gt"]) / max(1, sum(1 for r in res if r["gt"])),
                mull=sum(r["mulls"] for r in res) / n)


def paired(a, b):
    """mean difference b-a in win points (pp), with 95% CI."""
    return H.paired(a, b, "win")


def cast_rate(res, card):
    return 100 * sum(1 for r in res if r["cast"].get(card) or r["cast"].get("(Gateway) " + card)) / len(res)


def fmt(s):
    mt = f"{s['mean_turn']:.1f}" if s["mean_turn"] else "-"
    return (f"win {s['win']:5.1f}% ±{s['ci']:.1f}  turno {mt}  ≤T8 {s['k8']:4.1f}%  ≤T10 {s['k10']:4.1f}%  "
            f"pierde rival {s['lost_rival']:4.1f}% combate {s['lost_combat']:4.1f}%  Giada T{s['giada_t']:.1f}")
