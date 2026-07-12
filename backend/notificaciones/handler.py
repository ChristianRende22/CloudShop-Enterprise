"""
Consumer de eventos -> SES.

No es un endpoint HTTP: esta Lambda se dispara por una regla de EventBridge
(ver infra/terraform/eventbridge.tf) cuando pedidos/handler.py publica
"PedidoCreado" o "PedidoCancelado". Así el envío de correo queda totalmente
desacoplado de la creación del pedido (si SES tarda o falla, no bloquea ni
retrasa la respuesta al cliente) — arquitectura basada en eventos, sección 6
del enunciado.

El event recibido aquí es el evento de EventBridge completo, con el payload
original de publicar_evento() en event["detail"].
"""
import json
import logging
import os

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

_ses = boto3.client("ses")
REMITENTE = os.environ.get("SES_SENDER_EMAIL", "")

PLANTILLAS = {
    "PedidoCreado": {
        "asunto": "Confirmamos tu pedido en CloudShop",
        "cuerpo": "Tu pedido {pedido_id} fue recibido correctamente. Total: ${total}. Te avisaremos cuando cambie de estado.",
    },
    "PedidoCancelado": {
        "asunto": "Tu pedido en CloudShop fue cancelado",
        "cuerpo": "Tu pedido {pedido_id} fue cancelado. Si no reconoces esta acción, contacta a soporte.",
    },
}


def enviar_notificacion(event, context):
    detail_type = event.get("detail-type")
    detail = event.get("detail", {})
    plantilla = PLANTILLAS.get(detail_type)

    if not plantilla:
        logger.warning(json.dumps({"tipo": "NOTIFICACION_IGNORADA", "detail_type": detail_type}))
        return {"status": "ignorado", "detail_type": detail_type}

    destinatario = detail.get("cliente_email")
    if not destinatario or not REMITENTE:
        logger.error(json.dumps({"tipo": "NOTIFICACION_SIN_DESTINATARIO", "detail": detail}))
        return {"status": "error", "razon": "falta destinatario o remitente configurado"}

    cuerpo = plantilla["cuerpo"].format(
        pedido_id=detail.get("pedido_id", ""),
        total=detail.get("total", ""),
    )

    try:
        _ses.send_email(
            Source=REMITENTE,
            Destination={"ToAddresses": [destinatario]},
            Message={
                "Subject": {"Data": plantilla["asunto"]},
                "Body": {"Text": {"Data": cuerpo}},
            },
        )
        logger.info(json.dumps({"tipo": "CORREO_ENVIADO", "destinatario": destinatario, "detail_type": detail_type}))
        return {"status": "enviado", "destinatario": destinatario}
    except Exception as e:
        # No relanzamos: un fallo de SES no debe generar reintentos infinitos
        # de EventBridge ni afectar al pedido, que ya se creo correctamente.
        logger.error(json.dumps({"tipo": "CORREO_ERROR", "error": str(e), "destinatario": destinatario}))
        return {"status": "error", "razon": str(e)}
