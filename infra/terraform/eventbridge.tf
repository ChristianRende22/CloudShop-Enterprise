# Bus de eventos propio del proyecto (seccion 6 - Arquitectura Basada en Eventos).
resource "aws_cloudwatch_event_bus" "cloudshop" {
  name = "${local.name_prefix}-bus"
  tags = local.common_tags
}

# Regla: cuando pedidos/handler.py publica PedidoCreado o PedidoCancelado,
# EventBridge invoca la Lambda de notificaciones (desacoplado del flujo
# sincrono de creacion del pedido).
resource "aws_cloudwatch_event_rule" "pedido_eventos" {
  name           = "${local.name_prefix}-pedido-eventos"
  event_bus_name = aws_cloudwatch_event_bus.cloudshop.name
  description    = "Dispara notificaciones por correo cuando se crea o cancela un pedido"

  event_pattern = jsonencode({
    source      = ["cloudshop.pedidos"]
    detail-type = ["PedidoCreado", "PedidoCancelado"]
  })

  tags = local.common_tags
}

resource "aws_cloudwatch_event_target" "notificaciones" {
  rule           = aws_cloudwatch_event_rule.pedido_eventos.name
  event_bus_name = aws_cloudwatch_event_bus.cloudshop.name
  arn            = aws_lambda_function.notificaciones.arn
}

resource "aws_lambda_permission" "eventbridge_invoca_notificaciones" {
  statement_id  = "AllowEventBridgeInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.notificaciones.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.pedido_eventos.arn
}
