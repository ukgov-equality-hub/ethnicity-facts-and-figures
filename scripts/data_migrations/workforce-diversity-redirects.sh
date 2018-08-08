#!/bin/bash

for app in rd-cms-dev rd-cms-staging rd-cms; do
  heroku run -a ${app} ./manage.py add_redirect_rule --from_uri 'work-pay-and-benefits/public-sector-workforce/armed-forces-workforce' --to_uri 'workforce-and-business/workforce-diversity/armed-forces-workforce'
  heroku run -a ${app} ./manage.py add_redirect_rule --from_uri 'work-pay-and-benefits/public-sector-workforce/civil-service-workforce' --to_uri 'workforce-and-business/workforce-diversity/civil-service-workforce'
  heroku run -a ${app} ./manage.py add_redirect_rule --from_uri 'work-pay-and-benefits/public-sector-workforce/judges-and-non-legal-members-of-courts-and-tribunals-in-the-workforce' --to_uri 'workforce-and-business/workforce-diversity/judges-and-non-legal-members-of-courts-and-tribunals-in-the-workforce'
  heroku run -a ${app} ./manage.py add_redirect_rule --from_uri 'work-pay-and-benefits/public-sector-workforce/nhs-workforce' --to_uri 'workforce-and-business/workforce-diversity/nhs-workforce'
  heroku run -a ${app} ./manage.py add_redirect_rule --from_uri 'work-pay-and-benefits/public-sector-workforce/success-of-shortlisted-nhs-job-applicants' --to_uri 'workforce-and-business/workforce-diversity/success-of-shortlisted-nhs-job-applicants'
  heroku run -a ${app} ./manage.py add_redirect_rule --from_uri 'work-pay-and-benefits/public-sector-workforce/nhs-trust-board-membership' --to_uri 'workforce-and-business/workforce-diversity/nhs-trust-board-membership'
  heroku run -a ${app} ./manage.py add_redirect_rule --from_uri 'work-pay-and-benefits/public-sector-workforce/police-workforce' --to_uri 'workforce-and-business/workforce-diversity/police-workforce'
  heroku run -a ${app} ./manage.py add_redirect_rule --from_uri 'work-pay-and-benefits/public-sector-workforce/prison-officer-workforce' --to_uri 'workforce-and-business/workforce-diversity/prison-officer-workforce'
  heroku run -a ${app} ./manage.py add_redirect_rule --from_uri 'work-pay-and-benefits/public-sector-workforce/school-teacher-workforce' --to_uri 'workforce-and-business/workforce-diversity/school-teacher-workforce'
  heroku run -a ${app} ./manage.py add_redirect_rule --from_uri 'work-pay-and-benefits/public-sector-workforce/social-workers-for-children-and-families' --to_uri 'workforce-and-business/workforce-diversity/social-workers-for-children-and-families'
done
