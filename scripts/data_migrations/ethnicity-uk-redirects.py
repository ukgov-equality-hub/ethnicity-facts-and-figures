#!/usr/bin/env python

import subprocess

redirect_pairs = [
    ('ethnicity-in-the-uk/population-by-ethnicity', 'british-population/national-and-regional-populations/population-of-england-and-wales/latest'),
    ('ethnicity-in-the-uk/ethnic-groups-by-region', 'british-population/national-and-regional-populations/regional-ethnic-diversity/latest'),
    ('ethnicity-in-the-uk/ethnic-groups-by-gender', 'british-population/demographics/male-and-female-populations/latest'),
]

for from_uri, to_uri in redirect_pairs:
    subprocess.call(["./manage.py", "add_redirect_rule", "--from_uri", from_uri, "--to_uri", to_uri])
