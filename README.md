# mtg-simulador

Simuladores Monte Carlo de los mazos de Commander de Juan (Gandalf, Gorma, Giada, Blight Curse, Blor).

```
git clone --depth 1 https://github.com/L4mb0/mtg-simulador
cd mtg-simulador
PYTHONHASHSEED=0 python3 linea_base.py          # cada mazo contra su número de referencia
cd decks/<mazo> && PYTHONHASHSEED=0 python3 tests.py   # pruebas (Giada compara contra semillas guardadas con esta variable)
```

## Estructura

| Carpeta | Qué hay |
|---|---|
| `decks/gandalf/` | Gandalf, Goblins' Bane (spellslinger). `lab.py` corre partidas, `gandalf_1.6.txt` es la lista vigente, `audit.py` revisa identidad de color contra `texts.json` |
| `decks/gorma/` | Gorma (Witherbloom, aristócratas + persist). `gorma_ejemplo.py` tiene base, candidata, ablación y ruta |
| `decks/giada/` | Giada (ángeles). `v2runs.py` tiene base, ablación, candidatas y verificación en la mesa v2 |
| `decks/blight/` | Blight Curse (contadores -1/-1). `runs.py <fase>`; la mesa v2 está en `mesa2.py` |
| `decks/blor/` | Blor the Impervious (voltron). `decks.py` tiene todas las versiones; `runs.py <paso>` |
| `core/` | Base de cartas generada desde Forge (`cards_db.json`) y la comparación con los `cards.py` |

Cada simulador está **tal cual** venía del Project de Claude (fase 1 de la migración); solo se cambiaron rutas fijas.
La explicación de las reglas de cada mesa y el checklist de auditoría siguen en el Project
(`claude/simulador-montecarlo.md`).

## Base de cartas (fase 2)

`core/cards_db.json` sale de los guiones de MTG Forge (versión en `core/FORGE_VERSION`): coste, valor de maná, pips,
tipos, P/T, palabras clave, identidad de color y oracle de las ~790 cartas que usan los simuladores.

```
git clone --depth 1 --filter=blob:none --sparse https://github.com/Card-Forge/forge.git /tmp/forge
git -C /tmp/forge sparse-checkout set forge-gui/res/cardsfolder
python3 core/build_cards_db.py /tmp/forge/forge-gui/res/cardsfolder   # regenera la base
python3 core/compare.py                                                 # cards.py vs Forge -> core/diferencias.md
```

Para agregar una carta que todavía no usa ningún simulador, anotarla en `core/extra.txt` y regenerar.
Las diferencias que Juan revise y acepte van a `core/revisadas.txt`; `compare.py --test` falla solo con las nuevas.

## Línea base (22/11/2026, 2.000 partidas, `PYTHONHASHSEED=0`)

| Mazo | Bracket | Hoy | Referencia |
|---|---|---|---|
| Gandalf 1.6 | B3 | 44,5% | 43,4% |
| Gorma 1.0 | B3 | 9,2% | 8,7% (6.000 partidas; era 6,8% el 17/11, antes de las líneas de combo del 22/11) |
| Giada actual | B2 | 15,0% | 15,3% |
| Blight precon | B2 | 6,8% | 6,6% |
| Blor 1.6 | B3 | 19,6% | 17,9% |
