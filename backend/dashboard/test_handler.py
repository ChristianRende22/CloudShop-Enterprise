"""
Smoke tests del módulo Dashboard con moto.
Siembra datos directamente en las tablas (no pasa por pedidos.handler) para
mantener el test enfocado solo en la lógica de agregación.
Ejecutar desde backend/: pytest dashboard/test_handler.py -v
"""
import json
import os
from decimal import Decimal

import boto3
import pytest
from moto import mock_aws

os.environ["PEDIDOS_TABLE"] = "test-pedidos"
os.environ["PRODUCTOS_TABLE"] = "test-productos"
os.environ["ROLE_CLAIM_KEY"] = "custom:role"


def _evento(rol="Administrador", sub="admin-1"):
    return {
        "httpMethod": "GET",
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
            AttributeDefinitions=[{"AttributeName": "pedido_id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        ddb.create_table(
            TableName="test-productos",
            KeySchema=[{"AttributeName": "producto_id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "producto_id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )

        pedidos = boto3.resource("dynamodb", region_name="us-east-1").Table("test-pedidos")
        productos = boto3.resource("dynamodb", region_name="us-east-1").Table("test-productos")

        productos.put_item(Item={"producto_id": "p1", "nombre": "Mouse", "inventario_disponible": 0})
        productos.put_item(Item={"producto_id": "p2", "nombre": "Teclado", "inventario_disponible": 10})

        pedidos.put_item(Item={
            "pedido_id": "ped-1", "cliente_id": "cli-A", "cliente_email": "ana@correo.com",
            "estado": "Entregado", "total": Decimal("100"),
            "items": [{"producto_id": "p1", "nombre": "Mouse", "tienda_id": "t1", "cantidad": 2, "subtotal": Decimal("40")},
                      {"producto_id": "p2", "nombre": "Teclado", "tienda_id": "t1", "cantidad": 1, "subtotal": Decimal("60")}],
        })
        pedidos.put_item(Item={
            "pedido_id": "ped-2", "cliente_id": "cli-A", "cliente_email": "ana@correo.com",
            "estado": "Pendiente", "total": Decimal("40"),
            "items": [{"producto_id": "p1", "nombre": "Mouse", "tienda_id": "t1", "cantidad": 1, "subtotal": Decimal("40")}],
        })
        pedidos.put_item(Item={
            "pedido_id": "ped-3", "cliente_id": "cli-B", "cliente_email": "beto@correo.com",
            "estado": "Cancelado", "total": Decimal("500"),
            "items": [{"producto_id": "p2", "nombre": "Teclado", "tienda_id": "t2", "cantidad": 5, "subtotal": Decimal("500")}],
        })
        yield


def test_solo_administrador_ve_dashboard(aws_local):
    from dashboard import handler

    for rol in ("Operador", "Cliente"):
        resp = handler.resumen(_evento(rol=rol), None)
        assert resp["statusCode"] == 403

    resp = handler.resumen(_evento(rol="Administrador"), None)
    assert resp["statusCode"] == 200


def test_total_ventas_excluye_cancelados(aws_local):
    from dashboard import handler

    body = json.loads(handler.resumen(_evento(), None)["body"])
    # ped-1 (100) + ped-2 (40) = 140; ped-3 esta Cancelado, no cuenta
    assert body["total_ventas"] == 140


def test_pedidos_por_estado_incluye_cancelados(aws_local):
    from dashboard import handler

    body = json.loads(handler.resumen(_evento(), None)["body"])
    assert body["pedidos_por_estado"]["Cancelado"] == 1
    assert body["pedidos_por_estado"]["Entregado"] == 1
    assert body["pedidos_por_estado"]["Pendiente"] == 1


def test_productos_agotados(aws_local):
    from dashboard import handler

    body = json.loads(handler.resumen(_evento(), None)["body"])
    ids_agotados = [p["producto_id"] for p in body["productos_agotados"]]
    assert ids_agotados == ["p1"]


def test_productos_mas_vendidos_excluye_cancelados(aws_local):
    from dashboard import handler

    body = json.loads(handler.resumen(_evento(), None)["body"])
    por_id = {p["producto_id"]: p["unidades_vendidas"] for p in body["productos_mas_vendidos"]}
    # p1: 2 (ped-1) + 1 (ped-2) = 3.  p2: solo cuenta ped-1 (1), NO ped-3 (cancelado)
    assert por_id["p1"] == 3
    assert por_id["p2"] == 1


def test_clientes_top(aws_local):
    from dashboard import handler

    body = json.loads(handler.resumen(_evento(), None)["body"])
    assert body["clientes_top"][0]["cliente_id"] == "cli-A"
    assert body["clientes_top"][0]["cliente_email"] == "ana@correo.com"
    assert body["clientes_top"][0]["total_comprado"] == 140


def test_ventas_por_tienda(aws_local):
    from dashboard import handler

    body = json.loads(handler.resumen(_evento(), None)["body"])
    por_tienda = {v["tienda_id"]: v["total"] for v in body["ventas_por_tienda"]}
    assert por_tienda["t1"] == 140  # 40+60 (ped-1) + 40 (ped-2)
    assert "t2" not in por_tienda  # esa venta esta en el pedido cancelado
