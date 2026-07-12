# Módulo reutilizable: 1 método REST = aws_api_gateway_method + integración
# AWS_PROXY a Lambda + permiso de invocación. Se usa una vez por cada
# combinación (recurso, verbo HTTP) en todos los módulos del proyecto.

resource "aws_api_gateway_method" "this" {
  rest_api_id        = var.rest_api_id
  resource_id        = var.resource_id
  http_method        = var.http_method
  authorization      = var.authorization
  authorizer_id      = var.authorization == "COGNITO_USER_POOLS" ? var.authorizer_id : null
  request_parameters = var.request_parameters
}

resource "aws_api_gateway_integration" "this" {
  rest_api_id             = var.rest_api_id
  resource_id             = var.resource_id
  http_method             = aws_api_gateway_method.this.http_method
  integration_http_method = "POST" # API Gateway siempre invoca Lambda con POST, sin importar el verbo público
  type                     = "AWS_PROXY"
  uri                      = var.lambda_invoke_arn
}

resource "aws_lambda_permission" "apigw" {
  statement_id  = "AllowAPIGatewayInvoke-${var.http_method}-${md5(var.resource_id)}"
  action        = "lambda:InvokeFunction"
  function_name = var.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${var.api_execution_arn}/*/${var.http_method}/*"
}
