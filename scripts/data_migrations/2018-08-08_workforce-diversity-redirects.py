#!/usr/bin/env python

import subprocess

redirect_pairs = [
    (
        "work-pay-and-benefits/public-sector-workforce/armed-forces-workforce",
        "workforce-and-business/workforce-diversity/armed-forces-workforce",
    ),
    (
        "work-pay-and-benefits/public-sector-workforce/civil-service-workforce",
        "workforce-and-business/workforce-diversity/civil-service-workforce",
    ),
    (
        "work-pay-and-benefits/public-sector-workforce/judges-and-non-legal-members-of-courts-and-tribunals-in-the-workforce",  # noqa
        "workforce-and-business/workforce-diversity/judges-and-non-legal-members-of-courts-and-tribunals-in-the-workforce",  # noqa
    ),
    (
        "work-pay-and-benefits/public-sector-workforce/nhs-workforce",
        "workforce-and-business/workforce-diversity/nhs-workforce",
    ),
    (
        "work-pay-and-benefits/public-sector-workforce/success-of-shortlisted-nhs-job-applicants",
        "workforce-and-business/workforce-diversity/success-of-shortlisted-nhs-job-applicants",
    ),
    (
        "work-pay-and-benefits/public-sector-workforce/nhs-trust-board-membership",
        "workforce-and-business/workforce-diversity/nhs-trust-board-membership",
    ),
    (
        "work-pay-and-benefits/public-sector-workforce/police-workforce",
        "workforce-and-business/workforce-diversity/police-workforce",
    ),
    (
        "work-pay-and-benefits/public-sector-workforce/prison-officer-workforce",
        "workforce-and-business/workforce-diversity/prison-officer-workforce",
    ),
    (
        "work-pay-and-benefits/public-sector-workforce/school-teacher-workforce",
        "workforce-and-business/workforce-diversity/school-teacher-workforce",
    ),
    (
        "work-pay-and-benefits/public-sector-workforce/social-workers-for-children-and-families",
        "workforce-and-business/workforce-diversity/social-workers-for-children-and-families",
    ),
]

for from_uri, to_uri in redirect_pairs:
    subprocess.call(["./manage.py", "add_redirect_rule", "--from_uri", from_uri, "--to_uri", to_uri])
