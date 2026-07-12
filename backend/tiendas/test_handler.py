"""
Smoke tests del módulo Tiendas con moto.
Ejecutar desde backend/: pytest tiendas/test_handler.py -v
"""
import json
import os

import boto3
import pytest
from moto import mock_aws

os.environ["TIENDAS_TABLE"] = "test-tiendas"
os.environ["AUDIT_TABLE"] = "test-auditoria"
os.environ["ROLE_CLAIM_KEY"] = "custom:role"


def _evento(metodo, body=None, path_id=None, query=None, rol="Administrador", sub="user-1"):
    return {
        "httpMethod": metodo,
        "body": json.dumps(body) if body is not None else None,
        "pathParameters": {"id": path_id} if path_id else None,
        "queryStringParameters": query,
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
            TableName="test-tiendas",
            KeySchema=[{"AttributeName": "tienda_id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "tienda_id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        client.create_table(
            TableName="test-auditoria",
            KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        yield


def test_crear_tienda_admin_ok(dynamodb_local):
    from tiendas import handler

    resp = handler.crear(_evento("POST", {"nombre": "Tienda Central"}, rol="Administrador"), None)
    assert resp["statusCode"] == 201
    body = json.loads(resp["body"])
    assert body["estado"] == "ACTIVA"


def test_crear_tienda_operador_y_cliente_403(dynamodb_local):
    from tiendas import handler

    for rol in ("Operador", "Cliente"):
        resp = handler.crear(_evento("POST", {"nombre": "X"}, rol=rol), None)
        assert resp["statusCode"] == 403


def test_crear_tienda_sin_nombre_400(dynamodb_local):
    from tiendas import handler

    resp = handler.crear(_evento("POST", {}, rol="Administrador"), None)
    assert resp["statusCode"] == 400


def test_listar_y_obtener_cualquier_rol(dynamodb_local):
    from tiendas import handler

    crear_resp = handler.crear(_evento("POST", {"nombre": "Tienda A"}, rol="Administrador"), None)
    tienda_id = json.loads(crear_resp["body"])["tienda_id"]

    for rol in ("Administrador", "Operador", "Cliente"):
        resp = handler.listar(_evento("GET", rol=rol), None)
        assert resp["statusCode"] == 200

        resp = handler.obtener(_evento("GET", path_id=tienda_id, rol=rol), None)
        assert resp["statusCode"] == 200


def test_actualizar_solo_administrador(dynamodb_local):
    from tiendas import handler

    crear_resp = handler.crear(_evento("POST", {"nombre": "Tienda B"}, rol="Administrador"), None)
    tienda_id = json.loads(crear_resp["body"])["tienda_id"]

    resp = handler.actualizar(_evento("PATCH", {"nombre": "Tienda B Renovada"}, path_id=tienda_id, rol="Operador"), None)
    assert resp["statusCode"] == 403

    resp = handler.actualizar(_evento("PATCH", {"nombre": "Tienda B Renovada"}, path_id=tienda_id, rol="Administrador"), None)
    assert resp["statusCode"] == 200
    assert json.loads(resp["body"])["nombre"] == "Tienda B Renovada"


def test_actualizar_estado_invalido_400(dynamodb_local):
    from tiendas import handler

    crear_resp = handler.crear(_evento("POST", {"nombre": "Tienda C"}, rol="Administrador"), None)
    tienda_id = json.loads(crear_resp["body"])["tienda_id"]

    resp = handler.actualizar(_evento("PATCH", {"estado": "BORRADA"}, path_id=tienda_id, rol="Administrador"), None)
    assert resp["statusCode"] == 400


def test_desactivar_borrado_logico_solo_admin(dynamodb_local):
    from tiendas import handler

    crear_resp = handler.crear(_evento("POST", {"nombre": "Tienda D"}, rol="Administrador"), None)
    tienda_id = json.loads(crear_resp["body"])["tienda_id"]

    resp = handler.desactivar(_evento("DELETE", path_id=tienda_id, rol="Cliente"), None)
    assert resp["statusCode"] == 403

    resp = handler.desactivar(_evento("DELETE", path_id=tienda_id, rol="Administrador"), None)
    assert resp["statusCode"] == 200

    verificacion = handler.obtener(_evento("GET", path_id=tienda_id, rol="Administrador"), None)
    assert json.loads(verificacion["body"])["estado"] == "INACTIVA"


def test_obtener_tienda_inexistente_404(dynamodb_local):
    from tiendas import handler

    resp = handler.obtener(_evento("GET", path_id="no-existe", rol="Cliente"), None)
    assert resp["statusCode"] == 404
