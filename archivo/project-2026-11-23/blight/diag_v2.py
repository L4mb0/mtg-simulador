"""Diagnóstico de la mesa v2: qué hace la interacción rival por partida. python3 diag_v2.py [N] [brackets...]"""
import sys, collections, statistics as st
from multiprocessing import Pool
from engine import play
from scen import SCEN, ACTUAL

def one(a):
    deck, seed, b, pol = a
    g = play(deck, seed, mode="table", cfg=SCEN[b], policy=pol)
    D = dict(g.D); D["win"] = g.won; D["turn"] = g.turn; D["how"] = g.win_how
    D["auntie_on"] = g.auntie_turn is not None
    D["lost_how"] = g.wtype if g.lost else None
    return D

def diag(b, N=2000, deck=ACTUAL, pol=None, P=None):
    R = P.map(one, [(deck, 900000 + s, b, pol) for s in range(N)], chunksize=50)
    f = lambda k: sum(r[k] for r in R) / N
    names = collections.Counter(); cnt = collections.Counter(); wt = []
    for r in R:
        names.update(r["rem_names"]); cnt.update(r["cnt_us"]); wt += r["wipes"]
    att = f("attempts")
    out = dict(win=100 * f("win"), rem_used=f("rem_used"), rem_us=f("rem_us"), rem_auntie=f("rem_auntie"),
               ward=f("ward_paid"), inst=f("inst"), wipes=len(wt) / N, wipe_t=st.mean(wt) if wt else 0,
               cnt=sum(cnt.values()) / N, cnt_auntie=cnt.get("Auntie Ool, Cursewretch", 0) / N, att=att,
               others=f("others"), ctrl=f("controlled"), ans=f("answered"), turn=st.mean(r["turn"] for r in R))
    print(f"{b:6s} win {out['win']:5.1f}% | remoción usada {out['rem_used']:.2f}/partida, contra ti {out['rem_us']:.2f} "
          f"(Auntie {out['rem_auntie']:.2f}; rival pagó ward {out['ward']:.2f}; al instante {out['inst']:.2f}) | "
          f"barridas {out['wipes']:.2f} (T{out['wipe_t']:.1f}) | counters a ti {out['cnt']:.2f} (Auntie {out['cnt_auntie']:.2f}) | "
          f"intentos {att:.2f}: otros frenan {out['others']:.2f}, tu control {out['ctrl']:.2f}, tus respuestas {out['ans']:.2f} | turnos {out['turn']:.1f}")
    print("        piezas que te quitan (por 100 partidas):", {k.split(",")[0]: round(100 * v / N) for k, v in names.most_common(7)})
    return out

if __name__ == "__main__":
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
    bs = sys.argv[2:] or ["B1", "B2", "B3", "B3+B4", "B4", "B5"]
    with Pool(2) as P:
        for b in bs:
            diag(b, N, P=P)
