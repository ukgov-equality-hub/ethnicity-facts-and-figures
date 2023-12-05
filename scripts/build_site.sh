#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

python3 "${SCRIPT_DIR}/../manage.py" force_build_static_site > /var/log/static-site-build.log 2>&1 &
