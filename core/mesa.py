"""Mesa v2: los parámetros por bracket y las funciones de reloj que comparten todos los simuladores.

Fuente única. Cada simulador arma sus tablas propias a partir de aquí; lo que todavía es propio de un mazo
(pesos por carta, a qué apunta la remoción, cómo barre) sigue en decks/<mazo>/. Los desvíos de un mazo
respecto de esta tabla se declaran en DESVIOS, para que se vean y se puedan revisar.

Origen de los números: mesa v2 hecha con Juan regla por regla (14–16/11/2026) a partir de la IA de MTG Forge
y de 6.532 mazos de Archidekt por bracket; tipos de victoria de Playgroup.gg; Mazmorra = claude/mesa-mazmorra.md.
"""
import math

# ---------------------------------------------------------------- reglas generales (iguales en todos los brackets)
SPREAD = 0.9          # dispersión del reloj de cada rival (logística)
RETRY = 0.7           # frenado, reintenta al 70% ...
DELAY = 2             # ... después de rearmar 2 turnos
REM_THR = 0.5         # el rival usa remoción en lo que pesa 0,5+ (0,4 si ve 2+)
KEEP_LAST = 0.4       # guarda la última remoción el 40% de las veces (salvo bombas)
BOMB = 0.8
TAU = 0.3             # softmax para elegir blanco en toda la mesa
ARCH = 0.3            # bonus de "archienemigo" al que va ganando
NOISE = 0.2           # ruido en la evaluación de amenazas
P_INST = 0.5          # respuesta al instante
P_REM_STOP = 0.4      # la remoción de otro rival frena un intento el 40% de las veces
CNT_UP = 0.75         # el azul deja maná arriba en tu turno
COUNTER_BY_MV = {0: 0.02, 1: 0.02, 2: 0.05, 3: 0.15}
COUNTER_HI = 0.30     # coste 4+ que no es clave
WIPE_MARGIN = 1.5     # barre si la mesa de los demás supera la suya por 1,5
REM_TYPES = (("cre", 0.55), ("any", 0.20), ("ae", 0.20), ("edict", 0.05))

# ---------------------------------------------------------------- tipos de victoria (Playgroup 2026)
# combate, daño directo, pérdida de vida, combo/alternativa; el azul aparte
WT_CASUAL = (("combat", 0.66), ("dmg", 0.10), ("loss", 0.09), ("combo", 0.15))
WT_B4 = (("combat", 0.55), ("dmg", 0.10), ("loss", 0.10), ("combo", 0.25))
WT_B5 = (("combat", 0.25), ("dmg", 0.05), ("loss", 0.05), ("combo", 0.65))
WB_CASUAL = (("combat", 0.49), ("dmg", 0.05), ("loss", 0.05), ("combo", 0.41))
WB_B4 = (("combat", 0.40), ("dmg", 0.05), ("loss", 0.05), ("combo", 0.50))
WB_B5 = (("combat", 0.15), ("dmg", 0.03), ("loss", 0.02), ("combo", 0.80))


def mix(wt):
    """Los tipos de victoria como tupla de probabilidades (formato de Blight)."""
    return tuple(p for _, p in wt)


# ---------------------------------------------------------------- por bracket
# mus: turno típico de cada rival · rem/cpt: remociones por 99 y cartas por turno · blue/cnt: jugadores azules y
# counters por 99 · wipes y su ventana (wipe_lo, wipe_hi) · gyh/gyh_perm: odio a cementerio (prob., fracción tipo
# Rest in Peace) · arth: odio a artefactos · aem: odio masivo a artefactos y encantamientos · curve: valor de la mesa
# rival (v0, dv, vmax) · combat_start: desde qué turno atacan · nb: fracción de tierras no básicas · wt/wb: victorias
BRACKETS = {
    "B1": dict(mus=(10, 11, 12), cpt=1.1, rem=5, blue=1, cnt=3, wipes=2, wipe_lo=6, wipe_hi=10, gyh=0.05, gyh_perm=0.0,
               arth=0.10, aem=0.20, curve=(-0.1, 0.1, 0.8), combat_start=6, nb=0.20, wt=WT_CASUAL, wb=WB_CASUAL),
    "B2": dict(mus=(9, 10, 11), cpt=1.2, rem=5, blue=1, cnt=3, wipes=2, wipe_lo=5, wipe_hi=9, gyh=0.10, gyh_perm=0.2,
               arth=0.15, aem=0.25, curve=(0.0, 0.1, 0.9), combat_start=6, nb=0.35, wt=WT_CASUAL, wb=WB_CASUAL),
    "B3": dict(mus=(7, 8, 9), cpt=1.3, rem=5, blue=1, cnt=5, wipes=2, wipe_lo=4, wipe_hi=8, gyh=0.20, gyh_perm=0.3,
               arth=0.25, aem=0.30, curve=(0.1, 0.1, 1.0), combat_start=5, nb=0.50, wt=WT_CASUAL, wb=WB_CASUAL),
    "B4": dict(mus=(5, 6, 7), cpt=1.5, rem=5, blue=1, cnt=7, wipes=2, wipe_lo=4, wipe_hi=7, gyh=0.35, gyh_perm=0.4,
               arth=0.35, aem=0.35, curve=(0.2, 0.1, 1.1), combat_start=4, nb=0.65, wt=WT_B4, wb=WB_B4),
    "B5": dict(mus=(3, 4, 4), cpt=2.0, rem=4, blue=2, cnt=10, wipes=1, wipe_lo=3, wipe_hi=6, gyh=0.50, gyh_perm=0.5,
               arth=0.40, aem=0.40, curve=(0.3, 0.1, 1.2), combat_start=3, nb=0.80, wt=WT_B5, wb=WB_B5),
    "B3+B4": dict(mus=(5, 8, 9), cpt=1.4, rem=5, blue=1, cnt=6, wipes=2, wipe_lo=4, wipe_hi=8, gyh=0.25, gyh_perm=0.3,
                  arth=0.30, aem=0.30, curve=(0.1, 0.1, 1.0), combat_start=5, nb=0.50, wt=WT_CASUAL, wb=WB_CASUAL),
}
BRACKET_NAMES = list(BRACKETS)

# ---------------------------------------------------------------- Mazmorra (torneo B3 de La Mazmorra TCG)
# Receta de claude/mesa-mazmorra.md: relojes 4/5/6 con dispersión 1,0, 7 remociones, azul con 8 counters,
# 1,5 cartas por turno, curva y victorias de B4; turbo que rearma en 1 turno y reintenta al 85%; remoción entre
# rivales que le tumba un intento al más rápido; golpes parciales; edictos (Sephiroth) y Strip Mine (Tifa).
# Juan (17/11): sin límite de tiempo salvo que se pida (time_turns es la variante "con desempate por vida").
MAZMORRA = dict(BRACKETS["B4"], mus=(4, 5, 6), spread=1.0, rem=7, cnt=8, cpt=1.5, wipes=2,
                retry=RETRY, delay=DELAY, retry_turbo=0.85, delay_turbo=1, rem_slows=0.5, rem_stop=P_REM_STOP,
                p_partial=0.4, edict=(3 / 11, 0.35), strip=(3 / 11, 0.5),
                time_turns=((6, 0.2), (7, 0.4), (8, 0.4)), me_life=(25, 38), opp_other_dmg=(0, 15))
MAZMORRA_VARIANTES = {"Mazmorra optimista": dict(mus=(4, 5, 7)), "Mazmorra pesimista": dict(mus=(3, 5, 6))}

# Desvíos conocidos de un mazo respecto de esta tabla (se mantienen para no cambiar sus números; revisar con Juan)
DESVIOS = {
    "gandalf": "Mazmorra: odio a cementerio 0,30 (B4 dice 0,35; Gorma usa todo el odio de B3: 0,20 / 0,3 / 0,25, "
               "ventana 4–8). No tiene las variantes optimista y pesimista.",
    "gorma": "Mazmorra: odio a cementerio y combate desde el turno de B3, no de B4.",
    "blor": "Mazmorra: parte de B3 y cambia relojes, remoción, counters, cartas por turno, curva y victorias a B4; "
            "el odio masivo a artefactos y encantamientos queda en 0,35 (B4).",
    "giada": "Sin Mazmorra todavía.",
    "blight": "Sin Mazmorra todavía.",
}


def bracket(name):
    """Parámetros de una mesa (bracket o Mazmorra y sus variantes)."""
    if name in BRACKETS:
        return BRACKETS[name]
    if name == "Mazmorra":
        return MAZMORRA
    if name in MAZMORRA_VARIANTES:
        return dict(MAZMORRA, **MAZMORRA_VARIANTES[name])
    raise KeyError(name)


# ---------------------------------------------------------------- relojes y sorteos
def F(t, mu, sp):
    """Probabilidad acumulada de que un rival con turno típico mu ya lo haya intentado en el turno t."""
    return 1 / (1 + math.exp(-(t + 0.5 - mu) / sp))


def attempt_p(t, mu, sp=SPREAD):
    """Probabilidad de que lo intente justo en el turno t si no lo intentó antes."""
    f0 = F(t - 1, mu, sp)
    return (F(t, mu, sp) - f0) / max(1e-9, 1 - f0)


def pick(rng, table):
    """Elige una clave de ((clave, prob), ...) con un solo rng.random()."""
    r = rng.random()
    for k, p in table:
        r -= p
        if r < 0:
            return k
    return table[-1][0]


def cfg_v2(name):
    """Claves de la mesa v2 con el formato de TableCfg de Giada y Blor."""
    v = bracket(name)
    d = dict(bracket=name, mus=v["mus"], win_types=v["wt"], win_blue=v["wb"], aem=v["aem"], opp_curve=v["curve"],
             rem=v["rem"], cpt=v["cpt"], wipes=v["wipes"], cnt=v["cnt"])
    if v["blue"] != 1:
        d["n_blue"] = v["blue"]
    return d
