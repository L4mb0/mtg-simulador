import sys, time, lab as L
t0 = time.time()
N = 6000; SEED = 3_100_000
d16 = L.load("gandalf_1.6.txt")
fis = L.swap(d16, [("Lava Dart", "Simian Spirit Guide"), ("Fireblast", "Lightning Greaves")])   # mazo fisico de hoy
GC = ["Jeska's Will", "Underworld Breach", "The One Ring"]
# ---- 1) colección nueva en el mazo actual (Mazmorra y B3), por Guttersnipe ----
print("== Nuevas de la coleccion, en el mazo fisico (por Guttersnipe) ==", flush=True)
B = {m: L.run(fis, N, SEED, m) for m in ("Mazmorra", "B3")}
print(f"fisico: Mazmorra {L.w(B['Mazmorra']):.1f} | B3 {L.w(B['B3']):.1f}", flush=True)
for c in ["Lotus Bloom", "Price of Progress", "Chromatic Lantern", "Skullclamp", "Krark, the Thumbless", "Cathartic Reunion"]:
    dd = L.swap(fis, [("Guttersnipe", c)]); o = []
    for m in ("Mazmorra", "B3"):
        o.append(L.diff(B[m], L.run(dd, N, SEED, m)))
    print(f"  {c:26s} Mz {o[0][0]:+.1f} ±{o[0][1]:.1f} | B3 {o[1][0]:+.1f} ±{o[1][1]:.1f}", flush=True)
# ---- 2) B2: valor de cada Game Changer y candidatas para sus cupos ----
print("== B2 ==", flush=True)
Bf = L.run(fis, N, SEED, "B2"); print(f"fisico con los 3 GC: {L.w(Bf):.1f}", flush=True)
for g in GC:
    m, e = L.diff(Bf, L.run(L.swap(fis, [(g, "Blank")]), N, SEED, "B2")); print(f"  sin {g:20s} {m:+.1f} ±{e:.1f}", flush=True)
nogc = L.swap(fis, [(g, "Blank") for g in GC])
B0 = L.run(nogc, N, SEED, "B2"); print(f"sin los 3 (3 cartas muertas): {L.w(B0):.1f}", flush=True)
CAND = ["Pirate's Pillage", "Needle Drop", "Flashback", "Cathartic Reunion", "Krark, the Thumbless", "Lotus Bloom", "Price of Progress",
        "Chromatic Lantern", "Mind Stone", "Fire Diamond", "Storm-Kiln Artist", "Kessig Flamebreather", "Firebrand Archer", "Mishra's Bauble",
        "Skullclamp", "Mysidian Elder", "Emeritus of Conflict", "Faithless Salvaging", "Implement of Combustion", "Demon Bolt",
        "Crash Through", "Boltwave", "Magmatic Insight", "Valakut Awakening", "Strike It Rich", "Fiery Emancipation"]
rows = []
for c in CAND:
    m, e = L.diff(B0, L.run(L.swap(nogc, [("Blank", c)]), N, SEED, "B2")); rows.append((m, e, c))
    print(f"  +{c:26s} {m:+.1f} ±{e:.1f}", flush=True)
print("---- ordenado")
for m, e, c in sorted(rows, reverse=True): print(f"  +{c:26s} {m:+.1f} ±{e:.1f}")
print(f"[{time.time()-t0:.0f}s]")
