# SES en modo sandbox (por defecto en cuentas nuevas de AWS) requiere
# verificar tanto el remitente como cada destinatario antes de poder enviar
# correos reales. Terraform solo declara la identidad; el enlace de
# verificacion llega al correo y hay que confirmarlo manualmente una vez.
resource "aws_ses_email_identity" "remitente" {
  email = var.ses_sender_email
}
