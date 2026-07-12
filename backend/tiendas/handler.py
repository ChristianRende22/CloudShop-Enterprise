"""
Módulo 3 - Gestión de Tiendas.

Una tienda puede tener múltiples productos (Módulo 2, vía tienda_id).
Reglas de rol (sección 5 del enunciado): Administrador gestiona tiendas
(crear/actualizar/desactivar); Operador y Cliente solo consultan (necesitan
ver el catálogo de tiendas para navegar/operar sobre productos).

No existe DELETE físico — igual que Usuarios, se usa borrado lógico
(estado=INACTIVA) para preservar el histórico de productos/pedidos asociados.
"""
import json
import time
import uuid

from common.audit import registrar_auditoria
from common.auth import require_roles
from common.db import table
from common.parsing import parse_body
from common.responses import bad_request, created, not_found, ok
from common.validation import campos_requeridos

TABLA = "TIENDAS_TABLE"
CAMPOS_EDITABLES = ["nombre", "descripcion", "estado"]
ESTADOS_VALIDOS = ("ACTIVA", "INACTIVA")


@require_roles("Administrador")
def crear(event, context):
    """POST /tiendas — solo Administrador."""
    try:
        data = parse_body(event)
    except json.JSONDecodeError:
        return bad_request("Body no es JSON válido")

    faltantes = campos_requeridos(data, ["nombre"])
    if faltantes:
        return bad_request(f"Campos requeridos faltantes: {', '.join(faltantes)}")

    tienda_id = str(uuid.uuid4())
    item = {
        "tienda_id": tienda_id,
        "nombre": data["nombre"],
        "descripcion": data.get("descripcion", ""),
        "estado": "ACTIVA",
        "fecha_creacion": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    table(TABLA).put_item(Item=item)
    registrar_auditoria(event["_user"]["username"], "CREAR_TIENDA", detalle={"tienda_id": tienda_id, "nombre": item["nombre"]})
    return created(item)


@require_roles("Administrador", "Operador", "Cliente")
def listar(event, context):
    """GET /tiendas — todos los roles pueden ver el catálogo de tiendas."""
    params = event.get("queryStringParameters") or {}
    tiendas = table(TABLA)
    resultado = tiendas.scan(Limit=int(params.get("limit", 50)))
    return ok({"items": resultado.get("Items", []), "count": resultado.get("Count", 0)})


@require_roles("Administrador", "Operador", "Cliente")
def obtener(event, context):
    """GET /tiendas/{id} — todos los roles."""
    tienda_id = event["pathParameters"]["id"]
    item = table(TABLA).get_item(Key={"tienda_id": tienda_id}).get("Item")
    if not item:
        return not_found("Tienda no encontrada")
    return ok(item)


@require_roles("Administrador")
def actualizar(event, context):
    """PATCH /tiendas/{id} — solo Administrador."""
    tienda_id = event["pathParameters"]["id"]
    try:
        data = parse_body(event)
    except json.JSONDecodeError:
        return bad_request("Body no es JSON válido")

    if not table(TABLA).get_item(Key={"tienda_id": tienda_id}).get("Item"):
        return not_found("Tienda no encontrada")

    if "estado" in data and data["estado"] not in ESTADOS_VALIDOS:
        return bad_request(f"estado inválido. Debe ser uno de: {', '.join(ESTADOS_VALIDOS)}")

    tiendas = table(TABLA)
    expr_names, expr_values, sets = {}, {}, []
    for campo in CAMPOS_EDITABLES:
        if campo in data:
            expr_names[f"#{campo}"] = campo
            expr_values[f":{campo}"] = data[campo]
            sets.append(f"#{campo} = :{campo}")

    if not sets:
        return bad_request("No se enviaron campos válidos para actualizar")

    tiendas.update_item(
        Key={"tienda_id": tienda_id},
        UpdateExpression="SET " + ", ".join(sets),
        ExpressionAttributeNames=expr_names,
        ExpressionAttributeValues=expr_values,
    )
    registrar_auditoria(event["_user"]["username"], "ACTUALIZAR_TIENDA", detalle={"tienda_id": tienda_id, "campos": list(data.keys())})
    return ok(tiendas.get_item(Key={"tienda_id": tienda_id}).get("Item"))


@require_roles("Administrador")
def desactivar(event, context):
    """DELETE /tiendas/{id} — borrado LÓGICO (estado=INACTIVA). Solo Administrador."""
    tienda_id = event["pathParameters"]["id"]
    tiendas = table(TABLA)
    if not tiendas.get_item(Key={"tienda_id": tienda_id}).get("Item"):
        return not_found("Tienda no encontrada")

    tiendas.update_item(
        Key={"tienda_id": tienda_id},
        UpdateExpression="SET estado = :estado",
        ExpressionAttributeValues={":estado": "INACTIVA"},
    )
    registrar_auditoria(event["_user"]["username"], "DESACTIVAR_TIENDA", detalle={"tienda_id": tienda_id})
    return ok({"tienda_id": tienda_id, "estado": "INACTIVA"})
