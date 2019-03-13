#!/usr/bin/env python

import subprocess

redirect_pairs = [
    (
        "work-pay-and-benefits/business-and-self-employment/self-employment",
        "workforce-and-business/business-and-self-employment/self-employment",
    ),
    (
        "work-pay-and-benefits/business-and-self-employment/access-to-start-up-loans",
        "workforce-and-business/business-and-self-employment/access-to-start-up-loans",
    ),
]

for from_uri, to_uri in redirect_pairs:
    subprocess.call(["./manage.py", "add_redirect_rule", "--from_uri", from_uri, "--to_uri", to_uri])
