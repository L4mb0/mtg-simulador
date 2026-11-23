# mtg-simulador

Simuladores Monte Carlo de los mazos de Commander de Juan (Gandalf, Gorma, Giada, Blight Curse, Blor).

```
git clone --depth 1 https://github.com/L4mb0/mtg-simulador
cd mtg-simulador
python3 sim.py blor                                   # lista vigente en sus mesas por defecto
python3 sim.py gorma -m B2,B3,B4 -n 6000 -g           # varias mesas + goldfish
python3 sim.py blor -k "Rancor>Ancient Tomb" "Rancor>The One Ring"   # candidatas, pareadas contra la base
python3 sim.py gandalf -c "Shock>Needle Drop" --nuevas                  # cambio verificado con semillas nuevas
python3 sim.py giada -L                               # listas y mesas disponibles
python3 linea_base.py                                 # cada mazo contra su número de referencia
cd decks/<mazo> && PYTHONHASHSEED=0 python3 tests.py  # pruebas de reglas de un mazo
```

`sim.py` imprime un resumen de pocas líneas; cada partida y cada comparación quedan en `resultados/` (no va al repo).
Se relanza solo con `PYTHONHASHSEED=0`, que es lo que hace reproducibles los números.

## Estructura

| Carpeta | Qué hay |
|---|---|
| `sim.py` | Punto de entrada único: lista, mesas, cambios, candidatas, semillas nuevas |
| `core/mesa.py` | **Fuente única de la mesa v2**: relojes, remoción, counters, barridas, odio, curva rival y tipos de victoria por bracket; receta de la Mazmorra; reloj (`attempt_p`) y sorteo (`pick`). `DESVIOS` lista lo que cada mazo hace distinto |
| `core/harness.py` | Lotes con semillas fijas, comparación pareada e intervalos al 95% |
| `core/cards_db.json` | Base de cartas generada desde Forge y su comparación con los `cards.py` |
| `decks/<mazo>/` | Motor, cartas, IA y la parte de la mesa propia del mazo (pesos por carta, blancos). `adaptador.py` conecta el mazo con `sim.py` |
| `tools/huella.py` | Para refactorizar: 150 partidas por mesa y mazo que tienen que salir idénticas |

Mazos: `gandalf` (Goblins' Bane, spellslinger), `gorma` (Witherbloom, aristócratas + persist), `giada` (ángeles),
`blight` (Blight Curse, contadores -1/-1), `blor` (voltron). Las reglas de cada mesa y el checklist de auditoría
están en el Project de Claude (`claude/simulador-montecarlo.md`).

**Para agregar un mazo:** su carpeta en `decks/` con motor y cartas, tablas de mesa armadas desde `core/mesa.py`,
y un `adaptador.py` con `SEED0`, `LISTAS`, `DEFAULT`, `MESAS`, `DEFAULT_MESAS`, `lista()`, `conoce()` y `_one()`.

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
