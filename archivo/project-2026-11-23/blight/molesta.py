"""Ruta 'molesta que drena': greedy sin tocar las piezas de control. PYTHONHASHSEED=0 python3 molesta.py"""
import json, time, statistics as st
from multiprocessing import Pool
from cards import swap, LANDS, PRECON_DECK
from harness import run, summary, paired, paired_turn
from scen import SCEN, ACTUAL
from runs import ruta, OUT, ABL_T, NT
import versiones as V

# piezas que hacen al estilo molesto + interacción: no salen
PROTEGIDAS = {"Auntie Ool, Cursewretch", "Kulrath Knight", "Carnifex Demon", "Necroskitter", "Skinrender",
              "The Scorpion God", "Massacre Girl, Known Killer", "Midnight Banshee", "Soul Snuffers",
              "Village Pillagers", "Everlasting Torment", "Black Sun's Zenith", "Blowfly Infestation",
              "Grave Venerations", "Lasting Tarfire", "Hapatra, Vizier of Poisons", "Flourishing Defenses",
              "Tree of Perdition", "Oft-Nabbed Goat", "Glissa Sunslayer", "Vraska, Betrayal's Sting",
              "Assassin's Trophy", "Fire Covenant", "Infernal Grasp", "Putrefy", "Terminate", "Cathartic Pyre",
              "Chain Reaction", "Incremental Blight", "Sol Ring", "Arcane Signet", "Ignoble Hierarch",
              "Channeler Initiate", "Devoted Druid", "Dread Tiller", "Sinister Gnarlbark", "Evolution Sage",
              "Contagion Clasp", "Binding the Old Gods", "The Reaper, King No More", "Wickerbough Elder"}
OUTS = sorted({c for c in PRECON_DECK if c not in LANDS and c not in PROTEGIDAS})
# entradas: molestas que drenan o castigan, ordenadas por valor (candidatas contra Ferrafor; nuevas medidas abajo)
POOL = ["All Will Be One", "Persistent Constrictor", "Heroic Intervention", "Bastion of Remembrance", "Nest of Scarabs",
        "Obelisk Spider", "Cauldron of Essence", "Massacre Wurm", "Archfiend of Sorrows", "The Meathook Massacre",
        "Zulaport Cutthroat", "Ammit Eternal", "Farseek", "Rampant Growth", "Contagion Engine", "Darkness Descends",
        "Crumbling Ashes", "Nature's Lore"]

if __name__ == "__main__":
    t = time.time()
    with Pool(2) as P:
        # 1) valor de las cartas nuevas contra la misma salida (Ferrafor)
        bases = {s: run(ACTUAL, NT, "table", cfg=SCEN[s], pool=P) for s in ABL_T}
        new = {}
        for c in ("Massacre Wurm", "Archfiend of Sorrows", "The Meathook Massacre", "Darkness Descends", "Crumbling Ashes"):
            d = swap(ACTUAL, "Ferrafor, Young Yew", c)
            new[c] = sum(paired(bases[s], run(d, NT, "table", cfg=SCEN[s], pool=P))[0] for s in ABL_T) / 3
            print("candidata", c, round(new[c], 2), flush=True)
        cand = json.load(open(f"{OUT}/candidatas.json"))
        val = {c: (new[c] if c in new else cand[c]["avg"]) for c in POOL}
        ins = [c for c in sorted(POOL, key=lambda c: -val[c]) if val[c] > 0.2]
        print("orden de entradas", [(c, round(val[c], 2)) for c in ins], flush=True)
        res = ruta(P, ins, OUTS, "molesta_drena")
        json.dump(dict(val=val, ins=ins), open(f"{OUT}/molesta_vals.json", "w"), indent=1)
    print("tiempo", round(time.time() - t), "s")


def barata():
    """Misma ruta con cartas de hasta ~$7."""
    cheap = ["Bastion of Remembrance", "Nest of Scarabs", "Obelisk Spider", "Cauldron of Essence", "Zulaport Cutthroat",
             "Ammit Eternal", "Massacre Wurm", "Farseek", "Rampant Growth", "Nature's Lore", "Darkness Descends"]
    val = json.load(open(f"{OUT}/molesta_vals.json"))["val"]
    ins = sorted(cheap, key=lambda c: -val[c])
    with Pool(2) as P:
        ruta(P, ins, OUTS, "molesta_drena_barata")
