#!/usr/bin/env bash

set -o pipefail

if [ "$#" -ne 2 ]; then
  echo "Required args [postgres url] and [output file and path]" >&2
  echo "e.g. ./get_data.sh postgres://[username]:[password]@[host]:[port]/[db] /tmp/data.dump"
  exit 1
fi

pg_dump --no-acl --no-owner -Fc -d $1 > $2
