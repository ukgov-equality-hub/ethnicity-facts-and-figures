import enum
import re
from datetime import datetime, timedelta
from functools import total_ordering

import sqlalchemy
from bidict import bidict
from sqlalchemy import inspect, ForeignKeyConstraint, PrimaryKeyConstraint, UniqueConstraint, ForeignKey, not_, Index
from sqlalchemy.dialects.postgresql import JSON, ARRAY
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relation, relationship, backref, make_transient
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

publish_status = bidict(
    REJECTED=0, DRAFT=1, INTERNAL_REVIEW=2, DEPARTMENT_REVIEW=3, APPROVED=4, UNPUBLISH=5, UNPUBLISHED=6
)

user_page = db.Table(
    "user_page",
    db.Column("user_id", db.Integer, db.ForeignKey("users.id"), primary_key=True),
    db.Column("page_id", db.String, primary_key=True),
)


class TypeOfData(enum.Enum):
    ADMINISTRATIVE = "Administrative"
    SURVEY = "Survey (including census)"


class UKCountry(enum.Enum):
    ENGLAND = "England"
    WALES = "Wales"
    SCOTLAND = "Scotland"
    NORTHERN_IRELAND = "Northern Ireland"
    UK = "UK"


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


class FrequencyOfRelease(db.Model):
    __tablename__ = "frequency_of_release"

    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(), nullable=False)
    position = db.Column(db.Integer, nullable=False)


class TypeOfStatistic(db.Model):
    __tablename__ = "type_of_statistic"

    id = db.Column(db.Integer, primary_key=True)
    internal = db.Column(db.String(), nullable=False)
    external = db.Column(db.String(), nullable=False)
    position = db.Column(db.Integer, nullable=False)


@total_ordering
class Page(db.Model):
    """
    The Page model holds data about all pages in the page hierarchy of the website:
    Homepage (root) -> Topics -> Subtopics -> Measure pages (leaves)

    Most of our Pages are measure pages, and many of the fields in this model are only relevant to measure pages.
    Home, topic and subtopic pages define the structure of the site through parent-child relationships.

    A measure page can have multiple versions in different states (e.g. versions 1.0 and 1.1 published, 2.0 in draft).
    Each version of a measure page is one record in the Page model, so we have a compound key consisting of `guid`
    coupled with `version`.
    """

    __tablename__ = "page"

    def __eq__(self, other):
        return self.guid == other.guid and self.version == other.version

    def __hash__(self):
        return hash((self.guid, self.version))

    def __lt__(self, other):
        if self.major() < other.major():
            return True
        elif self.major() == other.major() and self.minor() < other.minor():
            return True
        else:
            return False

    # PAGE ORGANISATION, LIFECYCLE AND METADATA
    # =========================================

    guid = db.Column(db.String(255), nullable=False)  # identifier for a measure (but not a page)
    version = db.Column(db.String(), nullable=False)  # combined with guid forms primary key for page table
    internal_reference = db.Column(db.String())  # optional internal reference number for measures
    latest = db.Column(db.Boolean, default=True)  # True if the current row is the latest version of a measure
    #                                               (latest created, not latest published, so could be a new draft)

    uri = db.Column(db.String(255))  # slug to be used in URLs for the page
    review_token = db.Column(db.String())  # used for review page URLs
    description = db.Column(db.Text)  # TOPIC PAGES ONLY: a sentence below topic heading on homepage
    additional_description = db.Column(db.TEXT)  # TOPIC PAGES ONLY: short paragraph displayed on topic page itself
    page_type = db.Column(db.String(255))  # one of measure, homepage, subtopic, topic
    position = db.Column(db.Integer, default=0)  # ordering for MEASURE and SUBTOPIC pages

    # status for measure pages is one of APPROVED, DRAFT, DEPARTMENT_REVIEW, INTERNAL_REVIEW, REJECTED, UNPUBLISHED
    # but it's free text in the DB and for other page types we have NULL or "draft" ¯\_(ツ)_/¯
    status = db.Column(db.String(255))

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)  # timestamp when page created
    created_by = db.Column(db.String(255))  # email address of user who created the page
    updated_at = db.Column(db.DateTime)  # timestamp when page updated
    last_updated_by = db.Column(db.String(255))  # email address of user who made the most recent update

    # Only MEASURE PAGES are published. All other pages have published=False (or sometimes NULL)
    published = db.Column(db.BOOLEAN, default=False)  # set to True when a page version is published
    publication_date = db.Column(db.Date)  # date set automatically by CMS when a page version is published
    published_by = db.Column(db.String(255))  # email address of user who published the page
    unpublished_by = db.Column(db.String(255))  # email address of user who unpublished the page

    # parent_guid defines the hierarchy between pages of the site
    # TOPIC pages have "homepage" as parent_guid
    # SUBTOPIC pages have "topic_xxx" as parent_guid
    # MEASURE pages have "subtopic_xxx" as parent_guid
    # The homepage and test area topic page have no parent_guid
    parent_guid = db.Column(db.String(255))
    parent_version = db.Column(db.String())  # version number of the parent page, as guid+version is PK
    parent = relation("Page", remote_side=[guid, version], backref=backref("children", order_by="Page.position"))

    __table_args__ = (
        PrimaryKeyConstraint("guid", "version", name="page_guid_version_pk"),
        ForeignKeyConstraint([parent_guid, parent_version], ["page.guid", "page.version"]),
        UniqueConstraint("guid", "version", name="uix_page_guid_version"),
        Index("ix_page_type_uri", page_type, uri),
        {},
    )

    db_version_id = db.Column(db.Integer, nullable=False)  # used to detect and prevent stale updates
    __mapper_args__ = {"version_id_col": db_version_id}

    # Uploads and dimensions belonging to this measure can be discovered through these relationships
    uploads = db.relationship("Upload", backref="page", lazy="dynamic", cascade="all,delete")
    dimensions = db.relationship(
        "Dimension", backref="page", lazy="dynamic", order_by="Dimension.position", cascade="all,delete"
    )

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

    # lowest_level_of_geography is not displayed on the public site but is used for geographic dashboard
    lowest_level_of_geography_id = db.Column(
        db.String(255), ForeignKey("lowest_level_of_geography.name"), nullable=True
    )
    lowest_level_of_geography = relationship("LowestLevelOfGeography", back_populates="pages")

    # Contact details for measure - not displayed on public site!
    contact_name = db.Column(db.TEXT)  # name of "Contact 1"
    contact_phone = db.Column(db.TEXT)  # phone of "Contact 1"
    contact_email = db.Column(db.TEXT)  # email address of "Contact 1"
    contact_2_name = db.Column(db.TEXT)  # name of "Contact 2"
    contact_2_phone = db.Column(db.TEXT)  # phone of "Contact 2"
    contact_2_email = db.Column(db.TEXT)  # email address of "Contact 2"

    # Departmental users can only access measure pages that have been shared with them, as defined by this relationship
    shared_with = db.relationship(
        "User",
        lazy="subquery",
        secondary=user_page,
        primaryjoin="Page.guid == user_page.columns.page_id",
        secondaryjoin="User.id == user_page.columns.user_id",
        backref=db.backref("pages", lazy=True),
    )

    # Methodology section
    # -------------------
    methodology = db.Column(db.TEXT)  # "Methodology"
    suppression_and_disclosure = db.Column(db.TEXT)  # "Suppression rules and disclosure control"
    estimation = db.Column(db.TEXT)  # "Rounding"
    related_publications = db.Column(db.TEXT)  # "Related publications"
    qmi_url = db.Column(db.TEXT)  # "Quality and methodology information"
    further_technical_information = db.Column(db.TEXT)  # "Further technical information"

    # Primary Source
    # --------------
    # TODO: rename these to be consistent with secondary sources.
    source_text = db.Column(db.TEXT)  # "Source" link text for primary data source_url
    source_url = db.Column(db.TEXT)  # "Source" URL for the primary data source

    # "Type of data" in primary Data sources section; zero or more of (ADMINISTRATIVE, SURVEY)
    type_of_data = db.Column(ArrayOfEnum(db.Enum(TypeOfData, name="type_of_data_types")), default=[])

    # "Type of statistic" in primary Data sources section
    type_of_statistic_id = db.Column(db.Integer, ForeignKey("type_of_statistic.id"))
    type_of_statistic_description = relationship("TypeOfStatistic", foreign_keys=[type_of_statistic_id])

    # "Publisher" in primary Data sources section
    department_source_id = db.Column(db.String(255), ForeignKey("organisation.id"), nullable=True)
    department_source = relationship("Organisation", foreign_keys=[department_source_id], back_populates="pages")

    published_date = db.Column(db.String(255))  # "Date first published" for primary source (not currently shown)
    note_on_corrections_or_updates = db.Column(db.TEXT)  # "Note on corrections or updates" for primary source

    # "Publication frequency" in primary Data sources section
    frequency_id = db.Column(db.Integer, ForeignKey("frequency_of_release.id"))
    frequency_of_release = relationship("FrequencyOfRelease", foreign_keys=[frequency_id])
    frequency_other = db.Column(db.String(255))  # free text for when "Other" is chosen for frequency_of_release
    data_source_purpose = db.Column(db.TEXT)  # "Purpose of data source" in primary Data sources section

    # Secondary Source
    # ----------------
    secondary_source_1_title = db.Column(db.TEXT)  # "Source" link text for secondary data source_url
    secondary_source_1_url = db.Column(db.TEXT)  # "Source" URL for the secondary data source

    # "Type of data" in secondary Data sources section; zero or more of (ADMINISTRATIVE, SURVEY)
    secondary_source_1_type_of_data = db.Column(ArrayOfEnum(db.Enum(TypeOfData, name="type_of_data_types")), default=[])

    # "Type of statistic" in secondary Data sources section
    secondary_source_1_type_of_statistic_id = db.Column(db.Integer, ForeignKey("type_of_statistic.id"))
    secondary_source_1_type_of_statistic_description = relationship(
        "TypeOfStatistic", foreign_keys=[secondary_source_1_type_of_statistic_id]
    )  # noqa

    # "Publisher" in secondary Data sources section
    secondary_source_1_publisher_id = db.Column(
        db.String(255), ForeignKey("organisation.id", name="organisation_secondary_source_1_fkey"), nullable=True
    )
    secondary_source_1_publisher = relationship("Organisation", foreign_keys=[secondary_source_1_publisher_id])

    secondary_source_1_date = db.Column(db.TEXT)  # "Date first published" for secondary source (not currently shown)
    secondary_source_1_note_on_corrections_or_updates = db.Column(db.TEXT)  # "Note on corrections or updates" 2ndary

    # "Publication frequency" in secondary Data sources section
    secondary_source_1_frequency_id = db.Column(
        db.Integer, ForeignKey("frequency_of_release.id", name="frequency_secondary_source_1_fkey")
    )
    secondary_source_1_frequency_of_release = relationship(
        "FrequencyOfRelease", foreign_keys=[secondary_source_1_frequency_id]
    )
    secondary_source_1_frequency_other = db.Column(db.String(255))  # free text for when "Other" is chosen for frequency
    secondary_source_1_data_source_purpose = db.Column(db.TEXT)  # "Purpose of data source" in secondary Data sources

    # Returns an array of measures which have been published, and which
    # were either first version (1.0) or the first version of an update
    # eg (2.0, 3.0, 4.0) but not a minor update (1.1 or 2.1).
    @classmethod
    def published_major_versions(cls):
        return cls.query.filter(
            cls.publication_date.isnot(None), cls.version.endswith(".0"), cls.page_type == "measure"
        )

    # Returns an array of measures which have been published, and which
    # were the first version (1.0)
    @classmethod
    def published_first_versions(cls):
        return cls.query.filter(cls.publication_date.isnot(None), cls.version == "1.0", cls.page_type == "measure")

    # Returns an array of published subsequent (major) updates at their initial
    # release (eg 2.0, 3.0, 4.0 and so on...)
    @classmethod
    def published_updates_first_versions(cls):
        return cls.query.filter(
            cls.publication_date.isnot(None),
            cls.page_type == "measure",
            cls.version.endswith(".0"),
            not_(cls.version == "1.0"),
        )

    def get_dimension(self, guid):
        try:
            dimension = Dimension.query.filter_by(guid=guid, page=self).one()
            return dimension
        except NoResultFound as e:
            raise DimensionNotFoundException

    def get_upload(self, guid):
        try:
            upload = Upload.query.filter_by(guid=guid).one()
            return upload
        except NoResultFound as e:
            raise UploadNotFoundException

    def publish_status(self, numerical=False):
        current_status = self.status.upper()
        if numerical:
            return publish_status[current_status]
        else:
            return current_status

    def available_actions(self):

        if self.parent.parent.guid == "topic_testingspace":
            return ["UPDATE"]
        if self.status == "DRAFT":
            return ["APPROVE", "UPDATE"]

        if self.status == "INTERNAL_REVIEW":
            return ["APPROVE", "REJECT"]

        if self.status == "DEPARTMENT_REVIEW":
            return ["APPROVE", "REJECT"]

        if self.status == "APPROVED":
            return ["UNPUBLISH"]

        if self.status in ["REJECTED", "UNPUBLISHED"]:
            return ["RETURN_TO_DRAFT"]
        else:
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

    def unpublish(self):
        unpublish_state = publish_status.inv[5]
        message = 'Request to un-publish page "{}" - page will be removed from site'.format(self.title)
        self.status = unpublish_state
        return message

    def not_editable(self):
        if self.publish_status(numerical=True) == 5:
            return False
        else:
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

    def next_version_number_by_type(self, version_type):
        if version_type == "copy":
            return "1.0"
        if version_type == "minor":
            return self.next_minor_version()
        return self.next_major_version()

    def latest_version(self):
        versions = self.get_versions()
        versions.sort(reverse=True)
        return versions[0] if versions else self

    def number_of_versions(self):
        return len(self.get_versions())

    def has_minor_update(self):
        return len(self.minor_updates()) > 0

    def has_major_update(self):
        return len(self.major_updates()) > 0

    def is_minor_version(self):
        return self.minor() != 0

    def is_major_version(self):
        return not self.is_minor_version()

    def get_versions(self, include_self=True):
        if include_self:
            return self.query.filter(Page.guid == self.guid).all()
        else:
            return self.query.filter(Page.guid == self.guid, Page.version != self.version).all()

    def get_previous_version(self):
        versions = self.get_versions(include_self=False)
        versions.sort(reverse=True)
        return versions[0] if versions else None

    def has_no_later_published_versions(self):
        updates = self.minor_updates() + self.major_updates()
        published = [page for page in updates if page.status == "APPROVED"]
        return len(published) == 0

    @property
    def is_published_measure_or_parent_of(self):
        if self.page_type == "measure":
            return self.published

        return any(child.is_published_measure_or_parent_of for child in self.children)

    def minor_updates(self):
        versions = Page.query.filter(Page.guid == self.guid, Page.version != self.version)
        return [page for page in versions if page.major() == self.major() and page.minor() > self.minor()]

    def major_updates(self):
        versions = Page.query.filter(Page.guid == self.guid, Page.version != self.version)
        return [page for page in versions if page.major() > self.major()]

    def format_area_covered(self):
        if self.area_covered is None:
            return ""
        if len(self.area_covered) == 0:
            return ""
        if len(self.area_covered) == 1:
            return self.area_covered[0].value
        else:
            last = self.area_covered[-1]
            first = self.area_covered[:-1]
            comma_separated = ", ".join([item.value for item in first])
            return "%s and %s" % (comma_separated, last.value)

    def to_dict(self, with_dimensions=False):
        page_dict = {
            "guid": self.guid,
            "title": self.title,
            "measure_summary": self.measure_summary,
            "summary": self.summary,
            "area_covered": self.area_covered,
            "lowest_level_of_geography": self.lowest_level_of_geography,
            "time_covered": self.time_covered,
            "need_to_know": self.need_to_know,
            "ethnicity_definition_summary": self.ethnicity_definition_summary,
            "source_text": self.source_text,
            "source_url": self.source_url,
            "department_source": self.department_source,
            "published_date": self.published_date,
            "frequency": self.frequency_of_release.description if self.frequency_of_release else None,
            "related_publications": self.related_publications,
            "contact_name": self.contact_name,
            "contact_phone": self.contact_phone,
            "contact_email": self.contact_email,
            "data_source_purpose": self.data_source_purpose,
            "methodology": self.methodology,
            "type_of_data": [t.name for t in self.type_of_data] if self.type_of_data else None,
            "suppression_and_disclosure": self.suppression_and_disclosure,
            "estimation": self.estimation,
            "type_of_statistic": self.type_of_statistic_description.external
            if self.type_of_statistic_description
            else None,
            "qmi_url": self.qmi_url,
            "further_technical_information": self.further_technical_information,
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


class Dimension(db.Model):
    __tablename__ = "dimension"

    guid = db.Column(db.String(255), primary_key=True)
    title = db.Column(db.String(255))
    time_period = db.Column(db.String(255))
    summary = db.Column(db.Text())

    chart = db.Column(JSON)
    table = db.Column(JSON)
    chart_builder_version = db.Column(db.Integer)
    chart_source_data = db.Column(JSON)
    chart_2_source_data = db.Column(JSON)

    table_source_data = db.Column(JSON)
    table_builder_version = db.Column(db.Integer)
    table_2_source_data = db.Column(JSON)

    page_id = db.Column(db.String(255), nullable=False)
    page_version = db.Column(db.String(), nullable=False)

    position = db.Column(db.Integer)

    chart_id = db.Column(db.Integer, ForeignKey("dimension_chart.id", name="dimension_chart_id_fkey"))
    table_id = db.Column(db.Integer, ForeignKey("dimension_table.id", name="dimension_table_id_fkey"))

    dimension_chart = relationship("Chart")
    dimension_table = relationship("Table")

    __table_args__ = (ForeignKeyConstraint([page_id, page_version], [Page.guid, Page.version]), {})

    classification_links = db.relationship(
        "DimensionClassification", backref="dimension", lazy="dynamic", cascade="all,delete"
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

    # This updates the metadata on the associated dimension_classification object
    # from either the chart or table, depending upon which exists, or the one with
    # the highest number of ethnicities if both exist.
    def update_dimension_classification_from_chart_or_table(self):

        chart_or_table = None

        if self.dimension_chart and (self.dimension_table is None):
            chart_or_table = self.dimension_chart
        elif self.dimension_table and (self.dimension_chart is None):
            chart_or_table = self.dimension_table
        elif self.dimension_table and self.dimension_chart:
            if (
                self.dimension_chart.classification.ethnicities_count
                > self.dimension_table.classification.ethnicities_count
            ):
                chart_or_table = self.dimension_chart
            else:
                chart_or_table = self.dimension_table

        if chart_or_table:
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

    # TODO: Refactor Dimension so that all chart and table data lives in dimension_chart and dimension_table
    # Once the chart and table data is moved out into dimension_chart and dimension_table models we can add
    # delete() ChartAndTableMixin so we can just do dimension.chart.delete() and dimension.table.delete()
    # without the need for the repeated code in the two methods below.
    def delete_chart(self):
        self.chart = sqlalchemy.null()
        self.chart_source_data = sqlalchemy.null()
        self.chart_2_source_data = sqlalchemy.null()

        chart_id = self.chart_id
        self.chart_id = None

        db.session.add(self)
        db.session.commit()

        chart = Chart.query.get(chart_id)
        db.session.delete(chart)
        db.session.commit()

        self.update_dimension_classification_from_chart_or_table()

    def delete_table(self):
        self.table = sqlalchemy.null()
        self.table_source_data = sqlalchemy.null()
        self.table_2_source_data = sqlalchemy.null()

        table_id = self.table_id
        self.table_id = None

        db.session.add(self)
        db.session.commit()

        table = Table.query.get(table_id)
        db.session.delete(table)
        db.session.commit()

        self.update_dimension_classification_from_chart_or_table()

    def to_dict(self):
        return {
            "guid": self.guid,
            "title": self.title,
            "measure": self.page.guid,
            "time_period": self.time_period,
            "summary": self.summary,
            "chart": self.chart,
            "table": self.table,
            "chart_builder_version": self.chart_builder_version,
            "chart_source_data": self.chart_source_data,
            "chart_2_source_data": self.chart_2_source_data,
            "table_source_data": self.table_source_data,
            "table_2_source_data": self.table_2_source_data,
            "table_builder_version": self.table_builder_version,
        }

    # Note that this copy() function does not commit the new object to the database.
    # It it up to the caller to add and commit the copied object.
    def copy(self):
        # get a list of classification_links from this dimension before we make any changes
        # TODO: In reality there will only ever be one of these. We should refactor the model to reflect this.
        links = []
        for link in self.classification_links:
            db.session.expunge(link)
            make_transient(link)
            links.append(link)

        # get the existing chart and table before we lift from session
        chart_object = self.dimension_chart
        table_object = self.dimension_table

        # lift dimension from session
        db.session.expunge(self)
        make_transient(self)

        # update disassociated dimension
        self.guid = create_guid(self.title)

        if chart_object:
            self.dimension_chart = chart_object.copy()

        if table_object:
            self.dimension_table = table_object.copy()

        for dc in links:
            self.classification_links.append(dc)

        return self


class Upload(db.Model):
    __tablename__ = "upload"

    guid = db.Column(db.String(255), primary_key=True)
    title = db.Column(db.String(255))
    file_name = db.Column(db.String(255))
    description = db.Column(db.Text())
    size = db.Column(db.String(255))

    page_id = db.Column(db.String(255), nullable=False)
    page_version = db.Column(db.String(), nullable=False)

    __table_args__ = (ForeignKeyConstraint([page_id, page_version], [Page.guid, Page.version]), {})

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
    db.Column("classification_id", db.Integer, ForeignKey("classification.id")),
    db.Column("ethnicity_id", db.Integer, ForeignKey("ethnicity.id")),
)
parent_association_table = db.Table(
    "parent_ethnicity_in_classification",
    db.metadata,
    db.Column("classification_id", db.Integer, ForeignKey("classification.id")),
    db.Column("ethnicity_id", db.Integer, ForeignKey("ethnicity.id")),
)


class Classification(db.Model):

    id = db.Column(db.String(255), primary_key=True)
    title = db.Column(db.String(255))
    long_title = db.Column(db.String(255))
    subfamily = db.Column(db.String(255))
    position = db.Column(db.Integer)

    dimension_links = db.relationship(
        "DimensionClassification", backref="classification", lazy="dynamic", cascade="all,delete"
    )

    ethnicities = relationship("Ethnicity", secondary=association_table, back_populates="classifications")
    parent_values = relationship(
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

    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.String(255))
    position = db.Column(db.Integer())

    classifications = relationship("Classification", secondary=association_table, back_populates="ethnicities")
    classifications_as_parent = relationship(
        "Classification", secondary=parent_association_table, back_populates="parent_values"
    )


class DimensionClassification(db.Model):
    __tablename__ = "dimension_categorisation"

    dimension_guid = db.Column(db.String(255), primary_key=True)
    classification_id = db.Column("classification_id", db.Integer, primary_key=True)

    includes_parents = db.Column(db.Boolean)
    includes_all = db.Column(db.Boolean)
    includes_unknown = db.Column(db.Boolean)

    __table_args__ = (
        ForeignKeyConstraint([dimension_guid], [Dimension.guid]),
        ForeignKeyConstraint([classification_id], [Classification.id]),
        {},
    )


# This encapsulates common fields and functionality for chart and table models
class ChartAndTableMixin(object):

    id = db.Column(db.Integer, primary_key=True)
    classification_id = db.Column("classification_id", db.Integer)
    includes_parents = db.Column(db.Boolean)
    includes_all = db.Column(db.Boolean)
    includes_unknown = db.Column(db.Boolean)

    @classmethod
    def get_by_id(cls, id):
        return cls.query.filter_by(id=id).first()

    @declared_attr
    def classification(cls):
        return relationship("Classification")

    @declared_attr
    def __table_args__(cls):
        return (ForeignKeyConstraint([cls.classification_id], [Classification.id]), {})

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

    def __str__(self):
        return f"{self.id} {self.classification_id} includes_parents:{self.includes_parents} includes_all:{self.includes_all} includes_unknown:{self.includes_unknown}"


class Chart(db.Model, ChartAndTableMixin):
    __tablename__ = "dimension_chart"


class Table(db.Model, ChartAndTableMixin):
    __tablename__ = "dimension_table"


class Organisation(db.Model):
    __tablename__ = "organisation"

    id = db.Column(db.String(255), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    other_names = db.Column(ARRAY(db.String), default=[])
    abbreviations = db.Column(ARRAY(db.String), default=[])
    organisation_type = db.Column(db.Enum(TypeOfOrganisation, name="type_of_organisation_types"), nullable=False)

    pages = relationship("Page", back_populates="department_source", foreign_keys=[Page.department_source_id])

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
    __tablename__ = "lowest_level_of_geography"

    name = db.Column(db.String(255), primary_key=True)
    description = db.Column(db.String(255), nullable=True)
    position = db.Column(db.Integer, nullable=False)

    pages = relationship("Page", back_populates="lowest_level_of_geography")
