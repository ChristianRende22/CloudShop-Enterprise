# Bus de eventos propio del proyecto (sección 6 — Arquitectura Basada en Eventos).
# Las reglas concretas (ej. PedidoCreado -> Lambda de notificaciones SES) se
# agregan en el módulo de Pedidos, reutilizando este mismo bus.
resource "aws_cloudwatch_event_bus" "cloudshop" {
  name = "${local.name_prefix}-bus"
  tags = local.common_tags
}
