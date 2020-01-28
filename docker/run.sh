#!/bin/bash

./manage.py db upgrade
./manage.py db migrate
./manage.py db upgrade

./manage.py server
