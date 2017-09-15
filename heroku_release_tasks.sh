#!/usr/bin/env bash
python manage.py db upgrade
npm install
gulp sass scripts