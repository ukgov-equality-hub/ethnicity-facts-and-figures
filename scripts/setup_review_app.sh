#!/bin/bash

set -o pipefail

function display_result {
  EXIT_STATUS=$1

  if [ $RESULT -ne 0 ]; then
    echo -e "\033[31m$Setup failed\033[0m"
    exit $EXIT_STATUS
  else
    echo -e "\033[32m$Setup successful\033[0m"
  fi
}

psql -d $DATABASE_URL -c "drop schema public cascade;"
display_result $? 1 "Drop schema as PR may have migrations not yet applied to master"

pg_dump -F custom --no-acl --no-owner -d $DB_FOR_REVIEW_APPS | pg_restore -c -d $DATABASE_URL
display_result $? 1 "Copy over db from dev/master"

./manage.py db upgrade
display_result $? 1 "Apply migrations including any in review app PR"
