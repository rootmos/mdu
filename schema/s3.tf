data "aws_s3_bucket" "www" {
  bucket = "rootmos-www"
}

resource "aws_iam_role_policy" "app-www-write" {
  name = "${var.prefix}app-www-write"
  role = aws_iam_role.app.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:PutObjectACL",
        ]
        Resource = [
          "${data.aws_s3_bucket.www.arn}${var.www-prefix}/*",
        ]
      }
    ]
  })
}
