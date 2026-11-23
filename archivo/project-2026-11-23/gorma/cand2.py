from multiprocessing import Pool
from harness import summary, paired, run
from mz_runs import cfg, f, N, S1
from scen import CONS
from cards import swap
def R(d, sc, P): return run(d, N, "table", cfg=cfg(sc), seed0=S1, pool=P)
A = (["Walking Ballista", "Green Sun's Zenith", "Night's Whisper", "Allosaurus Shepherd", "Defense Grid", "Sylvan Library"],
     ["Pest Rescuer", "Morbid Opportunist", "Jadar, Ghoulcaller of Nephalia"])
Bm = (["Carpet of Flowers", "Mox Amber", "Lotus Petal", "Cabal Ritual", "Dark Ritual", "Elves of Deep Shadow", "Fyndhorn Elves",
       "Arbor Elf", "Deathrite Shaman", "Talisman of Resilience"], ["Fanatic of Rhonas", "Arcane Signet", "Pest Rescuer"])
if __name__ == "__main__":
    with Pool() as P:
        for sc in ("B3", "Mazmorra"):
            b = R(CONS, sc, P); print(f"\n== {sc} (1.1 {summary(b)['win']:.1f}%) ==")
            for ins, outs in (A, Bm):
                for c in ins:
                    print(f"{c:24s} " + "  ".join(f"por {o.split(',')[0]} {f(paired(b, R(swap(CONS, o, c), sc, P)))}" for o in outs))
            d = swap(swap(CONS, "Pest Rescuer", "Witherbloom Apprentice"), "Morbid Opportunist", "Chain of Smog")
            print(f"{'Apprentice + Chain of Smog':24s} por Pest Rescuer y Morbid {f(paired(b, R(d, sc, P)))}")
