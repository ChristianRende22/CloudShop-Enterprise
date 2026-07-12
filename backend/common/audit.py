"""
Auditoría (sección 7 del proyecto): toda acción relevante se registra con
usuario, acción, fecha y resultado — igual al formato de ejemplo del enunciado:

{
  "usuario": "admin01",
  "accion": "ELIMINAR_PRODUCTO",
  "fecha": "2026-07-25",
  "resultado": "EXITOSO"
}

Se registra en dos lugares:
1. CloudWatch Logs (logger.info con JSON estructurado) -> visible de inmediato,
   barato, y es lo que se usa para las métricas/alarmas de Clase 29.
2. Tabla DynamoDB de auditoría -> permite consultar el historial desde el
   Dashboard Ejecutivo o un panel de auditoría sin tener que hacer Insights sobre logs.
"""
import json
import logging
import time
import uuid

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

_dynamodb = boto3.resource("dynamodb")


def registrar_auditoria(usuario, accion, resultado="EXITOSO", detalle=None):
    import os

    audit_table_name = os.environ.get("AUDIT_TABLE")

    registro = {
        "id": str(uuid.uuid4()),
        "usuario": usuario or "anonimo",
        "accion": accion,
        "fecha": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "resultado": resultado,
        "detalle": detalle or {},
    }

    logger.info(json.dumps({"tipo": "AUDITORIA", **registro}, default=str))

    if not audit_table_name:
        return registro

    try:
        _dynamodb.Table(audit_table_name).put_item(Item=registro)
    except Exception as e:  # nunca tumbar la operación principal por un fallo de auditoría
        logger.error(json.dumps({"tipo": "AUDITORIA_ERROR", "error": str(e), "registro": registro}, default=str))

    return registro
