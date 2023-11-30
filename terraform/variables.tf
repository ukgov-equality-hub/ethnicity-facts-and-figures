
variable "service_name" {
  type = string
  description = "The short name of the service."
  default = "eff"
}

variable "service_name_hyphens" {
  type = string
  description = "The short name of the service (using hyphen-style)."
  default = "eff"
}

variable "environment" {
  type = string
  description = "The environment name."
}

variable "environment_hyphens" {
  type = string
  description = "The environment name (using hyphen-style)."
}

variable "create_dns_record__static_website" {
  type = bool
  description = "Should terraform create a Route53 alias record for the (sub)domain - for the static website"
}
variable "dns_record_subdomain_including_dot__static_website" {
  type = string
  description = "The subdomain (including dot - e.g. 'dev.' or just '' for production) for the Route53 alias record - for the static website"
}

variable "create_redirect_from_root_domain" {
  type = bool
  description = "Should terraform create a CloudFront distribution to redirect the root domain to www. - for the static site"
}
variable "dns_record_root_domain_including_dot" {
  type = string
  description = "The root domain (including dot - e.g. 'dev.' or just '' for production) for the static site redirect"
}

variable "aws_region" {
  type = string
  description = "The AWS region used for the provider and resources."
  default = "eu-west-2"
}

// SECRETS
// These variables are set in GitHub Actions environment-specific secrets
// Most of these are passed to the application via Elastic Beanstalk environment variables
variable "BASIC_AUTH_USERNAME" {
  type = string
  default = ""
}
variable "BASIC_AUTH_PASSWORD" {
  type = string
  default = ""
}
