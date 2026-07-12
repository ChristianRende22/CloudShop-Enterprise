"""
Autenticación y control de acceso basado en roles (RBAC).

API Gateway, con el Cognito Authorizer configurado en Terraform, valida el JWT
ANTES de invocar la Lambda e inyecta los claims del usuario en
event["requestContext"]["authorizer"]["claims"]. Aquí solo leemos esos claims
y aplicamos la regla de negocio: qué rol puede ejecutar qué operación.

Esto es exactamente el patrón de Clase 16 (API Gateway valida antes de que
Lambda gaste cómputo) y Clase 29 (IAM trata igual a personas y funciones).
"""
import functools
import os

from .responses import forbidden, unauthorized

ROLE_CLAIM_KEY = os.environ.get("ROLE_CLAIM_KEY", "custom:role")


def get_claims(event):
    try:
        return event["requestContext"]["authorizer"]["claims"]
    except (KeyError, TypeError):
        return None


def get_current_user(event):
    """Normaliza los claims de Cognito a un dict simple usado en toda la app."""
    claims = get_claims(event)
    if not claims:
        return None
    return {
        "sub": claims.get("sub"),
        "email": claims.get("email"),
        "username": claims.get("cognito:username", claims.get("sub")),
        "role": claims.get(ROLE_CLAIM_KEY, "Cliente"),
    }


def require_roles(*allowed_roles):
    """
    Decorator para handlers Lambda.

    - 401 si no hay token válido (no hay claims).
    - 403 si el rol del usuario no está en allowed_roles.
    - Si pasa, inyecta event["_user"] con el usuario normalizado y ejecuta el handler.

    Uso:
        @require_roles("Administrador")
        def desactivar(event, context):
            ...
    """

    def decorator(handler_fn):
        @functools.wraps(handler_fn)
        def wrapper(event, context):
            user = get_current_user(event)
            if user is None:
                return unauthorized("Token inválido o ausente")
            if allowed_roles and user["role"] not in allowed_roles:
                return forbidden(f"Rol '{user['role']}' no autorizado para esta operación")
            event["_user"] = user
            return handler_fn(event, context)

        return wrapper

    return decorator
