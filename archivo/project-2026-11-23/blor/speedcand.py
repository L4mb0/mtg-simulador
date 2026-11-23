"""Speed: goldfish turn delta (and table) for each candidate against the same out, and speed ablation."""
import sys
from multiprocessing import Pool
from harness import run, summary, paired, paired_turn
from decks import DECKS, swap_many
from scen import cfg
from cards import is_land
N = int(sys.argv[2]) if len(sys.argv) > 2 else 3000
step = sys.argv[1]
BASE = sys.argv[3] if len(sys.argv) > 3 else "Blor 1.0"
OUT = sys.argv[4] if len(sys.argv) > 4 else "Spore Frog"
CANDS = ["Brass Squire", "Lavaspur Boots", "Wayfarer's Bauble", "Arbor Elf", "Elvish Spirit Guide",
         "Selvala, Heart of the Wilds", "Somberwald Sage", "Exploration", "Burgeoning", "Harrow", "Priest of Titania",
         "Karametra's Acolyte", "Sylvan Caryatid", "Paradise Druid", "Lotus Cobra", "Sakura-Tribe Scout",
         "Elemental Bond", "Guardian Project", "Swiftfoot Boots", "Lightning Greaves", "Colossus Hammer", "Rancor",
         "Mask of Memory", "Sixth Sense", "Garruk's Uprising", "Colossal Majesty", "Explore", "Skyshroud Claim",
         "Umezawa's Jitte", "Sword of Feast and Famine", "Avarice Amulet", "Ohran Frostfang", "Hardened Scales",
         "Garruk, Primal Hunter", "Become Immense", "Thought Vessel", "Herd Heirloom", "Drover of the Mighty",
         "Overgrowth", "The One Ring", "Mana Vault", "Grim Monolith", "Chrome Mox", "Mox Diamond", "Seedborn Muse",
         "Emerald Medallion", "Curse of Predation", "Sword of Hearth and Home", "Tarrian's Soulcleaver"]
LANDC = ["Ancient Tomb", "Gaea's Cradle", "Castle Garenbrig", "Cavern of Souls"]
if __name__ == "__main__":
    deck = DECKS[BASE]
    with Pool() as pool:
        g0 = run(deck, N, mode="goldfish", pool=pool)
        t0 = run(deck, N, cfg=cfg("Realista"), pool=pool)
        print(BASE, "goldfish", round(summary(g0)["mean_turn"], 2), "realista", round(summary(t0)["win"], 1),
              "turno", round(summary(t0)["mean_turn"], 2), flush=True)
        if step == "abl":
            items = [(c, swap_many(deck, [c], ["Blank"])) for c in sorted(set(x for x in deck if not is_land(x) and x != "Blank"))]
        else:
            items = [(c, swap_many(deck, ["Forest" if is_land(c) else OUT], [c])) for c in CANDS + LANDC if c not in deck]
        for c, d in items:
            g = run(d, N, mode="goldfish", pool=pool)
            t = run(d, N, cfg=cfg("Realista"), pool=pool)
            mg, cg = paired_turn(g0, g)
            mt, ct = paired(t0, t)
            print(f"{c:28s} goldfish {mg:+.2f} ±{cg:.2f}   realista {mt:+.1f} ±{ct:.1f}", flush=True)
