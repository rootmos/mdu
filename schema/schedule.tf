module "schedule" {
  source = "git::https://git.sr.ht/~rootmos/lambda-scheduler"

  function_name = aws_lambda_function.app.function_name

  period_minutes = 4*60

  input = <<EOF
{
  "schedule": {
    "arn": "<aws.scheduler.schedule-arn>",
    "scheduled-time": "<aws.scheduler.scheduled-time>",
    "execution-id": "<aws.scheduler.execution-id>",
    "attempt-number": "<aws.scheduler.attempt-number>"
  }
}
EOF

  alarm_actions = [ data.aws_sns_topic.alerts.arn ]
  ok_actions = [ data.aws_sns_topic.alerts.arn ]
}
