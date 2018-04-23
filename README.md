[![Heroku CI Status](https://ci-badges.herokuapp.com/pipelines/84693d88-8bc1-4940-8f68-4111828a2278/master.svg)](https://dashboard.heroku.com/pipelines/84693d88-8bc1-4940-8f68-4111828a2278/tests)


:skull: *Work in progress* :skull:

# RD CMS

## Prerequisites

- Python 3
- Postgres
- Node.js, NPM and Gulp
- [ChromeDriver](https://sites.google.com/a/chromium.org/chromedriver/downloads)

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
pip install -r requirements-test.txt
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
values for local development and test. For our deployments we are using Heroku and therefore any
variables needed for the application need to be set manually on Heroku.

```
SECRET_KEY=[whatever you like]
ENVIRONMENT=LOCAL_DEV
PUSH_ENABLED=FALSE
DATABASE_URL=postgresql://postgres@localhost:5432/rdcms
TEST_DATABASE_URL=postgresql://postgres@localhost:5432/rdcms_test
LOGIN_DISABLED=False
GITHUB_ACCESS_TOKEN=[generate one on Github]
RDU_GITHUB_URL=github.com/racedisparityaudit
STATIC_BUILD_DIR=[some directory on your machine]
FILE_SERVICE=S3
S3_UPLOAD_BUCKET_NAME=[make one on s3 and put name here]
S3_STATIC_SITE_BUCKET=[make one on s3 and put name here]
S3_REGION=eu-west-2
AWS_ACCESS_KEY_ID=[generate one in AWS]
AWS_SECRET_ACCESS_KEY=[generate one in AWS]
PUBLICATION_STATES=['APPROVED']
BUILD_SITE=True
ATTACHMENT_SCANNER_API_URL=https://beta.attachmentscanner.com/requests
ATTACHMENT_SCANNER_API_KEY=[ask someone who knows]
PUSH_SITE=False
DEPLOY_SITE=False
JSON_ENABLED=True
PGSSLMODE=allow
MAILGUN_SMTP_SERVER=smtp.mailgun.org
MAILGUN_SMTP_PORT=465
MAILGUN_SMTP_LOGIN=postmaster@devmail.ethnicity-facts-figures.service.gov.uk
MAILGUN_SMTP_PASSWORD=[ask someone who knows]
ACCOUNT_WHITELIST="['if your email is not a gov.uk one']"
SURVEY_ENABLED=False

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

#### User accounts

This application uses Flask Security for login, and has a basic User model but does not use
the Role model from that plugin.

To create your local user account

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


