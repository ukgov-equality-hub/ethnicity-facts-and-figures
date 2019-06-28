from application.cms.models import DataSource

from tests.models import DataSourceFactory, OrganisationFactory


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

        assert DataSource.search("home office survey") == [data_source]

    def test_search_should_match_publisher_abbreviation(self):

        dwp = OrganisationFactory.create(name="Department for Work and Pensions", abbreviations=["DWP"])
        dfe = OrganisationFactory.create(name="Department for Education", abbreviations=["FO"])

        data_source = DataSourceFactory.create(title="Workforce Survey", source_url=None, publisher=dwp)
        DataSourceFactory.create(title="Workforce Survey", source_url=None, publisher=dfe)

        assert DataSource.search("dwp workforce") == [data_source]

    def test_search_be_limited_by_param(self):

        for _ in range(20):
            DataSourceFactory.create(title="Workforce Survey")

        assert len(DataSource.search("survey", limit=10)) == 10
