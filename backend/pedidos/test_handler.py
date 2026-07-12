"""
Smoke tests del módulo Pedidos con moto.
Ejecutar desde backend/: pytest pedidos/test_handler.py -v
"""
import json
import os

import boto3
import pytest
from moto import mock_aws

os.environ["PEDIDOS_TABLE"] = "test-pedidos"
os.environ["PRODUCTOS_TABLE"] = "test-productos"
os.environ["AUDIT_TABLE"] = "test-auditoria"
os.environ["EVENT_BUS_NAME"] = "test-bus"
os.environ["ROLE_CLAIM_KEY"] = "custom:role"


def _evento(metodo, body=None, path_id=None, query=None, rol="Cliente", sub="cliente-1"):
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
def aws_local():
    with mock_aws():
        ddb = boto3.client("dynamodb", region_name="us-east-1")
        ddb.create_table(
            TableName="test-pedidos",
            KeySchema=[{"AttributeName": "pedido_id", "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": "pedido_id", "AttributeType": "S"},
                {"AttributeName": "cliente_id", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "cliente_id-index",
                    "KeySchema": [{"AttributeName": "cliente_id", "KeyType": "HASH"}],
                    "Projection": {"ProjectionType": "ALL"},
                }
            ],
        )
        ddb.create_table(
            TableName="test-productos",
            KeySchema=[{"AttributeName": "producto_id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "producto_id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        ddb.create_table(
            TableName="test-auditoria",
            KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        events = boto3.client("events", region_name="us-east-1")
        events.create_event_bus(Name="test-bus")

        productos = boto3.resource("dynamodb", region_name="us-east-1").Table("test-productos")
        productos.put_item(Item={
            "producto_id": "p1", "nombre": "Mouse", "tienda_id": "t1",
            "precio": 10, "inventario_disponible": 5,
        })
        productos.put_item(Item={
            "producto_id": "p2", "nombre": "Teclado", "tienda_id": "t1",
            "precio": 20, "inventario_disponible": 2,
        })
        yield


def test_crear_pedido_actualiza_inventario_y_genera_evento(aws_local):
    from pedidos import handler

    resp = handler.crear(_evento("POST", {"items": [{"producto_id": "p1", "cantidad": 2}]}), None)
    assert resp["statusCode"] == 201
    body = json.loads(resp["body"])
    assert body["estado"] == "Pendiente"
    assert body["total"] == 20

    productos = boto3.resource("dynamodb", region_name="us-east-1").Table("test-productos")
    item = productos.get_item(Key={"producto_id": "p1"}).get("Item")
    assert item["inventario_disponible"] == 3  # 5 - 2


def test_crear_pedido_sin_stock_devuelve_409_y_no_toca_otros_productos(aws_local):
    from pedidos import handler

    # p2 solo tiene 2 unidades, pedimos 5 -> debe fallar y NO afectar el stock de p1
    resp = handler.crear(_evento("POST", {"items": [
        {"producto_id": "p1", "cantidad": 1},
        {"producto_id": "p2", "cantidad": 5},
    ]}), None)
    assert resp["statusCode"] == 409

    productos = boto3.resource("dynamodb", region_name="us-east-1").Table("test-productos")
    p1 = productos.get_item(Key={"producto_id": "p1"}).get("Item")
    assert p1["inventario_disponible"] == 5  # se revirtio el descuento (rollback)


def test_solo_cliente_puede_crear_pedido(aws_local):
    from pedidos import handler

    for rol in ("Administrador", "Operador"):
        resp = handler.crear(_evento("POST", {"items": [{"producto_id": "p1", "cantidad": 1}]}, rol=rol), None)
        assert resp["statusCode"] == 403


def test_cliente_solo_ve_sus_propios_pedidos(aws_local):
    from pedidos import handler

    handler.crear(_evento("POST", {"items": [{"producto_id": "p1", "cantidad": 1}]}, sub="cliente-A"), None)
    handler.crear(_evento("POST", {"items": [{"producto_id": "p1", "cantidad": 1}]}, sub="cliente-B"), None)

    resp = handler.listar(_evento("GET", rol="Cliente", sub="cliente-A"), None)
    body = json.loads(resp["body"])
    assert body["count"] == 1
    assert body["items"][0]["cliente_id"] == "cliente-A"

    resp = handler.listar(_evento("GET", rol="Administrador", sub="admin-1"), None)
    assert json.loads(resp["body"])["count"] == 2


def test_cliente_no_puede_ver_pedido_ajeno(aws_local):
    from pedidos import handler

    crear_resp = handler.crear(_evento("POST", {"items": [{"producto_id": "p1", "cantidad": 1}]}, sub="cliente-A"), None)
    pedido_id = json.loads(crear_resp["body"])["pedido_id"]

    resp = handler.obtener(_evento("GET", path_id=pedido_id, rol="Cliente", sub="cliente-B"), None)
    assert resp["statusCode"] == 403


def test_actualizar_estado_avance_secuencial(aws_local):
    from pedidos import handler

    crear_resp = handler.crear(_evento("POST", {"items": [{"producto_id": "p1", "cantidad": 1}]}), None)
    pedido_id = json.loads(crear_resp["body"])["pedido_id"]

    # saltar de Pendiente directo a Enviado -> invalido
    resp = handler.actualizar(_evento("PATCH", {"estado": "Enviado"}, path_id=pedido_id, rol="Operador"), None)
    assert resp["statusCode"] == 400

    resp = handler.actualizar(_evento("PATCH", {"estado": "Confirmado"}, path_id=pedido_id, rol="Operador"), None)
    assert resp["statusCode"] == 200
    assert json.loads(resp["body"])["estado"] == "Confirmado"


def test_cliente_no_puede_actualizar_estado(aws_local):
    from pedidos import handler

    crear_resp = handler.crear(_evento("POST", {"items": [{"producto_id": "p1", "cantidad": 1}]}), None)
    pedido_id = json.loads(crear_resp["body"])["pedido_id"]

    resp = handler.actualizar(_evento("PATCH", {"estado": "Confirmado"}, path_id=pedido_id, rol="Cliente"), None)
    assert resp["statusCode"] == 403


def test_cancelar_devuelve_inventario(aws_local):
    from pedidos import handler

    crear_resp = handler.crear(_evento("POST", {"items": [{"producto_id": "p1", "cantidad": 2}]}), None)
    pedido_id = json.loads(crear_resp["body"])["pedido_id"]

    resp = handler.cancelar(_evento("DELETE", path_id=pedido_id, rol="Cliente"), None)
    assert resp["statusCode"] == 200
    assert json.loads(resp["body"])["estado"] == "Cancelado"

    productos = boto3.resource("dynamodb", region_name="us-east-1").Table("test-productos")
    item = productos.get_item(Key={"producto_id": "p1"}).get("Item")
    assert item["inventario_disponible"] == 5  # se devolvio el stock


def test_no_se_puede_cancelar_pedido_entregado(aws_local):
    from pedidos import handler

    crear_resp = handler.crear(_evento("POST", {"items": [{"producto_id": "p1", "cantidad": 1}]}), None)
    pedido_id = json.loads(crear_resp["body"])["pedido_id"]

    for estado in ("Confirmado", "En preparación", "Enviado", "Entregado"):
        handler.actualizar(_evento("PATCH", {"estado": estado}, path_id=pedido_id, rol="Operador"), None)

    resp = handler.cancelar(_evento("DELETE", path_id=pedido_id, rol="Administrador"), None)
    assert resp["statusCode"] == 409
