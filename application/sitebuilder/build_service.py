import atexit
import traceback
import uuid
from contextlib import contextmanager
from datetime import datetime

import boto3
import shutil

import os
from sqlalchemy import desc
from sqlalchemy.orm import sessionmaker

from application import db
from application.cms.file_service import S3FileSystem
from application.sitebuilder.models import Build, BuildStatus
from application.sitebuilder.build import do_it, get_static_dir

YEAR_IN_SECONDS = 60 * 60 * 24 * 365
HOUR_IN_SECONDS = 60 * 60
FIFTEEN_MINUTES_IN_SECONDS = 60 * 15


class BuildException(Exception):
    def __init__(self, original_exception):
        self.original_exception = original_exception


def request_build():
    build = Build()
    build.id = str(uuid.uuid4())
    db.session.add(build)
    db.session.commit()
    return build


def _any_build_has_been_started(session):
    started_builds = session.query(Build).filter(Build.status == BuildStatus.STARTED).all()

    return True if started_builds else False


def _retrieve_and_start_latest_pending_build(session):
    builds = (
        session.query(Build)
        .filter(Build.status == BuildStatus.PENDING)
        .order_by(desc(Build.created_at))
        .with_for_update()
        .all()
    )

    if not builds:
        return None

    target_build = builds[0]
    target_build.status = BuildStatus.STARTED
    session.add(target_build)

    superseded_builds = builds[1:]
    for superseded_build in superseded_builds:
        superseded_build.status = BuildStatus.SUPERSEDED
        session.add(superseded_build)

    session.commit()

    return target_build


def build_site(app):
    def print_stacktrace():
        traceback.print_stack()

    atexit.register(print_stacktrace)

    Session = sessionmaker(db.engine)
    with make_session_scope(Session) as session:
        if _any_build_has_been_started(session):
            print("An existing build is in progress; will not start a concurrent build")
            return

        build = _retrieve_and_start_latest_pending_build(session)
        if not build:
            print("No pending builds at", datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))
            return

        print("DEBUG _build_site(): Starting build...")
        _start_build(app, build, session)
        print("DEBUG _build_site(): Finished build.")


def s3_deployer(app, build_dir, measure_versions_to_delete=[]):
    _delete_files_not_needed_for_deploy(build_dir)

    site_bucket_name = app.config["S3_STATIC_SITE_BUCKET"]
    s3 = S3FileSystem(site_bucket_name, region=app.config["S3_REGION"])
    resource = boto3.resource("s3")
    bucket = resource.Bucket(site_bucket_name)

    for measure_version in measure_versions_to_delete:
        version = (
            "latest" if measure_version == measure_version.measure.latest_published_version else measure_version.version
        )

        topic_slug = measure_version.measure.subtopic.topic.slug
        subtopic_slug = measure_version.measure.subtopic.slug
        prefix = f"{topic_slug}/{subtopic_slug}/{measure_version.measure.slug}/{version}"
        to_delete = list(bucket.objects.filter(Prefix=prefix))

        for d in to_delete:
            print("Deleting: " + d.key)
            resource.Object(bucket.name, key=d.key).delete()

    # Ensure static assets (css, JavaScripts, etc) are uploaded before the rest of the site
    _upload_dir_to_s3(build_dir, s3, specific_subdirectory=get_static_dir())

    # Upload the whole site now the updated static assets are in place
    _upload_dir_to_s3(build_dir, s3)


def _upload_dir_to_s3(source_dir, s3, specific_subdirectory=None):
    target_dir = os.path.join(source_dir, specific_subdirectory) if specific_subdirectory else source_dir

    for root, dirs, files in os.walk(target_dir):
        for file_ in files:
            file_path = os.path.join(root, file_)

            # this is temp hack to work around that static site on s3 not
            # actually enabled for hosting static site and therefore
            # index files in sub directories do not work.
            # therefore use directory name as bucket key and index file contents
            # as bucket content
            bucket_key = file_path.replace(source_dir + os.path.sep, "")
            bucket_key = bucket_key.replace("/index.html", "")

            print("Uploading: " + bucket_key)

            if _is_versioned_asset(file_):
                s3.write(file_path, bucket_key, max_age_seconds=YEAR_IN_SECONDS, strict=False)
            elif _measure_related(file_):
                s3.write(file_path, bucket_key, max_age_seconds=FIFTEEN_MINUTES_IN_SECONDS, strict=False)
            else:
                s3.write(file_path, bucket_key, max_age_seconds=HOUR_IN_SECONDS, strict=False)


def _delete_files_not_needed_for_deploy(build_dir):
    to_delete = [".git", "README.md", ".gitignore"]
    for file in to_delete:
        path = os.path.join(build_dir, file)
        if os.path.isdir(path):
            shutil.rmtree(path)
        elif os.path.isfile(path):
            os.remove(path)


def _start_build(app, build, session):
    build_exception = None
    try:
        print("DEBUG _start_build(): Refreshing materialized views...")
        from manage import refresh_materialized_views

        refresh_materialized_views()
        print("DEBUG _start_build(): Doing it...")
        do_it(app, build)
        print("DEBUG _start_build(): Done it!")

        build.status = BuildStatus.DONE
        build.succeeded_at = datetime.utcnow()

    except Exception as e:
        print("DEBUG _start_build(): Exception: Build failed...")
        build.status = BuildStatus.FAILED
        build.failed_at = datetime.utcnow()
        print("DEBUG _start_build(): Formatting exception...")

        build.failure_reason = traceback.format_exc()
        build_exception = e

    finally:
        print("DEBUG _start_build(): Adding build to session...")

        session.add(build)
        if build_exception:
            raise BuildException(build_exception)


def _is_versioned_asset(file):
    import re

    match = re.search(r"(application|all|charts)-(\w+).(css|js)$", file)
    if match:
        return match.group(1) in ["application", "all", "charts"]
    return False


def _measure_related(file):
    return file.split(".")[-1] in ["html", "json", "csv"]


@contextmanager
def make_session_scope(Session):
    session = Session()
    session.expire_on_commit = False
    try:
        print("DEBUG make_session_scope(): Yielding session...")
        yield session
        print("DEBUG make_session_scope(): Committing session[1]...")
        session.commit()
    except BuildException as e:
        print("DEBUG make_session_scope(): BuildException: Committing session[2]...")
        session.commit()
        raise e.original_exception
    except Exception as e:
        print("DEBUG make_session_scope(): Exception: Rolling back session...")
        session.rollback()
        raise e
    finally:
        print("DEBUG make_session_scope(): Closing session...")
        session.close()
