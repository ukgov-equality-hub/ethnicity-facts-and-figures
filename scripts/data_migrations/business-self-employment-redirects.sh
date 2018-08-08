#!/bin/bash

for app in rd-cms-dev rd-cms-staging rd-cms; do
  heroku run -a ${app} ./manage.py add_redirect_rule --from_uri 'work-pay-and-benefits/business-and-self-employment/self-employment' --to_uri 'workforce-and-business/business-and-self-employment/self-employment'
  heroku run -a ${app} ./manage.py add_redirect_rule --from_uri 'work-pay-and-benefits/business-and-self-employment/access-to-start-up-loans' --to_uri 'workforce-and-business/business-and-self-employment/access-to-start-up-loans'
done
