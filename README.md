![Build Status](https://circleci.com/gh/methods/rd_cms.svg?style=shield&circle-token=:circle-token)

:skull: *Work in progress* :skull:

# RD CMS

## Prerequisites

- Python 3

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
GIT_USER=[speak to Tom Ridd if you want to test against real remote repo]
GIT_PASSWORD=[speak to Tom Ridd - as above]
```

Remember do not commit sensitive data to the repo.

If we ever move of Heroku we'll find another way to generate a .env for production or use something else.

For CI variables are in circle.yml


## Run the tests

```
scripts/run_tests.sh
```

## Run the app

```
scripts/run.sh
```