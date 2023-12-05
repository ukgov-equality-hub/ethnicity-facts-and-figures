
// An S3 bucket to store the static website
resource "aws_s3_bucket" "s3_bucket__static_site" {
  bucket_prefix = lower("${var.service_name_hyphens}--${var.environment_hyphens}--static-site-")
}

resource "aws_s3_bucket_public_access_block" "static_website_s3_bucket_public_access_block" {
  bucket = aws_s3_bucket.s3_bucket__static_site.id

  block_public_acls       = true
  ignore_public_acls      = true
  block_public_policy     = false  // We want to use a Bucket Policy to allow access (via CloudFront)
  restrict_public_buckets = false  // We want to use a Bucket Policy to allow access (via CloudFront)
}

resource "aws_s3_bucket_website_configuration" "s3_bucket_website_configuration__static_site" {
  bucket = aws_s3_bucket.s3_bucket__static_site.id

  index_document {
    suffix = "index.html"
  }

  lifecycle {
    ignore_changes = [routing_rule, routing_rules]
  }
}

data "aws_iam_policy_document" "static_website_s3_policy" {
  statement {
    effect    = "Allow"
    principals {
      type = "*"
      identifiers = ["*"]
    }
    actions   = ["s3:GetObject"]
    resources = [
      "${aws_s3_bucket.s3_bucket__static_site.arn}/*"  // The files within the bucket
    ]
    condition {
      test = "StringEquals"                         // We would like the static website to be available ONLY via CLoudFront
      variable = "aws:Referer"                      // e.g. so that Google doesn't index the *.s3-website.eu-west-2.amazonaws.com domain
      values = [var.STATIC_SITE_S3_SECRET_REFERER]  // So CloudFront adds a secret "Referer" header and the S3 bucket policy checks for it
    }
  }
}

resource "aws_s3_bucket_policy" "static_website_s3_bucket_policy" {
  bucket = aws_s3_bucket.s3_bucket__static_site.id
  policy = data.aws_iam_policy_document.static_website_s3_policy.json
}
