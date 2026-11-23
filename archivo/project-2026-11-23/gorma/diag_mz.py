"""Mazmorra: comportamiento para contrastar con la tienda (y con Gandalf 1.6)"""
import sys, statistics
from multiprocessing import Pool
import engine
from scen import SCEN, ACTUAL, CONS
def job(a):
    deck, sc, s = a
    g = engine.play(deck, 900000 + s, mode="table", cfg=SCEN[sc])
    st = g.stats
    return dict(T=g.turn, won=g.won, fa=st.get("first_att_any", 99), stops=st.get("others_stop", 0) + st.get("we_stop", 0),
                we=st.get("we_stop", 0), cut=st.get("time_cut", 0), tw=st.get("time_win", 0), lt=st.get("life_t", {}),
                ed_t=st.get("mz_edict_table", 0), ed=st.get("mz_edicts", 0), edg=st.get("mz_edict_gorma", 0),
                strip=st.get("mz_strip", 0), rem=st.get("rem_us", 0), cnt=st.get("cnt_used", 0),
                pus=st.get("mz_partial_us", 0), pk=st.get("mz_partial_kill", 0), dmg=st.get("dmg_taken", 0),
                combo=1 if st["combo_turn"] else 0, wipes=st.get("wipe_cards", 0))
if __name__ == "__main__":
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
    with Pool() as p:
        for dn, deck in (("1.0", ACTUAL), ("1.1", CONS)):
            print(f"\n=== Gorma {dn} ===")
            for sc in ("B3", "Mazmorra", "Mazmorra optimista", "Mazmorra pesimista"):
                r = p.map(job, [(deck, sc, s) for s in range(N)], chunksize=100)
                f = lambda k: sum(x[k] for x in r) / N
                le = lambda t: sum(1 for x in r if x["T"] <= t) / N * 100
                l6 = [x["lt"][6] for x in r if 6 in x["lt"]]; l7 = [x["lt"][7] for x in r if 7 in x["lt"]]
                q = lambda L: f"mediana {statistics.median(L):.0f}, {100*sum(1 for v in L if v >= 25)/len(L):.0f}% con 25+" if L else "-"
                print(f"{sc:20s} gana {100*f('won'):.1f}% (por tiempo {100*f('tw'):.1f})  fin <=T5 {le(5):.0f}% <=T6 {le(6):.0f}% <=T7 {le(7):.0f}%"
                      f"  1er intento rival <=T4 {100*sum(1 for x in r if x['fa']<=4)/N:.0f}%  frenos/partida {f('stops'):.2f} (tuyos {f('we'):.2f})  al corte {100*f('cut'):.0f}%")
                print(f"{'':20s} tu vida T6: {q(l6)} | T7: {q(l7)} | daño de combate recibido {f('dmg'):.1f}"
                      f" | edictos: mesa con Sephiroth {100*f('ed_t'):.0f}%, {f('ed'):.2f} por partida (Gorma {100*f('edg'):.1f}%)"
                      f" | Strip Mine {f('strip'):.2f} tierras | remoción a ti {f('rem'):.2f}, counters {f('cnt'):.2f}, barridas te quitan {f('wipes'):.2f} cartas"
                      f" | mueres por golpe parcial {100*f('pus'):.1f}%")
