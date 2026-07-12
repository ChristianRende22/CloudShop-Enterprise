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

# Modulo 3 - Tiendas
resource "aws_dynamodb_table" "tiendas" {
  name         = "${local.name_prefix}-tiendas"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "tienda_id"

  attribute {
    name = "tienda_id"
    type = "S"
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = local.common_tags
}

# Modulo 4 - Carrito de Compras
# PK usuario_id + SK producto_id: cada producto en el carrito es un item
# independiente (permite upsert de cantidad, borrado individual y vaciado
# via Query + BatchWrite sin tocar los demas items de otros usuarios).
resource "aws_dynamodb_table" "carrito" {
  name         = "${local.name_prefix}-carrito"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "usuario_id"
  range_key    = "producto_id"

  attribute {
    name = "usuario_id"
    type = "S"
  }

  attribute {
    name = "producto_id"
    type = "S"
  }

  tags = local.common_tags
}

# Modulo 5 - Pedidos
# GSI cliente_id-index: permite "Cliente ve solo sus pedidos" y "clientes con
# mas compras" (Dashboard) con Query en vez de Scan.
resource "aws_dynamodb_table" "pedidos" {
  name         = "${local.name_prefix}-pedidos"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "pedido_id"

  attribute {
    name = "pedido_id"
    type = "S"
  }

  attribute {
    name = "cliente_id"
    type = "S"
  }

  global_secondary_index {
    name            = "cliente_id-index"
    hash_key        = "cliente_id"
    projection_type = "ALL"
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = local.common_tags
}
