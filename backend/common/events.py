"""
Publicación de eventos en EventBridge (sección 6 — Arquitectura Basada en Eventos).

Usado principalmente por el módulo de Pedidos: al crear un pedido se publica un
evento "PedidoCreado" que dispara, de forma desacoplada, la actualización de
métricas, el envío de correo por SES (consumer aparte) y cualquier otra
integración futura sin acoplar el Lambda de pedidos a esa lógica.
"""
import json
import logging
import os

import boto3

logger = logging.getLogger()
_eventbridge = boto3.client("events")

EVENT_SOURCE = "cloudshop.pedidos"


def publicar_evento(detail_type, detail: dict):
    event_bus_name = os.environ.get("EVENT_BUS_NAME", "default")
    try:
        response = _eventbridge.put_events(
            Entries=[
                {
                    "Source": EVENT_SOURCE,
                    "DetailType": detail_type,
                    "Detail": json.dumps(detail, default=str),
                    "EventBusName": event_bus_name,
                }
            ]
        )
        if response.get("FailedEntryCount", 0) > 0:
            logger.error(json.dumps({"tipo": "EVENTBRIDGE_FALLO", "response": response}, default=str))
        return response
    except Exception as e:
        logger.error(json.dumps({"tipo": "EVENTBRIDGE_ERROR", "error": str(e)}, default=str))
        return None
