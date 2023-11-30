
data "aws_route53_zone" "route_53_zone_for_our_domain" {
  name = "ethnicity-facts-figures.service.gov.uk."
}

resource "aws_route53_record" "dns_alias_record__static_website" {
  count = var.create_dns_record__static_website ? 1 : 0  // Only create this DNS record if "var.create_dns_record__static_website" is true

  zone_id = data.aws_route53_zone.route_53_zone_for_our_domain.zone_id
  name    = "${var.dns_record_subdomain_including_dot__static_website}${data.aws_route53_zone.route_53_zone_for_our_domain.name}"
  type    = "A"

  alias {
    evaluate_target_health = false
    name = aws_cloudfront_distribution.distribution__static_site.domain_name
    zone_id = aws_cloudfront_distribution.distribution__static_site.hosted_zone_id
  }
}

resource "aws_route53_record" "dns_alias_record__redirect" {
  count = var.create_redirect_from_root_domain ? 1 : 0  // Only create this DNS record if "var.create_redirect_from_root_domain" is true

  zone_id = data.aws_route53_zone.route_53_zone_for_our_domain.zone_id
  name    = "${var.dns_record_root_domain_including_dot}${data.aws_route53_zone.route_53_zone_for_our_domain.name}"
  type    = "A"

  alias {
    evaluate_target_health = false
    name = aws_cloudfront_distribution.distribution__root_domain_redirect[0].domain_name
    zone_id = aws_cloudfront_distribution.distribution__root_domain_redirect[0].hosted_zone_id
  }
}
