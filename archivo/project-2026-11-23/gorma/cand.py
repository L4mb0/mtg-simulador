import sys
from multiprocessing import Pool
from harness import run, summary, paired
from scen import CONS, B
from cards import swap
N = 4000
def R(d, br="B3", seed=500_000, P=None):
    return run(d, N, "table", cfg=B(br), seed0=seed, pool=P)
def f(x): return f"{x[0]:+.1f} ±{x[1]:.1f}"
G = {
 "combo/tutores": (["Altar of Dementia", "Archdruid's Charm", "Collected Company", "Worldly Tutor", "Chord of Calling",
                    "Fauna Shaman", "Grim Tutor", "Finale of Devastation", "Wishclaw Talisman", "Blasting Station",
                    "Yawgmoth, Thran Physician", "Ashnod's Altar", "Warren Soultrader", "Gravecrawler"],
                   ["Pest Rescuer", "Mazirek, Kraul Death Priest", "Jadar, Ghoulcaller of Nephalia", "Greater Good"]),
 "interaccion": (["Heroic Intervention", "Ravenous Chupacabra", "Cast Down", "Power Word Kill", "Test of Courage", "Archdruid's Charm"],
                 ["Mortality Spear", "Immoral Bargain", "Desperate Plea", "Toxic Deluge"]),
 "ramp": (["Llanowar Elves", "Three Visits", "Cultivate", "Thought Vessel", "Coalition Relic", "Jadzia Dax"],
          ["Fanatic of Rhonas", "Arcane Signet"]),
 "descartadas": (["Phyrexian Tower", "Diabolic Intent", "Grave Pact", "Bloodflow Connoisseur", "Vampire Aristocrat",
                  "The Meathook Massacre", "Mirkwood Bats", "Golgari Charm", "Dr. Joseph M'Benga", "Beast Within",
                  "Vengeance Mission", "Eldritch Evolution", "Beseech the Mirror"], ["Pest Rescuer"]),
}
if __name__ == "__main__":
    with Pool() as P:
        base = R(CONS, P=P); print(f"1.1 en B3: {summary(base)['win']:.1f}%")
        for g, (ins, outs) in G.items():
            print(f"\n== {g} (entra por: {', '.join(outs)}) ==")
            for c in ins:
                row = []
                for o in outs:
                    if c == "Phyrexian Tower":
                        d = swap(CONS, "Swamp", c)
                    else:
                        d = swap(CONS, o, c)
                    row.append(f(paired(base, R(d, P=P))))
                print(f"{c:28s} " + "  ".join(row))
        print("\n== Warren Soultrader + Gravecrawler juntas (por Pest Rescuer y Jadar) ==")
        d = swap(swap(CONS, "Pest Rescuer", "Warren Soultrader"), "Jadar, Ghoulcaller of Nephalia", "Gravecrawler")
        print(f(paired(base, R(d, P=P))))
