## Static site error pages

This directory structure (`static_site/error`) is depended upon by CloudFront and Heroku. Heroku serves its static
error pages from the root of this directory using two files:

* `service_unavailable.html`: served to a user when Heroku fails to get a valid reply from the publisher
* `site_maintenance.html`: served when we put the publisher into maintenance mode


The subdirectory, `major-errors`, is used by CloudFront to serve pages for HTTP status codes (4xx and 5xx). The name
of the directory is important, as CloudFront uses it to know when to switch from looking in the static site bucket to
our separate bucket of error pages.
