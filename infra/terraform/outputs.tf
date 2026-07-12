output "api_invoke_url" {
  description = "URL base de la API (ej. para pegar en el frontend como VITE_API_URL)"
  value       = aws_api_gateway_stage.cloudshop.invoke_url
}

output "usuarios_table_name" {
  value = aws_dynamodb_table.usuarios.name
}

output "productos_table_name" {
  value = aws_dynamodb_table.productos.name
}

output "tiendas_table_name" {
  value = aws_dynamodb_table.tiendas.name
}

output "carrito_table_name" {
  value = aws_dynamodb_table.carrito.name
}

output "pedidos_table_name" {
  value = aws_dynamodb_table.pedidos.name
}

output "notificaciones_lambda_name" {
  value = aws_lambda_function.notificaciones.function_name
}

output "cloudfront_domain_name" {
  description = "Dominio publico del frontend (https://<esto>)"
  value       = aws_cloudfront_distribution.frontend.domain_name
}

output "frontend_bucket_name" {
  value = aws_s3_bucket.frontend.bucket
}

output "waf_web_acl_arn" {
  value = aws_wafv2_web_acl.cloudshop.arn
}

output "cloudwatch_dashboard_url" {
  value = "https://${var.aws_region}.console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#dashboards:name=${aws_cloudwatch_dashboard.cloudshop.dashboard_name}"
}

output "sns_alarmas_topic_arn" {
  value = aws_sns_topic.alarmas.arn
}

output "auditoria_table_name" {
  value = aws_dynamodb_table.auditoria.name
}

output "event_bus_name" {
  value = aws_cloudwatch_event_bus.cloudshop.name
}

output "lambda_exec_role_arn" {
  value = aws_iam_role.lambda_exec.arn
}

output "cognito_user_pool_id" {
  description = "Para VITE_COGNITO_USER_POOL_ID en frontend/.env.production"
  value       = aws_cognito_user_pool.cloudshop.id
}

output "cognito_client_id" {
  description = "Para VITE_COGNITO_CLIENT_ID en frontend/.env.production"
  value       = aws_cognito_user_pool_client.frontend.id
}

output "cognito_region" {
  value = var.aws_region
}
