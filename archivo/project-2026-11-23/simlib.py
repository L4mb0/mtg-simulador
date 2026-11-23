"""Utilidades para comparar versiones de un mazo con el simulador (Gandalf, mono-rojo spellslinger).

Uso típico:
    import simlib as S
    base = S.load("gandalf_1.5.txt")
    print(S.pct(S.winrate(base, bracket="B3")))                    # mesa B3 sin calibrar
    print(S.pct(S.winrate(base, bracket="B3", calibrated=True)))   # los rivales también se frenan entre sí (67%)
    alt = S.swap(base, [("Shock", "Lotus Petal")])
    print(S.diff(S.winrate(alt, bracket="B3"), S.winrate(base, bracket="B3")))   # (puntos, IC 95%)

Antes de cada lote: python3 tests.py (reglas y sinergias) y python3 audit.py (identidad de color).
"""
import math, statistics, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ai, table, engine, audit
from run import load

# Mesa vieja (13/11 y antes): equivale a B2 sin odio ni archienemigo
TBL = dict(clocks=[(8, 10), (9, 11), (10, 12)], a=0.7, delay=2)
BRACKETS = table.BRACKETS
N = 4000

def swap(deck, pairs):
    d = deck[:]
    for a, b in pairs:
        if audit.identity(b):
            raise ValueError(f"{b} está fuera de la identidad del comandante")
        d[d.index(a)] = b
    return d

def setflags(fast=True, mull=True, blaze=True, search=8):
    """Políticas del piloto: apertura rápida (Petal/rituales), mulligan explosivo, Embereth Blaze en desarrollo,
    órdenes alternativos probados en el turno del kill."""
    ai.FAST_OPEN[0] = fast; ai.MULL_EXPL[0] = mull; ai.BLAZE_DEV[0] = blaze; table.SEARCH_KILL[0] = search

def winrate(deck, n=None, seed0=900_000, strat="E", bracket=None, calibrated=False, details=False):
    """Lista de 0/1 por partida con semillas fijas (comparación pareada). bracket=None usa la mesa vieja."""
    engine.DEV_TUTOR[:] = ["Ojer Axonil, Deepest Might", "Harmonic Prodigy", "Ruby Medallion", "Past in Flames"]
    if bracket:
        tb, ix = table.calibrated(bracket) if calibrated else BRACKETS[bracket]
    else:
        tb, ix = TBL, ai.IX_DEFAULT
    out = []
    for i in range(n or N):
        t, s, r = table.play_table(deck, strat, seed0 + i, tb, ix=ix)
        out.append((int(r == "win"), t, getattr(s, "g_turn", None), getattr(s, "cause", None)) if details else int(r == "win"))
    return out

def goldfish(deck, n=3000):
    """Turno de kill sin interacción: (media, mediana, % turno 6 o antes, % turno 7 o antes)."""
    ts = sorted(ai.play_game(deck, "C", 700000 + i)[0] for i in range(n))
    return statistics.mean(ts), statistics.median(ts), sum(t <= 6 for t in ts) / n, sum(t <= 7 for t in ts) / n

def pct(w):
    return 100 * sum(w) / len(w)

def diff(a, b):
    """Diferencia pareada a - b en puntos de % de victorias, con medio ancho del IC 95%."""
    d = [x - y for x, y in zip(a, b)]
    return 100 * statistics.mean(d), 196 * statistics.pstdev(d) / math.sqrt(len(d))

def job(args):
    deck, pairs, kw = (args + ({},))[:3] if len(args) == 2 else args
    return pairs, winrate(swap(deck, pairs) if pairs else deck, **kw)

if __name__ == "__main__":
    base = load(os.path.join(os.path.dirname(os.path.abspath(__file__)), "gandalf_1.5.txt"))
    for b in ("B2", "B3"):
        w = winrate(base, n=500, bracket=b)
        print(f"Gandalf 1.5 en {b}: {pct(w):.1f}% de victorias en 500 partidas")
