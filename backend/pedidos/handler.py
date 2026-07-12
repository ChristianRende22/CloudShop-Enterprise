"""
Módulo 5 - Gestión de Pedidos.

Es el módulo que conecta todo el sistema: al crear un pedido se actualiza
inventario, se publica un evento en EventBridge (sección 6 del enunciado),
se registra auditoría y (via el consumer en backend/notificaciones) se envía
un correo por SES. Esto es exactamente el "Caso 2" de prueba obligatorio.

Roles (sección 5):
- Cliente: crea pedidos, consulta y cancela SUS PROPIOS pedidos.
- Operador: "gestiona pedidos" -> consulta todos, avanza el estado, cancela cualquiera.
- Administrador: todo lo anterior + ve reportes (vía Dashboard).

Estados (orden fijo, solo se avanza secuencialmente):
Pendiente -> Confirmado -> En preparación -> Enviado -> Entregado
Cancelado es un estado terminal alcanzable desde cualquier estado ANTES de
"Enviado" (una vez enviado, ya no se puede cancelar en este modelo).
"""
import json
import time
import uuid

from botocore.exceptions import ClientError

from common.audit import registrar_auditoria
from common.auth import require_roles
from common.db import table
from common.events import publicar_evento
from common.parsing import parse_body
from common.responses import bad_request, conflict, created, forbidden, not_found, ok
from common.validation import campos_requeridos, es_entero_positivo

TABLA = "PEDIDOS_TABLE"
TABLA_PRODUCTOS = "PRODUCTOS_TABLE"

ESTADOS_ORDEN = ["Pendiente", "Confirmado", "En preparación", "Enviado", "Entregado"]
ESTADOS_CANCELABLES = ("Pendiente", "Confirmado", "En preparación")


def _reservar_inventario(producto_id, cantidad):
    """UpdateItem condicional y atomico: descuenta stock SOLO si hay suficiente.
    Devuelve el producto actualizado (con precio y tienda_id) o None si no
    hay stock / no existe -> evita condiciones de carrera (Clase 22)."""
    productos = table(TABLA_PRODUCTOS)
    try:
        resp = productos.update_item(
            Key={"producto_id": producto_id},
            UpdateExpression="SET inventario_disponible = inventario_disponible - :cant",
            ConditionExpression="attribute_exists(producto_id) AND inventario_disponible >= :cant",
            ExpressionAttributeValues={":cant": cantidad},
            ReturnValues="ALL_NEW",
        )
        return resp["Attributes"]
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return None
        raise


def _liberar_inventario(producto_id, cantidad):
    """Compensacion: devuelve stock (usado en rollback y en cancelaciones)."""
    table(TABLA_PRODUCTOS).update_item(
        Key={"producto_id": producto_id},
        UpdateExpression="SET inventario_disponible = inventario_disponible + :cant",
        ExpressionAttributeValues={":cant": cantidad},
    )


@require_roles("Cliente")
def crear(event, context):
    """POST /pedidos
    Body: {"items": [{"producto_id": "...", "cantidad": N}, ...]}
    """
    solicitante = event["_user"]
    try:
        data = parse_body(event)
    except json.JSONDecodeError:
        return bad_request("Body no es JSON válido")

    items_solicitados = data.get("items")
    if not items_solicitados or not isinstance(items_solicitados, list):
        return bad_request("items es requerido y debe ser una lista no vacía")

    for it in items_solicitados:
        faltantes = campos_requeridos(it, ["producto_id", "cantidad"])
        if faltantes:
            return bad_request(f"Cada item requiere: {', '.join(faltantes)}")
        if not es_entero_positivo(it["cantidad"]) or it["cantidad"] == 0:
            return bad_request(f"cantidad inválida para producto {it['producto_id']}")

    # Reserva de inventario item por item, con compensacion si algo falla a mitad de camino
    items_confirmados = []
    for it in items_solicitados:
        producto = _reservar_inventario(it["producto_id"], it["cantidad"])
        if producto is None:
            for confirmado in items_confirmados:
                _liberar_inventario(confirmado["producto_id"], confirmado["cantidad"])
            return conflict(f"Sin inventario suficiente para el producto {it['producto_id']}")

        precio_unitario = producto["precio"]
        items_confirmados.append(
            {
                "producto_id": it["producto_id"],
                "nombre": producto.get("nombre", ""),
                "tienda_id": producto.get("tienda_id", ""),
                "cantidad": it["cantidad"],
                "precio_unitario": precio_unitario,
                "subtotal": precio_unitario * it["cantidad"],
            }
        )

    total = sum(i["subtotal"] for i in items_confirmados)
    pedido_id = str(uuid.uuid4())
    ahora = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    pedido = {
        "pedido_id": pedido_id,
        "cliente_id": solicitante["sub"],
        "cliente_email": solicitante["email"],
        "cliente_username": solicitante["username"],
        "items": items_confirmados,
        "total": total,
        "estado": "Pendiente",
        "fecha_creacion": ahora,
        "fecha_actualizacion": ahora,
    }
    table(TABLA).put_item(Item=pedido)

    publicar_evento("PedidoCreado", {
        "pedido_id": pedido_id,
        "cliente_id": solicitante["sub"],
        "cliente_email": solicitante["email"],
        "total": str(total),
        "items": items_confirmados,
    })

    registrar_auditoria(solicitante["username"], "CREAR_PEDIDO", detalle={"pedido_id": pedido_id, "total": str(total)})
    return created(pedido)


@require_roles("Administrador", "Operador", "Cliente")
def listar(event, context):
    """GET /pedidos
    Administrador/Operador ven todos los pedidos; Cliente solo los suyos
    (Query por el GSI cliente_id-index, evita Scan)."""
    solicitante = event["_user"]
    params = event.get("queryStringParameters") or {}
    pedidos = table(TABLA)

    if solicitante["role"] == "Cliente":
        resultado = pedidos.query(
            IndexName="cliente_id-index",
            KeyConditionExpression="cliente_id = :c",
            ExpressionAttributeValues={":c": solicitante["sub"]},
        )
    elif params.get("cliente_id"):
        resultado = pedidos.query(
            IndexName="cliente_id-index",
            KeyConditionExpression="cliente_id = :c",
            ExpressionAttributeValues={":c": params["cliente_id"]},
        )
    else:
        resultado = pedidos.scan(Limit=int(params.get("limit", 50)))

    return ok({"items": resultado.get("Items", []), "count": resultado.get("Count", 0)})


@require_roles("Administrador", "Operador", "Cliente")
def obtener(event, context):
    """GET /pedidos/{id} — Cliente solo el propio; Admin/Operador cualquiera."""
    pedido_id = event["pathParameters"]["id"]
    solicitante = event["_user"]

    item = table(TABLA).get_item(Key={"pedido_id": pedido_id}).get("Item")
    if not item:
        return not_found("Pedido no encontrado")
    if solicitante["role"] == "Cliente" and item["cliente_id"] != solicitante["sub"]:
        return forbidden("No puedes consultar pedidos de otro cliente")
    return ok(item)


@require_roles("Administrador", "Operador")
def actualizar(event, context):
    """PATCH /pedidos/{id} — avanza el estado UN paso en la secuencia.
    Body: {"estado": "Confirmado"} (debe ser el siguiente estado valido)."""
    pedido_id = event["pathParameters"]["id"]
    try:
        data = parse_body(event)
    except json.JSONDecodeError:
        return bad_request("Body no es JSON válido")

    nuevo_estado = data.get("estado")
    if nuevo_estado not in ESTADOS_ORDEN:
        return bad_request(f"estado inválido. Debe ser uno de: {', '.join(ESTADOS_ORDEN)}")

    pedidos = table(TABLA)
    pedido = pedidos.get_item(Key={"pedido_id": pedido_id}).get("Item")
    if not pedido:
        return not_found("Pedido no encontrado")

    estado_actual = pedido["estado"]
    if estado_actual == "Cancelado":
        return conflict("El pedido está cancelado, no se puede cambiar su estado")
    if estado_actual == "Entregado":
        return conflict("El pedido ya fue entregado, no admite más cambios de estado")

    indice_actual = ESTADOS_ORDEN.index(estado_actual)
    indice_nuevo = ESTADOS_ORDEN.index(nuevo_estado)
    if indice_nuevo != indice_actual + 1:
        return bad_request(f"Transición inválida: de '{estado_actual}' solo se puede avanzar a '{ESTADOS_ORDEN[indice_actual + 1]}'")

    ahora = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    pedidos.update_item(
        Key={"pedido_id": pedido_id},
        UpdateExpression="SET estado = :estado, fecha_actualizacion = :fecha",
        ExpressionAttributeValues={":estado": nuevo_estado, ":fecha": ahora},
    )
    registrar_auditoria(event["_user"]["username"], "ACTUALIZAR_ESTADO_PEDIDO", detalle={"pedido_id": pedido_id, "de": estado_actual, "a": nuevo_estado})
    return ok(pedidos.get_item(Key={"pedido_id": pedido_id}).get("Item"))


@require_roles("Administrador", "Operador", "Cliente")
def cancelar(event, context):
    """DELETE /pedidos/{id} — Cliente puede cancelar SU pedido; Admin/Operador cualquiera.
    Borrado logico (estado=Cancelado) + devuelve el inventario reservado."""
    pedido_id = event["pathParameters"]["id"]
    solicitante = event["_user"]

    pedidos = table(TABLA)
    pedido = pedidos.get_item(Key={"pedido_id": pedido_id}).get("Item")
    if not pedido:
        return not_found("Pedido no encontrado")

    if solicitante["role"] == "Cliente" and pedido["cliente_id"] != solicitante["sub"]:
        return forbidden("No puedes cancelar pedidos de otro cliente")

    if pedido["estado"] not in ESTADOS_CANCELABLES:
        return conflict(f"No se puede cancelar un pedido en estado '{pedido['estado']}'")

    for item in pedido["items"]:
        _liberar_inventario(item["producto_id"], item["cantidad"])

    ahora = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    pedidos.update_item(
        Key={"pedido_id": pedido_id},
        UpdateExpression="SET estado = :estado, fecha_actualizacion = :fecha",
        ExpressionAttributeValues={":estado": "Cancelado", ":fecha": ahora},
    )

    publicar_evento("PedidoCancelado", {
        "pedido_id": pedido_id,
        "cliente_id": pedido["cliente_id"],
        "cliente_email": pedido["cliente_email"],
    })
    registrar_auditoria(solicitante["username"], "CANCELAR_PEDIDO", detalle={"pedido_id": pedido_id})
    return ok({"pedido_id": pedido_id, "estado": "Cancelado"})
