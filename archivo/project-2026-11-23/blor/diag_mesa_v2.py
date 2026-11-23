from multiprocessing import Pool
import engine
from decks import DECKS, swap_many
from scen import cfg
D = swap_many(DECKS["Blor 1.1 (vigilancia)"], ["Forest"], ["Dryad Arbor"])
K = ["att", "others_stop", "others_stop_rem", "others_stop_cnt", "we_stop", "cnt_us", "cnt_blor", "rem_us", "pariah_saves"]
def job(a):
    sc, s = a
    g = engine.play(D, 120000 + s, cfg=cfg(sc))
    d = {k: g.stats.get(k, 0) for k in K}; d.update(won=g.won, lost=g.lost, T=g.turn)
    return d
if __name__ == "__main__":
    with Pool() as p:
        for sc in ["B1", "B2", "B3", "B4", "B5", "B3+B4"]:
            r = p.map(job, [(sc, s) for s in range(4000)], chunksize=100)
            m = {k: sum(x[k] for x in r) / len(r) for k in r[0]}
            a = max(1e-9, m["att"])
            print(f"{sc:6s} intentos {m['att']:.2f}  frena otro rival {100*m['others_stop']/a:.0f}% (remocion {m['others_stop_rem']:.2f}, counter {m['others_stop_cnt']:.2f})"
                  f"  frenas tu {100*m['we_stop']/a:.0f}%  counters a ti {m['cnt_us']:.2f} (a Blor {m['cnt_blor']:.2f})  remocion a ti {m['rem_us']:.2f}"
                  f"  ganas {100*m['won']:.1f}%  pierdes {100*m['lost']:.1f}%  fin T{m['T']:.1f}")
