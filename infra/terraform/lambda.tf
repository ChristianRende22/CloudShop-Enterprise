# Empaqueta TODO backend/ (common/ + cada modulo) en un solo zip, asi cada
# Lambda puede hacer `from common.x import y` y `from productos import handler`
# sin duplicar codigo. Terraform re-empaqueta automaticamente cuando cambia
# cualquier archivo fuente (source_code_hash).
data "archive_file" "backend" {
  type        = "zip"
  source_dir  = "${path.module}/../../backend"
  output_path = "${path.module}/build/backend.zip"
  excludes    = ["__pycache__", ".pytest_cache", "test_handler.py", "requirements.txt"]
}

# Un entry por endpoint. Se va ampliando conforme se agregan Tiendas, Carrito,
# Pedidos y Dashboard (mismo patron: una Lambda = una operacion CRUD,
# "funciones enfocadas" de Clase 22).
locals {
  lambda_functions = {
    usuarios_crear = {
      handler = "usuarios.handler.crear"
    }
    usuarios_listar = {
      handler = "usuarios.handler.listar"
    }
    usuarios_obtener = {
      handler = "usuarios.handler.obtener"
    }
    usuarios_actualizar = {
      handler = "usuarios.handler.actualizar"
    }
    usuarios_desactivar = {
      handler = "usuarios.handler.desactivar"
    }
    productos_crear = {
      handler = "productos.handler.crear"
    }
    productos_listar = {
      handler = "productos.handler.listar"
    }
    productos_obtener = {
      handler = "productos.handler.obtener"
    }
    productos_actualizar = {
      handler = "productos.handler.actualizar"
    }
    productos_eliminar = {
      handler = "productos.handler.eliminar"
    }
  }
}

resource "aws_lambda_function" "this" {
  for_each = local.lambda_functions

  function_name    = "${local.name_prefix}-${each.key}"
  role             = aws_iam_role.lambda_exec.arn
  handler          = each.value.handler
  runtime          = "python3.12"
  filename         = data.archive_file.backend.output_path
  source_code_hash = data.archive_file.backend.output_base64sha256
  timeout          = 10
  memory_size      = 128

  environment {
    variables = {
      USUARIOS_TABLE  = aws_dynamodb_table.usuarios.name
      PRODUCTOS_TABLE = aws_dynamodb_table.productos.name
      AUDIT_TABLE     = aws_dynamodb_table.auditoria.name
      EVENT_BUS_NAME  = aws_cloudwatch_event_bus.cloudshop.name
      ROLE_CLAIM_KEY  = "custom:role"
    }
  }

  tags = local.common_tags
}

resource "aws_cloudwatch_log_group" "lambda" {
  for_each = local.lambda_functions

  name              = "/aws/lambda/${local.name_prefix}-${each.key}"
  retention_in_days = 14
  tags              = local.common_tags
}
