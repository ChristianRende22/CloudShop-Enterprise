"""
Módulo 1 - Gestión de Usuarios.

Cada función es una Lambda independiente (una operación CRUD por función,
"funciones enfocadas" — buena práctica vista en Clase 22), todas comparten la
tabla DynamoDB "Usuarios" (clave primaria: user_id = sub de Cognito).

Reglas de negocio (sección 5 del enunciado):
- Administrador: gestiona usuarios (cualquier rol, cualquier operación).
- Operador / Cliente: solo pueden ver/editar su propio perfil.
- Roles válidos: Administrador, Operador, Cliente.
"""
import json
import time
import uuid

from common.audit import registrar_auditoria
from common.auth import require_roles
from common.db import table
from common.parsing import parse_body
from common.responses import bad_request, conflict, created, forbidden, not_found, ok
from common.validation import campos_requeridos, es_email_valido

TABLA = "USUARIOS_TABLE"
ROLES_VALIDOS = ("Administrador", "Operador", "Cliente")


@require_roles("Administrador", "Operador", "Cliente")
def crear(event, context):
    """POST /usuarios
    Crea el perfil de aplicación de un usuario ya autenticado en Cognito.
    Un Administrador puede crear el perfil de cualquier rol para cualquier
    user_id; cualquier otro usuario solo puede crear SU PROPIO perfil como Cliente.
    """
    try:
        data = parse_body(event)
    except json.JSONDecodeError:
        return bad_request("Body no es JSON válido")

    faltantes = campos_requeridos(data, ["nombre", "email"])
    if faltantes:
        return bad_request(f"Campos requeridos faltantes: {', '.join(faltantes)}")
    if not es_email_valido(data["email"]):
        return bad_request("Email inválido")

    solicitante = event["_user"]
    rol_solicitado = data.get("rol", "Cliente")
    if rol_solicitado not in ROLES_VALIDOS:
        return bad_request(f"Rol inválido. Debe ser uno de: {', '.join(ROLES_VALIDOS)}")

    es_admin = solicitante["role"] == "Administrador"
    if not es_admin and rol_solicitado != "Cliente":
        return forbidden("Solo un Administrador puede asignar roles distintos a Cliente")

    user_id = data.get("user_id") if es_admin and data.get("user_id") else solicitante["sub"]
    if not es_admin and user_id != solicitante["sub"]:
        return forbidden("No puedes crear el perfil de otro usuario")

    usuarios = table(TABLA)
    if usuarios.get_item(Key={"user_id": user_id}).get("Item"):
        return conflict("El usuario ya existe")

    item = {
        "user_id": user_id,
        "nombre": data["nombre"],
        "email": data["email"],
        "rol": rol_solicitado,
        "estado": "ACTIVO",
        "fecha_creacion": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    usuarios.put_item(Item=item)
    registrar_auditoria(solicitante["username"], "CREAR_USUARIO", detalle={"user_id": user_id, "rol": rol_solicitado})
    return created(item)


@require_roles("Administrador")
def listar(event, context):
    """GET /usuarios — solo Administrador. Soporta paginación simple vía
    querystring `limit` (por defecto 50) para no hacer Scan completos costosos."""
    limit = int((event.get("queryStringParameters") or {}).get("limit", 50))
    usuarios = table(TABLA)
    resultado = usuarios.scan(Limit=limit)
    return ok({"items": resultado.get("Items", []), "count": resultado.get("Count", 0)})


@require_roles("Administrador", "Operador", "Cliente")
def obtener(event, context):
    """GET /usuarios/{id}
    Administrador/Operador pueden consultar a cualquiera; Cliente solo a sí mismo.
    """
    user_id = event["pathParameters"]["id"]
    solicitante = event["_user"]
    if solicitante["role"] == "Cliente" and solicitante["sub"] != user_id:
        return forbidden("No puedes consultar el perfil de otro usuario")

    item = table(TABLA).get_item(Key={"user_id": user_id}).get("Item")
    if not item:
        return not_found("Usuario no encontrado")
    return ok(item)


@require_roles("Administrador", "Operador", "Cliente")
def actualizar(event, context):
    """PATCH /usuarios/{id} — actualización parcial.
    Cliente/Operador solo pueden editar su propio `nombre`.
    Administrador puede editar nombre, email, rol y estado de cualquiera.
    """
    user_id = event["pathParameters"]["id"]
    solicitante = event["_user"]
    es_admin = solicitante["role"] == "Administrador"
    if not es_admin and solicitante["sub"] != user_id:
        return forbidden("No puedes modificar el perfil de otro usuario")

    try:
        data = parse_body(event)
    except json.JSONDecodeError:
        return bad_request("Body no es JSON válido")

    usuarios = table(TABLA)
    if not usuarios.get_item(Key={"user_id": user_id}).get("Item"):
        return not_found("Usuario no encontrado")

    campos_editables = ["nombre"] if not es_admin else ["nombre", "email", "rol", "estado"]
    if "rol" in data and data["rol"] not in ROLES_VALIDOS:
        return bad_request(f"Rol inválido. Debe ser uno de: {', '.join(ROLES_VALIDOS)}")
    if "email" in data and not es_email_valido(data["email"]):
        return bad_request("Email inválido")

    expr_names, expr_values, sets = {}, {}, []
    for campo in campos_editables:
        if campo in data:
            expr_names[f"#{campo}"] = campo
            expr_values[f":{campo}"] = data[campo]
            sets.append(f"#{campo} = :{campo}")

    if not sets:
        return bad_request("No se enviaron campos válidos para actualizar")

    usuarios.update_item(
        Key={"user_id": user_id},
        UpdateExpression="SET " + ", ".join(sets),
        ExpressionAttributeNames=expr_names,
        ExpressionAttributeValues=expr_values,
    )
    registrar_auditoria(solicitante["username"], "ACTUALIZAR_USUARIO", detalle={"user_id": user_id, "campos": list(data.keys())})
    return ok(usuarios.get_item(Key={"user_id": user_id}).get("Item"))


@require_roles("Administrador")
def desactivar(event, context):
    """DELETE /usuarios/{id} — borrado LÓGICO (estado=INACTIVO), preserva histórico
    para auditoría (mismo criterio de Clase 22: borrado físico vs lógico). Solo Administrador."""
    user_id = event["pathParameters"]["id"]
    usuarios = table(TABLA)
    if not usuarios.get_item(Key={"user_id": user_id}).get("Item"):
        return not_found("Usuario no encontrado")

    usuarios.update_item(
        Key={"user_id": user_id},
        UpdateExpression="SET estado = :estado",
        ExpressionAttributeValues={":estado": "INACTIVO"},
    )
    registrar_auditoria(event["_user"]["username"], "DESACTIVAR_USUARIO", detalle={"user_id": user_id})
    return ok({"user_id": user_id, "estado": "INACTIVO"})
