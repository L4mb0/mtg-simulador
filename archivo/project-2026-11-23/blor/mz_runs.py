"""Mazmorra para Blor (19/11): comportamiento, linea base, causas de derrota. python3 mz_runs.py base|resp|cand"""
import sys
from multiprocessing import Pool
import engine
from harness import run, summary, paired
from decks import DECKS, swap_many
from scen import cfg
D = DECKS["Blor 1.6"]; N = 6000; S = 4100000
def job(a):
    deck, sc, s, kw = a
    g = engine.play(deck, S + s, mode="table", cfg=cfg(sc, **kw))
    st = g.stats
    if g.won: cause = "gana"
    elif st.get("mz_partial_us"): cause = "golpe parcial"
    elif g.loss == "combat": cause = "combate"
    elif g.loss == "rival": cause = "intento rival"
    elif g.loss == "self": cause = "propia"
    else: cause = "sin terminar"
    return dict(cause=cause, turn=g.turn, att1=st.get("att1"), stops=st.get("others_stop", 0) + st.get("we_stop", 0),
                we=st.get("we_stop", 0), et=st.get("mz_edict_table", False), ed=st.get("mz_edict", 0),
                edb=st.get("mz_edict_blor", 0), strip=st.get("mz_strip", 0), po=st.get("mz_partial_opp", 0),
                kills=len(st["kills"]), bt=g.blor_turn, pariah=st.get("pariah_saves", 0), slowed=st.get("mz_slowed", 0))
def behave(P, deck, sc, n=N, **kw):
    R = P.map(job, [(deck, sc, s, kw) for s in range(n)], chunksize=50)
    f = lambda c: 100 * sum(1 for r in R if c(r)) / n
    out = dict(win=f(lambda r: r["cause"] == "gana"),
               fin5=f(lambda r: r["turn"] <= 5), fin6=f(lambda r: r["turn"] <= 6), fin7=f(lambda r: r["turn"] <= 7),
               att4=f(lambda r: r["att1"] is not None and r["att1"] <= 4), stops=sum(r["stops"] for r in R) / n,
               we=sum(r["we"] for r in R) / n, ed_tab=f(lambda r: r["et"]), ed_hit=f(lambda r: r["ed"] > 0),
               ed_blor=f(lambda r: r["edb"] > 0), strip=sum(r["strip"] for r in R) / n,
               po=f(lambda r: r["po"] > 0), kills=sum(r["kills"] for r in R) / n, pariah=f(lambda r: r["pariah"] > 0))
    causes = {}
    for r in R:
        causes[r["cause"]] = causes.get(r["cause"], 0) + 1
    out["causes"] = {k: round(100 * v / n, 1) for k, v in sorted(causes.items(), key=lambda x: -x[1])}
    wt = [r["turn"] for r in R if r["cause"] == "gana"]; out["win_turn"] = sum(wt) / max(1, len(wt))
    return out
def fmt(o):
    return (f"gana {o['win']:.1f}% (T{o['win_turn']:.1f}) | fin<=T5 {o['fin5']:.0f}% <=T6 {o['fin6']:.0f}% <=T7 {o['fin7']:.0f}% | "
            f"1er intento<=T4 {o['att4']:.0f}% | frenos {o['stops']:.2f} (tuyos {o['we']:.2f}) | edicto en mesa {o['ed_tab']:.0f}%, "
            f"te pega {o['ed_hit']:.0f}%, se lleva a Blor {o['ed_blor']:.0f}% | Strip {o['strip']:.2f} tierras | "
            f"rival muerto por golpe parcial {o['po']:.0f}% | rivales que mata Blor {o['kills']:.2f} | Pariah salva {o['pariah']:.0f}%\n   causas {o['causes']}")
if __name__ == "__main__":
    st = sys.argv[1]
    with Pool() as P:
        if st == "base":
            for sc in ("B3", "Mazmorra", "Mazmorra optimista", "Mazmorra pesimista"):
                print(sc, fmt(behave(P, D, sc)), flush=True)
