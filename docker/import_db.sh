#!/bin/bash

./manage.py pull_prod_data --default_user_password="$DEFAULT_USER_PASSWORD"
./manage.py refresh_materialized_views
