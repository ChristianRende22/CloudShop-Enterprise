"""
Helpers de respuesta HTTP para Lambdas detras de API Gateway (integracion AWS_PROXY).
Centraliza headers CORS y codigos de estado consistentes en todos los modulos.
"""
import decimal
import json


class DecimalEncoder(json.JSONEncoder):
    """DynamoDB devuelve numeros como Decimal; json.dumps no los serializa por defecto."""

    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return int(o) if o % 1 == 0 else float(o)
        return super().default(o)


CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type,Authorization",
    "Access-Control-Allow-Methods": "GET,POST,PUT,PATCH,DELETE,OPTIONS",
}


def _response(status_code, body=None, extra_headers=None):
    headers = {**CORS_HEADERS, "Content-Type": "application/json"}
    if extra_headers:
        headers.update(extra_headers)
    # OJO: no pasar default=str aqui. json.JSONEncoder usa `default` como
    # atributo de instancia y PISA el metodo default() de DecimalEncoder,
    # lo que serializaba los Decimal como strings en vez de numeros.
    return {
        "statusCode": status_code,
        "headers": headers,
        "body": json.dumps(body if body is not None else {}, cls=DecimalEncoder),
    }


def ok(body=None):
    return _response(200, body)


def created(body=None):
    return _response(201, body)


def no_content():
    return _response(204)


def bad_request(message):
    return _response(400, {"error": message})


def unauthorized(message="No autenticado"):
    return _response(401, {"error": message})


def forbidden(message="No autorizado"):
    return _response(403, {"error": message})


def not_found(message="Recurso no encontrado"):
    return _response(404, {"error": message})


def conflict(message="Conflicto"):
    return _response(409, {"error": message})


def server_error(message="Error interno del servidor"):
    return _response(500, {"error": message})
