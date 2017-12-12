[![Build Status](https://ci-badges.herokuapp.com/pipelines/84693d88-8bc1-4940-8f68-4111828a2278/master.svg)](https://ci-badges.herokuapp.com/pipelines/84693d88-8bc1-4940-8f68-4111828a2278/tests)


:skull: *Work in progress* :skull:

# RD CMS

## Prerequisites

- Python 3
- Postgres
- Node.js and NPM

#### Bootstrap your local dev environment

After checking out make a virtualenv and activate it.

Use mkvirtualenv to make your life very much easier.

```
pip install virtualenvwrapper
```

Add this to your .profile, or .zshrc (depending on what shell you use)

```
export WORKON_HOME=$HOME/.virtualenvs
source /usr/local/bin/virtualenvwrapper.sh
```
Then you can create the virtualenv and activate it

Note the flag -p python3 is only relevant if you python3 is not the default on your system.

```
mkvirtualenv -p python3 rd-cms
workon rd-cms
```

Install the Python server requirements:

```
pip install -r test_requirements.txt
```

Install the Node.js requirements (for front end assets):

```
npm install
```

Then generate the assets using:

```
gulp version
```


#### Environment variables

We're using python-dotenv at the moment. Add a file called .env in the root of the project
containing the values below. This file should not be committed and is in .gitignore. Only add
values for local development and test. For our deployments we are using Heroku and therefor any
variables needed for the application need to be set manually on Heroku.

```
SECRET_KEY=[for local dev and test doesn't matter]
ENVIRONMENT=dev
DATABASE_URL=postgresql://localhost/rdcms
STATIC_BUILD_DIR=/somepath/onyourmachine # this only matters if you want to test static build
GITHUB_ACCESS_TOKEN=[ask a grown up]
GITHUB_URL=github.com/racedisparityaudit
PUBLICATION_STATES=['ACCEPTED']
FILE_SERVICE=LOCAL
ACCEPT_HIGHCHARTS_LICENSE=YES

```

Remember do not commit sensitive data to the repo.

If we ever move of Heroku we'll find another way to generate a .env for production or use something else.

For CI variables are in circle.yml


#### Create local dev and test dbs (using postgres commands)

```
createdb rdcms
createdb rdcms_test
```

#### Run initial db migrations (using flask-migrate)
```
./manage.py db upgrade
```

If you add any models, you need to add them to the manage.py script then run the following steps:

```
./manage.py db migrate # generated the migration scripts
./manage.py db upgrade # runs the migration scripts
```

#### User accounts

This application uses Flask Security for login, and has a basic User and Role model.

To start you will  need to create the basic roles of ADMIN and USER. You only need to run this step once when
you first setup your database, or anytime you tear down your database and start again.

```
./manage.py create_roles
```

Then you can create your local user account

```
./manage.py create_local_user_account --email someemail@somedept.gov.uk
```

This will print out a url for you to vist to finish creating the account.


In production account creation is via the users page that is under /admin.

However there is an management command avaialable as well that will email the account activation link to a user.

```
./manage.py create_user_account --email someemail@somedept.gov.uk
```

Accounts can only be made for gov.uk email addresses. To setup an account for a non gov.uk email, you need to whitelist the specific email. To do that add an environment variable:

```
ACCOUNT_WHITELIST="['someperson@gmail.com']"
```

Note the quoting of the list and the list item above.


#### Run the tests

```
scripts/run_tests.sh
```

#### Run the app

If you wish to use the app without affecting the master content repo branch please create a remote branch
 and check it out on your local machine.

To run the application server:

```
scripts/run.sh
```

To run the Gulp build process for static assets (CSS and javascript) whenever they are changed:

```
gulp watch
```

## The static site

To make hosting simpler, and more secure, it is possible to generate a completely static copy of the website 
suitable for hosting on S3 or similar.

This can be generated using the following script to kick of a build of the site as soon as possible:

```
./manage.py force_build_static_site
```

On heroku a scheduled job runs every ten minutes to check if a build is required, usually by a page being approved. 
However you can also request a build on the normal schedule using the following management. This will add an entry to the
build table that will be processed when the scheduled job runs.

```
./manage.py request_static_build
```


This requires the presence of a `STATIC_BUILD_DIR` environment variable to tell the script where to save the static files.

## Deployment


