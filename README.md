![Build Status](https://circleci.com/gh/methods/rd_cms.svg?style=shield&circle-token=0ae822a0f946160095ed880b97c5c012de899155)

:skull: *Work in progress* :skull:

# RD CMS

## Prerequisites

- Python 3
- Postgres (user account database)

#### Bootstrap your local dev environment

After checking out make a virtualenv and activate it.

Use mkvirtualenv to make your life easier. Adjust path after -p flag if necessary.

```
pip install virtualenvwrapper
```

Add this to your .profile, or .zshrc (depending on what shell you use)

```
export WORKON_HOME=$HOME/.virtualenvs
source /usr/local/bin/virtualenvwrapper.sh
```
Then you can create the virtualenv and activate it


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
RD_CONTENT_REPO=/somepath
GITHUB_ACCESS_TOKEN=[speak to Tom Ridd if you want to test against real remote repo]
REPO_BRANCH=[for dev make your own branch on github]
ENVIRONMENT=dev
DATABASE_URL=postgresql://localhost/rdcms
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

Note that to make your life more pleasant during development set the following value
in config.DevConfig 

```
LOGIN_DISABLED = True
```

Then you won't have to login all the time for local dev. Remove that when you want to
make sure all is well.


```
./manage.py create_user --email youremail@somewhere.com --password somepassword
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

## Deployment


