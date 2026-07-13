resource "aws_api_gateway_rest_api" "cloudshop" {
  name = "${local.name_prefix}-api"

  endpoint_configuration {
    types = ["REGIONAL"]
  }

  tags = local.common_tags
}

# Autoriza cada request validando el JWT de Cognito ANTES de invocar Lambda
# (Clase 16: ahorra computo y protege el backend desde el borde).
resource "aws_api_gateway_authorizer" "cognito" {
  name            = "${local.name_prefix}-cognito-authorizer"
  rest_api_id     = aws_api_gateway_rest_api.cloudshop.id
  type            = "COGNITO_USER_POOLS"
  provider_arns   = [aws_cognito_user_pool.cloudshop.arn]
  identity_source = "method.request.header.Authorization"
}

# --- Recursos /usuarios y /usuarios/{id} ---

resource "aws_api_gateway_resource" "usuarios" {
  rest_api_id = aws_api_gateway_rest_api.cloudshop.id
  parent_id   = aws_api_gateway_rest_api.cloudshop.root_resource_id
  path_part   = "usuarios"
}

resource "aws_api_gateway_resource" "usuarios_id" {
  rest_api_id = aws_api_gateway_rest_api.cloudshop.id
  parent_id   = aws_api_gateway_resource.usuarios.id
  path_part   = "{id}"
}

module "usuarios_post" {
  source                = "./modules/api_method"
  rest_api_id            = aws_api_gateway_rest_api.cloudshop.id
  resource_id            = aws_api_gateway_resource.usuarios.id
  http_method            = "POST"
  authorizer_id          = aws_api_gateway_authorizer.cognito.id
  lambda_invoke_arn      = aws_lambda_function.this["usuarios_crear"].invoke_arn
  lambda_function_name   = aws_lambda_function.this["usuarios_crear"].function_name
  api_execution_arn      = aws_api_gateway_rest_api.cloudshop.execution_arn
}

module "usuarios_get_all" {
  source                = "./modules/api_method"
  rest_api_id            = aws_api_gateway_rest_api.cloudshop.id
  resource_id            = aws_api_gateway_resource.usuarios.id
  http_method            = "GET"
  authorizer_id          = aws_api_gateway_authorizer.cognito.id
  lambda_invoke_arn      = aws_lambda_function.this["usuarios_listar"].invoke_arn
  lambda_function_name   = aws_lambda_function.this["usuarios_listar"].function_name
  api_execution_arn      = aws_api_gateway_rest_api.cloudshop.execution_arn
}

module "usuarios_get_one" {
  source              = "./modules/api_method"
  rest_api_id          = aws_api_gateway_rest_api.cloudshop.id
  resource_id          = aws_api_gateway_resource.usuarios_id.id
  http_method          = "GET"
  authorizer_id        = aws_api_gateway_authorizer.cognito.id
  lambda_invoke_arn    = aws_lambda_function.this["usuarios_obtener"].invoke_arn
  lambda_function_name = aws_lambda_function.this["usuarios_obtener"].function_name
  api_execution_arn    = aws_api_gateway_rest_api.cloudshop.execution_arn
  request_parameters   = { "method.request.path.id" = true }
}

module "usuarios_patch" {
  source              = "./modules/api_method"
  rest_api_id          = aws_api_gateway_rest_api.cloudshop.id
  resource_id          = aws_api_gateway_resource.usuarios_id.id
  http_method          = "PATCH"
  authorizer_id        = aws_api_gateway_authorizer.cognito.id
  lambda_invoke_arn    = aws_lambda_function.this["usuarios_actualizar"].invoke_arn
  lambda_function_name = aws_lambda_function.this["usuarios_actualizar"].function_name
  api_execution_arn    = aws_api_gateway_rest_api.cloudshop.execution_arn
  request_parameters   = { "method.request.path.id" = true }
}

module "usuarios_delete" {
  source              = "./modules/api_method"
  rest_api_id          = aws_api_gateway_rest_api.cloudshop.id
  resource_id          = aws_api_gateway_resource.usuarios_id.id
  http_method          = "DELETE"
  authorizer_id        = aws_api_gateway_authorizer.cognito.id
  lambda_invoke_arn    = aws_lambda_function.this["usuarios_desactivar"].invoke_arn
  lambda_function_name = aws_lambda_function.this["usuarios_desactivar"].function_name
  api_execution_arn    = aws_api_gateway_rest_api.cloudshop.execution_arn
  request_parameters   = { "method.request.path.id" = true }
}

module "usuarios_cors" {
  source      = "./modules/cors_options"
  rest_api_id = aws_api_gateway_rest_api.cloudshop.id
  resource_id = aws_api_gateway_resource.usuarios.id
}

module "usuarios_id_cors" {
  source      = "./modules/cors_options"
  rest_api_id = aws_api_gateway_rest_api.cloudshop.id
  resource_id = aws_api_gateway_resource.usuarios_id.id
}

# --- Recursos /productos y /productos/{id} ---

resource "aws_api_gateway_resource" "productos" {
  rest_api_id = aws_api_gateway_rest_api.cloudshop.id
  parent_id   = aws_api_gateway_rest_api.cloudshop.root_resource_id
  path_part   = "productos"
}

resource "aws_api_gateway_resource" "productos_id" {
  rest_api_id = aws_api_gateway_rest_api.cloudshop.id
  parent_id   = aws_api_gateway_resource.productos.id
  path_part   = "{id}"
}

module "productos_post" {
  source                = "./modules/api_method"
  rest_api_id            = aws_api_gateway_rest_api.cloudshop.id
  resource_id            = aws_api_gateway_resource.productos.id
  http_method            = "POST"
  authorizer_id          = aws_api_gateway_authorizer.cognito.id
  lambda_invoke_arn      = aws_lambda_function.this["productos_crear"].invoke_arn
  lambda_function_name   = aws_lambda_function.this["productos_crear"].function_name
  api_execution_arn      = aws_api_gateway_rest_api.cloudshop.execution_arn
}

module "productos_get_all" {
  source                = "./modules/api_method"
  rest_api_id            = aws_api_gateway_rest_api.cloudshop.id
  resource_id            = aws_api_gateway_resource.productos.id
  http_method            = "GET"
  authorizer_id          = aws_api_gateway_authorizer.cognito.id
  lambda_invoke_arn      = aws_lambda_function.this["productos_listar"].invoke_arn
  lambda_function_name   = aws_lambda_function.this["productos_listar"].function_name
  api_execution_arn      = aws_api_gateway_rest_api.cloudshop.execution_arn
}

module "productos_get_one" {
  source              = "./modules/api_method"
  rest_api_id          = aws_api_gateway_rest_api.cloudshop.id
  resource_id          = aws_api_gateway_resource.productos_id.id
  http_method          = "GET"
  authorizer_id        = aws_api_gateway_authorizer.cognito.id
  lambda_invoke_arn    = aws_lambda_function.this["productos_obtener"].invoke_arn
  lambda_function_name = aws_lambda_function.this["productos_obtener"].function_name
  api_execution_arn    = aws_api_gateway_rest_api.cloudshop.execution_arn
  request_parameters   = { "method.request.path.id" = true }
}

module "productos_patch" {
  source              = "./modules/api_method"
  rest_api_id          = aws_api_gateway_rest_api.cloudshop.id
  resource_id          = aws_api_gateway_resource.productos_id.id
  http_method          = "PATCH"
  authorizer_id        = aws_api_gateway_authorizer.cognito.id
  lambda_invoke_arn    = aws_lambda_function.this["productos_actualizar"].invoke_arn
  lambda_function_name = aws_lambda_function.this["productos_actualizar"].function_name
  api_execution_arn    = aws_api_gateway_rest_api.cloudshop.execution_arn
  request_parameters   = { "method.request.path.id" = true }
}

module "productos_delete" {
  source              = "./modules/api_method"
  rest_api_id          = aws_api_gateway_rest_api.cloudshop.id
  resource_id          = aws_api_gateway_resource.productos_id.id
  http_method          = "DELETE"
  authorizer_id        = aws_api_gateway_authorizer.cognito.id
  lambda_invoke_arn    = aws_lambda_function.this["productos_eliminar"].invoke_arn
  lambda_function_name = aws_lambda_function.this["productos_eliminar"].function_name
  api_execution_arn    = aws_api_gateway_rest_api.cloudshop.execution_arn
  request_parameters   = { "method.request.path.id" = true }
}

module "productos_cors" {
  source      = "./modules/cors_options"
  rest_api_id = aws_api_gateway_rest_api.cloudshop.id
  resource_id = aws_api_gateway_resource.productos.id
}

module "productos_id_cors" {
  source      = "./modules/cors_options"
  rest_api_id = aws_api_gateway_rest_api.cloudshop.id
  resource_id = aws_api_gateway_resource.productos_id.id
}

# --- Recursos /tiendas y /tiendas/{id} ---

resource "aws_api_gateway_resource" "tiendas" {
  rest_api_id = aws_api_gateway_rest_api.cloudshop.id
  parent_id   = aws_api_gateway_rest_api.cloudshop.root_resource_id
  path_part   = "tiendas"
}

resource "aws_api_gateway_resource" "tiendas_id" {
  rest_api_id = aws_api_gateway_rest_api.cloudshop.id
  parent_id   = aws_api_gateway_resource.tiendas.id
  path_part   = "{id}"
}

module "tiendas_post" {
  source                = "./modules/api_method"
  rest_api_id            = aws_api_gateway_rest_api.cloudshop.id
  resource_id            = aws_api_gateway_resource.tiendas.id
  http_method            = "POST"
  authorizer_id          = aws_api_gateway_authorizer.cognito.id
  lambda_invoke_arn      = aws_lambda_function.this["tiendas_crear"].invoke_arn
  lambda_function_name   = aws_lambda_function.this["tiendas_crear"].function_name
  api_execution_arn      = aws_api_gateway_rest_api.cloudshop.execution_arn
}

module "tiendas_get_all" {
  source                = "./modules/api_method"
  rest_api_id            = aws_api_gateway_rest_api.cloudshop.id
  resource_id            = aws_api_gateway_resource.tiendas.id
  http_method            = "GET"
  authorizer_id          = aws_api_gateway_authorizer.cognito.id
  lambda_invoke_arn      = aws_lambda_function.this["tiendas_listar"].invoke_arn
  lambda_function_name   = aws_lambda_function.this["tiendas_listar"].function_name
  api_execution_arn      = aws_api_gateway_rest_api.cloudshop.execution_arn
}

module "tiendas_get_one" {
  source              = "./modules/api_method"
  rest_api_id          = aws_api_gateway_rest_api.cloudshop.id
  resource_id          = aws_api_gateway_resource.tiendas_id.id
  http_method          = "GET"
  authorizer_id        = aws_api_gateway_authorizer.cognito.id
  lambda_invoke_arn    = aws_lambda_function.this["tiendas_obtener"].invoke_arn
  lambda_function_name = aws_lambda_function.this["tiendas_obtener"].function_name
  api_execution_arn    = aws_api_gateway_rest_api.cloudshop.execution_arn
  request_parameters   = { "method.request.path.id" = true }
}

module "tiendas_patch" {
  source              = "./modules/api_method"
  rest_api_id          = aws_api_gateway_rest_api.cloudshop.id
  resource_id          = aws_api_gateway_resource.tiendas_id.id
  http_method          = "PATCH"
  authorizer_id        = aws_api_gateway_authorizer.cognito.id
  lambda_invoke_arn    = aws_lambda_function.this["tiendas_actualizar"].invoke_arn
  lambda_function_name = aws_lambda_function.this["tiendas_actualizar"].function_name
  api_execution_arn    = aws_api_gateway_rest_api.cloudshop.execution_arn
  request_parameters   = { "method.request.path.id" = true }
}

module "tiendas_delete" {
  source              = "./modules/api_method"
  rest_api_id          = aws_api_gateway_rest_api.cloudshop.id
  resource_id          = aws_api_gateway_resource.tiendas_id.id
  http_method          = "DELETE"
  authorizer_id        = aws_api_gateway_authorizer.cognito.id
  lambda_invoke_arn    = aws_lambda_function.this["tiendas_desactivar"].invoke_arn
  lambda_function_name = aws_lambda_function.this["tiendas_desactivar"].function_name
  api_execution_arn    = aws_api_gateway_rest_api.cloudshop.execution_arn
  request_parameters   = { "method.request.path.id" = true }
}

module "tiendas_cors" {
  source      = "./modules/cors_options"
  rest_api_id = aws_api_gateway_rest_api.cloudshop.id
  resource_id = aws_api_gateway_resource.tiendas.id
}

module "tiendas_id_cors" {
  source      = "./modules/cors_options"
  rest_api_id = aws_api_gateway_rest_api.cloudshop.id
  resource_id = aws_api_gateway_resource.tiendas_id.id
}

# --- Recursos /carrito y /carrito/{id} ---
# El carrito es siempre "el mio" (usuario_id sale del token), por eso no hay
# id de usuario en la ruta. {id} aqui es el producto_id dentro del carrito.

resource "aws_api_gateway_resource" "carrito" {
  rest_api_id = aws_api_gateway_rest_api.cloudshop.id
  parent_id   = aws_api_gateway_rest_api.cloudshop.root_resource_id
  path_part   = "carrito"
}

resource "aws_api_gateway_resource" "carrito_id" {
  rest_api_id = aws_api_gateway_rest_api.cloudshop.id
  parent_id   = aws_api_gateway_resource.carrito.id
  path_part   = "{id}"
}

module "carrito_post" {
  source                = "./modules/api_method"
  rest_api_id            = aws_api_gateway_rest_api.cloudshop.id
  resource_id            = aws_api_gateway_resource.carrito.id
  http_method            = "POST"
  authorizer_id          = aws_api_gateway_authorizer.cognito.id
  lambda_invoke_arn      = aws_lambda_function.this["carrito_agregar"].invoke_arn
  lambda_function_name   = aws_lambda_function.this["carrito_agregar"].function_name
  api_execution_arn      = aws_api_gateway_rest_api.cloudshop.execution_arn
}

module "carrito_get_all" {
  source                = "./modules/api_method"
  rest_api_id            = aws_api_gateway_rest_api.cloudshop.id
  resource_id            = aws_api_gateway_resource.carrito.id
  http_method            = "GET"
  authorizer_id          = aws_api_gateway_authorizer.cognito.id
  lambda_invoke_arn      = aws_lambda_function.this["carrito_listar"].invoke_arn
  lambda_function_name   = aws_lambda_function.this["carrito_listar"].function_name
  api_execution_arn      = aws_api_gateway_rest_api.cloudshop.execution_arn
}

module "carrito_delete_all" {
  source                = "./modules/api_method"
  rest_api_id            = aws_api_gateway_rest_api.cloudshop.id
  resource_id            = aws_api_gateway_resource.carrito.id
  http_method            = "DELETE"
  authorizer_id          = aws_api_gateway_authorizer.cognito.id
  lambda_invoke_arn      = aws_lambda_function.this["carrito_vaciar"].invoke_arn
  lambda_function_name   = aws_lambda_function.this["carrito_vaciar"].function_name
  api_execution_arn      = aws_api_gateway_rest_api.cloudshop.execution_arn
}

module "carrito_patch" {
  source              = "./modules/api_method"
  rest_api_id          = aws_api_gateway_rest_api.cloudshop.id
  resource_id          = aws_api_gateway_resource.carrito_id.id
  http_method          = "PATCH"
  authorizer_id        = aws_api_gateway_authorizer.cognito.id
  lambda_invoke_arn    = aws_lambda_function.this["carrito_modificar"].invoke_arn
  lambda_function_name = aws_lambda_function.this["carrito_modificar"].function_name
  api_execution_arn    = aws_api_gateway_rest_api.cloudshop.execution_arn
  request_parameters   = { "method.request.path.id" = true }
}

module "carrito_delete_one" {
  source              = "./modules/api_method"
  rest_api_id          = aws_api_gateway_rest_api.cloudshop.id
  resource_id          = aws_api_gateway_resource.carrito_id.id
  http_method          = "DELETE"
  authorizer_id        = aws_api_gateway_authorizer.cognito.id
  lambda_invoke_arn    = aws_lambda_function.this["carrito_eliminar"].invoke_arn
  lambda_function_name = aws_lambda_function.this["carrito_eliminar"].function_name
  api_execution_arn    = aws_api_gateway_rest_api.cloudshop.execution_arn
  request_parameters   = { "method.request.path.id" = true }
}

module "carrito_cors" {
  source      = "./modules/cors_options"
  rest_api_id = aws_api_gateway_rest_api.cloudshop.id
  resource_id = aws_api_gateway_resource.carrito.id
}

module "carrito_id_cors" {
  source      = "./modules/cors_options"
  rest_api_id = aws_api_gateway_rest_api.cloudshop.id
  resource_id = aws_api_gateway_resource.carrito_id.id
}

# --- Recursos /pedidos y /pedidos/{id} ---

resource "aws_api_gateway_resource" "pedidos" {
  rest_api_id = aws_api_gateway_rest_api.cloudshop.id
  parent_id   = aws_api_gateway_rest_api.cloudshop.root_resource_id
  path_part   = "pedidos"
}

resource "aws_api_gateway_resource" "pedidos_id" {
  rest_api_id = aws_api_gateway_rest_api.cloudshop.id
  parent_id   = aws_api_gateway_resource.pedidos.id
  path_part   = "{id}"
}

module "pedidos_post" {
  source                = "./modules/api_method"
  rest_api_id            = aws_api_gateway_rest_api.cloudshop.id
  resource_id            = aws_api_gateway_resource.pedidos.id
  http_method            = "POST"
  authorizer_id          = aws_api_gateway_authorizer.cognito.id
  lambda_invoke_arn      = aws_lambda_function.this["pedidos_crear"].invoke_arn
  lambda_function_name   = aws_lambda_function.this["pedidos_crear"].function_name
  api_execution_arn      = aws_api_gateway_rest_api.cloudshop.execution_arn
}

module "pedidos_get_all" {
  source                = "./modules/api_method"
  rest_api_id            = aws_api_gateway_rest_api.cloudshop.id
  resource_id            = aws_api_gateway_resource.pedidos.id
  http_method            = "GET"
  authorizer_id          = aws_api_gateway_authorizer.cognito.id
  lambda_invoke_arn      = aws_lambda_function.this["pedidos_listar"].invoke_arn
  lambda_function_name   = aws_lambda_function.this["pedidos_listar"].function_name
  api_execution_arn      = aws_api_gateway_rest_api.cloudshop.execution_arn
}

module "pedidos_get_one" {
  source              = "./modules/api_method"
  rest_api_id          = aws_api_gateway_rest_api.cloudshop.id
  resource_id          = aws_api_gateway_resource.pedidos_id.id
  http_method          = "GET"
  authorizer_id        = aws_api_gateway_authorizer.cognito.id
  lambda_invoke_arn    = aws_lambda_function.this["pedidos_obtener"].invoke_arn
  lambda_function_name = aws_lambda_function.this["pedidos_obtener"].function_name
  api_execution_arn    = aws_api_gateway_rest_api.cloudshop.execution_arn
  request_parameters   = { "method.request.path.id" = true }
}

module "pedidos_patch" {
  source              = "./modules/api_method"
  rest_api_id          = aws_api_gateway_rest_api.cloudshop.id
  resource_id          = aws_api_gateway_resource.pedidos_id.id
  http_method          = "PATCH"
  authorizer_id        = aws_api_gateway_authorizer.cognito.id
  lambda_invoke_arn    = aws_lambda_function.this["pedidos_actualizar"].invoke_arn
  lambda_function_name = aws_lambda_function.this["pedidos_actualizar"].function_name
  api_execution_arn    = aws_api_gateway_rest_api.cloudshop.execution_arn
  request_parameters   = { "method.request.path.id" = true }
}

module "pedidos_delete" {
  source              = "./modules/api_method"
  rest_api_id          = aws_api_gateway_rest_api.cloudshop.id
  resource_id          = aws_api_gateway_resource.pedidos_id.id
  http_method          = "DELETE"
  authorizer_id        = aws_api_gateway_authorizer.cognito.id
  lambda_invoke_arn    = aws_lambda_function.this["pedidos_cancelar"].invoke_arn
  lambda_function_name = aws_lambda_function.this["pedidos_cancelar"].function_name
  api_execution_arn    = aws_api_gateway_rest_api.cloudshop.execution_arn
  request_parameters   = { "method.request.path.id" = true }
}

module "pedidos_cors" {
  source      = "./modules/cors_options"
  rest_api_id = aws_api_gateway_rest_api.cloudshop.id
  resource_id = aws_api_gateway_resource.pedidos.id
}

module "pedidos_id_cors" {
  source      = "./modules/cors_options"
  rest_api_id = aws_api_gateway_rest_api.cloudshop.id
  resource_id = aws_api_gateway_resource.pedidos_id.id
}

# --- Recurso /dashboard (solo lectura, exclusivo Administrador via IAM/rol app) ---

resource "aws_api_gateway_resource" "dashboard" {
  rest_api_id = aws_api_gateway_rest_api.cloudshop.id
  parent_id   = aws_api_gateway_rest_api.cloudshop.root_resource_id
  path_part   = "dashboard"
}

module "dashboard_get" {
  source                = "./modules/api_method"
  rest_api_id            = aws_api_gateway_rest_api.cloudshop.id
  resource_id            = aws_api_gateway_resource.dashboard.id
  http_method            = "GET"
  authorizer_id          = aws_api_gateway_authorizer.cognito.id
  lambda_invoke_arn      = aws_lambda_function.this["dashboard_resumen"].invoke_arn
  lambda_function_name   = aws_lambda_function.this["dashboard_resumen"].function_name
  api_execution_arn      = aws_api_gateway_rest_api.cloudshop.execution_arn
}

module "dashboard_cors" {
  source      = "./modules/cors_options"
  rest_api_id = aws_api_gateway_rest_api.cloudshop.id
  resource_id = aws_api_gateway_resource.dashboard.id
}

# --- Deployment + Stage ---
# El trigger fuerza un nuevo deployment cada vez que cambia algun metodo o
# recurso; sin esto Terraform no vuelve a desplegar la API en cada apply.
resource "aws_api_gateway_deployment" "cloudshop" {
  rest_api_id = aws_api_gateway_rest_api.cloudshop.id

  triggers = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_resource.usuarios.id,
      aws_api_gateway_resource.usuarios_id.id,
      module.usuarios_post.method_id,
      module.usuarios_get_all.method_id,
      module.usuarios_get_one.method_id,
      module.usuarios_patch.method_id,
      module.usuarios_delete.method_id,
      module.usuarios_cors.method_id,
      module.usuarios_id_cors.method_id,
      aws_api_gateway_resource.productos.id,
      aws_api_gateway_resource.productos_id.id,
      module.productos_post.method_id,
      module.productos_get_all.method_id,
      module.productos_get_one.method_id,
      module.productos_patch.method_id,
      module.productos_delete.method_id,
      module.productos_cors.method_id,
      module.productos_id_cors.method_id,
      aws_api_gateway_resource.tiendas.id,
      aws_api_gateway_resource.tiendas_id.id,
      module.tiendas_post.method_id,
      module.tiendas_get_all.method_id,
      module.tiendas_get_one.method_id,
      module.tiendas_patch.method_id,
      module.tiendas_delete.method_id,
      module.tiendas_cors.method_id,
      module.tiendas_id_cors.method_id,
      aws_api_gateway_resource.carrito.id,
      aws_api_gateway_resource.carrito_id.id,
      module.carrito_post.method_id,
      module.carrito_get_all.method_id,
      module.carrito_delete_all.method_id,
      module.carrito_patch.method_id,
      module.carrito_delete_one.method_id,
      module.carrito_cors.method_id,
      module.carrito_id_cors.method_id,
      aws_api_gateway_resource.pedidos.id,
      aws_api_gateway_resource.pedidos_id.id,
      module.pedidos_post.method_id,
      module.pedidos_get_all.method_id,
      module.pedidos_get_one.method_id,
      module.pedidos_patch.method_id,
      module.pedidos_delete.method_id,
      module.pedidos_cors.method_id,
      module.pedidos_id_cors.method_id,
      aws_api_gateway_resource.dashboard.id,
      module.dashboard_get.method_id,
      module.dashboard_cors.method_id,
    ]))
  }

  # depends_on explicito: aunque los outputs ya se referencian arriba en
  # `triggers` (lo que en teoria ya crea la dependencia implicita), en la
  # practica un `terraform apply` real fallo con "No integration defined for
  # method" porque los modulos *_id_cors (OPTIONS de /recurso/{id}) no
  # estaban referenciados en ningun lado y Terraform los creo en paralelo con
  # el deployment. Este depends_on fuerza que las 37 integraciones (26
  # metodos + 11 CORS) existan antes de crear el deployment, sin excepcion.
  depends_on = [
    module.usuarios_post, module.usuarios_get_all, module.usuarios_get_one, module.usuarios_patch, module.usuarios_delete, module.usuarios_cors, module.usuarios_id_cors,
    module.productos_post, module.productos_get_all, module.productos_get_one, module.productos_patch, module.productos_delete, module.productos_cors, module.productos_id_cors,
    module.tiendas_post, module.tiendas_get_all, module.tiendas_get_one, module.tiendas_patch, module.tiendas_delete, module.tiendas_cors, module.tiendas_id_cors,
    module.carrito_post, module.carrito_get_all, module.carrito_delete_all, module.carrito_patch, module.carrito_delete_one, module.carrito_cors, module.carrito_id_cors,
    module.pedidos_post, module.pedidos_get_all, module.pedidos_get_one, module.pedidos_patch, module.pedidos_delete, module.pedidos_cors, module.pedidos_id_cors,
    module.dashboard_get, module.dashboard_cors,
  ]

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_cloudwatch_log_group" "api_gateway" {
  name              = "/aws/apigateway/${local.name_prefix}"
  retention_in_days = 14
  tags              = local.common_tags
}

resource "aws_api_gateway_stage" "cloudshop" {
  deployment_id = aws_api_gateway_deployment.cloudshop.id
  rest_api_id   = aws_api_gateway_rest_api.cloudshop.id
  stage_name    = var.environment

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gateway.arn
    format = jsonencode({
      requestId    = "$context.requestId"
      ip           = "$context.identity.sourceIp"
      caller       = "$context.identity.caller"
      user         = "$context.identity.user"
      requestTime  = "$context.requestTime"
      httpMethod   = "$context.httpMethod"
      resourcePath = "$context.resourcePath"
      status       = "$context.status"
      errorMessage = "$context.error.message"
    })
  }

  tags = local.common_tags
}

# Metricas detalladas de API Gateway para CloudWatch (seccion 8 del enunciado).
resource "aws_api_gateway_method_settings" "cloudshop" {
  rest_api_id = aws_api_gateway_rest_api.cloudshop.id
  stage_name  = aws_api_gateway_stage.cloudshop.stage_name
  method_path = "*/*"

  settings {
    metrics_enabled    = true
    logging_level      = "INFO"
    data_trace_enabled = false
  }
}
