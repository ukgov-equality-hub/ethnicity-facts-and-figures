#!/usr/bin/env bash
python manage.py db upgrade
npm install
python manage.py request_build
