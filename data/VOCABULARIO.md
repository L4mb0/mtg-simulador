# Vocabulario de `data/efectos.yaml`

Una entrada por carta, con el nombre que usa el simulador (Gandalf aparece como `Gandalf`), compartida por los cinco
mazos. Lo que una carta **hace** va aquí; cómo la **pilotea** cada mazo sigue en su motor. Coste, tipo y P/T salen de
Forge (`core/cards_db.json` vía `core/stats.py`); cada `cards.py` solo escribe a mano los ajustes revisados.

Lector: `core/efectos.py`. Traducción a las claves de cada `cards.py`: `core/mapeo.py`.
Pendientes (excepciones, notas, efectos escritos a mano): `python3 core/efectos.py`.

## Campos comunes

| Campo | Qué es | Ejemplo |
|---|---|---|
| `tags` | Roles, palabras clave y tipos que algún motor consulta | `[outlet, persist, flying]` |
| `answer` / `answer_sorc` | Remoción instantánea / de conjuro: `cre`, `ae` (artefacto o encantamiento), `other`, `any` | `[cre, ae]` |
| `rock` | Maná que da una roca (`COM` = del color del comandante) | `CC` |
| `draw` | Cartas que roba al resolverse | `3` |
| `equip` | Coste de equipar | `2` |
| `power_bonus` | Fuerza que suma un aura o un equipo | `3` |
| `grants` | Palabras clave que da un aura o un equipo | `[haste, lifelink]` |
| `on_hit` | Al hacer daño de combate | `{draw: 1}` |
| `enabler` | Habilitador de bucles de persist (prioridad, menor = mejor) | `5` |
| `recur` | Vuelve del cementerio: `[coste para lanzarla, coste del retorno]` | `[2, 2]` |
| `on_death` | Disparadores "cuando muere una criatura" (abajo) | |
| `on_cast` | Disparadores "cuando lanzas..." (abajo) | |
| `propio` | El efecto sigue escrito a mano en un motor: dónde y qué hace | `"gorma/engine.dies: ..."` |
| `<mazo>` | Lo que solo usa ese mazo (claves de su `cards.py`), más `no` y `motor` | |

### Etiquetas (`tags`)

- **Palabras clave:** `flying`, `vigilance`, `lifelink`, `first_strike`, `flash`, `menace`, `trample`, `haste`, `persist`,
  `wither`, `deathtouch`, `defender`, `reach`, `shadow`, `myriad`, `cantblock` (no puede bloquear).
- **Tipos y hechos:** `angel`, `cleric`, `elf`, `wizard`, `shaman`, `zombie`, `legendary`, `black`, `artifact`,
  `enchantment`, `colorless`, `mdfc`, `etb_tapped`, `game_changer`.
- **Roles:** `ramp`, `dork`, `ritual`, `tutor`, `tutor_hand` (tutor a la mano sin restricción), `outlet` (sacrificio),
  `inf_mana_outlet` (outlet que da maná: bucle infinito), `drainer`, `closer` (cierra la partida), `drain_each`,
  `enabler`, `recursive`, `pact` (edicto al morir), `rites`, `mazirek_combo`, `wipe`, `wipe_small`, `fog`,
  `enchantress`, `prot_spot` (protección puntual), `selfc` (se pone contadores -1/-1 a sí misma).
- **Respuestas de Gorma:** `answer_<cre|any|ae>_<inst|sorc|hand>`.

### Disparadores de muerte (`on_death`)

```yaml
Blood Artist:
  on_death:
  - orden: 0               # cómo apila el piloto los disparadores de una misma muerte (menor primero)
    propia: true           # también cuando muere ella misma
    controla: cualquiera   # también cuando muere una criatura rival (por defecto: solo las propias)
    efectos: {drain_one: 1, gain: 1}
```

Condiciones: `propia`, `otra` (no cuando muere ella), `no_ficha` (la que muere no es una ficha), `sacrificada`, `controla: rival` (solo cuando muere una criatura rival; Meathook),
`una_vez` (una vez por muerte aunque haya varias copias), `controla`.
Efectos (en el orden escrito): `drain_one` (al rival con menos vida), `drain_each`, `gain`, `draw`, `token` (tipo de
ficha: `spawn`, `pest`, `treasure`...).

El orden importa: drenar a uno y después a todos no da lo mismo que al revés si un rival está a 1.

### Disparadores al lanzar (`on_cast`)

```yaml
Guttersnipe:
  on_cast:
  - hechizo: instant_sorcery   # o noncreature (cualquier hechizo que no sea criatura)
    multiplica: true           # la duplica Harmonic Prodigy (si es mago o chamán)
    efectos: {dmg_each: 2}
```

Efectos: `dmg_each`, `dmg_one`, `mana` (color), `scry`, `impulse` (exiliar y poder jugar).

## Bloque de un mazo

```yaml
Millikin:
  rock: C
  blor: {mana: 1, no: [rock]}          # clave propia de Blor; y Blor todavía no la trata como roca
  giada: {no: [artifact]}              # Giada todavía no la trata como artefacto
Ojer Axonil, Deepest Might:
  gandalf: {motor: {roles: [amp, key_amp, threat], threat_rank: 0, threat_w: 0.6}}
```

- `no`: etiquetas o campos comunes que ese mazo **todavía no modela** en esa carta. Son inconsistencias entre mazos
  para revisar con Juan; se mantienen para no cambiar números.
- `motor`: decisiones del piloto o de la mesa de ese mazo que todavía viven en su motor: pesos de amenaza
  (`threat_w`, `threat_rank`), qué counterean los rivales (`counter_key`), qué guardar (`keep_home`), prioridades
  (`key_target`), etc. `nota`: algo para revisar.

## Agregar una carta

1. Su línea en `decks/<mazo>/cards.py`: `"Nombre": FORGE,` (o `card("Nombre")` en Gandalf y Blor) y el coste, el tipo y
   el P/T salen de Forge (`core/stats.py`). Solo si el simulador la modela distinto (un X elegido, una carta "mitad"),
   se escriben a mano.
2. Su entrada aquí con las etiquetas y efectos que correspondan. Si la carta ya existe por otro mazo, se comparte.
3. Si su efecto no está en el vocabulario, va como `propio` y en el motor; si se repite en varias cartas, conviene
   sumarlo al vocabulario (y a `core/efectos.py`).
4. `python3 tools/huella.py comparar` solo cambia si la carta está en una lista que se simula.
