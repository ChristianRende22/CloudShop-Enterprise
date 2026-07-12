# Seccion 8 del enunciado: Logs de Lambda, Metricas de API Gateway, Errores
# de autenticacion, Errores de aplicacion, Latencia promedio.

resource "aws_sns_topic" "alarmas" {
  name = "${local.name_prefix}-alarmas"
  tags = local.common_tags
}

resource "aws_sns_topic_subscription" "alarmas_email" {
  count     = var.alert_email != "" ? 1 : 0
  topic_arn = aws_sns_topic.alarmas.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# Una alarma de errores por cada Lambda de negocio ("Logs de Lambda" /
# "Errores de aplicacion"). Usa el mismo mapa que ya define todas las
# funciones en lambda.tf, asi se mantiene sincronizado automaticamente.
resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  for_each = local.lambda_functions

  alarm_name          = "${local.name_prefix}-${each.key}-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Sum"
  threshold           = 0
  alarm_description   = "Errores de aplicacion en la funcion ${each.key}"

  dimensions = {
    FunctionName = aws_lambda_function.this[each.key].function_name
  }

  alarm_actions = [aws_sns_topic.alarmas.arn]
  ok_actions    = [aws_sns_topic.alarmas.arn]
  tags          = local.common_tags
}

resource "aws_cloudwatch_metric_alarm" "notificaciones_errors" {
  alarm_name          = "${local.name_prefix}-notificaciones-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Sum"
  threshold           = 0
  alarm_description   = "Fallos al procesar eventos de pedidos / enviar correos SES"

  dimensions = {
    FunctionName = aws_lambda_function.notificaciones.function_name
  }

  alarm_actions = [aws_sns_topic.alarmas.arn]
  tags          = local.common_tags
}

# Errores 5xx de API Gateway (errores de aplicacion / servidor).
resource "aws_cloudwatch_metric_alarm" "api_gateway_5xx" {
  alarm_name          = "${local.name_prefix}-api-5xx"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "5XXError"
  namespace           = "AWS/ApiGateway"
  period              = 300
  statistic           = "Sum"
  threshold           = 5
  alarm_description   = "Mas de 5 errores 5xx en 5 minutos en la API"

  dimensions = {
    ApiName = aws_api_gateway_rest_api.cloudshop.name
    Stage   = aws_api_gateway_stage.cloudshop.stage_name
  }

  alarm_actions = [aws_sns_topic.alarmas.arn]
  tags          = local.common_tags
}

# Errores 4xx: incluye los 401/403 devueltos por common.auth.require_roles
# en cada Lambda -> "Errores de autenticacion" del enunciado.
resource "aws_cloudwatch_metric_alarm" "api_gateway_4xx" {
  alarm_name          = "${local.name_prefix}-api-4xx"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "4XXError"
  namespace           = "AWS/ApiGateway"
  period              = 300
  statistic           = "Sum"
  threshold           = 20
  alarm_description   = "Mas de 20 errores 4xx en 5 minutos (posibles accesos no autorizados)"

  dimensions = {
    ApiName = aws_api_gateway_rest_api.cloudshop.name
    Stage   = aws_api_gateway_stage.cloudshop.stage_name
  }

  alarm_actions = [aws_sns_topic.alarmas.arn]
  tags          = local.common_tags
}

# Latencia promedio de la API.
resource "aws_cloudwatch_metric_alarm" "api_gateway_latency" {
  alarm_name          = "${local.name_prefix}-api-latency"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "Latency"
  namespace           = "AWS/ApiGateway"
  period              = 300
  statistic           = "Average"
  threshold           = 2000
  alarm_description   = "Latencia promedio de la API superior a 2 segundos"

  dimensions = {
    ApiName = aws_api_gateway_rest_api.cloudshop.name
    Stage   = aws_api_gateway_stage.cloudshop.stage_name
  }

  alarm_actions = [aws_sns_topic.alarmas.arn]
  tags          = local.common_tags
}

# Dashboard visual de CloudWatch (Clase 29: "dashboards personalizados en
# tiempo real"). Distinto del Modulo 6 (que es de negocio) — este es
# operativo/tecnico.
resource "aws_cloudwatch_dashboard" "cloudshop" {
  dashboard_name = "${local.name_prefix}-dashboard"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6
        properties = {
          title  = "API Gateway - Requests y Errores"
          view   = "timeSeries"
          region = var.aws_region
          metrics = [
            ["AWS/ApiGateway", "Count", "ApiName", aws_api_gateway_rest_api.cloudshop.name, "Stage", aws_api_gateway_stage.cloudshop.stage_name],
            ["AWS/ApiGateway", "4XXError", "ApiName", aws_api_gateway_rest_api.cloudshop.name, "Stage", aws_api_gateway_stage.cloudshop.stage_name],
            ["AWS/ApiGateway", "5XXError", "ApiName", aws_api_gateway_rest_api.cloudshop.name, "Stage", aws_api_gateway_stage.cloudshop.stage_name],
          ]
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 12
        height = 6
        properties = {
          title  = "API Gateway - Latencia promedio (ms)"
          view   = "timeSeries"
          region = var.aws_region
          metrics = [
            ["AWS/ApiGateway", "Latency", "ApiName", aws_api_gateway_rest_api.cloudshop.name, "Stage", aws_api_gateway_stage.cloudshop.stage_name, { stat = "Average" }],
          ]
        }
      }
    ]
  })
}
