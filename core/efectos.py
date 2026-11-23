"""Efectos de las cartas como datos: lee data/efectos.yaml.

Una entrada por carta, compartida por todos los mazos. Lo que una carta *hace* vive aquí; cómo la pilotea cada
mazo (cuándo la juega, a quién apunta) sigue en su motor. Vocabulario en data/VOCABULARIO.md.

    tags: [outlet, persist, flying, ...]       roles y palabras clave
    enabler: 5                                 prioridad como habilitador de bucles (menor = mejor)
    recur: [2, 2]                              vuelve del cementerio: [coste para lanzarla, coste del retorno]
    on_death:                                  disparadores "cuando muere una criatura"
      - {orden: 0, propia: true, efectos: {drain_one: 1, gain: 1}}
    propio: "texto"                            lo que todavía está escrito a mano en el motor (y en cuál)
"""
import os
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "data", "efectos.yaml")
_DB = None

# condiciones que puede llevar un disparador y efectos que sabe aplicar un motor
CONDICIONES = {"propia", "otra", "no_ficha", "sacrificada", "una_vez", "orden"}
EFECTOS = {"drain_one", "drain_each", "gain", "draw", "token"}


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
            groups.setdefault(tr.get("orden", 99), {})[n] = tr
    return sorted(groups.items())


def check():
    """Errores de forma del archivo (para tests)."""
    errs = []
    for n, e in db().items():
        if not isinstance(e, dict):
            errs.append(f"{n}: no es un mapa"); continue
        for k in e:
            if k not in {"tags", "enabler", "recur", "on_death", "propio"}:
                errs.append(f"{n}: clave desconocida '{k}'")
        try:
            for tr in e.get("on_death", ()):
                triggers("on_death", [n])
        except ValueError as x:
            errs.append(str(x))
    return errs
