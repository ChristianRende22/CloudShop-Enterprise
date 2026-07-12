# User Pool propio de CloudShop Enterprise (antes el proyecto asumia uno
# externo via variable). Trae el atributo custom "role" (Administrador |
# Operador | Cliente) que exigen todos los Lambdas via common.auth.require_roles
# (Clase 16 / 28: el authorizer de API Gateway valida el JWT, pero el rol
# se re-valida siempre server-side, nunca se confia solo en el frontend).
resource "aws_cognito_user_pool" "cloudshop" {
  name = "${local.name_prefix}-users"

  # El username es el email; Cognito lo verifica por correo antes de dejar
  # loguearse (auto_verified_attributes).
  username_attributes     = ["email"]
  auto_verified_attributes = ["email"]

  password_policy {
    minimum_length    = 8
    require_lowercase = true
    require_uppercase = true
    require_numbers   = true
    require_symbols   = false
  }

  schema {
    name                = "email"
    attribute_data_type = "String"
    mutable             = true
    required            = true
  }

  schema {
    name                = "role"
    attribute_data_type = "String"
    mutable             = true
    required            = false
    string_attribute_constraints {
      min_length = 1
      max_length = 20
    }
  }

  admin_create_user_config {
    allow_admin_create_user_only = false
  }

  tags = local.common_tags
}

# App Client SIN secret (obligatorio para usarlo desde el navegador con
# amazon-cognito-identity-js). ALLOW_USER_SRP_AUTH es el flujo que usa
# authenticateUser() por defecto en esa libreria (visto ya en CloudBox:
# sin este flag tira "USER_SRP_AUTH is not enabled for the client").
resource "aws_cognito_user_pool_client" "frontend" {
  name         = "${local.name_prefix}-frontend"
  user_pool_id = aws_cognito_user_pool.cloudshop.id

  generate_secret = false

  explicit_auth_flows = [
    "ALLOW_USER_SRP_AUTH",
    "ALLOW_USER_PASSWORD_AUTH",
    "ALLOW_REFRESH_TOKEN_AUTH",
  ]

  access_token_validity  = 60
  id_token_validity      = 60
  refresh_token_validity = 30

  token_validity_units {
    access_token  = "minutes"
    id_token      = "minutes"
    refresh_token = "days"
  }

  read_attributes  = ["email", "custom:role"]
  write_attributes = ["email", "custom:role"]
}
