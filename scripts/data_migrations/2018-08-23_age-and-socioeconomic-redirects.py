#!/usr/bin/env python

import subprocess

redirect_pairs = [
    (
        "ethnicity-in-the-uk/ethnic-groups-by-economic-status",
        "british-population/demographics/socioeconomic-status/latest",
    ),
    ("ethnicity-in-the-uk/ethnic-groups-by-age", "british-population/demographics/age-groups/latest"),
]

for from_uri, to_uri in redirect_pairs:
    subprocess.call(["./manage.py", "add_redirect_rule", "--from_uri", from_uri, "--to_uri", to_uri])
