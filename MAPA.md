# Mapa del repo (23/11/2026)

Una página para orientarse al empezar una sesión. Detalle en `README.md`; reglas de cada mesa y decisiones con Juan en
los docs del Project de Claude «Magic» (`claude/mesa-mazmorra.md`, `claude/simulador-montecarlo.md`,
`claude/mazo-<mazo>.md`).

## Empezar

```
git clone --depth 1 https://github.com/L4mb0/mtg-simulador && cd mtg-simulador
python3 linea_base.py                 # ¿todo da lo de siempre? (8 referencias, ~1 min)
python3 sim.py <mazo> -L              # listas y mesas del mazo
python3 sim.py <mazo> -m B3,Mazmorra -k "Sale>Entra" ...    # probar candidatas (pareadas)
```

## Dónde está cada cosa

| Quiero... | Archivo |
|---|---|
| Correr simulaciones | `sim.py` (uno para los cinco mazos; detalle de cada partida en `resultados/`) |
| Cambiar una mesa (relojes, remoción, odio, Mazmorra) | `core/mesa.py` (fuente única; los cinco mazos la leen) |
| Ver o cambiar qué hace una carta | `data/efectos.yaml` (vocabulario en `data/VOCABULARIO.md`) |
| Coste, tipo y P/T de una carta | Forge: `core/cards_db.json` (`core/build_cards_db.py` la regenera) vía `core/stats.py` |
| Agregar una carta | `"Nombre": FORGE` en `decks/<mazo>/cards.py` + su entrada en `data/efectos.yaml` |
| Cómo pilotea un mazo | `decks/<mazo>/engine.py` (y `ai.py` / `table.py` en Gandalf) |
| La lista vigente de un mazo | `decks/<mazo>/adaptador.py` (`DEFAULT`) |
| Comparar con lotes y pareadas | `core/harness.py` |
| Refactorizar sin mover números | `tools/huella.py comparar` (150 partidas por mesa, deben salir idénticas) |
| Pruebas | `python3 core/tests.py` y `decks/<mazo>/tests.py` (`PYTHONHASHSEED=0`) |
| Lo que el simulador modela distinto de la carta | `core/revisadas.txt`, `python3 core/stats.py`, `python3 core/efectos.py` |
| Código viejo del Project (experimentos, simulador v1) | `archivo/project-2026-11-23/` (tal cual; no se ejecuta desde aquí) |

## Mazos (referencias de `linea_base.py`, 6.000 partidas)

| Mazo | Lista | Bracket | Mazmorra |
|---|---|---|---|
| `gandalf` (Goblins' Bane, spellslinger) | 1.6 | B3 43,4% | 9,2% |
| `gorma` (Witherbloom, aristócratas) | 1.0 | B3 8,7% | 1,9% |
| `giada` (ángeles) | actual | B2 15,3% | — |
| `blight` (Blight Curse, −1/−1) | precon | B2 6,6% | — |
| `blor` (voltron) | Blor 1.6 | B3 17,9% | 3,2% |

## Reglas de la casa

- Siempre `PYTHONHASHSEED=0` (`sim.py` y `linea_base.py` lo ponen solos).
- Un cambio de modelado se mide pareado (mismas semillas) y se verifica con `--nuevas` antes de creerlo.
- La Mazmorra va sin límite de tiempo salvo que Juan pida "Mazmorra con tiempo".
- `sim.py` rechaza cartas repetidas y fuera de la identidad del comandante.

## Pendiente

- Mazmorra para Giada y Blight cuando vayan a torneo (`core.mesa.SIN_MAZMORRA`).
- La parte de la mesa que vive en cada motor (a qué apuntan la remoción y las barridas) detrás de una interfaz común.
- Efectos únicos todavía escritos a mano (`propio` en el YAML): pasarlos a datos cuando un patrón se repita.
