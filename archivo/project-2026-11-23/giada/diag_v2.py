"""Diagnóstico de la mesa v2 de Giada: números de comportamiento por bracket."""
import sys, statistics as st
from collections import Counter
from multiprocessing import Pool
from engine import play
from cards import ACTUAL
from scen import cfg

def one(a):
    br, seed, deck = a
    g = play(deck, seed, mode="table", cfg=cfg(br))
    s = g.stats
    return dict(won=g.won, loss=g.loss, turn=g.turn, gt=g.g_turn, **{k: s.get(k, 0) for k in (
        "rem_drawn", "rem_us", "rem_opp", "rem_giada", "wipes", "wipe_saved", "cnt_us", "att", "others_stop",
        "we_stop", "herald_stop", "aem", "instant", "edict_us")}, rem_tgt=s.get("rem_tgt", {}), wipe_t=s.get("wipe_t", []),
        cnt_on=s.get("cnt_on", {}))

def report(br, R):
    N = len(R)
    m = lambda k: sum(r[k] for r in R) / N
    tg = Counter(); [tg.update(r["rem_tgt"]) for r in R]
    co = Counter(); [co.update(r["cnt_on"]) for r in R]
    wt = [t for r in R for t in r["wipe_t"]]
    att = m("att")
    lc = Counter(r["loss"] for r in R if r["loss"])
    tot_rem = sum(tg.values())
    print(f"== {br}: win {100*m('won'):.1f}%  dura {st.mean(r['turn'] for r in R):.1f} turnos  Giada T{st.mean(r['gt'] for r in R if r['gt']):.1f}")
    print(f"  remoción: robada {m('rem_drawn'):.2f}, usada contra otro rival {m('rem_opp'):.2f}, contra ti {m('rem_us'):.2f} "
          f"(al instante {m('instant'):.2f}, edictos {m('edict_us'):.2f}); Giada {m('rem_giada'):.2f} por partida")
    print("   te quita:", ", ".join(f"{n} {100*c/max(1,tot_rem):.0f}%" for n, c in tg.most_common(7)))
    print(f"  barridas {m('wipes'):.2f} por partida (turno medio {st.mean(wt) if wt else 0:.1f}; en {100*sum(1 for r in R if r['wipes'])/N:.0f}% de las partidas), Flawless salva {m('wipe_saved'):.2f}; odio a art/ench {m('aem'):.2f}")
    print(f"  counters contra ti {m('cnt_us'):.2f}:", ", ".join(f"{n} {c}" for n, c in co.most_common(5)))
    print(f"  intentos rivales {att:.2f} por partida: frena otro rival {100*m('others_stop')/max(att,1e-9):.0f}%, tú {100*m('we_stop')/max(att,1e-9):.0f}%, Herald {100*m('herald_stop')/max(att,1e-9):.0f}%")
    print("  derrotas:", ", ".join(f"{k} {100*v/N:.0f}%" for k, v in lc.most_common()))

if __name__ == "__main__":
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
    brs = sys.argv[2].split(",") if len(sys.argv) > 2 else ["B1", "B2", "B3", "B4", "B5", "B3+B4"]
    with Pool(2) as p:
        for br in brs:
            report(br, p.map(one, [(br, 70000 + i, ACTUAL) for i in range(N)], chunksize=100))
