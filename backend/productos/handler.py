"""
Módulo 2 - Gestión de Productos.

Cada producto pertenece a una tienda (`tienda_id`, ver Módulo 3). Reglas de rol
(sección 5 del enunciado):
- Administrador: crear, actualizar (cualquier campo), eliminar, consultar.
- Operador: "gestiona inventario" -> solo puede tocar `inventario_disponible`.
- Cliente: solo consulta (para poder comprar).
- DELETE /productos es EXCLUSIVO de Administrador (regla explícita del enunciado).
"""
import json
import time
import uuid

from common.audit import registrar_auditoria
from common.auth import require_roles
from common.db import table
from common.parsing import parse_body
from common.responses import bad_request, created, forbidden, not_found, ok
from common.validation import campos_requeridos, es_entero_positivo, es_numero_positivo

TABLA = "PRODUCTOS_TABLE"
CAMPOS_ADMIN_EDITABLES = ["nombre", "descripcion", "categoria", "precio", "inventario_disponible", "tienda_id"]


def _validar_datos_producto(data, requerir_todos=True):
    campos = ["codigo", "nombre", "categoria", "precio", "inventario_disponible", "tienda_id"]
    if requerir_todos:
        faltantes = campos_requeridos(data, campos)
        if faltantes:
            return f"Campos requeridos faltantes: {', '.join(faltantes)}"
    if "precio" in data and not es_numero_positivo(data["precio"]):
        return "precio debe ser un número >= 0"
    if "inventario_disponible" in data and not es_entero_positivo(data["inventario_disponible"]):
        return "inventario_disponible debe ser un entero >= 0"
    return None


@require_roles("Administrador")
def crear(event, context):
    """POST /productos — solo Administrador."""
    try:
        data = parse_body(event)
    except json.JSONDecodeError:
        return bad_request("Body no es JSON válido")

    error = _validar_datos_producto(data, requerir_todos=True)
    if error:
        return bad_request(error)

    producto_id = str(uuid.uuid4())
    item = {
        "producto_id": producto_id,
        "codigo": data["codigo"],
        "nombre": data["nombre"],
        "descripcion": data.get("descripcion", ""),
        "categoria": data["categoria"],
        "precio": data["precio"],
        "inventario_disponible": data["inventario_disponible"],
        "tienda_id": data["tienda_id"],
        "fecha_creacion": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    table(TABLA).put_item(Item=item)
    registrar_auditoria(event["_user"]["username"], "CREAR_PRODUCTO", detalle={"producto_id": producto_id, "codigo": item["codigo"]})
    return created(item)


@require_roles("Administrador", "Operador", "Cliente")
def listar(event, context):
    """GET /productos — todos los roles pueden ver el catálogo.
    Filtro opcional ?tienda_id=... usando el GSI tienda_id-index (evita Scan)."""
    params = event.get("queryStringParameters") or {}
    productos = table(TABLA)

    if params.get("tienda_id"):
        resultado = productos.query(
            IndexName="tienda_id-index",
            KeyConditionExpression="tienda_id = :t",
            ExpressionAttributeValues={":t": params["tienda_id"]},
        )
    else:
        resultado = productos.scan(Limit=int(params.get("limit", 50)))

    return ok({"items": resultado.get("Items", []), "count": resultado.get("Count", 0)})


@require_roles("Administrador", "Operador", "Cliente")
def obtener(event, context):
    """GET /productos/{id} — todos los roles."""
    producto_id = event["pathParameters"]["id"]
    item = table(TABLA).get_item(Key={"producto_id": producto_id}).get("Item")
    if not item:
        return not_found("Producto no encontrado")
    return ok(item)


@require_roles("Administrador", "Operador")
def actualizar(event, context):
    """PATCH /productos/{id}
    Administrador: puede editar cualquier campo.
    Operador: solo puede editar `inventario_disponible` (gestiona inventario)."""
    producto_id = event["pathParameters"]["id"]
    solicitante = event["_user"]
    es_admin = solicitante["role"] == "Administrador"

    try:
        data = parse_body(event)
    except json.JSONDecodeError:
        return bad_request("Body no es JSON válido")

    if not table(TABLA).get_item(Key={"producto_id": producto_id}).get("Item"):
        return not_found("Producto no encontrado")

    campos_permitidos = CAMPOS_ADMIN_EDITABLES if es_admin else ["inventario_disponible"]
    campos_no_permitidos = [c for c in data if c not in campos_permitidos]
    if not es_admin and campos_no_permitidos:
        return forbidden(f"Operador solo puede modificar 'inventario_disponible'. Campos no permitidos: {', '.join(campos_no_permitidos)}")

    error = _validar_datos_producto(data, requerir_todos=False)
    if error:
        return bad_request(error)

    productos = table(TABLA)
    expr_names, expr_values, sets = {}, {}, []
    for campo in campos_permitidos:
        if campo in data:
            expr_names[f"#{campo}"] = campo
            expr_values[f":{campo}"] = data[campo]
            sets.append(f"#{campo} = :{campo}")

    if not sets:
        return bad_request("No se enviaron campos válidos para actualizar")

    productos.update_item(
        Key={"producto_id": producto_id},
        UpdateExpression="SET " + ", ".join(sets),
        ExpressionAttributeNames=expr_names,
        ExpressionAttributeValues=expr_values,
    )
    registrar_auditoria(solicitante["username"], "ACTUALIZAR_PRODUCTO", detalle={"producto_id": producto_id, "campos": list(data.keys())})
    return ok(productos.get_item(Key={"producto_id": producto_id}).get("Item"))


@require_roles("Administrador")
def eliminar(event, context):
    """DELETE /productos/{id} — exclusivo Administrador (regla explícita del enunciado)."""
    producto_id = event["pathParameters"]["id"]
    productos = table(TABLA)
    if not productos.get_item(Key={"producto_id": producto_id}).get("Item"):
        return not_found("Producto no encontrado")

    productos.delete_item(Key={"producto_id": producto_id})
    registrar_auditoria(event["_user"]["username"], "ELIMINAR_PRODUCTO", detalle={"producto_id": producto_id})
    return ok({"producto_id": producto_id, "eliminado": True})
