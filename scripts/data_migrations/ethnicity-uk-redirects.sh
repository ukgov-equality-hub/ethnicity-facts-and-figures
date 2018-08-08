#!/bin/bash

for app in rd-cms-dev rd-cms-staging rd-cms; do
  heroku run -a ${app} ./manage.py add_redirect_rule --from_uri 'ethnicity-in-the-uk/population-by-ethnicity' --to_uri 'british-population/national-and-regional-populations/population-of-england-and-wales/latest'
  heroku run -a ${app} ./manage.py add_redirect_rule --from_uri 'ethnicity-in-the-uk/ethnic-groups-by-region' --to_uri 'british-population/national-and-regional-populations/regional-ethnic-diversity/latest'
  heroku run -a ${app} ./manage.py add_redirect_rule --from_uri 'ethnicity-in-the-uk/ethnic-groups-by-gender' --to_uri 'british-population/demographics/male-and-female-populations/latest'
done
