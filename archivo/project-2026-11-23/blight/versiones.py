"""Tabla de versiones (estilo Giada): win rate, cambios, costo y 'molestia'. PYTHONHASHSEED=0 python3 versiones.py"""
import json, statistics as st, time
from dataclasses import replace
from multiprocessing import Pool
from cards import apply, FASE1
from harness import run, summary, paired, paired_turn
from scen import SCEN, ACTUAL

# Card Kingdom NM, no foil más barata con stock, 12/11/2026 (* = sin stock, último precio)
P = {"Bastion of Remembrance": .69, "Cauldron of Essence": 4.49, "Zulaport Cutthroat": 2.79, "Scuzzback Scrounger": .99,
     "Ammit Eternal": .69, "Farseek": .99, "Rampant Growth": .79, "Nature's Lore": 3.49, "All Will Be One": 15.99,
     "Heroic Intervention": 14.99, "Nest of Scarabs": 5.49, "Obelisk Spider": 3.99, "Persistent Constrictor": 19.99,
     "Generous Patron": .79, "Dawnhand Dissident": .49, "Maha, Its Feathers Night": 22.99, "Harbinger of Night": 18.99,
     "Grim Affliction": .59, "Massacre Wurm": 6.49, "Archfiend of Sorrows": .35, "Crumbling Ashes": 21.99,
     "The Meathook Massacre": 29.99, "Darkness Descends": .35, "Banewhip Punisher": .39, "Whisper of the Dross": .69,
     "Contagion Engine": 17.99, "Demonic Tutor": 79.99, "Vampiric Tutor": 64.99,
     "Blood Artist": 4.49, "Diabolic Intent": 19.99, "Diabolic Tutor": 1.79, "Grim Tutor": 27.99,
     "High-Society Hunter": .79, "Mahadi, Emporium Master": 1.99, "Morselhoarder": .35, "Pollenbright Druid": .35,
     "Shadow Urchin": .49, "Tezzeret's Gambit": .59, "Yawgmoth, Thran Physician": 34.99}

D1 = [("Kulrath Knight", "Bastion of Remembrance"), ("Puca's Covenant", "Obelisk Spider"),
      ("Carnifex Demon", "Cauldron of Essence"), ("The Scorpion God", "Zulaport Cutthroat"),
      ("Eventide's Shadow", "Scuzzback Scrounger"), ("Necroskitter", "Ammit Eternal"), ("Contagion Clasp", "Farseek"),
      ("Skinrender", "Rampant Growth"), ("Harmonize", "Nature's Lore")]
D2 = [("Kulrath Knight", "All Will Be One"), ("Puca's Covenant", "Persistent Constrictor"),
      ("Dusk Urchins", "Heroic Intervention"), ("The Scorpion God", "Bastion of Remembrance"),
      ("Necroskitter", "Nest of Scarabs"), ("Eventide's Shadow", "Obelisk Spider"), ("Skinrender", "Cauldron of Essence"),
      ("Contagion Clasp", "Scuzzback Scrounger"), ("Harmonize", "Ammit Eternal"), ("Carnifex Demon", "Farseek"),
      ("Wickersmith's Tools", "Rampant Growth")]
M1 = [("Puca's Covenant", "Massacre Wurm"), ("Dusk Urchins", "Obelisk Spider"),
      ("Eventide's Shadow", "Archfiend of Sorrows"), ("Harmonize", "Darkness Descends"),
      ("Ferrafor, Young Yew", "Grim Affliction"), ("Painful Truths", "Banewhip Punisher"),
      ("Hoarder's Greed", "Whisper of the Dross"), ("Commander's Sphere", "Farseek"),
      ("Wickersmith's Tools", "Rampant Growth")]
M2 = M1 + [("Liliana, Death Wielder", "Persistent Constrictor"), ("Night's Whisper", "Crumbling Ashes"),
           ("Chimil, the Inner Sun", "Contagion Engine"), ("Burning Curiosity", "The Meathook Massacre")]
H1 = [("Puca's Covenant", "Massacre Wurm"), ("Dusk Urchins", "Obelisk Spider"),
      ("Eventide's Shadow", "Bastion of Remembrance"), ("Harmonize", "Cauldron of Essence"),
      ("Ferrafor, Young Yew", "Zulaport Cutthroat"), ("Painful Truths", "Archfiend of Sorrows"),
      ("Hoarder's Greed", "Ammit Eternal"), ("Commander's Sphere", "Farseek"),
      ("Wickersmith's Tools", "Rampant Growth")]
H2 = H1 + [("Liliana, Death Wielder", "Persistent Constrictor"), ("Night's Whisper", "All Will Be One"),
           ("Chimil, the Inner Sun", "Nest of Scarabs"), ("Burning Curiosity", "Heroic Intervention")]
C3 = D1 + [("Night's Whisper", "Demonic Tutor"), ("Burning Curiosity", "Vampiric Tutor")]
# combo de Blowfly (sin Game Changers): motores, pagos y tutores
CB1 = [("Puca's Covenant", "Nest of Scarabs"), ("Ferrafor, Young Yew", "Obelisk Spider"),
       ("Harmonize", "Diabolic Tutor"), ("Painful Truths", "Zulaport Cutthroat"),
       ("Hoarder's Greed", "Bastion of Remembrance"), ("Eventide's Shadow", "Blood Artist"),
       ("Dusk Urchins", "Cauldron of Essence"), ("Commander's Sphere", "Farseek"), ("Wickersmith's Tools", "Rampant Growth")]
CB2 = CB1 + [("Liliana, Death Wielder", "Grim Tutor"), ("Chimil, the Inner Sun", "Yawgmoth, Thran Physician"),
             ("Night's Whisper", "All Will Be One"), ("Burning Curiosity", "Heroic Intervention"),
             ("Aberrant Return", "Diabolic Intent")]
CB3 = CB2 + [("Cathartic Reunion", "Demonic Tutor"), ("Grim Poppet", "Vampiric Tutor")]
# veneno con Vraska + proliferar
V1 = [("Puca's Covenant", "Pollenbright Druid"), ("Ferrafor, Young Yew", "Grim Affliction"),
      ("Harmonize", "Tezzeret's Gambit"), ("Painful Truths", "Whisper of the Dross"),
      ("Commander's Sphere", "Farseek"), ("Wickersmith's Tools", "Rampant Growth")]
V2 = V1 + [("Hoarder's Greed", "Contagion Engine"), ("Chimil, the Inner Sun", "Yawgmoth, Thran Physician")]
# motor de cartas con blight (Auntie roba por cada contador en tus criaturas)
B1 = [("Puca's Covenant", "Scuzzback Scrounger"), ("Ferrafor, Young Yew", "Shadow Urchin"),
      ("Harmonize", "Morselhoarder"), ("Painful Truths", "Mahadi, Emporium Master"),
      ("Hoarder's Greed", "High-Society Hunter"), ("Eventide's Shadow", "Generous Patron"),
      ("Dusk Urchins", "Dawnhand Dissident"), ("Commander's Sphere", "Farseek"), ("Wickersmith's Tools", "Rampant Growth")]

VERS = [("Precon", []), ("Fase 1 de las guías", FASE1),
        ("Drenaje barata", D1), ("Drenaje completa", D2), ("Drenaje barata + tutores (B3)", C3),
        ("Combo Blowfly barata", CB1), ("Combo Blowfly completa", CB2), ("Combo Blowfly + tutores GC (B3)", CB3),
        ("Molesta barata", M1), ("Molesta completa", M2),
        ("Molesta que drena (barata)", H1), ("Molesta que drena (completa)", H2),
        ("Veneno barata", V1), ("Veneno completa", V2), ("Motor de cartas (blight)", B1)]
SCEN["Calibrada (Playgroup)"] = replace(SCEN["Realista (base)"], p_others=0.67)
TABS = ["Realista (base)", "Rivales lentos (10-14)", "Optimista", "Calibrada (Playgroup)"]

if __name__ == "__main__":
    t = time.time()
    out = {}
    with Pool(2) as Pl:
        base = {s: run(ACTUAL, 4000, "table", cfg=SCEN[s], pool=Pl) for s in TABS}
        g0 = run(ACTUAL, 2000, "goldfish", pool=Pl)
        for name, sw in VERS:
            d = apply(ACTUAL, sw) if sw else ACTUAL
            row = dict(swaps=sw, n=len(sw), cost=round(sum(P[i] for _, i in sw), 2))
            for s in TABS:
                r = base[s] if not sw else run(d, 4000, "table", cfg=SCEN[s], pool=Pl)
                sm = summary(r)
                row[s] = dict(win=sm["win"], d=paired(base[s], r), how=sm["how"],
                              ctrl=st.mean(x["ctrl"] for x in r), okills=st.mean(x["okills"] for x in r), okus=st.mean(x["okus"] for x in r))
            g = g0 if not sw else run(d, 2000, "goldfish", pool=Pl)
            row["goldfish"] = summary(g)["mean_turn"]
            out[name] = row
            R = row["Rivales lentos (10-14)"]
            print(f"{name:32s} {row['n']:2d} ${row['cost']:7.2f} | " + " ".join(f"{row[s]['win']:5.1f}" for s in TABS)
                  + f" | gf {row['goldfish']:.2f} | frenados {R["ctrl"]:.2f} matas {R["okus"]:.1f}", flush=True)
    json.dump(out, open("results/versiones.json", "w"), ensure_ascii=False, indent=1)
    print("tiempo", round(time.time() - t), "s")
