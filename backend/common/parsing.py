"""
Parseo de body JSON compatible con DynamoDB.

boto3 (resource-level) rechaza `float` nativo de Python — hay que usar
`Decimal`. Centralizamos esto aquí para que ningún módulo lo vuelva a pisar
(bug real atrapado por los tests del módulo Productos: precio=19.99 tumbaba
el put_item con TypeError).
"""
import decimal
import json


def parse_body(event):
    """Parsea event['body'] a dict. Los números se parsean como Decimal.
    Lanza json.JSONDecodeError si el body no es JSON válido."""
    raw = event.get("body") or "{}"
    return json.loads(raw, parse_float=decimal.Decimal, parse_int=decimal.Decimal)
