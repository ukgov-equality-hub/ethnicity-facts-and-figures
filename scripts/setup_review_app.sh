#!/bin/bash

set -o pipefail

function display_result {
  RESULT=$1
  EXIT_STATUS=$2
  ACTION=$3

  if [[ $RESULT -ne 0 ]]; then
    echo -e "\033[31m$ACTION failed\033[0m"
    exit $EXIT_STATUS
  else
    echo -e "\033[32m$ACTION successful\033[0m"
  fi
}

psql -d $DATABASE_URL -c "drop schema public cascade; create schema public;"
display_result $? 1 "Drop schema as PR may have migrations not yet applied to master"

pg_dump -F custom --schema public -d $DB_FOR_REVIEW_APPS | pg_restore --no-owner --no-acl --schema public -d $DATABASE_URL
display_result $? 1 "Copy over db from dev/master"

./manage.py db upgrade
display_result $? 1 "Apply migrations including any in review app PR"

./manage.py delete_all_measures_except_two_per_subtopic
display_result $? 1 "Drop all but first two measures in each subtopic from database so rowcount < heroku limit of 10k"

./manage.py refresh_materialized_views
display_result $? 1 "Refresh materialized views"
