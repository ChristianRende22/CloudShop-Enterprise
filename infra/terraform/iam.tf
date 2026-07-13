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
      "dynamodb:BatchGetItem",
      "dynamodb:BatchWriteItem",
    ]
    resources = [
      aws_dynamodb_table.usuarios.arn,
      "${aws_dynamodb_table.usuarios.arn}/index/*",
      aws_dynamodb_table.auditoria.arn,
      aws_dynamodb_table.productos.arn,
      "${aws_dynamodb_table.productos.arn}/index/*",
      aws_dynamodb_table.tiendas.arn,
      aws_dynamodb_table.carrito.arn,
      aws_dynamodb_table.pedidos.arn,
      "${aws_dynamodb_table.pedidos.arn}/index/*",
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

# Rol SEPARADO para la Lambda de notificaciones: es la UNICA que puede
# enviar correo. El resto de Lambdas (usuarios, productos, pedidos, etc.)
# jamas tocan SES directamente -> minimo privilegio real, no solo en el papel.
data "aws_iam_policy_document" "notificaciones_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "notificaciones_exec" {
  name               = "${local.name_prefix}-notificaciones-exec-role"
  assume_role_policy = data.aws_iam_policy_document.notificaciones_assume_role.json
  tags               = local.common_tags
}

resource "aws_iam_role_policy_attachment" "notificaciones_basic_logs" {
  role       = aws_iam_role.notificaciones_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

data "aws_iam_policy_document" "notificaciones_ses" {
  statement {
    sid       = "CloudShopSendEmail"
    effect    = "Allow"
    actions   = ["ses:SendEmail", "ses:SendRawEmail"]
    resources = ["*"]
    condition {
      test     = "StringEquals"
      variable = "ses:FromAddress"
      values   = [var.ses_sender_email]
    }
  }
}

resource "aws_iam_policy" "notificaciones_ses" {
  name   = "${local.name_prefix}-notificaciones-ses-policy"
  policy = data.aws_iam_policy_document.notificaciones_ses.json
}

resource "aws_iam_role_policy_attachment" "notificaciones_ses" {
  role       = aws_iam_role.notificaciones_exec.name
  policy_arn = aws_iam_policy.notificaciones_ses.arn
}
