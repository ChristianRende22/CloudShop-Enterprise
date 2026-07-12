"""Validaciones básicas de entrada, reutilizadas por todos los módulos
(Clase 20/22: la validación de entrada es la primera línea de defensa)."""
import re

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def es_email_valido(email):
    return bool(email) and bool(EMAIL_RE.match(email))


def campos_requeridos(data: dict, campos: list):
    """Devuelve la lista de campos faltantes o vacíos en `data`."""
    return [c for c in campos if data.get(c) in (None, "", [])]


def es_numero_positivo(valor):
    try:
        return float(valor) >= 0
    except (TypeError, ValueError):
        return False


def es_entero_positivo(valor):
    try:
        return int(valor) >= 0 and float(valor) == int(valor)
    except (TypeError, ValueError):
        return False
