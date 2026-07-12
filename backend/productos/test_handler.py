"""
Smoke tests del módulo Productos con moto.
Ejecutar desde backend/: pytest productos/test_handler.py -v
"""
import json
import os

import boto3
import pytest
from moto import mock_aws

os.environ["PRODUCTOS_TABLE"] = "test-productos"
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


PRODUCTO_VALIDO = {
    "codigo": "SKU-001",
    "nombre": "Mouse inalámbrico",
    "descripcion": "Mouse óptico 2.4GHz",
    "categoria": "Periféricos",
    "precio": 19.99,
    "inventario_disponible": 100,
    "tienda_id": "tienda-01",
}


@pytest.fixture
def dynamodb_local():
    with mock_aws():
        client = boto3.client("dynamodb", region_name="us-east-1")
        client.create_table(
            TableName="test-productos",
            KeySchema=[{"AttributeName": "producto_id", "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": "producto_id", "AttributeType": "S"},
                {"AttributeName": "tienda_id", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "tienda_id-index",
                    "KeySchema": [{"AttributeName": "tienda_id", "KeyType": "HASH"}],
                    "Projection": {"ProjectionType": "ALL"},
                }
            ],
        )
        client.create_table(
            TableName="test-auditoria",
            KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        yield


def test_crear_producto_admin_ok(dynamodb_local):
    from productos import handler

    resp = handler.crear(_evento("POST", PRODUCTO_VALIDO, rol="Administrador"), None)
    assert resp["statusCode"] == 201
    body = json.loads(resp["body"])
    assert body["codigo"] == "SKU-001"


def test_crear_producto_cliente_403(dynamodb_local):
    from productos import handler

    resp = handler.crear(_evento("POST", PRODUCTO_VALIDO, rol="Cliente"), None)
    assert resp["statusCode"] == 403


def test_crear_producto_operador_403(dynamodb_local):
    from productos import handler

    resp = handler.crear(_evento("POST", PRODUCTO_VALIDO, rol="Operador"), None)
    assert resp["statusCode"] == 403


def test_crear_producto_precio_invalido_400(dynamodb_local):
    from productos import handler

    data = dict(PRODUCTO_VALIDO, precio=-5)
    resp = handler.crear(_evento("POST", data, rol="Administrador"), None)
    assert resp["statusCode"] == 400


def test_listar_y_obtener_cualquier_rol(dynamodb_local):
    from productos import handler

    crear_resp = handler.crear(_evento("POST", PRODUCTO_VALIDO, rol="Administrador"), None)
    producto_id = json.loads(crear_resp["body"])["producto_id"]

    resp = handler.listar(_evento("GET", rol="Cliente"), None)
    assert resp["statusCode"] == 200
    assert json.loads(resp["body"])["count"] == 1

    resp = handler.obtener(_evento("GET", path_id=producto_id, rol="Cliente"), None)
    assert resp["statusCode"] == 200


def test_listar_por_tienda_usa_gsi(dynamodb_local):
    from productos import handler

    handler.crear(_evento("POST", PRODUCTO_VALIDO, rol="Administrador"), None)
    otro = dict(PRODUCTO_VALIDO, codigo="SKU-002", tienda_id="tienda-02")
    handler.crear(_evento("POST", otro, rol="Administrador"), None)

    resp = handler.listar(_evento("GET", query={"tienda_id": "tienda-01"}, rol="Cliente"), None)
    body = json.loads(resp["body"])
    assert body["count"] == 1
    assert body["items"][0]["tienda_id"] == "tienda-01"


def test_operador_solo_puede_editar_inventario(dynamodb_local):
    from productos import handler

    crear_resp = handler.crear(_evento("POST", PRODUCTO_VALIDO, rol="Administrador"), None)
    producto_id = json.loads(crear_resp["body"])["producto_id"]

    # Operador intenta cambiar precio -> rechazado
    resp = handler.actualizar(_evento("PATCH", {"precio": 999}, path_id=producto_id, rol="Operador"), None)
    assert resp["statusCode"] == 403

    # Operador cambia inventario -> permitido
    resp = handler.actualizar(_evento("PATCH", {"inventario_disponible": 5}, path_id=producto_id, rol="Operador"), None)
    assert resp["statusCode"] == 200
    assert json.loads(resp["body"])["inventario_disponible"] == 5


def test_cliente_no_puede_actualizar(dynamodb_local):
    from productos import handler

    crear_resp = handler.crear(_evento("POST", PRODUCTO_VALIDO, rol="Administrador"), None)
    producto_id = json.loads(crear_resp["body"])["producto_id"]

    resp = handler.actualizar(_evento("PATCH", {"inventario_disponible": 1}, path_id=producto_id, rol="Cliente"), None)
    assert resp["statusCode"] == 403


def test_eliminar_solo_administrador(dynamodb_local):
    from productos import handler

    crear_resp = handler.crear(_evento("POST", PRODUCTO_VALIDO, rol="Administrador"), None)
    producto_id = json.loads(crear_resp["body"])["producto_id"]

    resp = handler.eliminar(_evento("DELETE", path_id=producto_id, rol="Operador"), None)
    assert resp["statusCode"] == 403

    resp = handler.eliminar(_evento("DELETE", path_id=producto_id, rol="Administrador"), None)
    assert resp["statusCode"] == 200

    resp = handler.obtener(_evento("GET", path_id=producto_id, rol="Administrador"), None)
    assert resp["statusCode"] == 404
