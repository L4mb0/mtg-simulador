from multiprocessing import Pool
from harness import run, summary, paired
from mz_runs import cfg, f
from verif import OWN
from cards import swap
N = 4000; S = 2_700_000
def sw(d, pairs):
    for o, i in pairs: d = swap(d, o, i)
    return d
OUT = ["Jadar, Ghoulcaller of Nephalia", "Greater Good", "Morbid Opportunist", "Find // Finality", "Pitiless Plunderer", "Pest Infestation"]
TURBO = ["Carpet of Flowers", "Dark Ritual", "Lotus Petal", "Elves of Deep Shadow", "Fyndhorn Elves", "Arbor Elf"]
RUTA4 = ["Walking Ballista", "Carpet of Flowers", "Chord of Calling", "Blasting Station"]
V = {"1.1 + tuyas": OWN,
     "+ turbo de maná (6: Carpet, Dark Ritual, Petal, 3 elfos)": sw(OWN, zip(OUT, TURBO)),
     "+ ruta (Ballista, Carpet, Chord, Blasting)": sw(OWN, zip(OUT, RUTA4)),
     "+ ruta + Dark Ritual, Petal": sw(OWN, zip(OUT, RUTA4 + ["Dark Ritual", "Lotus Petal"])),
     "+ ruta + Petal + 1 elfo": sw(OWN, zip(OUT, RUTA4 + ["Lotus Petal", "Elves of Deep Shadow"]))}
if __name__ == "__main__":
    with Pool() as P:
        b = {sc: run(OWN, N, "table", cfg=cfg(sc), seed0=S, pool=P) for sc in ("Mazmorra", "B3")}
        for nm, d in V.items():
            r = {sc: run(d, N, "table", cfg=cfg(sc), seed0=S, pool=P) for sc in b}
            g = run(d, N, "goldfish", seed0=S, pool=P)
            c5 = 100 * sum(1 for x in g if x[2] and x[1] <= 5) / N
            print(f"{nm:58s} Mazmorra {summary(r['Mazmorra'])['win']:.1f}% ({f(paired(b['Mazmorra'], r['Mazmorra']))})  B3 {summary(r['B3'])['win']:.1f}% ({f(paired(b['B3'], r['B3']))})  combo <=T5 {c5:.0f}%")
