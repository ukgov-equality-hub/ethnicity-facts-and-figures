
resource "aws_cloudfront_cache_policy" "cloudfront_cache_policy__static_site" {
  name = "${var.service_name_hyphens}--${var.environment_hyphens}-Cache-Policy--Static-Site"
  min_ttl = 0
  default_ttl = 60
  max_ttl = 600

  parameters_in_cache_key_and_forwarded_to_origin {
    cookies_config {
      cookie_behavior = "none"
    }
    headers_config {
      header_behavior = "none"
    }
    query_strings_config {
      query_string_behavior = "none"
    }
  }
}

locals {
  distribution_for_static_site__origin_id = "${var.service_name_hyphens}--${var.environment_hyphens}--Static-Site-origin"
}

resource "aws_cloudfront_distribution" "distribution__static_site" {
  // CloudFront distributions have to be created in the us-east-1 region (for some reason!)
  provider = aws.us-east-1

  comment = "${var.service_name_hyphens}--${var.environment_hyphens}--static-site"

  origin {
    domain_name = aws_s3_bucket_website_configuration.s3_bucket_website_configuration__static_site.website_endpoint
    origin_id = local.distribution_for_static_site__origin_id

    custom_origin_config {
      http_port = 80
      https_port = 443
      origin_protocol_policy = "http-only"
      origin_ssl_protocols = ["TLSv1.2"]
    }

    custom_header {                              // We would like the static website to be available ONLY via CLoudFront
      name = "Referer"                           // e.g. so that Google doesn't index the *.s3-website.eu-west-2.amazonaws.com domain
      value = var.STATIC_SITE_S3_SECRET_REFERER  // So CloudFront adds a secret "Referer" header and the S3 bucket policy checks for it
    }
  }

  price_class = "PriceClass_100"

  aliases = ["${var.dns_record_subdomain_including_dot__static_website}${data.aws_route53_zone.route_53_zone_for_our_domain.name}"]

  viewer_certificate {
    acm_certificate_arn = aws_acm_certificate_validation.certificate_validation_waiter__static_site.certificate_arn
    cloudfront_default_certificate = false
    minimum_protocol_version = "TLSv1"
    ssl_support_method = "sni-only"
  }

  default_root_object = "index.html"

  enabled = true
  is_ipv6_enabled = true

  default_cache_behavior {
    cache_policy_id = aws_cloudfront_cache_policy.cloudfront_cache_policy__static_site.id
    allowed_methods = ["GET", "HEAD"]
    cached_methods = ["GET", "HEAD"]
    target_origin_id = local.distribution_for_static_site__origin_id
    viewer_protocol_policy = "redirect-to-https"
    compress = true

    dynamic "function_association" {
      for_each = var.environment != "Prod" ? [1] : []  // Only create this Function Association in non-production environments (i.e. if "var.environment" is not "Prod")

      content {
        event_type = "viewer-request"
        function_arn = aws_cloudfront_function.http_basic_auth_function[0].arn
      }
    }
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
      locations = []
    }
  }
}

resource "aws_cloudfront_function" "http_basic_auth_function" {
  count = (var.environment != "Prod") ? 1 : 0  // Only create this CloudFront Function in non-production environments (i.e. if "var.environment" is not "Prod")

  name    = "${var.service_name_hyphens}--${var.environment_hyphens}--http-basic-auth-function"
  runtime = "cloudfront-js-1.0"
  publish = true
  code    = <<EOT
function handler(event) {
  var authHeaders = event.request.headers.authorization;

  // Configure authentication
  var authUser = '${var.BASIC_AUTH_USERNAME}';
  var authPass = '${var.BASIC_AUTH_PASSWORD}';

  function b2a(a) {
    var c, d, e, f, g, h, i, j, o, b = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=", k = 0, l = 0, m = "", n = [];
    if (!a) return a;
    do c = a.charCodeAt(k++), d = a.charCodeAt(k++), e = a.charCodeAt(k++), j = c << 16 | d << 8 | e,
    f = 63 & j >> 18, g = 63 & j >> 12, h = 63 & j >> 6, i = 63 & j, n[l++] = b.charAt(f) + b.charAt(g) + b.charAt(h) + b.charAt(i); while (k < a.length);
    return m = n.join(""), o = a.length % 3, (o ? m.slice(0, o - 3) :m) + "===".slice(o || 3);
  }

  // Construct the Basic Auth string
  var expected = 'Basic ' + b2a(authUser + ':' + authPass);

  // If an Authorization header is supplied and it's an exact match, pass the
  // request on through to CF/the origin without any modification.
  if (authHeaders && authHeaders.value === expected) {
    return event.request;
  }

  // But if we get here, we must either be missing the auth header or the
  // credentials failed to match what we expected.
  // Request the browser present the Basic Auth dialog.
  var response = {
    statusCode: 401,
    statusDescription: "Unauthorized",
    headers: {
      "www-authenticate": {
        value: 'Basic realm="Inclusion Confident Scheme design history"',
      },
    },
  };

  return response;
}
EOT
}
