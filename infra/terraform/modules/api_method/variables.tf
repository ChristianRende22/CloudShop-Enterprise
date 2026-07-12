variable "rest_api_id" {
  type = string
}

variable "resource_id" {
  type = string
}

variable "http_method" {
  type = string
}

variable "authorizer_id" {
  type    = string
  default = null
}

variable "authorization" {
  type    = string
  default = "COGNITO_USER_POOLS"
}

variable "lambda_invoke_arn" {
  type = string
}

variable "lambda_function_name" {
  type = string
}

variable "api_execution_arn" {
  type = string
}

variable "request_parameters" {
  type    = map(bool)
  default = {}
}
