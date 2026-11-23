"""Batch runner: same seeds for paired comparisons, IC 95%, multiprocessing (same pattern as Gorma/Giada/Blight)."""
import math
from multiprocessing import Pool
from engine import play, TableCfg

SEED0 = 12345


def _one(args):
    deck, seed, mode, cfg, mull = args
    g = play(deck, seed, mode=mode, cfg=cfg, mull_policy=mull)
    return dict(win=g.won, turn=g.win_turn, lost=g.lost, loss=g.loss, bt=g.blor_turn, mulls=g.stats["mulls"],
                cast=g.stats["cast"], t8=g.stats.get("t8"), life=g.life, kills=len(g.stats["kills"]),
                k1=g.stats.get("kill1"), left=g.stats["blor_left"], lost_att=g.stats["attach_lost"],
                casts=g.stats["blor_casts"], taken=g.stats.get("taken", 0), held=g.stats.get("held", 0),
                edict_blor=g.stats.get("edict_blor", 0), edicts=g.stats.get("edicts", 0), lands8=(g.stats.get("t8") or {}).get("lands"))


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
    k1 = [r["k1"] for r in res if r["k1"]]
    bts = [r["bt"] for r in res if r["bt"]]
    return dict(n=n, win=100 * p, ci=100 * 1.96 * math.sqrt(p * (1 - p) / n),
                mean_turn=sum(turns) / len(turns) if turns else None,
                k8=100 * sum(1 for t in turns if t <= 8) / n,
                k10=100 * sum(1 for t in turns if t <= 10) / n,
                first_kill=sum(k1) / len(k1) if k1 else None,
                kills=sum(r["kills"] for r in res) / n,
                lost_rival=100 * sum(1 for r in res if r["loss"] == "rival") / n,
                lost_combat=100 * sum(1 for r in res if r["loss"] == "combat") / n,
                blor_t=sum(bts) / len(bts) if bts else None,
                left=sum(r["left"] for r in res) / n, lost_att=sum(r["lost_att"] for r in res) / n,
                mull=sum(r["mulls"] for r in res) / n)


def paired(a, b):
    """mean difference b-a in win points (pp), with 95% CI."""
    d = [(1 if y["win"] else 0) - (1 if x["win"] else 0) for x, y in zip(a, b)]
    n = len(d)
    m = sum(d) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in d) / (n - 1))
    return 100 * m, 100 * 1.96 * sd / math.sqrt(n)


def paired_turn(a, b, cap=20):
    """goldfish: mean kill-turn difference b-a (no win = cap+1)."""
    ta = [x["turn"] if x["win"] else cap + 1 for x in a]
    tb = [x["turn"] if x["win"] else cap + 1 for x in b]
    d = [y - x for x, y in zip(ta, tb)]
    n = len(d)
    m = sum(d) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in d) / (n - 1))
    return m, 1.96 * sd / math.sqrt(n)


def cast_rate(res, card):
    return 100 * sum(1 for r in res if r["cast"].get(card) or r["cast"].get("(equip) " + card)) / len(res)


def fmt(s):
    mt = f"{s['mean_turn']:.1f}" if s["mean_turn"] else "-"
    fk = f"{s['first_kill']:.1f}" if s["first_kill"] else "-"
    return (f"win {s['win']:5.1f}% ±{s['ci']:.1f}  turno {mt}  1ª muerte T{fk}  muertes {s['kills']:.2f}  "
            f"pierde rival {s['lost_rival']:4.1f}% combate {s['lost_combat']:4.1f}%  Blor T{s['blor_t']:.1f}  "
            f"sale {s['left']:.2f}  pierde adjuntos {s['lost_att']:.2f}")
