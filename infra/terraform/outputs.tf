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

output "auditoria_table_name" {
  value = aws_dynamodb_table.auditoria.name
}

output "event_bus_name" {
  value = aws_cloudwatch_event_bus.cloudshop.name
}

output "lambda_exec_role_arn" {
  value = aws_iam_role.lambda_exec.arn
}
