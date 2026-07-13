output "method_id" {
  description = "Usado como dependencia en el trigger de redeployment de API Gateway (forzar redeploy si cambia el CORS)"
  value       = aws_api_gateway_method.options.id
}
