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
| `data/efectos.yaml` | **Efectos de las cartas como datos** (una entrada por carta, compartida por los cinco mazos): roles, palabras clave, respuestas, rocas, equipos, disparadores de muerte y el bloque `motor` de cada mazo (pesos de amenaza, prioridades). Vocabulario en `data/VOCABULARIO.md` |
| `core/efectos.py`, `core/mapeo.py` | Lector del YAML (`python3 core/efectos.py` lista pendientes) y traducción a las claves de cada `cards.py` |
| `core/cards_db.json` | Base de cartas generada desde Forge y su comparación con los `cards.py` |
| `decks/<mazo>/` | Motor, IA y la parte de la mesa propia del mazo. `cards.py` lista las cartas (`FORGE`) y los ajustes a mano. `adaptador.py` conecta el mazo con `sim.py` |
| `tools/huella.py` | Para refactorizar: 150 partidas por mesa y mazo que tienen que salir idénticas |

Mazos: `gandalf` (Goblins' Bane, spellslinger), `gorma` (Witherbloom, aristócratas + persist), `giada` (ángeles),
`blight` (Blight Curse, contadores -1/-1), `blor` (voltron). Las reglas de cada mesa y el checklist de auditoría
están en el Project de Claude (`claude/simulador-montecarlo.md`).

**Para agregar una carta:** `"Nombre": FORGE` en `decks/<mazo>/cards.py` (coste, tipo y P/T salen de Forge; solo
los ajustes van a mano, `python3 core/stats.py` los lista) y su entrada en `data/efectos.yaml` (ver
`data/VOCABULARIO.md`); si el efecto no está en el vocabulario, en el motor y marcado como `propio`.
`python3 core/tests.py` revisa el YAML.

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

## Línea base (23/11/2026, `python3 linea_base.py`)

| Mazo | Mesa | Referencia (6.000 partidas) |
|---|---|---|
| Gandalf 1.6 | B3 | 43,4% |
| Gandalf 1.6 | Mazmorra | 9,2% (optimista 10,9; pesimista 6,6; con tiempo 12,1) |
| Gorma 1.0 | B3 | 8,7% (era 6,8% el 17/11, antes de las líneas de combo del 22/11) |
| Gorma 1.0 | Mazmorra | 1,9% (optimista 2,1; pesimista 1,3; con tiempo 8,9) |
| Giada actual | B2 | 15,3% |
| Blight precon | B2 | 6,6% |
| Blor 1.6 | B3 | 17,9% |
| Blor 1.6 | Mazmorra | 3,2% (optimista 4,1; pesimista 2,7) |

**Mazmorra** (torneo B3 de La Mazmorra TCG): receta única en `core/mesa.py` desde el 23/11: base B4 + lo observado
el 15/11 (relojes 4/5/6, turbo que reintenta, 7 remociones, 8 counters, remoción entre rivales que frena al más rápido,
golpes parciales, edictos, Strip Mine). Sin límite de tiempo salvo que se pida ("Mazmorra con tiempo").
Giada y Blight todavía no la tienen (pendiente para cuando vayan a torneo).
