#!/usr/bin/env python

import subprocess


subprocess.call(
    [
        "./manage.py",
        "add_redirect_rule",
        "--from_uri",
        "dashboards/measure-progress",
        "--to_uri",
        "dashboards/planned-pages",
    ]
)
