
// An S3 bucket to store the uploads
resource "aws_s3_bucket" "s3_bucket__uploads" {
  bucket_prefix = lower("${var.service_name_hyphens}--${var.environment_hyphens}--uploads-")
}

resource "aws_s3_bucket_public_access_block" "uploads_s3_bucket_public_access_block" {
  bucket = aws_s3_bucket.s3_bucket__uploads.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
