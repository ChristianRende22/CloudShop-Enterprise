# Modulo 1 - Usuarios
resource "aws_dynamodb_table" "usuarios" {
  name         = "${local.name_prefix}-usuarios"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "user_id"

  attribute {
    name = "user_id"
    type = "S"
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = local.common_tags
}

# Seccion 7 - Auditoria (registro de toda accion relevante)
resource "aws_dynamodb_table" "auditoria" {
  name         = "${local.name_prefix}-auditoria"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "id"

  attribute {
    name = "id"
    type = "S"
  }

  tags = local.common_tags
}

# Modulo 2 - Productos
# GSI tienda_id-index: permite "listar productos de una tienda" con Query
# en vez de Scan (Clase 19/22: Query > Scan en costo y rendimiento).
resource "aws_dynamodb_table" "productos" {
  name         = "${local.name_prefix}-productos"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "producto_id"

  attribute {
    name = "producto_id"
    type = "S"
  }

  attribute {
    name = "tienda_id"
    type = "S"
  }

  global_secondary_index {
    name            = "tienda_id-index"
    hash_key        = "tienda_id"
    projection_type = "ALL"
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = local.common_tags
}

# NOTA: las tablas de Tiendas, Carrito y Pedidos se agregan en este mismo
# archivo cuando se implementen esos modulos (ver README para el estado
# actual del proyecto).
