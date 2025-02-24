import pathlib
from flask import abort, current_app, flash, redirect, render_template, request, url_for
from flask_login import login_required, current_user
from flask_httpauth import HTTPTokenAuth
from sqlalchemy import desc, func
from sqlalchemy.orm.exc import NoResultFound
from datetime import date, datetime, timedelta

from application import db
from application.api import api_blueprint
from application.admin.forms import AddUserForm, SiteBuildSearchForm, DataSourceSearchForm, DataSourceMergeForm
from application.auth.models import (
    User,
    TypeOfUser,
    CAPABILITIES,
    MANAGE_SYSTEM,
    MANAGE_USERS,
    MANAGE_DATA_SOURCES,
    MANAGE_TOPICS,
)
from application.cms.forms import SelectMultipleDataSourcesForm
from application.cms.models import user_measure, DataSource, Topic, Subtopic
from application.sitebuilder.models import Build, BuildStatus
from application.cms.page_service import page_service
from application.utils import create_and_send_activation_email, user_can
from application.cms.utils import get_form_errors


auth = HTTPTokenAuth(scheme='Bearer')

@auth.verify_token
def verify_token(token):
    if current_app.config.get('EFF_API_TOKEN') is None:
        return False

    return token == current_app.config.get('EFF_API_TOKEN')


@api_blueprint.route("/foo")
@auth.login_required
def index():
    return "hello"
