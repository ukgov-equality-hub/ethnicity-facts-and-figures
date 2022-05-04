import enum
import re
from datetime import datetime, timedelta
from functools import total_ordering
from typing import Optional, Iterable

import sqlalchemy
from bidict import bidict
#from dictalchemy import DictableModel
from sqlalchemy import inspect, ForeignKeyConstraint, UniqueConstraint, ForeignKey, not_, text, func, desc
from sqlalchemy.dialects.postgresql import JSON, ARRAY
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm.exc import NoResultFound

from application import db
from application.cms.exceptions import (
    CannotPublishRejected,
    AlreadyApproved,
    RejectionImpossible,
    DimensionNotFoundException,
    UploadNotFoundException,
)
from application.utils import get_token_age, create_guid
from application.utils import cleanup_filename

publish_status = bidict(REJECTED=0, DRAFT=1, INTERNAL_REVIEW=2, DEPARTMENT_REVIEW=3, APPROVED=4)

TESTING_SPACE_SLUG = "testing-space"


class NewVersionType(enum.Enum):
    NEW_MEASURE = "new_measure"
    MINOR_UPDATE = "minor"
    MAJOR_UPDATE = "major"


class TypeOfData(enum.Enum):
    ADMINISTRATIVE = "Administrative"
    SURVEY = "Survey (including census data)"


class UKCountry(enum.Enum):
    ENGLAND = "England"
    WALES = "Wales"
    SCOTLAND = "Scotland"
    NORTHERN_IRELAND = "Northern Ireland"
    OVERSEAS = "Overseas"


class TypeOfOrganisation(enum.Enum):
    MINISTERIAL_DEPARTMENT = "Ministerial department"
    NON_MINISTERIAL_DEPARTMENT = "Non-ministerial department"
    EXECUTIVE_OFFICE = "Executive office"
    EXECUTIVE_AGENCY = "Executive agency"
    DEVOLVED_ADMINISTRATION = "Devolved administration"
    COURT = "Court"
    TRIBUNAL_NON_DEPARTMENTAL_PUBLIC_BODY = "Tribunal non-departmental public body"
    CIVIL_SERVICE = "Civil Service"
    EXECUTIVE_NON_DEPARTMENTAL_PUBLIC_BODY = "Executive non-departmental public body"
    INDEPENDENT_MONITORING_BODY = "Independent monitoring body"
    PUBLIC_CORPORATION = "Public corporation"
    SUB_ORGANISATION = "Sub-organisation"
    AD_HOC_ADVISORY_GROUP = "Ad-hoc advisory group"
    ADVISORY_NON_DEPARTMENTAL_PUBLIC_BODY = "Advisory non-departmental public body"
    OTHER = "Other"

    def pluralise(self):

        if self == TypeOfOrganisation.CIVIL_SERVICE:
            return self.value

        if self == TypeOfOrganisation.EXECUTIVE_AGENCY:
            return self.value.replace("agency", "agencies")

        if self in [
            TypeOfOrganisation.TRIBUNAL_NON_DEPARTMENTAL_PUBLIC_BODY,
            TypeOfOrganisation.EXECUTIVE_NON_DEPARTMENTAL_PUBLIC_BODY,
            TypeOfOrganisation.INDEPENDENT_MONITORING_BODY,
            TypeOfOrganisation.ADVISORY_NON_DEPARTMENTAL_PUBLIC_BODY,
        ]:
            return self.value.replace("body", "bodies")

        return "%ss" % self.value


# This is from  http://docs.sqlalchemy.org/en/latest/dialects/postgresql.html#using-enum-with-array
class ArrayOfEnum(ARRAY):
    def bind_expression(self, bindvalue):
        return sqlalchemy.cast(bindvalue, self)

    def result_processor(self, dialect, coltype):
        super_rp = super(ArrayOfEnum, self).result_processor(dialect, coltype)

        def handle_raw_string(value):
            inner = re.match(r"^{(.*)}$", value).group(1)
            return inner.split(",") if inner else []

        def process(value):
            if value is None:
                return None
            return super_rp(handle_raw_string(value))

        return process


class CopyableModel(): #DictableModel):
    def copy(self, exclude_fields: Optional[Iterable]=None):
        if not exclude_fields:
            exclude_fields = []

        #copy = self.__class__()
        #copy.fromdict(self.asdict(exclude_pk=True, exclude=exclude_fields))

        #return copy
        return self


class FrequencyOfRelease(db.Model):
    # metadata
    __tablename__ = "frequency_of_release"

    # columns
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(), nullable=False)
    position = db.Column(db.Integer, nullable=False)

    # relationships
    data_sources = db.relationship("DataSource", back_populates="frequency_of_release")


class TypeOfStatistic(db.Model):
    # metadata
    __tablename__ = "type_of_statistic"

    # columns
    id = db.Column(db.Integer, primary_key=True)
    internal = db.Column(db.String(), nullable=False)
    external = db.Column(db.String(), nullable=False)
    position = db.Column(db.Integer, nullable=False)

    # relationships
    data_sources = db.relationship("DataSource", back_populates="type_of_statistic")


class DataSource(db.Model, CopyableModel):
    # metadata
    __tablename__ = "data_source"
    __table_args__ = (
        ForeignKeyConstraint(
            ["type_of_statistic_id"],
            ["type_of_statistic.id"],
            name="data_source_type_of_statistic_id_fkey",
            ondelete="restrict",
        ),
        ForeignKeyConstraint(
            ["publisher_id"], ["organisation.id"], name="data_source_publisher_id_fkey", ondelete="restrict"
        ),
        ForeignKeyConstraint(
            ["frequency_of_release_id"],
            ["frequency_of_release.id"],
            name="data_source_frequency_of_release_id_fkey",
            ondelete="restrict",
        ),
    )

    # columns
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=True)

    type_of_data = db.Column(ArrayOfEnum(db.Enum(TypeOfData, name="type_of_data_types")), default=[], nullable=True)
    type_of_statistic_id = db.Column(db.Integer, nullable=True)

    publisher_id = db.Column(db.String(255), nullable=True)
    source_url = db.Column(db.String(255), nullable=True)
    publication_date = db.Column(db.String(255), nullable=True)
    note_on_corrections_or_updates = db.Column(db.TEXT, nullable=True)

    frequency_of_release_id = db.Column(db.Integer, nullable=True)
    frequency_of_release_other = db.Column(db.String(255), nullable=True)

    purpose = db.Column(db.TEXT, nullable=True)

    # relationships
    type_of_statistic = db.relationship(
        "TypeOfStatistic", foreign_keys=[type_of_statistic_id], back_populates="data_sources"
    )
    publisher = db.relationship("Organisation", foreign_keys=[publisher_id], back_populates="data_sources")
    frequency_of_release = db.relationship(
        "FrequencyOfRelease", foreign_keys=[frequency_of_release_id], back_populates="data_sources"
    )
    measure_versions = db.relationship(
        "MeasureVersion", secondary="data_source_in_measure_version", back_populates="data_sources", lazy="dynamic"
    )

    def merge(self, data_source_ids=[]):
        """This merges the data sources with the IDs specified into this data source,
        by first updating any references to those data source to this one, and then
        deleting those data sources. This is irreversible.

        Note: this makes no attempt to merge the metadata fields associated with the
        specified data sources.

        Will raise an error no IDs specified, if any of the IDs specified don’t exist,
        or if one of the IDs is the ID for this data source."""

        if self.id in data_source_ids:
            raise ValueError("Can’t merge with self")

        if len(data_source_ids) == 0:
            raise ValueError("No data source IDs specified")

        data_sources_to_delete = DataSource.query.filter(DataSource.id.in_(data_source_ids))

        if (data_sources_to_delete.count()) != len(data_source_ids):

            difference = len(data_source_ids) - data_sources_to_delete.count()

            raise ValueError(f"#{difference} data sources not found")

        for data_source_to_delete in data_sources_to_delete:

            DataSourceInMeasureVersion.query.filter(
                DataSourceInMeasureVersion.data_source_id == data_source_to_delete.id
            ).update({"data_source_id": self.id})

            db.session.delete(data_source_to_delete)

        db.session.commit()

    @property
    def associated_with_published_measure_versions(self):

        return self.measure_versions.filter(MeasureVersion.status == "APPROVED").count() > 0

    @staticmethod
    def search(query, limit=False, exclude_data_sources=None):

        raw_sql = """
plainto_tsquery('english', :q)
@@
(
    to_tsvector(
        'english',
        title
        ||  ' '
        ||  coalesce(organisation.name, '')
        || ' '
        || coalesce(source_url, '')
        || ' '
        || to_tsvector(
            'english',
            array_to_string(organisation.abbreviations, ' ')
        )
    )
)
 """

        query_sql = text(raw_sql)
        query_sql = query_sql.bindparams(q=query)

        data_source_query = (
            DataSource.query.join(DataSource.publisher, isouter=True)
            .join(DataSourceInMeasureVersion, isouter=True)
            .filter(query_sql)
            .group_by(DataSource.id)
            .order_by(desc(func.count(DataSourceInMeasureVersion.measure_version_id)), desc(DataSource.id))
        )

        if exclude_data_sources:
            data_source_query = data_source_query.filter(
                ~DataSource.id.in_([data_source.id for data_source in exclude_data_sources])
            )

        if limit:
            data_source_query = data_source_query.limit(limit)

        return data_source_query.all()


class DataSourceInMeasureVersion(db.Model):
    # metadata
    __tablename__ = "data_source_in_measure_version"
    __table_args__ = (
        ForeignKeyConstraint(
            ["data_source_id"], ["data_source.id"], name="data_source_in_page_data_source_id_fkey", ondelete="restrict"
        ),
        ForeignKeyConstraint(["measure_version_id"], ["measure_version.id"], ondelete="cascade"),
    )

    data_source_id = db.Column(db.Integer, primary_key=True)
    measure_version_id = db.Column(db.Integer, primary_key=True)


user_measure = db.Table(
    "user_measure",
    db.Column("user_id", db.Integer, db.ForeignKey("users.id", ondelete="cascade"), primary_key=True),
    db.Column("measure_id", db.Integer, db.ForeignKey("measure.id", ondelete="cascade"), primary_key=True),
)


@total_ordering
class MeasureVersion(db.Model, CopyableModel):
    """
    The MeasureVersion model holds data about all measure versions in the website.

    A Measure page can have multiple MeasureVersions in different states (e.g. versions 1.0 and 1.1 published, 2.0 in
    draft).
    Each version of a measure page is one record in the MeasureVersion model.
    """

    # metadata
    __tablename__ = "measure_version"
    __table_args__ = (
        ForeignKeyConstraint(["measure_id"], ["measure.id"], ondelete="cascade"),
        UniqueConstraint("measure_id", "version"),
    )

    def __eq__(self, other):
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)

    def __lt__(self, other):
        if self.major() < other.major():
            return True
        elif self.major() == other.major() and self.minor() < other.minor():
            return True
        else:
            return False

    # columns
    id = db.Column(db.Integer, nullable=False, primary_key=True, autoincrement=True)
    measure_id = db.Column(db.Integer, nullable=True)  # FK to `measure` table
    version = db.Column(db.String(), nullable=False)  # The version number of this measure version in the format `X.y`.
    template_version = db.Column(
        db.String(2), default="1", nullable=False
    )  # The version number of this measure version in the format `X.y`.

    latest = db.Column(db.Boolean, default=True)  # True if the current row is the latest version of a measure
    #                                               (latest created, not latest published, so could be a new draft)

    review_token = db.Column(db.String())  # used for review page URLs
    description = db.Column(db.Text)  # A short summary used by search engines and social sharing.

    # status for measure versions is one of APPROVED, DRAFT, DEPARTMENT_REVIEW, INTERNAL_REVIEW, REJECTED
    status = db.Column(db.String(255))

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)  # timestamp when page created
    created_by = db.Column(db.String(255))  # email address of user who created the page
    updated_at = db.Column(db.DateTime)  # timestamp when page updated
    last_updated_by = db.Column(db.String(255))  # email address of user who made the most recent update

    published_at = db.Column(db.Date, nullable=True)  # date - set automatically when a measure version is published
    published_by = db.Column(db.String(255))  # email address of user who published the measure version

    db_version_id = db.Column(db.Integer, nullable=False)  # used to detect and prevent stale updates
    __mapper_args__ = {"version_id_col": db_version_id}

    # MEASURE-PAGE DATA
    # =================
    title = db.Column(db.String(255))  # <h1> on measure page
    summary = db.Column(db.TEXT)  # "The main facts and figures show that..." bullets at top of measure page
    need_to_know = db.Column(db.TEXT)  # "Things you need to know" on a measure page
    measure_summary = db.Column(db.TEXT)  # "What the data measures" on measure page
    ethnicity_definition_summary = db.Column(db.TEXT)  # "The ethnicies used in this data" on a measure page

    # Measure metadata
    # ----------------
    area_covered = db.Column(ArrayOfEnum(db.Enum(UKCountry, name="uk_country_types")), default=[])  # public metadata
    time_covered = db.Column(db.String(255))  # public metadata
    external_edit_summary = db.Column(db.TEXT)  # notes on new version, displayed on public measure page
    internal_edit_summary = db.Column(db.TEXT)  # internal notes on new version, not displayed on public measure page
    update_corrects_data_mistake = db.Column(db.Boolean)  # Whether or not a minor updates fixes a mistake in the data

    # Where a measure version is a correction, this points to the earliest version (within the same major version)
    # that contains the error.
    update_corrects_measure_version = db.Column(db.Integer, ForeignKey("measure_version.id"))

    # lowest_level_of_geography is not displayed on the public site but is used for geographic dashboard
    lowest_level_of_geography_id = db.Column(
        db.String(255), ForeignKey("lowest_level_of_geography.name", ondelete="restrict"), nullable=True
    )

    # Methodology section
    # -------------------
    methodology = db.Column(db.TEXT)  # "Methodology"
    suppression_and_disclosure = db.Column(db.TEXT)  # "Suppression rules and disclosure control"
    estimation = db.Column(db.TEXT)  # "Rounding"
    related_publications = db.Column(db.TEXT)  # "Related publications"
    qmi_url = db.Column(db.TEXT)  # "Quality and methodology information"
    further_technical_information = db.Column(db.TEXT)  # "Further technical information"

    # relationships
    measure = db.relationship("Measure", back_populates="versions")
    lowest_level_of_geography = db.relationship("LowestLevelOfGeography", back_populates="measure_versions")
    uploads = db.relationship("Upload", back_populates="measure_version", cascade="all, delete-orphan")
    dimensions = db.relationship(
        "Dimension",
        back_populates="measure_version",
        lazy="dynamic",
        order_by="Dimension.position",
        cascade="all, delete-orphan",
    )
    data_sources = db.relationship(
        "DataSource", secondary="data_source_in_measure_version", back_populates="measure_versions"
    )
    corrected_by_measure_version = db.relationship(
        "MeasureVersion",
        remote_side=[update_corrects_measure_version],
        uselist=False,
        backref=db.backref("correction_for_measure_version", remote_side=[id]),
    )

    @property
    def primary_data_source(self):
        return self.data_sources[0] if self.data_sources else None

    @property
    def secondary_data_source(self):
        return self.data_sources[1] if len(self.data_sources) >= 2 else None

    @property
    def social_description(self):
        """A short summary of the page exposed as metadata for use by search
        engines and social media platforms.

        For backwards-compatibility reasons, measure_versions without custom
        written descriptions expose the first bullet point from the "Main points"
        section instead."""

        def first_bullet(value):
            if not value:
                return None
            bullets = re.search(r"\*.+", value, re.MULTILINE)
            return bullets.group() if bullets else None

        if self.description:
            return self.description
        else:
            return first_bullet(self.summary)

    # Returns an array of measures which have been published, and which
    # were either first version (1.0) or the first version of an update
    # eg (2.0, 3.0, 4.0) but not a minor update (1.1 or 2.1).
    @classmethod
    def published_major_versions(cls):
        return cls.query.filter(cls.published_at.isnot(None), cls.version.endswith(".0"))

    # Returns an array of measures which have been published, and which
    # were the first version (1.0)
    @classmethod
    def published_first_versions(cls):
        return cls.query.filter(cls.published_at.isnot(None), cls.version == "1.0")

    # Returns an array of published subsequent (major) updates at their initial
    # release (eg 2.0, 3.0, 4.0 and so on...)
    @classmethod
    def published_updates_first_versions(cls):
        return cls.query.filter(cls.published_at.isnot(None), cls.version.endswith(".0"), not_(cls.version == "1.0"))

    def get_dimension(self, guid):
        try:
            dimension = Dimension.query.filter_by(guid=guid, measure_version=self).one()
            return dimension
        except NoResultFound:
            raise DimensionNotFoundException

    def get_upload(self, guid):
        try:
            upload = Upload.query.filter_by(guid=guid, measure_version=self).one()
            return upload
        except NoResultFound:
            raise UploadNotFoundException

    def publish_status(self, numerical=False):
        current_status = self.status.upper()
        if numerical:
            return publish_status[current_status]
        else:
            return current_status

    @property
    def next_approval_state(self) -> Optional[str]:
        """Returns the next state in the approval process, from ‘draft’ to ‘approved’. Once approved, returns `None`."""
        approval_state = None

        if "APPROVE" in self.available_actions:
            numerical_status = self.publish_status(numerical=True)
            approval_state = publish_status.inv[numerical_status + 1]

        return approval_state

    @property
    def available_actions(self):
        if self.measure and self.measure.subtopic.topic.slug == TESTING_SPACE_SLUG:
            return ["UPDATE"]

        if self.status == "DRAFT":
            return ["APPROVE", "UPDATE"]

        if self.status == "INTERNAL_REVIEW":
            return ["APPROVE", "REJECT"]

        if self.status == "DEPARTMENT_REVIEW":
            return ["APPROVE", "REJECT"]

        if self.status == "REJECTED":
            return ["RETURN_TO_DRAFT"]

        return []

    def next_state(self):
        num_status = self.publish_status(numerical=True)
        if num_status == 0:
            # You can only get out of rejected state by saving
            message = 'Page "{}" is rejected.'.format(self.title)
            raise CannotPublishRejected(message)
        elif num_status <= 3:
            new_status = publish_status.inv[num_status + 1]
            self.status = new_status
            return 'Sent page "{}" to {}'.format(self.title, new_status)
        else:
            message = 'Page "{}" is already approved'.format(self.title)
            raise AlreadyApproved(message)

    def reject(self):
        if self.status == "APPROVED":
            message = 'Page "{}" cannot be rejected in state {}'.format(self.title, self.status)
            raise RejectionImpossible(message)

        rejected_state = "REJECTED"
        message = 'Sent page "{}" to {}'.format(self.title, rejected_state)
        self.status = rejected_state
        return message

    def not_editable(self):
        return self.publish_status(numerical=True) >= 2

    def eligible_for_build(self):
        return self.status == "APPROVED"

    def major(self):
        return int(self.version.split(".")[0])

    def minor(self):
        return int(self.version.split(".")[1])

    def next_minor_version(self):
        return "%s.%s" % (self.major(), self.minor() + 1)

    def next_major_version(self):
        return "%s.0" % str(self.major() + 1)

    def next_version_number_by_type(self, version_type: NewVersionType):
        if version_type == NewVersionType.NEW_MEASURE:
            return "1.0"

        elif version_type == NewVersionType.MINOR_UPDATE:
            return self.next_minor_version()

        return self.next_major_version()

    def has_minor_update(self):
        return len(self.minor_updates()) > 0

    def is_minor_version(self):
        return self.minor() != 0

    def is_major_version(self):
        return not self.is_minor_version()

    def get_previous_version(self):
        # Relies on `measure.versions` being ordered
        my_index = self.measure.versions.index(self)
        if len(self.measure.versions) > my_index + 1:
            return self.measure.versions[my_index + 1]
        else:
            return None

    def has_no_later_published_versions(self):
        latest_published_version = self.measure.latest_published_version
        if latest_published_version is None:
            return True

        return latest_published_version <= self

    @property
    def previous_major_versions(self):
        return [v for v in self.measure.versions if v.major() < self.major() and not v.has_minor_update()]

    @property
    def previous_minor_versions(self):
        return [v for v in self.measure.versions if v.major() == self.major() and v.minor() < self.minor()]

    @property
    def previous_published_minor_versions(self):
        return [
            v
            for v in self.measure.versions
            if v.major() == self.major() and v.minor() < self.minor() and v.status == "APPROVED"
        ]

    @property
    def later_minor_versions(self):
        return [v for v in self.measure.versions if v.major() == self.major() and v.minor() > self.minor()]

    @property
    def later_published_minor_versions(self):
        return [
            v
            for v in self.measure.versions
            if v.major() == self.major() and v.minor() > self.minor() and v.status == "APPROVED"
        ]

    @property
    def latest_published_minor_version(self):
        """This returns the latest published version which matches the same major version
        as the current version.
        Note: this may return the same version (if it’s the only one published),
        or a previous version (if this one is not yet published). If there is no published
        version available yet, it returns None.
        """
        published_minor_versions = [
            v for v in self.measure.versions if v.major() == self.major() and v.status == "APPROVED"
        ]

        if len(published_minor_versions) > 0:
            return max(published_minor_versions)
        else:
            return None

    @property
    def first_published_date(self):
        return self.previous_minor_versions[-1].published_at if self.previous_minor_versions else self.published_at

    def minor_updates(self):
        versions = MeasureVersion.query.filter(
            MeasureVersion.measure_id == self.measure.id, MeasureVersion.version != self.version
        )
        return [page for page in versions if page.major() == self.major() and page.minor() > self.minor()]

    def format_area_covered(self):
        if self.area_covered is None:
            return ""
        if len(self.area_covered) == 0:
            return ""

        if set(self.area_covered) == {e for e in UKCountry if e is not UKCountry.OVERSEAS}:
            return "United Kingdom"

        if set(self.area_covered) == {e for e in UKCountry}:
            return "UK and overseas"

        if len(self.area_covered) == 1:
            return self.area_covered[0].value
        else:
            last = self.area_covered[-1]
            first = self.area_covered[:-1]
            comma_separated = ", ".join([item.value for item in first])
            formatted = "%s and %s" % (comma_separated, last.value)
            if self.area_covered[0] != UKCountry.OVERSEAS:
                formatted = formatted.replace("Overseas", "overseas")
            return formatted

    def to_dict(self, with_dimensions=False):
        page_dict = {
            "title": self.title,
            "measure_summary": self.measure_summary,
            "summary": self.summary,
            "area_covered": self.area_covered,
            "lowest_level_of_geography": self.lowest_level_of_geography,
            "time_covered": self.time_covered,
            "need_to_know": self.need_to_know,
            "ethnicity_definition_summary": self.ethnicity_definition_summary,
            "related_publications": self.related_publications,
            "methodology": self.methodology,
            "suppression_and_disclosure": self.suppression_and_disclosure,
            "estimation": self.estimation,
            "qmi_url": self.qmi_url,
            "further_technical_information": self.further_technical_information,
            "template_version": self.template_version,
        }

        if with_dimensions:
            page_dict["dimensions"] = []
            for dimension in self.dimensions:
                page_dict["dimensions"].append(dimension.to_dict())

        return page_dict

    def review_token_expires_in(self, config):
        try:
            token_age = get_token_age(self.review_token, config)
            max_token_age_days = config.get("PREVIEW_TOKEN_MAX_AGE_DAYS")
            expiry = token_age + timedelta(days=max_token_age_days)
            days_from_now = expiry.date() - datetime.today().date()
            return days_from_now.days
        except Exception:
            return 0

    @property
    def has_known_statistical_errors(self) -> bool:
        """Returns true if any later version is flagged as correcting a data mistake. This will still return true even
        if *this* version is correcting a mistake - because it might be that not all the mistakes were fixed by this
        version."""
        return any(
            later_minor_version.update_corrects_data_mistake
            and later_minor_version.correction_for_measure_version <= self
            for later_minor_version in self.later_published_minor_versions
        )

    @property
    def has_known_statistical_corrections(self) -> bool:
        """Returns true if this version, or an earlier version, is flagged as correcting a data mistake. This is not
        exclusive to the property above - a measure version can both be correcting errors in a previous version while
        still also having errors itself (presumably discovered at a later date)."""
        return self.update_corrects_data_mistake or any(
            previous_minor_version.update_corrects_data_mistake
            for previous_minor_version in self.previous_published_minor_versions
        )


class Dimension(db.Model):
    # metadata
    __tablename__ = "dimension"
    __table_args__ = (ForeignKeyConstraint(["measure_version_id"], ["measure_version.id"], ondelete="cascade"), {})

    # This is a database expression to get the current timestamp in UTC.
    # Possibly specific to PostgreSQL:
    #   https://www.postgresql.org/docs/current/functions-datetime.html#FUNCTIONS-DATETIME-ZONECONVERT
    __SQL_CURRENT_UTC_TIME = "timezone('utc', CURRENT_TIMESTAMP)"

    # columns
    guid = db.Column(db.String(255), primary_key=True)
    title = db.Column(db.String(255))
    time_period = db.Column(db.String(255))
    summary = db.Column(db.Text())

    created_at = db.Column(db.DateTime, server_default=__SQL_CURRENT_UTC_TIME, nullable=False)
    updated_at = db.Column(db.DateTime, server_default=__SQL_CURRENT_UTC_TIME, nullable=False)

    measure_version_id = db.Column(db.Integer, nullable=False)

    position = db.Column(db.Integer, nullable=False)

    chart_id = db.Column(db.Integer, ForeignKey("dimension_chart.id", name="dimension_chart_id_fkey"))
    table_id = db.Column(db.Integer, ForeignKey("dimension_table.id", name="dimension_table_id_fkey"))

    # relationships
    dimension_chart = db.relationship(
        "Chart", back_populates="dimension", single_parent=True, cascade="all, delete-orphan"
    )
    dimension_table = db.relationship(
        "Table", back_populates="dimension", single_parent=True, cascade="all, delete-orphan"
    )
    measure_version = db.relationship("MeasureVersion", back_populates="dimensions")
    classification_links = db.relationship(
        "DimensionClassification", back_populates="dimension", lazy="dynamic", cascade="all, delete-orphan"
    )

    @property
    def dimension_classification(self):
        return self.classification_links.first()

    @property
    def classification_source_string(self):
        if not self.dimension_classification:
            return None
        elif (
            self.dimension_table
            and self.dimension_table.classification_id == self.dimension_classification.classification_id
            and self.dimension_table.includes_all == self.dimension_classification.includes_all
            and self.dimension_table.includes_parents == self.dimension_classification.includes_parents
            and self.dimension_table.includes_unknown == self.dimension_classification.includes_unknown
        ):
            return "Table"
        elif (
            self.dimension_chart
            and self.dimension_chart.classification_id == self.dimension_classification.classification_id
            and self.dimension_chart.includes_all == self.dimension_classification.includes_all
            and self.dimension_chart.includes_parents == self.dimension_classification.includes_parents
            and self.dimension_chart.includes_unknown == self.dimension_classification.includes_unknown
        ):
            return "Chart"
        else:
            return "Manually selected"

    @property
    def static_file_name(self):
        if self.title:
            filename = "%s.csv" % cleanup_filename(self.title)
        else:
            filename = "%s.csv" % self.guid

        return filename

    @property
    def static_table_file_name(self):
        if self.title:
            table_filename = "%s-table.csv" % cleanup_filename(self.title)
        else:
            table_filename = "%s-table.csv" % self.guid

        return table_filename

    def set_updated_at(self):
        """
        This updates the model’s updated_at timestamp to the current time, using the
        clock on the database.
        """
        self.updated_at = text(self.__SQL_CURRENT_UTC_TIME)

    # This updates the metadata on the associated dimension_classification object
    # from either the chart or table, depending upon which exists, or the one with
    # the highest number of ethnicities if both exist.
    def update_dimension_classification_from_chart_or_table(self):

        chart_or_table = None

        # If there is a chart classification but no table classification, use the chart
        if (
            self.dimension_chart
            and self.dimension_chart.classification
            and (self.dimension_table is None or self.dimension_table.classification is None)
        ):
            chart_or_table = self.dimension_chart

        # If there is a table classification but no chart classification, use the table
        elif (
            self.dimension_table
            and self.dimension_table.classification
            and (self.dimension_chart is None or self.dimension_chart.classification is None)
        ):
            chart_or_table = self.dimension_table

        # If there is both a table classification and chart classification, use the most specific
        elif (
            self.dimension_table
            and self.dimension_table.classification
            and self.dimension_chart
            and self.dimension_chart.classification
        ):
            if (
                self.dimension_chart.classification.ethnicities_count
                > self.dimension_table.classification.ethnicities_count
            ):
                chart_or_table = self.dimension_chart
            else:
                chart_or_table = self.dimension_table

        if chart_or_table and chart_or_table.classification_id is not None:
            dimension_classification = self.dimension_classification or DimensionClassification()
            dimension_classification.classification_id = chart_or_table.classification_id
            dimension_classification.includes_parents = chart_or_table.includes_parents
            dimension_classification.includes_all = chart_or_table.includes_all
            dimension_classification.includes_unknown = chart_or_table.includes_unknown
            dimension_classification.dimension_guid = self.guid
            db.session.add(dimension_classification)

        elif self.dimension_classification:
            db.session.delete(self.dimension_classification)

        db.session.commit()

    def to_dict(self):
        return {
            "guid": self.guid,
            "title": self.title,
            "time_period": self.time_period,
            "summary": self.summary,
            "position": self.position,
            "measure_id": self.measure_version.measure.id,
            "measure_version_id": self.measure_version.id,
            "dimension_chart": self.dimension_chart.to_dict() if self.dimension_chart else None,
            "dimension_table": self.dimension_table.to_dict() if self.dimension_table else None,
            "static_file_name": self.static_file_name,
            "static_table_file_name": self.static_table_file_name,
        }

    def copy(self):
        # get a list of classification_links from this dimension before we make any changes
        # TODO: In reality there will only ever be one of these. We should refactor the model to reflect this.
        links = []
        for link in self.classification_links:
            db.session.expunge(link)
            db.make_transient(link)
            links.append(link)

        # get the existing chart and table before we lift from session
        chart_object = self.dimension_chart
        table_object = self.dimension_table

        # lift dimension from session
        db.session.expunge(self)
        db.make_transient(self)

        # update disassociated dimension
        self.guid = create_guid(self.title)

        if chart_object:
            copied_chart = chart_object.copy()
            db.session.add(copied_chart)
            db.session.flush()
            self.chart_id = copied_chart.id

        if table_object:
            copied_table = table_object.copy()
            db.session.add(copied_table)
            db.session.flush()
            self.table_id = copied_table.id

        for dc in links:
            dc.dimension_guid = self.guid
            self.classification_links.append(dc)

        db.session.add(self)
        db.session.commit()
        return self


class Upload(db.Model, CopyableModel):
    # metadata
    __tablename__ = "upload"
    __table_args__ = (ForeignKeyConstraint(["measure_version_id"], ["measure_version.id"], ondelete="cascade"), {})

    # columns
    guid = db.Column(db.String(255), primary_key=True)
    title = db.Column(db.String(255))
    file_name = db.Column(db.String(255))
    description = db.Column(db.Text())
    size = db.Column(db.String(255))

    measure_version_id = db.Column(db.Integer, nullable=False)

    # relationships
    measure_version = db.relationship("MeasureVersion", back_populates="uploads")

    def extension(self):
        return self.file_name.split(".")[-1]


"""
  The classification models allow us to associate dimensions with lists of values

  This allows us to (for example)...
   1. find measures use the 2011 18+1 breakdown (a DimensionClassification)
   2. find measures or dimensions that have information on Gypsy/Roma
"""

association_table = db.Table(
    "ethnicity_in_classification",
    db.metadata,
    db.Column("classification_id", db.String(255), ForeignKey("classification.id"), nullable=False),
    db.Column("ethnicity_id", db.Integer, ForeignKey("ethnicity.id"), nullable=False),
)
parent_association_table = db.Table(
    "parent_ethnicity_in_classification",
    db.metadata,
    db.Column("classification_id", db.String(255), ForeignKey("classification.id"), nullable=False),
    db.Column("ethnicity_id", db.Integer, ForeignKey("ethnicity.id"), nullable=False),
)


class Classification(db.Model):
    # metadata
    __tablename__ = "classification"
    __table_args__ = (UniqueConstraint("id", name="uq_classification_code"),)

    # columns
    id = db.Column(db.String(255), primary_key=True)
    title = db.Column(db.String(255))
    long_title = db.Column(db.String(255))
    subfamily = db.Column(db.String(255))
    position = db.Column(db.Integer)

    # relationships
    dimension_links = db.relationship(
        "DimensionClassification", back_populates="classification", lazy="dynamic", cascade="all, delete-orphan"
    )
    ethnicities = db.relationship("Ethnicity", secondary=association_table, back_populates="classifications")
    parent_values = db.relationship(
        "Ethnicity", secondary=parent_association_table, back_populates="classifications_as_parent"
    )

    @property
    def ethnicities_count(self):
        return len(self.ethnicities)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "long_title": self.long_title,
            "subfamily": self.subfamily,
            "position": self.position,
            "values": [v.value for v in self.ethnicities],
        }


class Ethnicity(db.Model):
    # metadata
    __tablename__ = "ethnicity"

    # columns
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.String(255))
    position = db.Column(db.Integer())

    # relationships
    classifications = db.relationship("Classification", secondary=association_table, back_populates="ethnicities")
    classifications_as_parent = db.relationship(
        "Classification", secondary=parent_association_table, back_populates="parent_values"
    )


class DimensionClassification(db.Model):
    # metadata
    __tablename__ = "dimension_categorisation"
    __table_args__ = (
        ForeignKeyConstraint(["dimension_guid"], ["dimension.guid"], ondelete="cascade"),
        ForeignKeyConstraint(["classification_id"], ["classification.id"], ondelete="restrict"),
        {},
    )

    # columns
    dimension_guid = db.Column(db.String(255), primary_key=True)
    classification_id = db.Column("classification_id", db.String(255), primary_key=True)

    includes_parents = db.Column(db.Boolean, nullable=False)
    includes_all = db.Column(db.Boolean, nullable=False)
    includes_unknown = db.Column(db.Boolean, nullable=False)

    # relationships
    classification = db.relationship("Classification", back_populates="dimension_links")
    dimension = db.relationship("Dimension", back_populates="classification_links")


# This encapsulates common fields and functionality for chart and table models
class ChartAndTableMixin(object):
    id = db.Column(db.Integer, primary_key=True)
    classification_id = db.Column("classification_id", db.String(255), nullable=True)
    includes_parents = db.Column(db.Boolean, nullable=True)
    includes_all = db.Column(db.Boolean, nullable=True)
    includes_unknown = db.Column(db.Boolean, nullable=True)

    settings_and_source_data = db.Column(JSON)

    @declared_attr
    def classification(cls):
        return db.relationship("Classification")

    @declared_attr
    def __table_args__(cls):
        return (ForeignKeyConstraint([cls.classification_id], ["classification.id"]), {})

    # Note that this copy() function does not commit the new object to the database.
    # It it up to the caller to add and commit the copied object.
    def copy(self):
        sqlalchemy_object_mapper = inspect(type(self))
        new_object = type(self)()
        for name, column in sqlalchemy_object_mapper.columns.items():
            # do not copy primary key or any other unique values
            if not column.primary_key and not column.unique:
                setattr(new_object, name, getattr(self, name))
        return new_object

    def delete(self):
        db.session.delete(self)
        db.session.commit()
        self.dimension.update_dimension_classification_from_chart_or_table()

    def __str__(self):
        return (
            f"{self.id} {self.classification_id} "
            f"includes_parents:{self.includes_parents} "
            f"includes_all:{self.includes_all} "
            f"includes_unknown:{self.includes_unknown}"
        )

    def to_dict(self):
        return {
            "classification_id": self.classification_id,
            "includes_parents": self.includes_parents,
            "includes_all": self.includes_all,
            "includes_unknown": self.includes_unknown,
            "settings_and_source_data": self.settings_and_source_data,
        }


class Chart(db.Model, ChartAndTableMixin):
    # metadata
    __tablename__ = "dimension_chart"

    # fields
    chart_object = db.Column(JSON)

    # relationships
    dimension = db.relationship("Dimension", back_populates="dimension_chart", uselist=False)

    def to_dict(self):
        return {**super().to_dict(), "chart_object": self.chart_object}


class Table(db.Model, ChartAndTableMixin):
    # metadata
    __tablename__ = "dimension_table"

    # fields
    table_object = db.Column(JSON)

    # relationships
    dimension = db.relationship("Dimension", back_populates="dimension_table", uselist=False)

    def to_dict(self):
        return {**super().to_dict(), "table_object": self.table_object}


class Organisation(db.Model):
    # metadata
    __tablename__ = "organisation"

    # columns
    id = db.Column(db.String(255), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    other_names = db.Column(ARRAY(db.String), default=[], nullable=False)
    abbreviations = db.Column(ARRAY(db.String), default=[], nullable=False)
    organisation_type = db.Column(db.Enum(TypeOfOrganisation, name="type_of_organisation_types"), nullable=False)

    # relationships
    data_sources = db.relationship("DataSource", back_populates="publisher")

    @classmethod
    def select_options_by_type(cls):
        organisations_by_type = []
        for org_type in TypeOfOrganisation:
            orgs = cls.query.filter_by(organisation_type=org_type).all()
            organisations_by_type.append((org_type, orgs))
        return organisations_by_type

    def abbreviations_data(self):
        return "|".join(self.abbreviations)

    def other_names_data(self):
        return "|".join(self.other_names)


class LowestLevelOfGeography(db.Model):
    # metadata
    __tablename__ = "lowest_level_of_geography"

    # columns
    name = db.Column(db.String(255), primary_key=True)
    description = db.Column(db.String(255), nullable=True)
    position = db.Column(db.Integer, nullable=False)

    # relationships
    measure_versions = db.relationship("MeasureVersion", back_populates="lowest_level_of_geography")


class Topic(db.Model):
    # metadata
    __tablename__ = "topic"

    # columns
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(64), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    short_title = db.Column(db.String(255), nullable=True)
    description = db.Column(db.Text, nullable=True)  # a sentence below topic heading on homepage
    additional_description = db.Column(db.TEXT, nullable=True)  # short paragraph displayed on topic page
    meta_description = db.Column(db.TEXT, nullable=True)  # sentence or two for search engines and social sharing

    # relationships
    subtopics = db.relationship("Subtopic", back_populates="topic", order_by="asc(Subtopic.position)")

    @property
    def has_published_measures(self):
        return any(subtopic.has_published_measures for subtopic in self.subtopics)

    @property
    def short_title_or_title(self):
        return self.short_title or self.title


class Subtopic(db.Model):
    # metadata
    __tablename__ = "subtopic"

    # columns
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(64), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    position = db.Column(db.Integer, default=0)  # for ordering on the page
    topic_id = db.Column(db.Integer, ForeignKey("topic.id"), nullable=True)

    # relationships
    topic = db.relationship("Topic", back_populates="subtopics")
    measures = db.relationship(
        "Measure", secondary="subtopic_measure", back_populates="subtopics", order_by="asc(Measure.position)"
    )

    @property
    def has_published_measures(self):
        return any(measure.has_published_version for measure in self.measures)


subtopic_measure = db.Table(
    "subtopic_measure",
    db.Column("subtopic_id", db.Integer, db.ForeignKey("subtopic.id", ondelete="restrict"), primary_key=True),
    db.Column("measure_id", db.Integer, db.ForeignKey("measure.id", ondelete="cascade"), primary_key=True),
)


class Measure(db.Model):
    # metadata
    __tablename__ = "measure"

    # columns
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(255), nullable=False)
    position = db.Column(db.Integer, default=0)  # for ordering on the page
    reference = db.Column(db.String(32), nullable=True)  # optional internal reference

    # relationships
    subtopics = db.relationship(
        "Subtopic", secondary="subtopic_measure", back_populates="measures", order_by="asc(Subtopic.id)"
    )
    versions = db.relationship("MeasureVersion", back_populates="measure", order_by="desc(MeasureVersion.version)")

    template_version = 1

    # Departmental users can only access measures that have been shared with them, as defined by this relationship
    shared_with = db.relationship(
        "User",
        lazy="subquery",
        secondary="user_measure",
        primaryjoin="Measure.id == user_measure.columns.measure_id",
        secondaryjoin="User.id == user_measure.columns.user_id",
        back_populates="measures",
    )

    @property
    def has_published_version(self):
        return any((version.status == "APPROVED" and version.published_at is not None) for version in self.versions)

    @property
    def latest_version(self):
        """Return the very latest version of a measure. This can include drafts."""
        return next(filter(lambda version: version.latest, self.versions), None)

    @property
    def latest_published_version(self):
        """Return the latest _published_ version of a measure."""

        published_versions = [
            version for version in self.versions if (version.status == "APPROVED" and version.published_at is not None)
        ]
        if published_versions:
            return max(published_versions, key=lambda version: (version.major(), version.minor()))

        return None

    @property
    def versions_to_publish(self):
        # Need to publish all approved versions with a publication date
        return [
            version for version in self.versions if (version.status == "APPROVED" and version.published_at is not None)
        ]

    @property
    def subtopic(self):
        """Get the first subtopic for this measure. Theoretically there can be more than one subtopic; practically,
        as of 2019/01/01, there will only ever be one. Which makes this shortcut semi-reasonable."""
        return self.subtopics[0]
