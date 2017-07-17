![Build Status](https://circleci.com/gh/methods/rd_cms.svg?style=shield&circle-token=0ae822a0f946160095ed880b97c5c012de899155)

:skull: *Work in progress* :skull:

# RD CMS

## Prerequisites

- Python 3
- Postgres

#### Bootstrap your local dev environment

After checking out make a virtualenv and activate it.

Use mkvirtualenv to make your life easier.

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

Install the requirements

```
pip install -r test_requirements.txt
```

#### Environment variables

We're using python-dotenv at the moment. Add a file called .env in the root of the project 
containing the values below. This file should not be committed and is in .gitignore. Only add
values for local development and test. For our deployments we are using Heroku and therefor any
variables needed for the application need to be set manually on Heroku.

```
SECRET_KEY=[for local dev and test doesn't matter]
GITHUB_ACCESS_TOKEN=[speak to Tom Ridd if you want to test against real remote repo]
ENVIRONMENT=dev
DATABASE_URL=postgresql://localhost/rdcms
BUILD_DIR=/somepath/onyourmachine # this only matters if you want to test static build
RDU_GITHUB_ACCESS_TOKEN=[ask a grown up]
RDU_GITHUB_URL=github.com/racedisparityaudit
BETA_PUBLICATION_STATES=['DEPARTMENT_REVIEW', 'ACCEPTED']
FILE_SERVICE=LOCAL
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
./manage.py create_internal_user --email someemail --password somepassword
```

You can also create departmental users

```
./manage.py create_departmental_user --email someemail --password somepassword
```


#### Run the tests

```
scripts/run_tests.sh
```

#### Run the app

If you wish to use the app without affecting the master content repo branch please create a remote branch
 and check it out on your local machine.

To run the app
```
scripts/run.sh
```

## The static site

This is also very much a :skull: *Work in progress* :skull:

This application has what will become the static public site in a directory that is, funnily
enough called static_site. You can find it at application/static_site. It will contain
all the templates and static assets to build the final output.

At the moment, once logged in you can view the site at /site.

The src SASS and js for these pages is in the src directory in the root of this project.

To work on the public front end pages you'll need some node build tools. In other words
install node now.

Install gulp. I needed to install this globally.

```
npm install -g gulp
```

Then I could install dependencies in package.json

```
npm install
```

Then you can run:

```
gulp watch
```

This will watch for changes in src sass or js files and put the resulting output into
application/static_site/static directory.



## Deployment


