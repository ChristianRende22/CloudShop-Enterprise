variable "aws_region" {
  description = "Región AWS donde se despliega CloudShop Enterprise"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Nombre base usado como prefijo de todos los recursos"
  type        = string
  default     = "cloudshop"
}

variable "environment" {
  description = "Ambiente de despliegue (dev, staging, prod) — también nombre del stage de API Gateway"
  type        = string
  default     = "dev"
}

variable "cognito_user_pool_arn" {
  description = "ARN del User Pool de Cognito usado por el Authorizer de API Gateway. Debe exponer el atributo custom 'custom:role' con valores Administrador|Operador|Cliente."
  type        = string
}

variable "ses_sender_email" {
  description = "Correo verificado en SES que enviará las notificaciones de pedidos (sandbox de SES requiere verificar también los destinatarios)"
  type        = string
  default     = ""
}

variable "alert_email" {
  description = "Correo que recibe las alarmas de CloudWatch"
  type        = string
  default     = ""
}
