"""
Smoke tests del consumer de notificaciones (EventBridge -> SES) con moto.
Ejecutar desde backend/: pytest notificaciones/test_handler.py -v
"""
import os

import boto3
import pytest
from moto import mock_aws

os.environ["SES_SENDER_EMAIL"] = "no-reply@cloudshop.test"


@pytest.fixture
def ses_local():
    with mock_aws():
        ses = boto3.client("ses", region_name="us-east-1")
        ses.verify_email_identity(EmailAddress="no-reply@cloudshop.test")
        yield


def _evento_eventbridge(detail_type, detail):
    return {
        "detail-type": detail_type,
        "source": "cloudshop.pedidos",
        "detail": detail,
    }


def test_envia_correo_en_pedido_creado(ses_local):
    from notificaciones import handler

    evento = _evento_eventbridge("PedidoCreado", {
        "pedido_id": "abc-123",
        "cliente_email": "cliente@test.com",
        "total": "50",
    })
    resp = handler.enviar_notificacion(evento, None)
    assert resp["status"] == "enviado"
    assert resp["destinatario"] == "cliente@test.com"


def test_envia_correo_en_pedido_cancelado(ses_local):
    from notificaciones import handler

    evento = _evento_eventbridge("PedidoCancelado", {
        "pedido_id": "abc-123",
        "cliente_email": "cliente@test.com",
    })
    resp = handler.enviar_notificacion(evento, None)
    assert resp["status"] == "enviado"


def test_ignora_tipos_de_evento_desconocidos(ses_local):
    from notificaciones import handler

    evento = _evento_eventbridge("AlgoQueNoNosImporta", {"pedido_id": "x"})
    resp = handler.enviar_notificacion(evento, None)
    assert resp["status"] == "ignorado"


def test_sin_email_destinatario_no_falla(ses_local):
    from notificaciones import handler

    evento = _evento_eventbridge("PedidoCreado", {"pedido_id": "x", "total": "10"})
    resp = handler.enviar_notificacion(evento, None)
    assert resp["status"] == "error"
