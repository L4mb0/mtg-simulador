"""Lo común de los harness: correr lotes con semillas fijas y comparar versiones partida por partida.

Cada simulador define su `_one(args)` (juega una partida y devuelve su registro) y llama a `run_batch`.
Las comparaciones son pareadas: la misma semilla juega la misma mano y la misma mesa con las dos listas,
así la diferencia sale con mucho menos ruido que comparar dos porcentajes sueltos.
"""
import math


def run_batch(one, args, pool=None, chunksize=200):
    """Aplica `one` a cada tupla de `args`, en paralelo si hay pool. El orden del resultado es el de `args`."""
    if pool is None:
        return [one(a) for a in args]
    return pool.map(one, args, chunksize=chunksize)


def _get(r, key):
    v = key(r) if callable(key) else r[key]
    return 1 if v is True else 0 if v in (False, None) else v


def mean_ci(d):
    """Media y semiancho del intervalo al 95% (desviación muestral, n-1)."""
    n = len(d)
    m = sum(d) / n
    if n < 2:
        return m, float("nan")
    sd = math.sqrt(sum((x - m) ** 2 for x in d) / (n - 1))
    return m, 1.96 * sd / math.sqrt(n)


def paired(a, b, key="win", scale=100):
    """Diferencia media b-a (en puntos si scale=100) con su semiancho al 95%."""
    m, h = mean_ci([_get(y, key) - _get(x, key) for x, y in zip(a, b)])
    return scale * m, scale * h


def win_ci(wins, n):
    """Porcentaje de victorias y su semiancho al 95%."""
    p = wins / n
    return 100 * p, 100 * 1.96 * math.sqrt(p * (1 - p) / n)
