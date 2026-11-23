"""Mesa v2 completa: comportamiento por bracket (para contrastar con la mesa real)"""
import sys
from multiprocessing import Pool
from collections import Counter
import engine
from scen import SCEN, ACTUAL, CONS
K = ["rem_used", "rem_us", "rem_used_eng", "rem_us_eng", "cnt_used", "wipes", "wipe_cards", "wipe_saved", "att",
     "others_stop", "others_stop_cnt", "others_stop_rem", "we_stop", "gy_hate", "gy_lock", "art_hate", "attacked",
     "dmg_taken", "edict_us", "pact_edicts"]
def job(a):
    deck, sc, s = a
    g = engine.play(deck, 900000 + s, mode="table", cfg=SCEN[sc])
    d = {k: g.stats.get(k, 0) for k in K}
    wt = g.stats.get("wipe_turns", [])
    d.update(won=g.won, lost=g.lost, T=g.turn, combo=1 if g.stats["combo_turn"] else 0, wt=sum(wt), nw=len(wt),
             combat_loss=1 if (g.lost and g.life <= 0) else 0)
    return d
if __name__ == "__main__":
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 4000
    decks = [("1.0", ACTUAL), ("1.1", CONS)]
    with Pool() as p:
        for dn, deck in decks:
            print(f"\n=== Gorma {dn} ===")
            for sc in ["B2", "B3", "B3+B4", "B4"]:
                r = p.map(job, [(deck, sc, s) for s in range(N)], chunksize=100)
                m = {k: sum(x[k] for x in r) / N for k in K + ["won", "lost", "combo", "T", "wt", "nw", "combat_loss"]}
                a = max(1e-9, m["att"])
                print(f"{sc:6s} ganas {100*m['won']:.1f}% (combo {100*m['combo']:.1f}%)  fin T{m['T']:.1f}  | remocion {m['rem_used']:.2f}, a ti {m['rem_us']:.2f}"
                      f" (con motor {100*m['rem_us_eng']/max(1e-9,m['rem_used_eng']):.0f}%)  counters a ti {m['cnt_used']:.2f}"
                      f" | barridas {m['wipes']:.2f} (turno medio {m['wt']/max(1e-9,m['nw']):.1f}, te quitan {m['wipe_cards']:.2f} cartas)"
                      f" | intentos rivales {m['att']:.2f}: frena otro {100*m['others_stop']/a:.0f}%, frenas tu {100*m['we_stop']/a:.0f}%"
                      f" | odio cementerio {100*m['gy_hate']:.0f}% (RIP {100*m['gy_lock']:.0f}%), artefactos {m['art_hate']:.2f}"
                      f" | te atacan {m['attacked']:.2f} veces, {m['dmg_taken']:.1f} de dano; mueres en combate {100*m['combat_loss']:.1f}%")
