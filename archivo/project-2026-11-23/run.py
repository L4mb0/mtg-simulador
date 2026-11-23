import sys, re, statistics, collections
sys.path.insert(0, '.')
from ai import play_game
def load(p):
    deck=[]
    for l in open(p):
        l=l.strip()
        m=re.match(r'^(\d+) (.+)$', l)
        if m and m.group(2)!="Gandalf, Goblins' Bane":
            deck += [m.group(2)]*int(m.group(1))
    import audit
    bad = sorted({c for c in deck if audit.identity(c)})
    if bad:
        raise ValueError(f"Cartas fuera de la identidad de Gandalf (mono-rojo): {bad}")
    return deck

def batch(deck, strat, n=1000, seed0=0):
    res = []
    for i in range(n):
        t, s = play_game(deck, strat, seed0 + i)
        res.append(t)
    return res

def summary(res):
    c = collections.Counter(res); n = len(res)
    cum = 0; out = []
    for t in range(4, 15):
        cum += c.get(t, 0)
        out.append((t, round(100 * cum / n)))
    killed = [r for r in res if r < 99]
    return dict(median=statistics.median(res), mean_killed=round(statistics.mean(killed), 2) if killed else None,
                not_by_14=round(100 * c.get(99, 0) / n), cum=out, early=sum(v for k, v in c.items() if k < 4))
