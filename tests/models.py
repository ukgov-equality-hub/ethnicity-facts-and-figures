"""
This module exposes a set of factories for generating realistic(ish) instances of our main models to aid with testing.
All of the models in our application code are likely to have a corresponding factory here, which declares all of the
same attributes (columns), as well as the most (if not all) of the relationships.

See `tests/README.md` for further information on our use of Factory Boy.
"""

import itertools
import random

from faker import Faker

import factory
from application.auth.models import CAPABILITIES, TypeOfUser, User
from application.cms.models import (
    publish_status,
    Chart,
    Classification,
    DataSource,
    Dimension,
    DimensionClassification,
    Ethnicity,
    FrequencyOfRelease,
    LowestLevelOfGeography,
    Measure,
    MeasureVersion,
    Organisation,
    Subtopic,
    Table,
    Topic,
    TypeOfData,
    TypeOfOrganisation,
    TypeOfStatistic,
    UKCountry,
    Upload,
)
from application.utils import generate_review_token

PARENT_AND_CHILD_ETHNICITIES = {
    "Cat": ["Tabby", "Maine Coon", "Ragdoll", "Scottish Fold", "Siamese", "Persian", "Russian Blue", "Munchkin"],
    "Dog": ["English Mastiff", "Irish Setter", "Pembroke Welsh Corgi", "Scottish Terrier", "Beagle", "Akita"],
    "Bird": ["Parrot", "Canary", "Robin", "Cockatiel", "Cockatoo", "Budgie", "Macaw", "Dove", "Pigeon", "Owl"],
}


def _random_combination(from_iterable):
    return random.choice(list(itertools.combinations(from_iterable, random.randint(1, len(list(from_iterable))))))


class UserFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = User
        sqlalchemy_session_persistence = "flush"
        exclude = ("_password_to_hash",)

    _password_to_hash = factory.Faker("word")

    id = factory.Sequence(lambda x: x)
    email = factory.Faker("email")
    # password = factory.LazyAttribute(lambda o: hash_password(o._password_to_hash))  # Using `hash_password` is SLOW
    password = factory.LazyAttribute(lambda o: o._password_to_hash)
    active = factory.Faker("boolean")
    confirmed_at = factory.Faker("past_date", start_date="-1y")
    user_type = factory.LazyFunction(lambda: random.choice(list(TypeOfUser)))
    capabilities = factory.LazyAttribute(lambda o: CAPABILITIES[o.user_type])


class FrequencyOfReleaseFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = FrequencyOfRelease
        sqlalchemy_session_persistence = "flush"

    id = factory.Sequence(lambda x: x)
    description = factory.Faker("text")
    position = factory.SelfAttribute("id")


class LowestLevelOfGeographyFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = LowestLevelOfGeography
        sqlalchemy_session_persistence = "flush"

    name = factory.Faker("sentence", nb_words=3)
    description = factory.Faker("sentence", nb_words=6)
    position = factory.Sequence(lambda x: x)


class TypeOfStatisticFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = TypeOfStatistic
        sqlalchemy_session_persistence = "flush"

    id = factory.Sequence(lambda x: x)
    internal = factory.Faker("sentence", nb_words=5)
    external = factory.Faker("sentence", nb_words=5)
    position = factory.SelfAttribute("id")


class OrganisationFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Organisation
        sqlalchemy_session_persistence = "flush"

    id = factory.Sequence(lambda x: x)
    name = factory.Faker("company")
    other_names = factory.LazyFunction(lambda: [])
    abbreviations = factory.LazyFunction(lambda: [])
    organisation_type = factory.LazyFunction(lambda: random.choice(list(TypeOfOrganisation)))


class DataSourceFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = DataSource
        sqlalchemy_session_persistence = "flush"

    id = factory.Sequence(lambda x: x)
    title = factory.Faker("sentence", nb_words=5)
    type_of_data = factory.LazyFunction(lambda: _random_combination(TypeOfData))
    type_of_statistic_id = factory.SelfAttribute("type_of_statistic.id")
    publisher_id = factory.SelfAttribute("publisher.id")
    source_url = factory.Faker("url")
    publication_date = factory.Faker("past_date", start_date="-30d")
    note_on_corrections_or_updates = factory.Faker("paragraph", nb_sentences=5)
    frequency_of_release_id = factory.SelfAttribute("frequency_of_release.id")
    frequency_of_release_other = factory.Faker("paragraph", nb_sentences=3)
    purpose = factory.Faker("paragraph", nb_sentences=3)

    # scalar relationships
    type_of_statistic = factory.SubFactory(TypeOfStatisticFactory)
    publisher = factory.SubFactory(OrganisationFactory)
    frequency_of_release = factory.SubFactory(FrequencyOfReleaseFactory)

    # array-based relationships
    @factory.post_generation
    def pages(self, create, extracted, **kwargs):
        if not create:
            return

        # If some pages were passed into the create invocation: eg factory.Create(pages=[page1, page2])
        if extracted is not None:
            # Attach those pages to this newly-created instance.
            for page in extracted:
                self.pages.append(page)


class UploadFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Upload
        sqlalchemy_session_persistence = None

    guid = factory.Faker("uuid4")
    title = factory.Faker("sentence", nb_words=5)
    file_name = factory.Faker("file_path", depth=3)
    description = factory.Faker("paragraph", nb_sentences=3)
    size = factory.LazyFunction(lambda: random.randint(0, 100_000))

    measure_version_id = None
    page_id = None
    page_version = None

    # array-based relationships
    @factory.post_generation
    def page(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            self.page = extracted
            self.measure_version_id = self.page.id
            self.page_id = self.page.guid
            self.page_version = self.page.version


class TopicFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Topic
        sqlalchemy_session_persistence = "flush"

    id = factory.Sequence(lambda x: x)
    slug = factory.LazyFunction(lambda: "-".join(Faker().words(nb=3)))
    title = factory.Faker("sentence", nb_words=6)
    description = factory.Faker("paragraph", nb_sentences=3)
    additional_description = factory.Faker("paragraph", nb_sentences=5)

    # array-based relationships
    @factory.post_generation
    def subtopics(self, create, extracted, **kwargs):
        if not create:
            return

        # If some subtopics were passed into the create invocation: eg factory.Create(subtopics=[subtopic1, subtopic2])
        if extracted is not None:
            # Attach those subtopics to this newly-created instance.
            for subtopic in extracted:
                self.subtopics.append(subtopic)

    # NOTE: Not including relationships 'towards' MeasureVersionFactory; see tests/README.md


class SubtopicFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Subtopic
        sqlalchemy_session_persistence = "flush"

    id = factory.Sequence(lambda x: x)
    slug = factory.LazyFunction(lambda: "-".join(Faker().words(nb=3)))
    title = factory.Faker("sentence", nb_words=6)
    position = factory.Sequence(lambda x: x)
    topic_id = factory.SelfAttribute("topic.id")

    # scalar relationships
    topic = factory.SubFactory(TopicFactory)

    @factory.post_generation
    def measures(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted is not None:
            for measure in extracted:
                self.measures.append(measure)

    # NOTE: Not including relationships 'towards' MeasureVersionFactory; see tests/README.md


class MeasureFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Measure
        sqlalchemy_session_persistence = "flush"

    id = factory.Sequence(lambda x: x)
    slug = factory.LazyFunction(lambda: "-".join(Faker().words(nb=3)))
    position = factory.Sequence(lambda x: x)
    reference = factory.LazyFunction(lambda: " ".join(Faker().words(nb=2)))

    # array-based relationships
    @factory.post_generation
    def subtopics(self, create, extracted, **kwargs):
        if not create:
            return

        # If some subtopics were passed into the create invocation: eg factory.Create(subtopics=[subtopic1, subtopic2])
        if extracted is not None:
            # Attach those subtopics to this newly-created instance.
            for subtopic in extracted:
                self.subtopics.append(subtopic)

        # Otherwise, just create an subtopic and attach it.
        else:
            self.subtopics = [SubtopicFactory(**kwargs)]


# TODO: REMOVE
class HomePageFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = MeasureVersion
        sqlalchemy_session_persistence = "flush"

    id = factory.Sequence(lambda x: x)
    guid = factory.Faker("uuid4")
    page_type = "homepage"
    version = "1.0"


class TopicPageFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = MeasureVersion
        sqlalchemy_session_persistence = "flush"

    id = factory.Sequence(lambda x: x)
    guid = factory.Faker("uuid4")
    page_type = "topic"
    title = factory.Faker("sentence", nb_words=3)
    description = factory.Faker("paragraph", nb_sentences=3)
    additional_description = factory.Faker("paragraph", nb_sentences=5)
    version = "1.0"

    parent = factory.SubFactory(HomePageFactory)
    parent_id = factory.SelfAttribute("parent.id")
    parent_guid = factory.SelfAttribute("parent.guid")
    parent_version = factory.SelfAttribute("parent.version")


class SubtopicPageFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = MeasureVersion
        sqlalchemy_session_persistence = "flush"

    id = factory.Sequence(lambda x: x)
    guid = factory.Faker("uuid4")
    page_type = "subtopic"
    title = factory.Faker("sentence", nb_words=3)
    description = factory.Faker("paragraph", nb_sentences=3)
    additional_description = factory.Faker("paragraph", nb_sentences=5)
    version = "1.0"

    parent = factory.SubFactory(TopicPageFactory)
    parent_id = factory.SelfAttribute("parent.id")
    parent_guid = factory.SelfAttribute("parent.guid")
    parent_version = factory.SelfAttribute("parent.version")


# TODO: END REMOVE


class MeasureVersionFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = MeasureVersion
        sqlalchemy_session_persistence = "flush"
        exclude = {"_creator", "_publisher", "_unpublished", "_unpublisher"}

    # Underscored attributes are helpers that assist in the creation of a valid (business-logic-wise) measure version.
    _creator = factory.SubFactory(UserFactory)
    _publisher = factory.SubFactory(UserFactory)
    _unpublished = factory.LazyAttribute(lambda o: o.status == "UNPUBLISHED")
    _unpublisher = factory.Maybe("_unpublished", yes_declaration=factory.SubFactory(UserFactory))

    # columns
    id = factory.Sequence(lambda x: x)
    measure_id = factory.SelfAttribute("measure.id")
    guid = factory.Faker("uuid4")
    version = factory.LazyFunction(lambda: "1.0")
    internal_reference = factory.Faker("sentence", nb_words=2)
    latest = True  # TODO: Add smarter logic
    slug = factory.LazyFunction(lambda: "-".join(Faker().words(nb=3)))
    review_token = factory.LazyAttribute(
        lambda o: generate_review_token(o.guid, o.version)
        if publish_status[o.status] >= publish_status["DEPARTMENT_REVIEW"]
        else None
    )
    description = factory.Faker("paragraph", nb_sentences=3)
    additional_description = factory.Faker("paragraph", nb_sentences=5)
    page_type = factory.LazyFunction(lambda: "measure")
    position = factory.Sequence(lambda x: x)
    status = factory.LazyFunction(lambda: random.choice([status for status in publish_status.keys()]))
    created_at = factory.Faker("date_between", start_date="-30d", end_date="-7d")
    created_by = factory.SelfAttribute("_creator.email")
    updated_at = factory.Faker("past_date", start_date="-7d")
    last_updated_by = factory.SelfAttribute("_creator.email")
    published = factory.LazyAttribute(lambda o: True if o.status == "APPROVED" else False)
    published_at = factory.Maybe("published", yes_declaration=factory.Faker("past_date", start_date="-7d"))
    published_by = factory.Maybe("published", yes_declaration=factory.SelfAttribute("_publisher.email"))
    unpublished_at = factory.Maybe("_unpublished", yes_declaration=Faker().past_date(start_date="-7d"))
    unpublished_by = factory.Maybe("_unpublished", yes_declaration=factory.SelfAttribute("_unpublisher.email"))
    db_version_id = factory.Sequence(lambda x: x)
    title = factory.Faker("sentence", nb_words=6)
    summary = factory.Faker("sentence", nb_words=10)
    need_to_know = factory.Faker("paragraph", nb_sentences=3)
    measure_summary = factory.Faker("paragraph", nb_sentences=3)
    ethnicity_definition_summary = factory.Faker("paragraph", nb_sentences=3)
    area_covered = factory.LazyFunction(lambda: _random_combination(UKCountry))
    time_covered = factory.Faker("paragraph", nb_sentences=3)
    external_edit_summary = factory.Faker("sentence", nb_words=10)
    internal_edit_summary = factory.Faker("sentence", nb_words=10)
    lowest_level_of_geography_id = factory.SelfAttribute("lowest_level_of_geography.name")
    methodology = factory.Faker("paragraph", nb_sentences=3)
    suppression_and_disclosure = factory.Faker("paragraph", nb_sentences=3)
    estimation = factory.Faker("paragraph", nb_sentences=3)
    related_publications = factory.Faker("paragraph", nb_sentences=3)
    qmi_url = factory.Faker("paragraph", nb_sentences=3)
    further_technical_information = factory.Faker("paragraph", nb_sentences=3)

    # TODO: REMOVE
    # unsupported: old way of doing things
    parent = factory.SubFactory(SubtopicPageFactory)
    parent_id = factory.SelfAttribute("parent.id")
    parent_guid = factory.SelfAttribute("parent.guid")
    parent_version = factory.SelfAttribute("parent.version")
    # TODO: END REMOVE

    # scalar relationships
    measure = factory.SubFactory(MeasureFactory)
    lowest_level_of_geography = factory.SubFactory(LowestLevelOfGeographyFactory)

    # one-to-many relatioships
    @factory.post_generation
    def uploads(self, create, extracted, **kwargs):
        if not create:
            return

        # If some uploads were passed into the create invocation: eg factory.Create(uploads=[upload1, upload2])
        if extracted:
            # Attach those uploads to this newly-created instance.
            for upload in extracted:
                self.uploads.append(upload)

        else:
            UploadFactory(page=self, **kwargs)

    # By default, do not create any dimensions. See alternative factory, `MeasureVersionWithDimensionFactory`
    dimensions = factory.LazyFunction(lambda: [])


class MeasureVersionWithDimensionFactory(MeasureVersionFactory):
    @factory.post_generation
    def dimensions(self, create, extracted, **kwargs):
        if not create:
            return

        # If some dimensions were passed into the create invocation:
        #   eg factory.Create(dimensions=[dimension1, dimension2])
        if extracted is not None:
            # Attach those dimensions to this newly-created instance.
            for dimension in extracted:
                self.dimensions.append(dimension)

        else:
            # self.dimensions.append(DimensionFactory(page=self, **kwargs))
            DimensionFactory(page=self, **kwargs)


class EthnicityFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Ethnicity
        sqlalchemy_session_persistence = "flush"

    id = factory.Sequence(lambda x: x)
    value = factory.Iterator([child for children in PARENT_AND_CHILD_ETHNICITIES.values() for child in children])
    position = factory.SelfAttribute("id")


class ClassificationFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Classification
        sqlalchemy_session_persistence = "flush"
        exclude = ("_parent_child_ethnicities",)

    _parent_child_ethnicities = factory.LazyFunction(
        lambda: {
            k: _random_combination(PARENT_AND_CHILD_ETHNICITIES[k])
            for k in _random_combination(PARENT_AND_CHILD_ETHNICITIES.keys())
        }
    )

    id = factory.Sequence(lambda x: str(x))
    title = factory.Faker("sentence", nb_words=5)
    long_title = factory.Faker("sentence", nb_words=10)
    subfamily = factory.Faker("word")
    position = factory.Sequence(lambda x: x)

    # array-based relationships
    @factory.lazy_attribute
    def parent_values(self):
        parent_values = []

        for i, parent in enumerate(self._parent_child_ethnicities.keys()):
            parent_values.append(EthnicityFactory(value=parent, position=i * 1000))

        return parent_values

    @factory.lazy_attribute
    def ethnicities(self):
        ethnicities = []

        for i, children in enumerate(self._parent_child_ethnicities.values()):
            for j, child in enumerate(children, start=1):
                ethnicities.append(EthnicityFactory(value=child, position=(i * 1000) + j))

        return ethnicities


class DimensionClassificationFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = DimensionClassification
        sqlalchemy_session_persistence = "flush"

    # columns
    dimension_guid = factory.SelfAttribute("dimension.guid")
    classification_id = factory.SelfAttribute("classification.id")

    includes_parents = factory.Faker("boolean")
    includes_all = factory.Faker("boolean")
    includes_unknown = factory.Faker("boolean")

    classification = factory.SubFactory(ClassificationFactory)
    dimension = factory.SubFactory("tests.models.DimensionFactory")

    # NOTE: Not including relationships 'towards' MeasureVersionFactory; see tests/README.md


class _ChartAndTableFactoryMixin(factory.alchemy.SQLAlchemyModelFactory):
    id = factory.Sequence(lambda x: x)
    classification_id = factory.SelfAttribute("classification.id")
    includes_parents = factory.Faker("boolean")
    includes_all = factory.Faker("boolean")
    includes_unknown = factory.Faker("boolean")

    # scalar relationships
    classification = factory.SubFactory(ClassificationFactory)


class ChartFactory(_ChartAndTableFactoryMixin):
    class Meta:
        model = Chart
        sqlalchemy_session_persistence = "flush"


class TableFactory(_ChartAndTableFactoryMixin):
    class Meta:
        model = Table
        sqlalchemy_session_persistence = "flush"


class DimensionFactory(factory.alchemy.SQLAlchemyModelFactory):
    """
    TODO: Needs further work around generating chart/table highcharts and source data (maybe).
    """

    class Meta:
        model = Dimension
        sqlalchemy_session_persistence = None

    guid = factory.Faker("uuid4")
    title = factory.Faker("sentence", nb_words=5)
    time_period = "2018/19"  # questionable
    summary = factory.Faker("sentence", nb_words=10)

    created_at = factory.Faker("past_date", start_date="-30d")
    updated_at = factory.Faker("past_date", start_date="-7d")

    # Too hard to realistically generate valid highcharts chart/table data, so leave these blank by default.
    # If tests need them ... DIY.
    chart = None
    table = None
    chart_builder_version = 2
    chart_source_data = None
    chart_2_source_data = None

    table_source_data = {}
    table_builder_version = 2
    table_2_source_data = {}

    measure_version_id = None  # Configured via `page` post_generation attribute
    page_id = None  # Configured via `page` post_generation attribute
    page_version = None  # Configured via `page` post_generation attribute

    position = factory.Sequence(lambda x: x)

    chart_id = factory.Maybe("dimension_chart", factory.SelfAttribute("dimension_chart.id"))
    table_id = factory.Maybe("dimension_table", factory.SelfAttribute("dimension_table.id"))

    # scalar relationships
    dimension_chart = factory.SubFactory(ChartFactory)
    dimension_table = factory.SubFactory(TableFactory)

    # array-based relationships
    @factory.post_generation
    def page(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            self.page = extracted
            self.measure_version_id = self.page.id
            self.page_id = self.page.guid
            self.page_version = self.page.version

        else:
            self.page = MeasureVersionFactory(dimensions=[self])
            self.measure_version_id = self.page.id
            self.page_id = self.page.guid
            self.page_version = self.page.version

    @factory.post_generation
    def classification_links(self, create, extracted, **kwargs):
        if not create:
            return

        # If some classification_links were passed into the create invocation:
        #   eg factory.Create(classification_links=[classification_link1, classification_link2])
        if extracted is not None:
            # Attach those classification_links to this newly-created instance.
            for classification_link in extracted:
                self.classification_links.append(classification_link)

        else:
            self.classification_links = [DimensionClassificationFactory(dimension=self, **kwargs)]

    # NOTE: Not including relationships 'towards' MeasureVersionFactory; see tests/README.md


def __get_all_subclasses(cls):
    all_subclasses = []

    for subclass in cls.__subclasses__():
        all_subclasses.append(subclass)
        all_subclasses.extend(__get_all_subclasses(subclass))

    return all_subclasses


ALL_FACTORIES = __get_all_subclasses(factory.alchemy.SQLAlchemyModelFactory)
__all__ = [factory.__name__ for factory in ALL_FACTORIES]
