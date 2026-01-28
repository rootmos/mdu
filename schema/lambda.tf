locals {
  runtime = "python3.14"
}

resource "aws_lambda_function" "app" {
  function_name = "${var.prefix}app"
  role = aws_iam_role.app.arn

  runtime = local.runtime
  handler = "schema.Lambda.harness"

  filename = "app.zip"
  source_code_hash = filebase64sha256("app.zip")

  layers = [
    aws_lambda_layer_version.deps.arn,
  ]

  timeout = 30

  environment {
    variables = {
      SCHEMA_LOG_LEVEL = "DEBUG"
      ALERT_SNS_TOPIC_ARN = data.aws_sns_topic.alerts.arn
      S3_BASE_URL = "s3://${data.aws_s3_bucket.www.id}${var.www-prefix}"
    }
  }
}

output "lambda_arn" {
  value = aws_lambda_function.app.arn
}

output "lambda_code" {
  value = aws_lambda_function.app.source_code_hash
}

resource "aws_lambda_layer_version" "deps" {
  layer_name = "${var.prefix}deps"

  filename = "deps.zip"
  source_code_hash = filebase64sha256("deps.zip")

  compatible_runtimes = [ local.runtime ]
}

output "lambda_deps_arn" {
  value = aws_lambda_layer_version.deps.arn
}

output "lambda_deps" {
  value = aws_lambda_layer_version.deps.source_code_hash
}

resource "aws_cloudwatch_log_group" "app" {
  name = "/aws/lambda/${aws_lambda_function.app.function_name}"
  retention_in_days = 3
}

resource "aws_iam_role" "app" {
  name = "${var.prefix}app"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Principal = { Service = "lambda.amazonaws.com" }
        Effect = "Allow"
      }
    ]
  })
}

resource "aws_iam_role_policy" "app" {
  name = "${var.prefix}app"
  role = aws_iam_role.app.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:PutLogEvents",
          "logs:CreateLogStream",
        ]
        Resource = [ "${aws_cloudwatch_log_group.app.arn}:*" ]
      },
      {
        Effect = "Allow"
        Action = [ "SNS:Publish" ]
        Resource = [
          data.aws_sns_topic.alerts.arn,
        ]
      },
    ]
  })
}
