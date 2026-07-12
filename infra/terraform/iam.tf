data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "lambda_exec" {
  name               = "${local.name_prefix}-lambda-exec-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
  tags               = local.common_tags
}

resource "aws_iam_role_policy_attachment" "lambda_basic_logs" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Principio de minimo privilegio (Clase 29 / seccion 5 del enunciado):
# solo las acciones de lectura/escritura de item necesarias, solo sobre las
# tablas del proyecto. Nunca dynamodb:* ni Resource "*".
data "aws_iam_policy_document" "lambda_dynamodb" {
  statement {
    sid    = "CloudShopDynamoDBAccess"
    effect = "Allow"
    actions = [
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
      "dynamodb:DeleteItem",
      "dynamodb:Query",
      "dynamodb:Scan",
    ]
    resources = [
      aws_dynamodb_table.usuarios.arn,
      "${aws_dynamodb_table.usuarios.arn}/index/*",
      aws_dynamodb_table.auditoria.arn,
      aws_dynamodb_table.productos.arn,
      "${aws_dynamodb_table.productos.arn}/index/*",
      aws_dynamodb_table.tiendas.arn,
    ]
  }
}

resource "aws_iam_policy" "lambda_dynamodb" {
  name   = "${local.name_prefix}-lambda-dynamodb-policy"
  policy = data.aws_iam_policy_document.lambda_dynamodb.json
}

resource "aws_iam_role_policy_attachment" "lambda_dynamodb" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = aws_iam_policy.lambda_dynamodb.arn
}

data "aws_iam_policy_document" "lambda_eventbridge" {
  statement {
    sid       = "CloudShopPutEvents"
    effect    = "Allow"
    actions   = ["events:PutEvents"]
    resources = [aws_cloudwatch_event_bus.cloudshop.arn]
  }
}

resource "aws_iam_policy" "lambda_eventbridge" {
  name   = "${local.name_prefix}-lambda-eventbridge-policy"
  policy = data.aws_iam_policy_document.lambda_eventbridge.json
}

resource "aws_iam_role_policy_attachment" "lambda_eventbridge" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = aws_iam_policy.lambda_eventbridge.arn
}

# NOTA: cuando se agregue el modulo de Pedidos con SES, se crea una policy
# adicional ses:SendEmail acotada al identity `var.ses_sender_email`, adjunta
# SOLO a la Lambda consumer de notificaciones (no a este rol compartido) -
# para no darle permiso de enviar correo a Lambdas que no lo necesitan.
