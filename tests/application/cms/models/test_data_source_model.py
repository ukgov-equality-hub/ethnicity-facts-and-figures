from application.cms.models import DataSource

import pytest

from tests.models import DataSourceFactory, OrganisationFactory, MeasureVersionFactory


class TestDataSourceModel:
    def test_search_should_match_full_phrase_case_insensitve(self):

        data_source = DataSourceFactory.create(title="Annual Population Survey", source_url=None, publisher_id=None)
        DataSourceFactory.create(title="2011 Census of England and Wales", source_url=None, publisher_id=None)

        assert DataSource.search("annual population survey") == [data_source]

    def test_search_should_match_keyword_case_insensitve(self):

        data_source = DataSourceFactory.create(title="Annual Population Survey", source_url=None, publisher_id=None)
        DataSourceFactory.create(title="2011 Census of England and Wales", source_url=None, publisher_id=None)

        assert DataSource.search("population") == [data_source]

    def test_search_should_only_return_results_matching_all_keywords(self):

        data_source = DataSourceFactory.create(title="Annual Population Survey", source_url=None, publisher_id=None)
        DataSourceFactory.create(title="Annual Workforce Survey", source_url=None, publisher_id=None)
        DataSourceFactory.create(title="Estimated Population Statistics", source_url=None, publisher_id=None)

        assert DataSource.search("survey population") == [data_source]

    def test_search_should_match_exact_source_url(self):

        data_source = DataSourceFactory.create(
            title="Annual Population Survey",
            source_url="https://assets.publishing.service.gov.uk/government/uploads/"
            + "system/uploads/attachment_data/file/4364643/2018-annual-population"
            + "-survey.pdf",
            publisher_id=None,
        )

        assert DataSource.search(
            "https://assets.publishing.service.gov.uk/government/uploads/system/uploads/"
            + "attachment_data/file/4364643/2018-annual-population-survey.pdf"
        ) == [data_source]

    def test_search_should_match_publisher_name(self):

        home_office = OrganisationFactory.create(name="Home Office")
        foreign_office = OrganisationFactory.create(name="Foreign Office")

        data_source = DataSourceFactory.create(title="Annual Population Survey", source_url=None, publisher=home_office)
        DataSourceFactory.create(title="Workforce Survey", source_url=None, publisher=foreign_office)

        assert DataSource.search("home office") == [data_source]

    def test_search_should_match_publisher_abbreviation(self):

        dwp = OrganisationFactory.create(name="Department for Work and Pensions", abbreviations=["DWP"])
        dfe = OrganisationFactory.create(name="Department for Education", abbreviations=["FO"])

        data_source = DataSourceFactory.create(title="Workforce Survey", source_url=None, publisher=dwp)
        DataSourceFactory.create(title="Workforce Survey", source_url=None, publisher=dfe)

        assert DataSource.search("dwp") == [data_source]

    def test_search_be_limited_by_param(self):

        for _ in range(5):
            DataSourceFactory.create(title="Workforce Survey")

        assert len(DataSource.search("survey", limit=2)) == 2

    def test_search_should_be_ordered_by_number_of_associated_measure_versions(self):

        data_source_associated_with_1_measure_version = DataSourceFactory.create(title="Survey")
        data_source_associated_with_2_measure_versions = DataSourceFactory.create(title="Survey")

        MeasureVersionFactory.create(data_sources=[data_source_associated_with_1_measure_version])

        for _ in range(2):
            MeasureVersionFactory.create(data_sources=[data_source_associated_with_2_measure_versions])

        search = DataSource.search("survey")

        assert len(search) == 2
        assert (
            data_source_associated_with_2_measure_versions == search[0]
        ), "Expected data source associated with 2 measure versions to be first"
        assert (
            data_source_associated_with_1_measure_version == search[1]
        ), "Expected data source associated with 1 measure version to be second"

    def test_merge_from_single_other_data_source(self):

        data_source_1 = DataSourceFactory.create()
        data_source_2 = DataSourceFactory.create()

        measure_version_associated_with_data_source_2 = MeasureVersionFactory.create(data_sources=[data_source_2])

        assert data_source_1.merge(data_source_ids=[data_source_2.id]) is True
        assert DataSource.query.get(data_source_2.id) is None

        assert measure_version_associated_with_data_source_2.data_sources == [data_source_1]

    def test_merge_from_two_other_data_sources(self):

        data_source_1 = DataSourceFactory.create()
        data_source_2 = DataSourceFactory.create()
        data_source_3 = DataSourceFactory.create()

        measure_version_associated_with_data_source_2 = MeasureVersionFactory.create(data_sources=[data_source_2])

        measure_version_associated_with_data_source_3 = MeasureVersionFactory.create(data_sources=[data_source_2])

        assert data_source_1.merge(data_source_ids=[data_source_2.id, data_source_3.id]) is True
        assert DataSource.query.get(data_source_2.id) is None
        assert DataSource.query.get(data_source_3.id) is None

        assert measure_version_associated_with_data_source_2.data_sources == [data_source_1]
        assert measure_version_associated_with_data_source_3.data_sources == [data_source_1]

    def test_merge_from_empty_array(self):

        data_source_1 = DataSourceFactory.create()

        with pytest.raises(ValueError):
            data_source_1.merge(data_source_ids=[])

    def test_merge_with_invalid_data_source_id(self):

        data_source_1 = DataSourceFactory.create()

        with pytest.raises(ValueError):
            data_source_1.merge(data_source_ids=[99999])
