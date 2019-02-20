import re

import pytest
from bs4 import BeautifulSoup
from flask import url_for

from application.auth.models import TypeOfUser
from application.cms.models import UKCountry, TypeOfData
from application.config import Config
from tests.models import (
    MeasureVersionFactory,
    DataSourceFactory,
    TopicFactory,
    SubtopicFactory,
    MeasureFactory,
    MeasureVersionWithDimensionFactory,
    UserFactory,
)


def test_homepage_includes_mailing_list_sign_up(test_app_client, logged_in_rdu_user, app):

    response = test_app_client.get(url_for("static_site.index"))

    assert response.status_code == 200
    page = BeautifulSoup(response.get_data(as_text=True), "html.parser")

    assert page.select_one(
        "form[action=" + app.config["NEWSLETTER_SUBSCRIBE_URL"] + "]"
    ), "Mailing list subscription form should be present"

    assert page.find_all("label", text="Email address")[0], "E-mail address label should be present"
    assert page.select_one("input[name=EMAIL]"), "E-mail address field should be present"
    assert page.find_all("button", text="Subscribe")[0], "Subscribe button should be present"


def test_homepage_search_links_to_google_custom_url_before_javascript(test_app_client):
    resp = test_app_client.get(url_for("static_site.search"))

    assert resp.status_code == 200
    page = BeautifulSoup(resp.get_data(as_text=True), "html.parser")

    search_forms = page.header.select("#search-form")
    assert len(search_forms) == 1

    assert search_forms[0]["action"] == "https://cse.google.com/cse/publicurl"
    assert search_forms[0].select("[name=cx]")[0]["value"] == Config.GOOGLE_CUSTOM_SEARCH_ID


def test_rdu_user_can_see_page_if_not_shared(test_app_client, logged_in_rdu_user):
    measure_version = MeasureVersionFactory(title="Test Measure Page", measure__shared_with=[])
    assert measure_version.measure.shared_with == []
    assert logged_in_rdu_user.measures == []

    resp = test_app_client.get(
        url_for(
            "static_site.measure_version",
            topic_slug=measure_version.measure.subtopic.topic.slug,
            subtopic_slug=measure_version.measure.subtopic.slug,
            measure_slug=measure_version.measure.slug,
            version=measure_version.version,
        )
    )

    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
    assert page.h1.text.strip() == "Test Measure Page"


def test_departmental_user_cannot_see_draft(test_app_client, logged_in_dept_user):
    measure_version = MeasureVersionFactory(title="Test Measure Page", measure__shared_with=[], status="DRAFT")
    assert measure_version.measure.shared_with == []
    assert logged_in_dept_user.measures == []

    resp = test_app_client.get(
        url_for(
            "static_site.measure_version",
            topic_slug=measure_version.measure.subtopic.topic.slug,
            subtopic_slug=measure_version.measure.subtopic.slug,
            measure_slug=measure_version.measure.slug,
            version=measure_version.version,
        )
    )

    assert resp.status_code == 403


def test_departmental_user_can_see_draft_measure_if_they_have_access(test_app_client, logged_in_dept_user):
    measure_version = MeasureVersionFactory(
        title="Test Measure Page", measure__shared_with=[logged_in_dept_user], status="DRAFT"
    )

    resp = test_app_client.get(
        url_for(
            "static_site.measure_version",
            topic_slug=measure_version.measure.subtopic.topic.slug,
            subtopic_slug=measure_version.measure.subtopic.slug,
            measure_slug=measure_version.measure.slug,
            version=measure_version.version,
        )
    )

    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
    assert page.h1.text.strip() == "Test Measure Page"


def test_departmental_user_can_see_published_measure(test_app_client, logged_in_dept_user):
    measure_version = MeasureVersionFactory(title="Test Measure Page", measure__shared_with=[], status="APPROVED")

    resp = test_app_client.get(
        url_for(
            "static_site.measure_version",
            topic_slug=measure_version.measure.subtopic.topic.slug,
            subtopic_slug=measure_version.measure.subtopic.slug,
            measure_slug=measure_version.measure.slug,
            version=measure_version.version,
        )
    )

    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
    assert page.h1.text.strip() == "Test Measure Page"


def test_departmental_user_can_see_latest_published_version(test_app_client, logged_in_dept_user):

    measure = MeasureFactory(shared_with=[])

    MeasureVersionFactory(title="Old Test Measure Page", status="APPROVED", measure=measure, version="1.0")
    MeasureVersionFactory(title="Updated Test Measure Page", status="DRAFT", measure=measure, version="2.0")

    resp = test_app_client.get(
        url_for(
            "static_site.measure_version",
            topic_slug=measure.subtopic.topic.slug,
            subtopic_slug=measure.subtopic.slug,
            measure_slug=measure.slug,
            version="latest",
        )
    )

    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
    assert page.h1.text.strip() == "Old Test Measure Page"


def test_departmental_user_can_see_latest_draft_version_if_they_have_access(test_app_client, logged_in_dept_user):

    measure = MeasureFactory(shared_with=[logged_in_dept_user])

    MeasureVersionFactory(title="Old Test Measure Page", status="APPROVED", measure=measure, version="1.0")
    MeasureVersionFactory(title="Updated Test Measure Page", status="DRAFT", measure=measure, version="2.0")

    resp = test_app_client.get(
        url_for(
            "static_site.measure_version",
            topic_slug=measure.subtopic.topic.slug,
            subtopic_slug=measure.subtopic.slug,
            measure_slug=measure.slug,
            version="latest",
        )
    )

    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
    assert page.h1.text.strip() == "Updated Test Measure Page"


def test_rdu_user_cans_see_latest_draft_version(test_app_client, logged_in_rdu_user):

    measure = MeasureFactory(shared_with=[])

    MeasureVersionFactory(title="Old Test Measure Page", status="APPROVED", measure=measure, version="1.0")
    MeasureVersionFactory(title="Updated Test Measure Page", status="DRAFT", measure=measure, version="2.0")

    resp = test_app_client.get(
        url_for(
            "static_site.measure_version",
            topic_slug=measure.subtopic.topic.slug,
            subtopic_slug=measure.subtopic.slug,
            measure_slug=measure.slug,
            version="latest",
        )
    )

    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
    assert page.h1.text.strip() == "Updated Test Measure Page"


def test_get_file_download_returns_404(test_app_client, logged_in_rdu_user):
    measure_version = MeasureVersionFactory(uploads=[])
    resp = test_app_client.get(
        url_for(
            "static_site.measure_version_file_download",
            topic_slug=measure_version.measure.subtopic.topic.slug,
            subtopic_slug=measure_version.measure.subtopic.slug,
            measure_slug=measure_version.measure.slug,
            version=measure_version.version,
            filename="nofile.csv",
        )
    )

    assert resp.status_code == 404


def test_view_export_page(test_app_client, logged_in_rdu_user):
    data_source = DataSourceFactory(
        title="DWP Stats",
        source_url="http://dwp.gov.uk",
        note_on_corrections_or_updates="Note on corrections or updates",
        publication_date="15th May 2017",
        publisher__name="Department for Work and Pensions",
        type_of_data=[TypeOfData.SURVEY],
        type_of_statistic__external="National",
        frequency_of_release__description="Quarterly",
        purpose="Purpose of data source",
    )
    measure_version = MeasureVersionFactory(
        status="DRAFT",
        title="Test Measure Page",
        area_covered=[UKCountry.ENGLAND],
        lowest_level_of_geography__name="UK",
        time_covered="4 months",
        need_to_know="Need to know this",
        measure_summary="Unemployment measure summary",
        ethnicity_definition_summary="This is a summary of ethnicity definitions",
        methodology="how we measure unemployment",
        suppression_and_disclosure="Suppression rules and disclosure control",
        data_sources=[data_source],
        measure__slug="test-measure-page-slug",
    )

    resp = test_app_client.get(
        url_for(
            "static_site.measure_version_markdown",
            topic_slug=measure_version.measure.subtopic.topic.slug,
            subtopic_slug=measure_version.measure.subtopic.slug,
            measure_slug=measure_version.measure.slug,
            version=measure_version.version,
        )
    )

    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
    assert page.h1.text.strip() == "Title: Test Measure Page"

    metadata = page.find("div", class_="metadata")
    assert metadata.find("div", attrs={"id": "department"}).text.strip() == "Department"
    assert metadata.find("div", attrs={"id": "area-covered"}).text.strip() == "Areas covered"
    assert metadata.find("div", attrs={"id": "lowest-level-of-geography"}).text.strip() == "Geographic breakdown"
    assert metadata.find("div", attrs={"id": "time-period"}).text.strip() == "Time period covered"

    assert metadata.find("div", attrs={"id": "department-name"}).text.strip() == "Department for Work and Pensions"
    assert metadata.find("div", attrs={"id": "area-covered-value"}).text.strip() == "England"
    assert metadata.find("div", attrs={"id": "lowest-level-of-geography-value"}).text.strip() == "UK"
    assert metadata.find("div", attrs={"id": "time-period-value"}).text.strip() == "4 months"

    things_to_know = page.find("div", attrs={"id": "things-you-need-to-know"})
    assert things_to_know.text.strip() == "Need to know this"

    what_measured = page.find("div", attrs={"id": "what-the-data-measures"})
    assert what_measured.text.strip() == "Unemployment measure summary"

    categories_used = page.find("div", attrs={"id": "ethnic-categories-used-in-this-data"})
    assert categories_used.text.strip() == "This is a summary of ethnicity definitions"

    methodology = page.find("div", attrs={"id": "methodology"})
    assert methodology.text.strip() == "how we measure unemployment"

    suppression_and_disclosure = page.find("div", attrs={"id": "suppression-and-disclosure"})
    assert suppression_and_disclosure.text.strip() == "Suppression rules and disclosure control"

    data_source_details = page.find("h1", attrs={"id": "data-sources"})
    assert data_source_details.text.strip() == "Data sources"

    primary_source = page.find("div", attrs={"id": "primary-source-title"})
    assert primary_source.text.strip() == "Title of data source"

    primary_source_value = page.find("div", attrs={"id": "primary-source-name"})
    assert primary_source_value.text.strip() == "DWP Stats"

    type_of_data = page.find("div", attrs={"id": "type-of-data"})
    assert type_of_data.text.strip() == "Type of data"

    type_of_data_value = page.find("div", attrs={"id": "type-of-data-value"})
    assert type_of_data_value.text.strip() == "Survey data"

    type_of_statistic = page.find("div", attrs={"id": "type-of-statistic"})
    assert type_of_statistic.text.strip() == "Type of statistic"

    type_of_statistic_value = page.find("div", attrs={"id": "type-of-statistic-value"})
    assert type_of_statistic_value.text.strip() == "National"

    publisher = page.find("div", attrs={"id": "publisher"})
    assert publisher.text.strip() == "Source data published by"

    publisher_value = page.find("div", attrs={"id": "publisher-value"})
    assert publisher_value.text.strip() == "Department for Work and Pensions"

    source_url = page.find("div", attrs={"id": "source-url"})
    assert source_url.text.strip() == "Link to data source"

    source_url_value = page.find("div", attrs={"id": "source-url-value"})
    assert source_url_value.text.strip() == "http://dwp.gov.uk"

    publication_release = page.find("div", attrs={"id": "publication-release-date"})
    assert publication_release.text.strip() == "Source data publication date"

    publication_release_value = page.find("div", attrs={"id": "publication-release-date-value"})
    assert publication_release_value.text.strip() == "15th May 2017"

    notes_on_corrections_or_updates = page.find("div", attrs={"id": "notes-on-corrections-or-update"})
    assert notes_on_corrections_or_updates.text.strip() == "Corrections or updates"

    notes_on_corrections_or_updates_value = page.find("div", attrs={"id": "notes-on-corrections-or-update-value"})
    assert notes_on_corrections_or_updates_value.text.strip() == "Note on corrections or updates"

    publication_frequency = page.find("div", attrs={"id": "publication-frequency"})
    assert publication_frequency.text.strip() == "How often is the source data published?"

    publication_frequency_value = page.find("div", attrs={"id": "publication-frequency-value"})
    assert publication_frequency_value.text.strip() == "Quarterly"

    purpose_of_data = page.find("div", attrs={"id": "purpose-of-data-source"})
    assert purpose_of_data.text.strip() == "Purpose of data source"

    purpose_of_data_value = page.find("div", attrs={"id": "purpose-of-data-source-value"})
    assert purpose_of_data_value.text.strip() == "Purpose of data source"


def test_view_topic_page(test_app_client, logged_in_rdu_user):
    topic = TopicFactory(title="Test topic page")
    resp = test_app_client.get(url_for("static_site.topic", topic_slug=topic.slug))

    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
    assert page.h1.text.strip() == "Test topic page"


def test_view_topic_page_contains_reordering_javascript_for_admin_user_only(test_app_client):
    rdu_user = UserFactory(user_type=TypeOfUser.RDU_USER)
    admin_user = UserFactory(user_type=TypeOfUser.ADMIN_USER)
    topic = TopicFactory(title="Test topic page")

    with test_app_client.session_transaction() as session:
        session["user_id"] = admin_user.id

    resp = test_app_client.get(url_for("static_site.topic", topic_slug=topic.slug))

    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
    assert page.h1.text.strip() == "Test topic page"
    assert len(page.find_all("script", text=re.compile("setupReorderableTables"))) == 1

    with test_app_client.session_transaction() as session:
        session["user_id"] = rdu_user.id

    resp = test_app_client.get(url_for("static_site.topic", topic_slug=topic.slug))

    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
    assert page.h1.text.strip() == "Test topic page"
    assert len(page.find_all("script", text=re.compile("setupReorderableTables"))) == 0


def test_view_topic_page_in_static_mode_does_not_contain_reordering_javascript(test_app_client, logged_in_admin_user):
    topic = TopicFactory(title="Test topic page")
    resp = test_app_client.get(url_for("static_site.topic", topic_slug=topic.slug))

    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
    assert page.h1.text.strip() == "Test topic page"
    assert len(page.find_all("script", text=re.compile("setupReorderableTables"))) == 1

    resp = test_app_client.get(url_for("static_site.topic", topic_slug=topic.slug, static_mode=True))

    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
    assert page.h1.text.strip() == "Test topic page"
    assert len(page.find_all("script", text=re.compile("setupReorderableTables"))) == 0


def test_view_index_page_only_contains_one_topic(test_app_client, logged_in_rdu_user):
    measure_version = MeasureVersionFactory(status="APPROVED")
    resp = test_app_client.get(url_for("static_site.index"))

    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
    assert page.h1.text.strip() == "Ethnicity facts and figures"
    topics = page.find_all("div", class_="topic")
    assert len(topics) == 1
    assert topics[0].find("a").text.strip() == measure_version.measure.subtopic.topic.title


def test_view_sandbox_topic(test_app_client, logged_in_rdu_user):

    sandbox_topic = TopicFactory(slug="testing-space", title="Test sandbox topic")
    resp = test_app_client.get(url_for("static_site.topic", topic_slug=sandbox_topic.slug))

    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
    assert page.h1.text.strip() == "Test sandbox topic"


def test_measure_page_social_sharing(app, test_app_client, logged_in_rdu_user):
    measure_version = MeasureVersionFactory(
        title="Test Measure Page", summary="Unemployment Summary\n * This is a summary bullet"
    )
    resp = test_app_client.get(
        url_for(
            "static_site.measure_version",
            topic_slug=measure_version.measure.subtopic.topic.slug,
            subtopic_slug=measure_version.measure.subtopic.slug,
            measure_slug=measure_version.measure.slug,
            version=measure_version.version,
        )
    )

    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")

    expected_social_attributes_and_values = {
        "og:type": "article",
        "og:title": "Test Measure Page",
        "og:image": app.config["RDU_SITE"] + "/static/images/opengraph-image.png",
        "og:description": "This is a summary bullet",
    }
    for attribute, value in expected_social_attributes_and_values.items():
        social_sharing_meta = page.findAll("meta", property=attribute)
        assert len(social_sharing_meta) == 1, f"Missing social sharing metadata for {attribute}"
        assert social_sharing_meta[0].get("content") == value

    expected_twitter_attributes_and_values = {"twitter:card": "summary"}
    for twitter_sharing_attribute, value in expected_twitter_attributes_and_values.items():
        twitter_sharing_meta = page.findAll("meta", {"name": twitter_sharing_attribute})
        assert len(twitter_sharing_meta) == 1, f"Missing twitter sharing metadata for {twitter_sharing_attribute}"
        assert twitter_sharing_meta[0].get("content") == value


def test_view_measure_page(test_app_client, logged_in_rdu_user):
    data_source = DataSourceFactory(
        title="DWP Stats",
        source_url="http://dwp.gov.uk",
        note_on_corrections_or_updates="Note on corrections or updates",
        publication_date="15th May 2017",
        publisher__name="Department for Work and Pensions",
        type_of_data=[TypeOfData.SURVEY],
        type_of_statistic__external="National",
        frequency_of_release__description="Quarterly",
        purpose="Purpose of data source",
    )
    measure_version = MeasureVersionFactory(
        status="DRAFT",
        title="Test Measure Page",
        area_covered=[UKCountry.ENGLAND],
        lowest_level_of_geography__name="UK",
        time_covered="4 months",
        need_to_know="Need to know this",
        measure_summary="Unemployment measure summary",
        ethnicity_definition_summary="This is a summary of ethnicity definitions",
        methodology="how we measure unemployment",
        suppression_and_disclosure="Suppression rules and disclosure control",
        data_sources=[data_source],
    )

    resp = test_app_client.get(
        url_for(
            "static_site.measure_version",
            topic_slug=measure_version.measure.subtopic.topic.slug,
            subtopic_slug=measure_version.measure.subtopic.slug,
            measure_slug=measure_version.measure.slug,
            version=measure_version.version,
        )
    )

    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")

    assert page.h1.text.strip() == measure_version.title

    # check that the status bar is shown
    assert page.find("div", class_="status")

    # check metadata
    metadata_titles = page.find("div", class_="metadata").find_all("dt")
    assert len(metadata_titles) == 4
    assert metadata_titles[0].text == "Department:"
    assert metadata_titles[1].text == "Source:"
    assert metadata_titles[2].text == "Area covered:"
    assert metadata_titles[3].text == "Time period:"

    metadata_values = page.find("div", class_="metadata").find_all("dd")
    assert len(metadata_values) == 4
    assert metadata_values[0].text.strip() == "Department for Work and Pensions"
    assert metadata_values[1].text.strip() == "DWP Stats"
    assert metadata_values[2].text.strip() == "England"
    assert metadata_values[3].text.strip() == "4 months"

    things_to_know = page.find("span", attrs={"id": "things-you-need-to-know"})
    assert things_to_know
    assert things_to_know.text.strip() == "Things you need to know"

    what_measured = page.find("span", attrs={"id": "what-the-data-measures"})
    assert what_measured
    assert what_measured.text.strip() == "What the data measures"

    categories_used = page.find("span", attrs={"id": "the-ethnic-categories-used-in-this-data"})
    assert categories_used
    assert categories_used.text.strip() == "The ethnic categories used in this data"

    # methodology accordion
    methodology = page.find("h2", attrs={"id": "methodology"})
    assert methodology.text.strip() == "Methodology"
    methodology_headings = methodology.parent.parent.find_all("h3")
    assert methodology_headings[0].text.strip() == "Methodology"
    assert methodology_headings[1].text.strip() == "Suppression rules and disclosure control"
    assert methodology_headings[2].text.strip() == "Rounding"
    assert methodology_headings[3].text.strip() == "Related publications"

    # data sources accordion
    data_source_details = page.find("h2", attrs={"id": "data-sources"})
    assert data_source_details.text.strip() == "Data sources"
    data_source_headings = data_source_details.parent.parent.find_all("h3")
    assert data_source_headings[0].text.strip() == "Source"
    assert data_source_headings[1].text.strip() == "Type of data"
    assert data_source_headings[2].text.strip() == "Type of statistic"
    assert data_source_headings[3].text.strip() == "Publisher"
    assert data_source_headings[4].text.strip() == "Note on corrections or updates"
    assert data_source_headings[5].text.strip() == "Publication frequency"
    assert data_source_headings[6].text.strip() == "Purpose of data source"
    # These dates are temporarliy excluded while being reviewed - remove this once they are added back to the page
    assert "Publication release date" not in data_source_headings

    download_the_data = page.find("h2", attrs={"id": "download-the-data"})
    assert download_the_data
    assert download_the_data.text.strip() == "Download the data"


@pytest.mark.parametrize(["number_of_topics", "row_counts"], ((1, (1,)), (3, (3,)), (5, (3, 2)), (9, (3, 3, 3))))
def test_homepage_topics_display_in_rows_with_three_columns(
    number_of_topics, row_counts, test_app_client, logged_in_rdu_user
):
    for i in range(number_of_topics):
        topic = TopicFactory(slug=f"topic-{i}", title=f"Test topic page #{i}")
        subtopic = SubtopicFactory(slug=f"subtopic-{i}", title=f"Test subtopic page #{i}", topic=topic)
        measure = MeasureFactory(slug=f"measure-{i}", subtopics=[subtopic])
        MeasureVersionFactory(status="APPROVED", title=f"Test measure page #{i}", version="1.0", measure=measure)

    resp = test_app_client.get(url_for("static_site.index"))
    assert resp.status_code == 200

    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
    topic_rows = page.select(".topic-row")

    assert len(topic_rows) == len(row_counts)
    for i, topic_row in enumerate(topic_rows):
        assert len(topic_rows[i].select(".topic")) == row_counts[i]


@pytest.mark.parametrize(
    "measure_published, static_mode, topic_should_be_visible",
    ((True, True, True), (True, False, True), (False, True, False), (False, False, True)),
)
def test_homepage_only_shows_topics_with_published_measures_for_site_type(
    measure_published, static_mode, topic_should_be_visible, test_app_client, logged_in_rdu_user
):
    MeasureVersionFactory(
        status="APPROVED" if measure_published else "DRAFT",
        published=measure_published,
        measure__subtopics__topic__title="Test topic page",
    )

    resp = test_app_client.get(url_for("static_site.index", static_mode=static_mode))
    assert resp.status_code == 200

    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")

    assert bool(page(string=re.compile("Test topic page"))) is topic_should_be_visible


@pytest.mark.parametrize(
    "measure_published, static_mode, subtopic_should_be_visible",
    ((True, True, True), (True, False, True), (False, True, False), (False, False, True)),
)
def test_topic_page_only_shows_subtopics_with_published_measures_for_static_site_build(
    measure_published, static_mode, subtopic_should_be_visible, test_app_client, logged_in_rdu_user
):
    MeasureVersionFactory(
        status="APPROVED" if measure_published else "DRAFT",
        published=measure_published,
        measure__subtopics__topic__slug="test-topic",
        measure__subtopics__topic__title="Test topic page",
        measure__subtopics__title="Test subtopic page",
    )

    resp = test_app_client.get(url_for("static_site.topic", topic_slug="test-topic", static_mode=static_mode))
    assert resp.status_code == 200

    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")

    assert bool(page(string=re.compile("Test subtopic page"))) is subtopic_should_be_visible


@pytest.mark.parametrize(
    "measure_shared, measure_published, subtopic_should_be_visible",
    ((True, True, True), (True, False, True), (False, True, True), (False, False, False)),
)
def test_topic_page_only_shows_subtopics_with_shared_or_published_measures_for_dept_user_type(
    measure_shared, measure_published, subtopic_should_be_visible, test_app_client, logged_in_dept_user
):
    MeasureVersionFactory(
        status="APPROVED" if measure_published else "DRAFT",
        published=measure_published,
        measure__shared_with=[logged_in_dept_user] if measure_shared else [],
        measure__subtopics__topic__slug="test-topic",
        measure__subtopics__topic__title="Test topic page",
        measure__subtopics__title="Test subtopic page",
    )

    resp = test_app_client.get(url_for("static_site.topic", topic_slug="test-topic"))
    assert resp.status_code == 200

    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")

    assert bool(page(string=re.compile("Test subtopic page"))) is subtopic_should_be_visible


@pytest.mark.parametrize(
    "user_type, empty_subtopic_should_be_visible", ((TypeOfUser.DEPT_USER, False), (TypeOfUser.RDU_USER, True))
)
def test_topic_page_only_shows_empty_subtopics_if_user_can_create_a_measure(
    user_type, empty_subtopic_should_be_visible, test_app_client
):
    user = UserFactory(user_type=user_type)
    SubtopicFactory(title="Test subtopic page", topic__slug="test-topic")

    with test_app_client.session_transaction() as session:
        session["user_id"] = user.id

    resp = test_app_client.get(url_for("static_site.topic", topic_slug="test-topic"))
    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")

    assert resp.status_code == 200
    assert bool(page(string=re.compile("Test subtopic page"))) is empty_subtopic_should_be_visible


def test_measure_page_share_links_do_not_contain_double_slashes_between_domain_and_path(
    test_app_client, logged_in_rdu_user
):
    measure_version = MeasureVersionFactory(
        status="DRAFT",
        measure__shared_with=[],
        measure__subtopics__topic__slug="topic",
        measure__subtopics__slug="subtopic",
        measure__slug="measure",
        measure__subtopics__topic__title="Test topic page",
        measure__subtopics__title="Test subtopic page",
    )
    assert measure_version.measure.shared_with == []
    assert logged_in_rdu_user.measures == []

    resp = test_app_client.get(
        url_for(
            "static_site.measure_version",
            topic_slug=measure_version.measure.subtopic.topic.slug,
            subtopic_slug=measure_version.measure.subtopic.slug,
            measure_slug=measure_version.measure.slug,
            version=measure_version.version,
        )
    )

    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")

    share_links = page.find("div", {"class": "share"}).findChildren("a")

    for share_link in share_links:
        assert (
            "https%3A//www.ethnicity-facts-figures.service.gov.uk/topic/subtopic/measure/latest" in share_link["href"]
        )


def test_latest_published_version_does_not_add_noindex_for_robots(test_app_client, logged_in_admin_user):
    # GIVEN the latest published version of a page with later draft created
    measure = MeasureFactory()
    # Outdated version
    MeasureVersionFactory(measure=measure, status="APPROVED", latest=False, version="1.0")
    # Latest published version
    latest_published_version = MeasureVersionFactory(measure=measure, status="APPROVED", latest=False, version="2.0")
    # Newer draft version
    MeasureVersionFactory(measure=measure, status="DRAFT", latest=True, version="2.1")

    # WHEN we get the rendered template

    resp = test_app_client.get(
        url_for(
            "static_site.measure_version",
            topic_slug=latest_published_version.measure.subtopic.topic.slug,
            subtopic_slug=latest_published_version.measure.subtopic.slug,
            measure_slug=latest_published_version.measure.slug,
            version=latest_published_version.version,
        )
    )
    # THEN it should not contain a noindex tag
    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
    robots_tags = page.find_all("meta", attrs={"name": "robots"}, content=lambda value: value and "noindex" in value)
    assert len(robots_tags) == 0


def test_previous_version_adds_noindex_for_robots(test_app_client, logged_in_admin_user):
    # GIVEN a page with a later published version
    measure = MeasureFactory()
    # Outdated version
    outdated_version = MeasureVersionFactory(measure=measure, status="APPROVED", latest=False, version="1.0")
    # Latest published version
    MeasureVersionFactory(measure=measure, status="APPROVED", latest=False, version="2.0")
    # Newer draft version
    MeasureVersionFactory(measure=measure, status="DRAFT", latest=True, version="2.1")

    # WHEN we get the rendered template

    resp = test_app_client.get(
        url_for(
            "static_site.measure_version",
            topic_slug=outdated_version.measure.subtopic.topic.slug,
            subtopic_slug=outdated_version.measure.subtopic.slug,
            measure_slug=outdated_version.measure.slug,
            version=outdated_version.version,
        )
    )
    # THEN it should contain a noindex tag
    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
    robots_tags = page.find_all("meta", attrs={"name": "robots"}, content=lambda value: value and "noindex" in value)
    assert len(robots_tags) == 1


class TestMeasurePage:
    """
    This class includes a set of tests that check download links for source data of a measure page.
    Unfortunately, without a refactor of how dimensions are passed into the measure page template, we aren't
    able to test how the static site renders these links. The static site builder passes in a specially-formatted
    set of dimensions that aren't available in 'static-mode style requests' to the CMS.

    Tech improvement ticket: https://trello.com/c/U4rMSk0w/70
    """

    @pytest.mark.parametrize(
        "static_mode, expected_url",
        (
            # ("yes", "<some_url>"),
            ("no", "/topic/subtopic/measure/1.0/dimension/dimension-guid/tabular-download"),
        ),
    )
    def test_measure_page_download_table_tabular_data_link_correct(
        self, test_app_client, logged_in_rdu_user, static_mode, expected_url
    ):
        from tests.test_data.chart_and_table import chart, simple_table

        MeasureVersionWithDimensionFactory(
            status="DRAFT",
            version="1.0",
            measure__subtopics__topic__slug="topic",
            measure__subtopics__slug="subtopic",
            measure__slug="measure",
            dimensions__guid="dimension-guid",
            dimensions__chart=chart,
            dimensions__table=simple_table(),
            uploads__guid="test-download",
        )

        resp = test_app_client.get(f"/topic/subtopic/measure/latest?static_mode={static_mode}", follow_redirects=False)
        page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")

        data_links = page.findAll("a", href=True, text="Download table data (CSV)")
        assert len(data_links) == 1
        assert data_links[0].attrs["href"] == expected_url

    @pytest.mark.parametrize(
        "static_mode, expected_url",
        (
            # ("yes", "<some_url>"),
            ("no", "/topic/subtopic/measure/1.0/dimension/dimension-guid/download"),
        ),
    )
    def test_measure_page_download_table_source_data_link_correct(
        self, test_app_client, logged_in_rdu_user, static_mode, expected_url
    ):
        from tests.test_data.chart_and_table import chart, simple_table

        MeasureVersionWithDimensionFactory(
            status="DRAFT",
            version="1.0",
            measure__subtopics__topic__slug="topic",
            measure__subtopics__slug="subtopic",
            measure__slug="measure",
            dimensions__guid="dimension-guid",
            dimensions__chart=chart,
            dimensions__table=simple_table(),
            uploads__guid="test-download",
        )
        resp = test_app_client.get(f"/topic/subtopic/measure/latest?static_mode={static_mode}", follow_redirects=False)
        page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")

        data_links = page.findAll("a", href=True, text="Source data (CSV)")
        assert len(data_links) == 1
        assert data_links[0].attrs["href"] == expected_url

    @pytest.mark.parametrize(
        "static_mode, expected_url",
        (
            # ("yes", "<some_url>"),
            ("no", "/topic/subtopic/measure/1.0/downloads/test-measure-page-data.csv"),
        ),
    )
    def test_measure_page_download_measure_source_data_link_correct(
        self, test_app_client, logged_in_rdu_user, static_mode, expected_url
    ):
        from tests.test_data.chart_and_table import chart, simple_table

        MeasureVersionWithDimensionFactory(
            status="DRAFT",
            version="1.0",
            measure__subtopics__topic__slug="topic",
            measure__subtopics__slug="subtopic",
            measure__slug="measure",
            dimensions__guid="dimension-guid",
            dimensions__chart=chart,
            dimensions__table=simple_table(),
            uploads__guid="test-download",
            uploads__title="Test measure page data",
            uploads__file_name="test-measure-page-data.csv",
        )
        resp = test_app_client.get("/topic/subtopic/measure/latest", follow_redirects=False)
        page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
        data_links = page.findAll("a", href=True, text=re.compile(r"Test measure page data\s+-\s+Spreadsheet"))
        assert len(data_links) == 1
        assert data_links[0].attrs["href"] == expected_url
