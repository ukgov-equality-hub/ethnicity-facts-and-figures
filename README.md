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

Add some environment variables to a file called environment.sh in the root of the project containing the following:
This file should not be committed and is in .gitignore.

```
export SECRET_KEY=[generate one using os.urandom(24) and copy output here]
export RD_CONTENT_REPO=/somepath
export GIT_USER=[speak to Tom Ridd]
export GIT_PASSWORD=[speak to Tom Ridd]
```

## Run the tests

```
scripts/run_tests.sh
```

## Run the app

```
scripts/run.sh
```