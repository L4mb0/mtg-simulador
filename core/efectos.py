"""Efectos de las cartas como datos: lee data/efectos.yaml.

Una entrada por carta, compartida por todos los mazos. Lo que una carta *hace* vive aquí; cómo la pilotea cada
mazo (cuándo la juega, a quién apunta) sigue en su motor. Vocabulario en data/VOCABULARIO.md.

    tags: [outlet, persist, flying, ...]       roles y palabras clave
    enabler: 5                                 prioridad como habilitador de bucles (menor = mejor)
    recur: [2, 2]                              vuelve del cementerio: [coste para lanzarla, coste del retorno]
    on_death:                                  disparadores "cuando muere una criatura"
      - {orden: 0, propia: true, controla: cualquiera, efectos: {drain_one: 1, gain: 1}}
    propio: "texto"                            lo que todavía está escrito a mano en el motor (y en cuál)
"""
import os
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "data", "efectos.yaml")
_DB = None

# condiciones que puede llevar un disparador y efectos que sabe aplicar un motor
CONDICIONES = {"propia", "otra", "no_ficha", "sacrificada", "una_vez", "orden", "controla",
               "hechizo", "multiplica"}   # on_cast: instant_sorcery | noncreature; multiplica: la duplica Harmonic Prodigy
EFECTOS = {"drain_one", "drain_each", "gain", "draw", "token", "dmg_each", "dmg_one", "mana", "scry", "impulse"}


def db():
    global _DB
    if _DB is None:
        loader = getattr(yaml, "CSafeLoader", yaml.SafeLoader)
        with open(PATH, encoding="utf-8") as f:
            _DB = yaml.load(f, Loader=loader) or {}
    return _DB


def card(name):
    return db().get(name, {})


def tags(name):
    return set(card(name).get("tags", ()))


def with_tag(tag, names=None):
    """Cartas con esa etiqueta, en el orden del archivo (o del iterable `names`)."""
    src = db() if names is None else names
    return [n for n in src if tag in db().get(n, {}).get("tags", ())]


def field(tag_field, names=None):
    """{carta: valor} de un campo (enabler, recur, ...), en el orden del archivo."""
    src = db() if names is None else names
    return {n: db()[n][tag_field] for n in src if tag_field in db().get(n, {})}


def with_value(key, value, names=None):
    """Cartas cuya lista `key` (p. ej. grants) contiene `value`, en el orden de `names`."""
    src = db() if names is None else names
    return [n for n in src if value in db().get(n, {}).get(key, ())]


def motor(mazo, name):
    """Bloque `motor` del mazo: decisiones del piloto o de su mesa que todavía son propias de ese motor."""
    return db().get(name, {}).get(mazo, {}).get("motor", {})


def motor_roles(mazo, role, names):
    return [n for n in names if role in motor(mazo, n).get("roles", ())]


def motor_field(mazo, key, names):
    return {n: motor(mazo, n)[key] for n in names if key in motor(mazo, n)}


def motor_order(mazo, key, names):
    """Lista ordenada por el valor `key` (para listas cuyo orden es una prioridad)."""
    f = motor_field(mazo, key, names)
    return sorted(f, key=f.get)


def rival_death_effect(effect, names):
    """Cartas con un disparador "cuando muere una criatura rival" (controla: rival) que tiene ese efecto."""
    return [n for n in names if any(tr.get("controla") == "rival" and effect in tr.get("efectos", {})
                                    for tr in db().get(n, {}).get("on_death", ()))]


def with_death_effect(effect, names, controla=None):
    """Cartas con un disparador de muerte que tiene ese efecto (y, si se pide, `controla: cualquiera`)."""
    out = []
    for n in names:
        for tr in db().get(n, {}).get("on_death", ()):
            if tr.get("controla") == "rival" and controla != "rival":
                continue
            if effect in tr.get("efectos", {}) and (controla is None or tr.get("controla") == controla):
                out.append(n); break
    return out


def cast_table(kind, names):
    """{carta: disparador} de on_cast para un tipo de hechizo, en el orden de `names`."""
    out = {}
    for n in names:
        for tr in db().get(n, {}).get("on_cast", ()):
            if tr["hechizo"] == kind:
                out[n] = tr
    return out


def triggers(event, names=None):
    """[(orden, {carta: disparador})] agrupados por orden ascendente. Dentro de un mismo orden los disparadores
    se resuelven en el orden de los permanentes en el campo (como el bucle original del motor)."""
    src = db() if names is None else names
    groups = {}
    for n in src:
        for tr in db().get(n, {}).get(event, ()):
            bad = set(tr) - CONDICIONES - {"efectos"} or set(tr.get("efectos", {})) - EFECTOS
            if bad:
                raise ValueError(f"{n}: {event} con claves desconocidas {bad}")
            if tr.get("controla") == "rival":
                continue   # "cuando muere una criatura rival": lo resuelve cada motor aparte (rival_death_effect)
            groups.setdefault(tr.get("orden", 99), {})[n] = tr
    return sorted(groups.items())


def check():
    """Errores de forma del archivo (para tests)."""
    errs = []
    for n, e in db().items():
        if not isinstance(e, dict):
            errs.append(f"{n}: no es un mapa"); continue
        for k in e:
            if k not in {"tags", "answer", "answer_sorc", "rock", "draw", "equip", "power_bonus", "grants", "on_hit",
                         "enabler", "recur", "on_death", "on_cast", "propio", "gandalf", "gorma", "giada", "blight", "blor"}:
                errs.append(f"{n}: clave desconocida '{k}'")
        try:
            for ev in ("on_death", "on_cast"):
                triggers(ev, [n])
        except ValueError as x:
            errs.append(str(x))
    return errs


def pendientes():
    """Lo que falta revisar o pasar a datos: excepciones por mazo, notas y efectos escritos a mano."""
    no, notas, propio = [], [], []
    for n, e in db().items():
        for m in ("gandalf", "gorma", "giada", "blight", "blor"):
            b = e.get(m, {})
            if b.get("no"):
                no.append(f"{n} — {m} no modela: {', '.join(b['no'])}")
            if b.get("motor", {}).get("nota"):
                notas.append(f"{n} — {m}: {b['motor']['nota']}")
        if e.get("propio"):
            propio.append(f"{n} — {e['propio']}")
    return no, notas, propio


if __name__ == "__main__":
    errs = check()
    no, notas, propio = pendientes()
    print(f"{len(db())} cartas; errores de forma: {len(errs)}")
    for x in errs:
        print("  ERROR", x)
    for titulo, xs in (("Excepciones por mazo (inconsistencias a revisar)", no), ("Notas", notas),
                       ("Efectos escritos a mano en un motor", propio)):
        print(f"\n{titulo} ({len(xs)}):")
        for x in xs:
            print("  " + x)
