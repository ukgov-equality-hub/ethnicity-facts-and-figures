#!/usr/bin/env bash
python manage.py db upgrade
npm install
python manage.py force_build_static_site
