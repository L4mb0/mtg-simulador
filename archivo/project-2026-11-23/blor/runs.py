"""Every step of the Blor analysis (13/11/2026). Usage: PYTHONHASHSEED=0 python3 runs.py <step> [N]

  estilos    8 lists (EDHREC average + 7 playstyles) in goldfish and 8 tables
  ablacion   each nonland card of a list -> "Blank" (Realista, Rivales lentos, Optimista)
  candidatas candidates into a list against the same out
  gc         Game Changers against Arcane Signet (or a Forest)
  pilotaje   piloting policies (target, tricks, holding mana)
  final      EDHREC average vs Mixto vs Blor 1.0 in every table
  log <seed> [list]  one logged game
"""
import sys
from multiprocessing import Pool
from harness import run, summary, paired, paired_turn, cast_rate, fmt
from decks import DECKS, swap_many
from scen import cfg, SCEN
from cards import is_land
from engine import play

THREE = ["Realista", "Rivales lentos", "Optimista"]
FOUR = THREE + ["Calibrada"]
CANDS = ["Leyline Axe", "Umezawa's Jitte", "Sword of Feast and Famine", "Sword of Fire and Ice",
         "Sword of Truth and Justice", "Sword of Hearth and Home", "Bone Sabres", "Colossus Hammer",
         "Belt of Giant Strength", "Swiftfoot Boots", "Lightning Greaves", "Assault Suit", "Thran Power Suit",
         "Mask of Memory", "Avarice Amulet", "Loxodon Warhammer", "Hardened Scales", "Branching Evolution",
         "Kami of Whispered Hopes", "Crystalline Armor", "Rancor", "Spider Umbra", "Indomitable Might",
         "Curse of Predation", "Colossal Majesty", "Garruk's Uprising", "Ohran Frostfang", "Fynn, the Fangbearer",
         "Grafted Exoskeleton", "Evolution Sage", "Season of Growth", "Sixth Sense", "Tyvar's Stand",
         "Become Immense", "Sylvan Library", "Skyshroud Claim", "Herd Heirloom", "Thought Vessel", "Millikin",
         "Drover of the Mighty", "Overgrowth", "Far Wanderings", "Stony Strength", "Adventurous Impulse",
         "Tarrian's Soulcleaver", "Moment's Peace", "Veil of Summer", "Garruk, Primal Hunter", "Explore",
         "Sword of the Animist", "Trailblazer's Boots", "Questing Beast", "Hexhaven Invigorator"]
LAND_CANDS = ["Ancient Tomb", "Gaea's Cradle", "Castle Garenbrig", "Cavern of Souls", "Myriad Landscape",
              "Evolving Wilds", "Thriving Grove", "Hickory Woodlot", "Gemstone Mine", "Path of Ancestry",
              "Roiling Canopy", "Oran-Rief, the Vastwood", "Command Tower", "Rishadan Port"]
GC = [("The One Ring", "Arcane Signet"), ("Mana Vault", "Arcane Signet"), ("Grim Monolith", "Arcane Signet"),
      ("Chrome Mox", "Arcane Signet"), ("Mox Diamond", "Arcane Signet"), ("Seedborn Muse", "Arcane Signet"),
      ("Ancient Tomb", "Forest"), ("Gaea's Cradle", "Forest")]
POL = {"Foco: el próximo en ganar": dict(focus="threat"), "Trucos: gastar maná sobrante": dict(pump="greedy"),
       "Nunca guardar maná": dict(hold_from_turn=99), "Guardar desde el turno 4": dict(hold_from_turn=4)}


def avg_delta(pool, base_deck, deck, N, scen=THREE):
    ds = []
    for sc in scen:
        a = run(base_deck, N, cfg=cfg(sc), pool=pool)
        b = run(deck, N, cfg=cfg(sc), pool=pool)
        ds.append(paired(a, b)[0])
    return sum(ds) / len(ds), ds


def main():
    step = sys.argv[1]
    N = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 3000
    if step == "log":
        seed = int(sys.argv[2])
        name = sys.argv[3] if len(sys.argv) > 3 else "Blor 1.0"
        g = play(DECKS[name], seed, cfg=cfg("Realista"), log=True)
        print("won", g.won, g.win_turn, "loss", g.loss, "cmd", g.cmd, "poison", g.poison)
        return
    with Pool() as pool:
        if step == "estilos":
            sc_list = ["Realista", "Rivales lentos", "Optimista", "Calibrada", "Mucho quitaencantamientos",
                       "Edictos", "Barrida de exilio", "Bloquean siempre"]
            for name, deck in DECKS.items():
                gf = summary(run(deck, N, mode="goldfish", pool=pool))
                row = [summary(run(deck, N, cfg=cfg(sc), pool=pool))["win"] for sc in sc_list]
                print(f"{name:28s} gf T{gf['mean_turn']:.1f} " + " ".join(f"{x:5.1f}" for x in row), flush=True)
        elif step == "ablacion":
            name = sys.argv[3] if len(sys.argv) > 3 else "Blor 1.0"
            deck = DECKS[name]
            base = {sc: run(deck, N, cfg=cfg(sc), pool=pool) for sc in THREE}
            for c in sorted(set(x for x in deck if not is_land(x) and x != "Blank")):
                d = swap_many(deck, [c], ["Blank"])
                ds = [paired(base[sc], run(d, N, cfg=cfg(sc), pool=pool))[0] for sc in THREE]
                print(f"{c:30s} {sum(ds)/3:+5.1f}  " + " ".join(f"{x:+5.1f}" for x in ds), flush=True)
        elif step == "candidatas":
            name = sys.argv[3] if len(sys.argv) > 3 else "Blor 1.0"
            out = sys.argv[4] if len(sys.argv) > 4 else "Arcane Signet"
            deck = DECKS[name]
            base = {sc: run(deck, N, cfg=cfg(sc), pool=pool) for sc in THREE}
            for c in CANDS + LAND_CANDS:
                if c in deck:
                    continue
                d = swap_many(deck, ["Forest" if is_land(c) else out], [c])
                ds = []
                for sc in THREE:
                    r = run(d, N, cfg=cfg(sc), pool=pool)
                    ds.append(paired(base[sc], r)[0])
                print(f"{c:28s} {sum(ds)/3:+5.1f}  " + " ".join(f"{x:+5.1f}" for x in ds), flush=True)
        elif step == "gc":
            deck = DECKS["Ruta 1 (8 cambios)"]
            base = {sc: run(deck, N, cfg=cfg(sc), pool=pool) for sc in FOUR}
            for inn, out in GC:
                d = swap_many(deck, [out], [inn])
                ds = [paired(base[sc], run(d, N, cfg=cfg(sc), pool=pool))[0] for sc in FOUR]
                print(f"{inn:20s} " + " ".join(f"{x:+5.1f}" for x in ds) + f"  media {sum(ds)/4:+.1f}", flush=True)
        elif step == "pilotaje":
            deck = DECKS["Ruta 1 (8 cambios)"]
            base = {sc: run(deck, N, cfg=cfg(sc), pool=pool) for sc in FOUR}
            for k, over in POL.items():
                ds = [paired(base[sc], run(deck, N, cfg=cfg(sc, **over), pool=pool)) for sc in FOUR]
                print(f"{k:32s} " + "  ".join(f"{m:+5.1f} ±{ci:.1f}" for m, ci in ds), flush=True)
        elif step == "final":
            names = ["Promedio EDHREC", "Mixto (auras + equipos)", "Blor 1.0"]
            G = {n: run(DECKS[n], N, mode="goldfish", pool=pool) for n in names}
            for n in names:
                s = summary(G[n])
                print(f"{n:24s} goldfish T{s['mean_turn']:.2f} ≤T8 {s['k8']:.0f}% ≤T10 {s['k10']:.0f}%")
            for sc in SCEN:
                R = {n: run(DECKS[n], N, cfg=cfg(sc), pool=pool) for n in names}
                m, ci = paired(R[names[0]], R[names[2]])
                print(f"{sc:28s} " + "  ".join(f"{summary(R[n])['win']:5.1f}" for n in names) +
                      f"   1.0 vs EDHREC {m:+.1f} ±{ci:.1f}", flush=True)


if __name__ == "__main__":
    main()
