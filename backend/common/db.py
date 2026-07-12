"""Acceso centralizado a DynamoDB. El nombre real de cada tabla llega por variable
de entorno de la Lambda (definida en Terraform), nunca hardcodeado en el código."""
import boto3

_dynamodb = boto3.resource("dynamodb")


def table(env_var_name):
    """
    Obtiene el recurso Table de DynamoDB a partir del nombre de una variable
    de entorno.

    Ejemplo: table("USUARIOS_TABLE")
    """
    import os

    table_name = os.environ[env_var_name]
    return _dynamodb.Table(table_name)
