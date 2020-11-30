#! /usr/bin/env python
import ast

import os
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

from flask_migrate import Migrate, MigrateCommand, upgrade
from flask_script import Manager, Server
from flask_security import SQLAlchemyUserDatastore
from flask_security.utils import hash_password
from sqlalchemy import desc, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound

from application import db
from application.admin.forms import AddUserForm
from application.auth.models import User, TypeOfUser, CAPABILITIES
from application.cms.classification_service import classification_service
from application.cms.models import MeasureVersion, Measure, Subtopic, Topic
from application.config import Config, DevConfig
from application.data.ethnicity_classification_synchroniser import EthnicityClassificationSynchroniser
from application.factory import create_app
from application.redirects.models import Redirect
from application.sitebuilder.build import build_and_upload_error_pages
from application.sitebuilder.exceptions import StalledBuildException
from application.sitebuilder.models import Build, BuildStatus
from application.utils import create_and_send_activation_email, send_email, TimedExecution

if os.environ.get("ENVIRONMENT", "DEVELOPMENT").lower().startswith("dev"):
    app = create_app(DevConfig)
else:
    app = create_app(Config)

manager = Manager(app)
# manager.add_command("server", Server())
if os.environ.get("FLASK_ENV") == "docker":
    manager.add_command("server", Server(host="0.0.0.0", port=5000))
else:
    manager.add_command("server", Server())


migrate = Migrate(app, db)
manager.add_command("db", MigrateCommand)

# Note not using Flask-Security Role model
user_datastore = SQLAlchemyUserDatastore(db, User, None)


@manager.option("--email", dest="email")
@manager.option("--user-type", dest="user_type", default="RDU_USER")
def create_local_user_account(email, user_type):
    form = AddUserForm(email=email, user_type=user_type)
    if form.email.validate(form):
        user = user_datastore.find_user(email=email)
        if user:
            print("User %s already exists" % email)
        else:
            user = User(email=email)
            if user_type == TypeOfUser.DEPT_USER.name:
                user.user_type = TypeOfUser.DEPT_USER
                user.capabilities = CAPABILITIES[TypeOfUser.DEPT_USER]
            elif user_type == TypeOfUser.RDU_USER.name:
                user.user_type = TypeOfUser.RDU_USER
                user.capabilities = CAPABILITIES[TypeOfUser.RDU_USER]
            elif user_type == TypeOfUser.DEV_USER.name:
                user.user_type = TypeOfUser.DEV_USER
                user.capabilities = CAPABILITIES[TypeOfUser.DEV_USER]
            else:
                print("Only DEPT_USER, RDU_USER or DEV_USER user types can be created with this command")
                sys.exit(-1)

            db.session.add(user)
            db.session.commit()
            confirmation_url = create_and_send_activation_email(email, app, devmode=True)
            print("User account created. To complete process go to %s" % confirmation_url)
    else:
        print("email is not a gov.uk email address and has not been whitelisted")


@manager.command
def build_static_site():
    if app.config["BUILD_SITE"]:
        from application.sitebuilder.build_service import build_site

        build_site(app)
    else:
        print("Build is disabled at the moment. Set BUILD_SITE to true to enable")
        print("change 1")


@manager.command
def request_static_build():
    if app.config["BUILD_SITE"]:
        from application.sitebuilder.build_service import request_build

        request_build()
        print("A build has been requested. It could be up to ten minutes before the request is processed")
    else:
        print("Build is disabled at the moment. Set BUILD_SITE to true to enable")


@manager.command
def force_build_static_site():
    if app.config["BUILD_SITE"]:
        from application.sitebuilder.build_service import request_build
        from application.sitebuilder.build_service import build_site

        request_build()
        print("An immediate build has been requested")
        build_site(app)
    else:
        print("Build is disabled at the moment. Set BUILD_SITE to true to enable")


# Run this command with the parameter default_user_password to set up additional default user accounts
# e.g. ./manage.py pull_prod_data --default_user_password=P@55w0rd
@manager.command
def pull_prod_data(default_user_password=None):
    environment = os.environ.get("ENVIRONMENT", "PRODUCTION")
    if environment.upper() == "PRODUCTION":
        print("It looks like you are running this in production or some unknown environment.")
        print("Do not run this command in this environment as it deletes data")
        sys.exit(-1)

    prod_db = os.environ.get("PROD_DB_URL")
    if prod_db is None:
        print("You need to set an environment variable 'PROD_DB_URL' with value of production postgres url")
        sys.exit(-1)

    import subprocess
    import shlex

    out_file = "/tmp/data.dump"
    command = "scripts/get_data.sh %s %s" % (prod_db, out_file)

    with TimedExecution("Pull prod data"):
        subprocess.call(shlex.split(command))

    # Drop all of the existing tables before doing a pg_restore from scratch
    db.session.execute("DROP SCHEMA public CASCADE;")
    db.session.execute("CREATE SCHEMA public;")
    db.session.commit()

    command = "pg_restore --no-owner -d %s %s" % (app.config["SQLALCHEMY_DATABASE_URI"], out_file)

    subprocess.call(shlex.split(command))

    print("Anonymising users...")
    db.session.execute(
        """
        UPDATE users
        SET email = ROUND(RANDOM() * 1000000000000)::TEXT || '@anon.invalid',
            password = NULL,
            active = FALSE
        """
    )
    db.session.commit()

    import contextlib

    with contextlib.suppress(FileNotFoundError):
        os.remove(out_file)

    print("Loaded data to", app.config["SQLALCHEMY_DATABASE_URI"])

    if default_user_password:
        print("Creating default users...")
        _create_default_users_with_password(default_user_password)

    print("Upgrading database from local migrations...")
    upgrade()

    print("Refreshing materialized views...")
    drop_and_create_materialized_views()

    if os.environ.get("PROD_UPLOAD_BUCKET_NAME"):
        #  Copy upload files from production to the upload bucket for the current environment
        import boto3

        s3 = boto3.resource("s3")
        source = s3.Bucket(os.environ.get("PROD_UPLOAD_BUCKET_NAME"))
        destination = s3.Bucket(os.environ.get("S3_UPLOAD_BUCKET_NAME"))

        def download_key(source_bucket_name, key_name):
            print(f"  Copying file {key_name}")
            destination.copy(CopySource={"Bucket": source_bucket_name, "Key": key_name}, Key=key_name)

        with TimedExecution(description=f"Copy upload files from bucket {source.name}"):
            # Clear out destination folder
            destination.objects.all().delete()

            pool = ThreadPoolExecutor(max_workers=32)
            keys = [key.key for key in source.objects.all()]

            for _ in pool.map(download_key, [source.name] * len(keys), keys):
                # Iterating over the map causes it to consume all the tasks, i.e. actually do the copying.
                pass

            pool.shutdown(wait=True)


def _create_default_users_with_password(password_for_default_users):
    environment = os.environ.get("ENVIRONMENT", "PRODUCTION")
    if environment.upper() == "PRODUCTION":
        print("No default users in production!")
        sys.exit(-1)
    if not password_for_default_users:
        print("Default users need a password!")
        sys.exit(-1)

    default_accounts = {
        "admin@eff.gov.uk": TypeOfUser.ADMIN_USER,
        "dept@eff.gov.uk": TypeOfUser.DEPT_USER,
        "dev@eff.gov.uk": TypeOfUser.DEV_USER,
        "rdu@eff.gov.uk": TypeOfUser.RDU_USER,
    }

    whitelisted_accounts = ast.literal_eval(os.environ.get("ACCOUNT_WHITELIST", "{}"))
    for email in whitelisted_accounts:
        default_accounts[email] = getattr(TypeOfUser, whitelisted_accounts[email])

    for email, user_type in default_accounts.items():
        _create_user_with_password(email, user_type, password_for_default_users)


def _create_user_with_password(email, user_type, password):
    user = User(email=email)
    user.user_type = user_type
    user.capabilities = CAPABILITIES[user_type]
    user.active = True
    user.password = hash_password(password)
    user.confirmed_at = datetime.utcnow()

    db.session.add(user)
    db.session.commit()


@manager.command
def delete_old_builds():
    from datetime import date

    a_week_ago = date.today() - timedelta(days=7)
    out = db.session.query(Build).filter(Build.created_at < a_week_ago).delete()
    db.session.commit()
    print("Deleted %d old builds" % out)


@manager.command
def report_broken_build():
    from datetime import date

    yesterday = date.today() - timedelta(days=1)
    failed = (
        db.session.query(Build)
        .filter(Build.status == "FAILED", Build.created_at > yesterday)
        .order_by(desc(Build.created_at))
        .first()
    )
    if failed:
        message = "Build failure in application %s. Build id %s created at %s<br><br>%s" % (
            app.config["ENVIRONMENT"],
            failed.id,
            failed.created_at,
            failed.failure_reason,
        )
        message += (
            f"Acknowledge with:<br>"
            f"<strong><code>"
            f'heroku run "./manage.py acknowledge_build_issue --build_id {failed.id}" -a APP_NAME'
            f"</code></strong>"
        )
        subject = "Build failure in application %s on %s" % (app.config["ENVIRONMENT"], date.today())
        recipients = db.session.query(User).filter(User.user_type == TypeOfUser.DEV_USER.name).all()
        for r in recipients:
            send_email(app.config["RDU_EMAIL"], r.email, message, subject)
        print(message)
    else:
        print("No failed builds today")


@manager.command
def report_stalled_build():
    from datetime import date

    half_an_hour_ago = datetime.now() - timedelta(minutes=30)
    stalled = (
        db.session.query(Build)
        .filter(
            Build.status == BuildStatus.STARTED,
            func.DATE(Build.created_at) == date.today(),
            Build.created_at <= half_an_hour_ago,
        )
        .order_by(desc(Build.created_at))
        .first()
    )

    if stalled:
        message = (
            f"Build stalled for more than 30 minutes in application {app.config['ENVIRONMENT']}.<br>"
            f"Build id {stalled.id} created at {stalled.created_at}<br><br>"
            f"Acknowledge with:<br>"
            f"<strong><code>"
            f'heroku run "./manage.py acknowledge_build_issue --build_id {stalled.id}" -a APP_NAME'
            f"</code></strong>"
        )
        subject = "Build stalled in application %s on %s" % (app.config["ENVIRONMENT"], date.today())
        recipients = db.session.query(User).filter(User.user_type == TypeOfUser.DEV_USER.name).all()
        for r in recipients:
            send_email(app.config["RDU_EMAIL"], r.email, message, subject)
        print(message)

        # Do a little dance to send this exception to Sentry, if configured, otherwise just let it bubble up.
        try:
            raise StalledBuildException(
                f"Build {stalled.id} has stalled. Acknowledge with:\n\n"
                f'heroku run "./manage.py acknowledge_build_issue --build_id {stalled.id}" -a APP_NAME'
            )

        except StalledBuildException as e:
            if "sentry" in app.extensions:
                app.extensions["sentry"].captureException()
            else:
                raise e

    else:
        print("No stalled builds")


@manager.command
def refresh_materialized_views():
    from application.dashboard.view_sql import refresh_all_dashboard_helper_views

    db.session.execute(refresh_all_dashboard_helper_views)
    db.session.commit()
    print("Refreshed data for MATERIALIZED VIEWS")


@manager.command
def drop_and_create_materialized_views():
    from application.dashboard.view_sql import (
        drop_all_dashboard_helper_views,
        latest_published_measure_versions_view,
        latest_published_measure_versions_by_geography_view,
        ethnic_groups_by_dimension_view,
        classifications_by_dimension,
    )

    db.session.execute(drop_all_dashboard_helper_views)
    db.session.execute(latest_published_measure_versions_view)
    db.session.execute(latest_published_measure_versions_by_geography_view)
    db.session.execute(ethnic_groups_by_dimension_view)
    db.session.execute(classifications_by_dimension)
    db.session.commit()
    print("Drop and create MATERIALIZED VIEWS done")


# Build stalled or failed emails continue until status is updated using
# this command.
@manager.option("--build_id", dest="build_id")
def acknowledge_build_issue(build_id):
    try:
        build = db.session.query(Build).filter(Build.id == build_id).one()
        build.status = BuildStatus.SUPERSEDED
        db.session.add(build)
        db.session.commit()
        print("Build id", build_id, "set to superseded")
    except NoResultFound:
        print("No build found with id", build_id)


@manager.command
def run_data_migration(migration=None):
    data_migrations_folder = os.path.join("scripts", "data_migrations")

    if migration is None:
        migrations = os.listdir(data_migrations_folder)
        print("The following data migrationas are available:")
        for migration in migrations:
            print(f' * {os.path.basename(migration).replace(".sql", "")}')

    else:
        migration_filename = os.path.join(data_migrations_folder, f"{migration}.sql")
        try:
            with open(migration_filename, "r") as migration_file:
                migration_sql = migration_file.read()

        except Exception as e:
            print(f"Unable to load data migration from {migration}: {e}")

        else:
            try:
                db.session.execute(migration_sql)
                db.session.commit()
            except IntegrityError as e:
                print(f"Unable to apply data migration: {e}")
            else:
                print(f"Applied data migration: {migration}")


# Add a redirect rule
@manager.option("--from_uri", dest="from_uri")
@manager.option("--to_uri", dest="to_uri")
def add_redirect_rule(from_uri, to_uri):
    created = datetime.utcnow()
    redirect = Redirect(created=created, from_uri=from_uri, to_uri=to_uri)

    db.session.add(redirect)
    db.session.commit()
    print("Redirect from", from_uri, "to", to_uri, "added")


# Remove a redirect rule
@manager.option("--from_uri", dest="from_uri")
def delete_redirect_rule(from_uri):
    try:
        redirect = Redirect.query.filter_by(from_uri=from_uri).one()
        db.session.delete(redirect)
        db.session.commit()
        print("Redirect rule with from_uri", from_uri, "deleted")
    except NoResultFound:
        print("Could not delete a redirect rule with from_uri ", from_uri)


@manager.command
def refresh_error_pages():
    build_and_upload_error_pages(app)


@manager.command
def synchronise_classifications():
    synchroniser = EthnicityClassificationSynchroniser(classification_service=classification_service)
    synchroniser.synchronise_classifications(app.classification_finder.get_classification_collection())


# TODO: START Delete me after migrating uploads
def get_latest_versions_for_all_measures():
    max_measure_versions = (
        MeasureVersion.query.with_entities(
            MeasureVersion.measure_id, func.max(MeasureVersion.version).label("max_version")
        )
        .group_by(MeasureVersion.measure_id)
        .cte("max_measure_versions")
    )

    latest_measure_versions = MeasureVersion.query.filter(
        MeasureVersion.version == max_measure_versions.c.max_version,
        MeasureVersion.measure_id == max_measure_versions.c.measure_id,
    ).all()

    return latest_measure_versions


@manager.command
def copy_guid_uploads_to_measure_id_uploads():
    latest_measure_versions = get_latest_versions_for_all_measures()

    for latest_measure_version in latest_measure_versions:
        for current_key in app.file_service.system.list_paths(latest_measure_version.guid):
            path_fragments = current_key.split("/")
            path_fragments[0] = str(latest_measure_version.measure.id)
            new_key = "/".join(path_fragments)
            print(f"Copying '{current_key}' to '{new_key}'")
            app.file_service.system.copy_file(current_key, new_key)


@manager.command
def delete_guid_based_uploads():
    latest_measure_versions = get_latest_versions_for_all_measures()

    for latest_measure_version in latest_measure_versions:
        for key_using_guid in app.file_service.system.list_paths(latest_measure_version.guid):
            print(f"Deleting '{key_using_guid}'")
            app.file_service.system.delete(key_using_guid)


@manager.command
def delete_all_measures_except_two_per_subtopic():
    """Delete a large proportion of records from our database by dropping all except the first two measures in each
    subtopic, and all of the records associated with those dropped measures. This is used to keep our review app
    databases under 10k rows, which is (as of 2019-04-01) the limit on Heroku."""
    from application.utils import TimedExecution
    from application.cms.models import (
        Subtopic,
        Measure,
        DataSource,
        DataSourceInMeasureVersion,
        MeasureVersion,
        Dimension,
        Chart,
        Table,
    )

    environment = os.environ.get("ENVIRONMENT", "PRODUCTION")
    if environment.upper().startswith("PROD"):
        print("It looks like you are running this in production or some unknown environment.")
        print("Do not run this command in this environment as it deletes data")
        sys.exit(-1)

    with TimedExecution("Delete 3rd measure and onward in each subtopic"):
        try:
            measure_ids_to_save = []

            subtopics = Subtopic.query.all()
            for subtopic in subtopics:
                measure_ids_to_save.extend(m.id for m in subtopic.measures[:2])

            measure_version_ids_to_delete = (
                db.session.query(MeasureVersion.id).filter(~MeasureVersion.measure_id.in_(measure_ids_to_save)).all()
            )

            data_source_ids_to_delete = (
                db.session.query(DataSourceInMeasureVersion.data_source_id)
                .filter(DataSourceInMeasureVersion.measure_version_id.in_(measure_version_ids_to_delete))
                .all()
            )

            dimension_guids_to_delete = (
                db.session.query(Dimension.guid)
                .filter(Dimension.measure_version_id.in_(measure_version_ids_to_delete))
                .all()
            )
            chart_ids_to_delete = (
                db.session.query(Dimension.chart_id)
                .filter(Dimension.measure_version_id.in_(measure_version_ids_to_delete))
                .all()
            )
            table_ids_to_delete = (
                db.session.query(Dimension.table_id)
                .filter(Dimension.measure_version_id.in_(measure_version_ids_to_delete))
                .all()
            )

            db.session.query(DataSourceInMeasureVersion).filter(
                DataSourceInMeasureVersion.data_source_id.in_(data_source_ids_to_delete)
            ).delete(synchronize_session=False)
            db.session.query(DataSource).filter(DataSource.id.in_(data_source_ids_to_delete)).delete(
                synchronize_session=False
            )
            db.session.query(Dimension).filter(Dimension.guid.in_(dimension_guids_to_delete)).delete(
                synchronize_session=False
            )
            db.session.query(Chart).filter(Chart.id.in_(chart_ids_to_delete)).delete(synchronize_session=False)
            db.session.query(Table).filter(Table.id.in_(table_ids_to_delete)).delete(synchronize_session=False)
            db.session.query(Measure).filter(~Measure.id.in_(measure_ids_to_save)).delete(synchronize_session=False)

        except Exception as e:
            print(e)

    db.session.commit()


@manager.option("--topic_slug", dest="topic_slug")
@manager.option("--subtopic_slug", dest="subtopic_slug")
@manager.option("--measure_slug", dest="measure_slug")
@manager.option("--version", dest="version")
def unpublish_measure_version(topic_slug, subtopic_slug, measure_slug, version):
    measure_version: MeasureVersion = MeasureVersion.query.filter(
        MeasureVersion.measure.has(Measure.subtopics.any(Subtopic.topic.has(Topic.slug == topic_slug))),
        MeasureVersion.measure.has(Measure.subtopics.any(Subtopic.slug == subtopic_slug)),
        MeasureVersion.measure.has(Measure.slug == measure_slug),
        MeasureVersion.version == version,
    ).one()

    measure_version.status = "DRAFT"
    measure_version.published_at = None
    measure_version.published_by = None

    db.session.commit()

    print(
        f"Measure version #{measure_version.id} "
        f"(topic:{topic_slug}, subtopic:{subtopic_slug}, measure:{measure_slug}, version:{version}) "
        f"has been returned to 'DRAFT' state.\n\n"
        f"Remember to delete objects in S3, if applicable."
    )


# Copy csv files from static to data lake bucket
@manager.command
def copy_data_to_lake():
    import boto3
    import os.path

    s3 = boto3.resource("s3")

    source_bucket = s3.Bucket(os.environ.get("S3_STATIC_SITE_BUCKET"))
    destination_bucket = s3.Bucket(os.environ.get("S3_EFF_LAKE_BUCKET"))
    filenames = []

    for obj in source_bucket.objects.all():
        if obj.key[-1] == "/":
            continue
        elif obj.key[-3:] == "csv" and obj.key.find("latest/downloads") != -1:

            copy_source = {"Bucket": os.environ.get("S3_STATIC_SITE_BUCKET"), "Key": obj.key}

            paths = obj.key.split("/")

            filename = paths[5].replace(".csv", "").replace("-", "_")
            if filename.startswith("by_ethnicity"):
                filename = paths[1] + paths[2] + "_" + filename

            filename = filename[0:220:] if len(filename) > 220 else filename

            if filename not in filenames:
                filenames.append(filename)
            else:
                filename = paths[0].replace("-", "_") + "_" + filename
                filename = filename[0:100:] + filename[-120:] if len(filename) > 220 else filename
                if filename not in filenames:
                    filenames.append(filename)
                else:
                    continue

            filename = filename.replace("-", "_")

            target = "public/eff/%s/%s.csv" % (filename, filename)

            destination_bucket.copy(copy_source, target)
            print(target)


if __name__ == "__main__":
    manager.run()
