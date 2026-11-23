"""Gandalf 1.6 en la mesa Mazmorra y sus variantes, con causas de derrota y daño colateral (16/11/2026)."""
import collections, statistics, sys
import diag_mazmorra as D, simlib as S, table
n = int(sys.argv[1]) if len(sys.argv) > 1 else 6000
d = S.load("gandalf_1.6.txt")
print("OBSERVADO (8 partidas)        gana ~25%  | fin ≤T5  ~45% ≤T6  ~75% ≤T7 ~100% med T6 | 1er intento ≤T4 ~75%")
for nm in list(table.MZ_VARIANTS) + ["B3", "B3+B4", "B4"]:
    R = D.run(d, nm, n)
    D.report(nm, R)
    if nm == "Mazmorra":
        loses = [r for r in R if not r["win"]]
        c = collections.Counter(("muerto por golpe parcial" if r["by_partial"] else (r["cause"] or "sin causa")) for r in loses)
        print("   derrotas:", {k: f"{100*v/len(loses):.0f}%" for k, v in c.most_common()})
        print(f"   turno de la derrota: mediana T{statistics.median(r['t'] for r in loses if r['t']<99):.0f}; "
              f"victorias: mediana T{statistics.median(r['t'] for r in R if r['win']):.0f}")
        ed = [r for r in R if r["edicts"]]; ld = [r for r in R if r["lands"]]
        print(f"   edictos que te pegan: {100*len(ed)/n:.0f}% de las partidas (Gandalf sacrificado en {100*sum(r['g_ed']>0 for r in R)/n:.0f}%); "
              f"tierras perdidas por Strip Mine: {100*len(ld)/n:.0f}% de las partidas (media {statistics.mean(r['lands'] for r in ld) if ld else 0:.1f})")
        print(f"   un rival elimina a otro: {100*sum(r['partial']>0 for r in R)/n:.0f}% de las partidas", flush=True)
