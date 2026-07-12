"""
Módulo 4 - Carrito de Compras.

El carrito es siempre "el mío": no hay {id} en la ruta, el usuario_id sale del
token (sub de Cognito) via event["_user"]. Exclusivo de rol Cliente (comprar
productos es una accion de Cliente segun la seccion 5 del enunciado).

Tabla Carrito: PK usuario_id + SK producto_id -> cada producto en el carrito
es un item independiente, con cantidad. Esto permite:
- agregar: upsert (ADD cantidad si ya existe, PutItem si es nuevo)
- modificar: UpdateItem de un solo item
- eliminar: DeleteItem de un solo item
- vaciar: Query de todos los items del usuario + BatchWriteItem de borrado
"""
import json

from common.auth import require_roles
from common.db import table
from common.parsing import parse_body
from common.responses import bad_request, created, not_found, ok
from common.validation import es_entero_positivo

TABLA = "CARRITO_TABLE"


@require_roles("Cliente")
def agregar(event, context):
    """POST /carrito
    Body: {"producto_id": "...", "cantidad": N}
    Si el producto ya esta en el carrito, suma la cantidad; si no, lo crea.
    """
    usuario_id = event["_user"]["sub"]
    try:
        data = parse_body(event)
    except json.JSONDecodeError:
        return bad_request("Body no es JSON válido")

    producto_id = data.get("producto_id")
    cantidad = data.get("cantidad", 1)
    if not producto_id:
        return bad_request("producto_id es requerido")
    if not es_entero_positivo(cantidad) or cantidad == 0:
        return bad_request("cantidad debe ser un entero > 0")

    carrito = table(TABLA)
    carrito.update_item(
        Key={"usuario_id": usuario_id, "producto_id": producto_id},
        UpdateExpression="SET cantidad = if_not_exists(cantidad, :cero) + :cantidad",
        ExpressionAttributeValues={":cantidad": cantidad, ":cero": 0},
    )
    item = carrito.get_item(Key={"usuario_id": usuario_id, "producto_id": producto_id}).get("Item")
    return created(item)


@require_roles("Cliente")
def listar(event, context):
    """GET /carrito — todos los productos en el carrito del usuario autenticado."""
    usuario_id = event["_user"]["sub"]
    carrito = table(TABLA)
    resultado = carrito.query(
        KeyConditionExpression="usuario_id = :u",
        ExpressionAttributeValues={":u": usuario_id},
    )
    items = resultado.get("Items", [])
    total_items = sum(int(i["cantidad"]) for i in items)
    return ok({"items": items, "count": len(items), "total_unidades": total_items})


@require_roles("Cliente")
def modificar(event, context):
    """PATCH /carrito/{producto_id}
    Body: {"cantidad": N} — reemplaza la cantidad (no suma)."""
    usuario_id = event["_user"]["sub"]
    producto_id = event["pathParameters"]["id"]

    try:
        data = parse_body(event)
    except json.JSONDecodeError:
        return bad_request("Body no es JSON válido")

    cantidad = data.get("cantidad")
    if not es_entero_positivo(cantidad) or cantidad == 0:
        return bad_request("cantidad debe ser un entero > 0 (usa DELETE para quitar el producto)")

    carrito = table(TABLA)
    if not carrito.get_item(Key={"usuario_id": usuario_id, "producto_id": producto_id}).get("Item"):
        return not_found("El producto no está en el carrito")

    carrito.update_item(
        Key={"usuario_id": usuario_id, "producto_id": producto_id},
        UpdateExpression="SET cantidad = :cantidad",
        ExpressionAttributeValues={":cantidad": cantidad},
    )
    return ok(carrito.get_item(Key={"usuario_id": usuario_id, "producto_id": producto_id}).get("Item"))


@require_roles("Cliente")
def eliminar(event, context):
    """DELETE /carrito/{producto_id} — quita un producto especifico del carrito."""
    usuario_id = event["_user"]["sub"]
    producto_id = event["pathParameters"]["id"]

    carrito = table(TABLA)
    if not carrito.get_item(Key={"usuario_id": usuario_id, "producto_id": producto_id}).get("Item"):
        return not_found("El producto no está en el carrito")

    carrito.delete_item(Key={"usuario_id": usuario_id, "producto_id": producto_id})
    return ok({"producto_id": producto_id, "eliminado": True})


@require_roles("Cliente")
def vaciar(event, context):
    """DELETE /carrito — elimina todos los productos del carrito del usuario."""
    usuario_id = event["_user"]["sub"]
    carrito = table(TABLA)

    resultado = carrito.query(
        KeyConditionExpression="usuario_id = :u",
        ExpressionAttributeValues={":u": usuario_id},
        ProjectionExpression="usuario_id, producto_id",
    )
    items = resultado.get("Items", [])
    with carrito.batch_writer() as batch:
        for item in items:
            batch.delete_item(Key={"usuario_id": usuario_id, "producto_id": item["producto_id"]})

    return ok({"usuario_id": usuario_id, "eliminados": len(items)})
