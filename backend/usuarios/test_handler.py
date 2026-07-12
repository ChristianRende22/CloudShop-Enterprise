"""
Smoke tests del módulo Usuarios usando moto (mock de AWS en memoria).
Corre localmente sin desplegar nada: valida las reglas de negocio antes de
gastar tiempo en `terraform apply`.

Ejecutar desde backend/:
    pytest usuarios/test_handler.py -v
"""
import json
import os

import boto3
import pytest
from moto import mock_aws

os.environ["USUARIOS_TABLE"] = "test-usuarios"
os.environ["AUDIT_TABLE"] = "test-auditoria"
os.environ["ROLE_CLAIM_KEY"] = "custom:role"


def _evento(metodo, body=None, path_id=None, rol="Administrador", sub="user-1"):
    return {
        "httpMethod": metodo,
        "body": json.dumps(body) if body is not None else None,
        "pathParameters": {"id": path_id} if path_id else None,
        "queryStringParameters": None,
        "requestContext": {
            "authorizer": {
                "claims": {
                    "sub": sub,
                    "email": f"{sub}@test.com",
                    "cognito:username": sub,
                    "custom:role": rol,
                }
            }
        },
    }


@pytest.fixture
def dynamodb_local():
    with mock_aws():
        client = boto3.client("dynamodb", region_name="us-east-1")
        client.create_table(
            TableName="test-usuarios",
            KeySchema=[{"AttributeName": "user_id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "user_id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        client.create_table(
            TableName="test-auditoria",
            KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        yield


def test_crear_usuario_admin_ok(dynamodb_local):
    from usuarios import handler

    evento = _evento("POST", {"nombre": "Ana Admin", "email": "ana@test.com", "user_id": "admin-01"}, rol="Administrador", sub="admin-01")
    resp = handler.crear(evento, None)
    assert resp["statusCode"] == 201
    body = json.loads(resp["body"])
    assert body["estado"] == "ACTIVO"
    assert body["rol"] == "Cliente"  # default cuando no se especifica


def test_crear_usuario_cliente_no_puede_asignarse_admin(dynamodb_local):
    from usuarios import handler

    evento = _evento("POST", {"nombre": "Juan", "email": "juan@test.com", "rol": "Administrador"}, rol="Cliente", sub="cliente-01")
    resp = handler.crear(evento, None)
    assert resp["statusCode"] == 403


def test_crear_usuario_duplicado_devuelve_409(dynamodb_local):
    from usuarios import handler

    evento = _evento("POST", {"nombre": "Ana", "email": "ana@test.com"}, rol="Cliente", sub="cliente-02")
    handler.crear(evento, None)
    resp = handler.crear(evento, None)
    assert resp["statusCode"] == 409


def test_listar_solo_administrador(dynamodb_local):
    from usuarios import handler

    evento_cliente = _evento("GET", rol="Cliente", sub="cliente-03")
    resp = handler.listar(evento_cliente, None)
    assert resp["statusCode"] == 403

    evento_admin = _evento("GET", rol="Administrador", sub="admin-02")
    resp = handler.listar(evento_admin, None)
    assert resp["statusCode"] == 200


def test_cliente_no_puede_ver_perfil_ajeno(dynamodb_local):
    from usuarios import handler

    handler.crear(_evento("POST", {"nombre": "Owner", "email": "owner@test.com"}, rol="Cliente", sub="owner-01"), None)

    evento_otro = _evento("GET", path_id="owner-01", rol="Cliente", sub="otro-01")
    resp = handler.obtener(evento_otro, None)
    assert resp["statusCode"] == 403

    evento_propio = _evento("GET", path_id="owner-01", rol="Cliente", sub="owner-01")
    resp = handler.obtener(evento_propio, None)
    assert resp["statusCode"] == 200


def test_actualizar_usuario_inexistente_404(dynamodb_local):
    from usuarios import handler

    evento = _evento("PATCH", {"nombre": "X"}, path_id="no-existe", rol="Administrador", sub="admin-03")
    resp = handler.actualizar(evento, None)
    assert resp["statusCode"] == 404


def test_desactivar_usuario_borrado_logico(dynamodb_local):
    from usuarios import handler

    handler.crear(_evento("POST", {"nombre": "Baja", "email": "baja@test.com"}, rol="Cliente", sub="baja-01"), None)

    evento = _evento("DELETE", path_id="baja-01", rol="Administrador", sub="admin-04")
    resp = handler.desactivar(evento, None)
    assert resp["statusCode"] == 200

    verificacion = _evento("GET", path_id="baja-01", rol="Administrador", sub="admin-04")
    item = json.loads(handler.obtener(verificacion, None)["body"])
    assert item["estado"] == "INACTIVO"  # el registro sigue existiendo (borrado lógico)


def test_sin_token_devuelve_401(dynamodb_local):
    from usuarios import handler

    evento = _evento("GET", path_id="cualquiera", rol="Cliente", sub="x")
    evento["requestContext"]["authorizer"] = {}  # simula ausencia de claims
    resp = handler.obtener(evento, None)
    assert resp["statusCode"] == 401
