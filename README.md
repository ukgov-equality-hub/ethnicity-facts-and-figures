[![Heroku CI Status](https://ci-badges.herokuapp.com/pipelines/84693d88-8bc1-4940-8f68-4111828a2278/master.svg)](https://dashboard.heroku.com/pipelines/84693d88-8bc1-4940-8f68-4111828a2278/tests)


:skull: *Work in progress* :skull:

# RD CMS

## Prerequisites

- Python 3 (version pinned in `runtime.txt`)
- Postgres (version 9.6)
- Node.js, NPM and Gulp (versions pinned in `package.json`)
- ChromeDriver

#### Bootstrap your local dev environment

After checking the repository out, make a virtualenv and activate it. We recommend using
`virtualenvwrapper`, installed to the system Python3, to simplify development.
```
pip install virtualenvwrapper
```

Add the below snippet to your .profile/.bash_profile/.zshrc (depending on what shell you use), where
`path_to_virtualenvwrapper.sh` is the absolute path to the system script (this can be found with
`which virtualenvwrapper.sh` and will be something like `/usr/local/bin/virtualenvwrapper.sh` or
`/Library/Frameworks/Python.framework/Versions/3.6/bin/virtualenvwrapper.sh`). Source your profile
again, either manually (`source <file>`) or by opening a new shell.
```
export WORKON_HOME=$HOME/.virtualenvs
source {path_to_virtualenvwrapper.sh}
```

You can now create the virtualenv and activate it. Note the flag -p python3 is only relevant if
python3 is not the default on your system.
```
mkvirtualenv -p python3 rd-cms
workon rd-cms
```

Install the Python server requirements:
```
pip install -r requirements-test.txt
```

Install the git hooks for enforcing formatting.
```
./scripts/install_hooks.sh
```

Install the Node.js requirements (for front end assets):
```
npm install
```

Then generate the assets using:
```
gulp make
```


#### Environment variables

We use python-dotenv to manage our app's configuration and secrets. Add a file called .env in the
root of the project containing the values below. This file should not be committed and is in
.gitignore. Only add values for local development and test. For our deployments we are using Heroku
and therefore any variables needed for the application need to be set manually on Heroku.
```
SECRET_KEY=[whatever you like]
ENVIRONMENT=LOCAL_DEV
PUSH_ENABLED=FALSE
DATABASE_URL=postgresql://postgres@localhost:5432/rdcms
TEST_DATABASE_URL=postgresql://postgres@localhost:5432/rdcms_test
LOGIN_DISABLED=False
GITHUB_ACCESS_TOKEN=[generate one on Github]
GITHUB_URL=github.com/racedisparityaudit
STATIC_BUILD_DIR=[some directory on your machine]
FILE_SERVICE=S3
S3_UPLOAD_BUCKET_NAME=[make one on s3 and put name here]
S3_STATIC_SITE_BUCKET=[make one on s3 and put name here]
S3_REGION=eu-west-2
AWS_ACCESS_KEY_ID=[generate one in AWS]
AWS_SECRET_ACCESS_KEY=[generate one in AWS]
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
PROD_DB_URL=[set this if you want to run the data migration from production]
PROD_UPLOAD_BUCKET_NAME=[set this if you want to run the data migration from production]

```

**Remember**: do not commit sensitive data to the repo.

If we ever move off Heroku we'll find another way to generate a .env for production or use something
else.

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

#### Populate local database

After creating and migrating the basic database structure, you are ready to populate it with the
latest data from production. You will need to define `S3_UPLOAD_BUCKET_NAME`, `PROD_DB_URL` and
`PROD_UPLOAD_BUCKET_NAME` in your `.env` file.

`S3_UPLOAD_BUCKET_NAME` should be set to something like `rd-cms-dev-<name>-uploads` and created
manually in the S3 console at https://s3.console.aws.amazon.com/s3/home?region=eu-west-2.

`PROD_DB_URL` can be found with these steps:
1) Visit https://dashboard.heroku.com/apps/rd-cms/resources
2) Click on one of the Postgres resources.
3) Go to the 'Credentials' tab.
4) Expand the default credential set.
5) Click 'Copy' beneath the URI.

`PROD_UPLOAD_BUCKET_NAME` can be found at https://s3.console.aws.amazon.com/s3/home?region=eu-west-2

With these set, run the following management tasks:
```
./manage.py pull_prod_data
./manage.py refresh_materialized_views
```

#### Run the tests

```
scripts/run_tests.sh
```

#### Run the app

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
./manage.py create_local_user_account --email someemail@somedept.gov.uk --user-type RDU_USER
```

This will print out a url for you to vist to finish creating the account.

The command can be used to create both DEV_USER and DEPT_USER types. The latter is useful for
testing locally.

e.g.
```
./manage.py create_local_user_account --email someemail@somedept.gov.uk --user-type DEPT_USER
```

Then use url that is output to complete process.


In the application account creation is via the users page that is under /admin.

Accounts can only be made for gov.uk email addresses. To setup an account for a non gov.uk email,
you need to whitelist the specific email. To do that add an environment variable:

```
ACCOUNT_WHITELIST="['someperson@gmail.com']"
```

Note the quoting of the list and the list item above.

## The static site

To make hosting simpler, and more secure, it is possible to generate a completely static copy of the
website suitable for hosting on S3 or similar.

### Starting the build process

The static site build process can be run manually via the following script:

```bash
./manage.py force_build_static_site
```

In order to initiate builds automatically in response to user actions in the CMS (eg publishing a new page), a `build` table acts as a basic job queue. New rows are added to this table whenever a build is requested.

To actually run these requested builds, the following script needs to be run at regular intervals:

```bash
./manage.py build_static_site
```

This will check for any requested builds in the `build` table, and if there is one, setting that row’s `status` to `STARTED`. When the job is finished, the status will be updated to `DONE`, and a timestamp set in the `succeeded_at` column. If the build fails for any reason, the `status` will set to `FAILED`, a timestamp set in the `failed_at` column, and a full stack trace saved to the `failure_reason` column.

If there is more than one requested build in the the table, then only the most-recently added one will be run, and the status of the other rows set to `SUPERSEDED`.

As well as builds being requested whenever a page is published, they can also be requested manually via the following script. This can also be run as a post-deploy step.

```bash
./manage.py request_static_build
```

### Running the build

The build process consists of the following steps:

#### 1. The website is saved to the local filesystem

The website, include all HTML files, images, CSS, javascript and CSV files, is saved as static files within a folder with a name based on the current timestamp. This folder will be generated at the location specified by the `STATIC_BUILD_DIR` environment variable (note: this must be a full filesystem path, eg `/app/site`).

#### 2. The website is pushed to a remote Git repo (optional)

This step acts as a kind of backup, and to provide a full audit history of every change to the website.

To enable this to work, you must set the following environment variables:

* `GITHUB_URL`: This should be the name of the Git host and the organisation (or user), eg `github.com/myusername`, but not the actual repo name
* `HTML_CONTENT_REPO`: This should be the name of the actual Git repo you'd like to save the content to, eg `static-website`
* `GITHUB_ACCESS_TOKEN`: This should be an OAuth access token which has pull and push permission to the repository
* `PUSH_SITE`: This should be set to `True`

#### 3. The website is pushed to a remote Amazon S3 bucket

This step enables the static files to be served by S3 as an actual website (either directly via S3 static hosting), or via Cloudfront using S3 as a source.

The following settings will need to be configured:

* `S3_REGION`: The name of the S3 region, eg `eu-west-2`
* `S3_STATIC_SITE_BUCKET`: The bucket name
* `AWS_ACCESS_KEY_ID`: An AWS access key with permissions to access the S3 bucket
* `AWS_SECRET_ACCESS_KEY`: An AWS secret access key for the above access key
* `DEPLOY_SITE`: This should be set to `True`

## Deployment
