"""
Smoke tests del módulo Carrito con moto.
Ejecutar desde backend/: pytest carrito/test_handler.py -v
"""
import json
import os

import boto3
import pytest
from moto import mock_aws

os.environ["CARRITO_TABLE"] = "test-carrito"
os.environ["ROLE_CLAIM_KEY"] = "custom:role"


def _evento(metodo, body=None, path_id=None, rol="Cliente", sub="cliente-1"):
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
            TableName="test-carrito",
            KeySchema=[
                {"AttributeName": "usuario_id", "KeyType": "HASH"},
                {"AttributeName": "producto_id", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "usuario_id", "AttributeType": "S"},
                {"AttributeName": "producto_id", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        yield


def test_agregar_producto_nuevo(dynamodb_local):
    from carrito import handler

    resp = handler.agregar(_evento("POST", {"producto_id": "p1", "cantidad": 2}), None)
    assert resp["statusCode"] == 201
    body = json.loads(resp["body"])
    assert body["cantidad"] == 2


def test_agregar_producto_existente_suma_cantidad(dynamodb_local):
    from carrito import handler

    handler.agregar(_evento("POST", {"producto_id": "p1", "cantidad": 2}), None)
    resp = handler.agregar(_evento("POST", {"producto_id": "p1", "cantidad": 3}), None)
    body = json.loads(resp["body"])
    assert body["cantidad"] == 5


def test_agregar_sin_producto_id_400(dynamodb_local):
    from carrito import handler

    resp = handler.agregar(_evento("POST", {"cantidad": 1}), None)
    assert resp["statusCode"] == 400


def test_agregar_cantidad_invalida_400(dynamodb_local):
    from carrito import handler

    resp = handler.agregar(_evento("POST", {"producto_id": "p1", "cantidad": 0}), None)
    assert resp["statusCode"] == 400


def test_solo_cliente_puede_usar_carrito(dynamodb_local):
    from carrito import handler

    for rol in ("Administrador", "Operador"):
        resp = handler.agregar(_evento("POST", {"producto_id": "p1", "cantidad": 1}, rol=rol), None)
        assert resp["statusCode"] == 403


def test_listar_carrito(dynamodb_local):
    from carrito import handler

    handler.agregar(_evento("POST", {"producto_id": "p1", "cantidad": 2}), None)
    handler.agregar(_evento("POST", {"producto_id": "p2", "cantidad": 3}), None)

    resp = handler.listar(_evento("GET"), None)
    body = json.loads(resp["body"])
    assert body["count"] == 2
    assert body["total_unidades"] == 5


def test_carritos_son_por_usuario(dynamodb_local):
    from carrito import handler

    handler.agregar(_evento("POST", {"producto_id": "p1", "cantidad": 1}, sub="cliente-A"), None)
    handler.agregar(_evento("POST", {"producto_id": "p1", "cantidad": 9}, sub="cliente-B"), None)

    resp_a = handler.listar(_evento("GET", sub="cliente-A"), None)
    resp_b = handler.listar(_evento("GET", sub="cliente-B"), None)
    assert json.loads(resp_a["body"])["items"][0]["cantidad"] == 1
    assert json.loads(resp_b["body"])["items"][0]["cantidad"] == 9


def test_modificar_cantidad(dynamodb_local):
    from carrito import handler

    handler.agregar(_evento("POST", {"producto_id": "p1", "cantidad": 2}), None)
    resp = handler.modificar(_evento("PATCH", {"cantidad": 10}, path_id="p1"), None)
    assert resp["statusCode"] == 200
    assert json.loads(resp["body"])["cantidad"] == 10


def test_modificar_producto_no_existente_404(dynamodb_local):
    from carrito import handler

    resp = handler.modificar(_evento("PATCH", {"cantidad": 5}, path_id="no-existe"), None)
    assert resp["statusCode"] == 404


def test_eliminar_producto_del_carrito(dynamodb_local):
    from carrito import handler

    handler.agregar(_evento("POST", {"producto_id": "p1", "cantidad": 2}), None)
    resp = handler.eliminar(_evento("DELETE", path_id="p1"), None)
    assert resp["statusCode"] == 200

    resp = handler.listar(_evento("GET"), None)
    assert json.loads(resp["body"])["count"] == 0


def test_vaciar_carrito(dynamodb_local):
    from carrito import handler

    handler.agregar(_evento("POST", {"producto_id": "p1", "cantidad": 1}), None)
    handler.agregar(_evento("POST", {"producto_id": "p2", "cantidad": 1}), None)
    handler.agregar(_evento("POST", {"producto_id": "p3", "cantidad": 1}), None)

    resp = handler.vaciar(_evento("DELETE"), None)
    assert json.loads(resp["body"])["eliminados"] == 3

    resp = handler.listar(_evento("GET"), None)
    assert json.loads(resp["body"])["count"] == 0
