import datetime
import re

import pytest
from bs4 import BeautifulSoup
from flask import url_for

from application.auth.models import TypeOfUser
from application.cms.models import UKCountry, TypeOfData, TESTING_SPACE_SLUG
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
from tests.utils import assert_strings_match_ignoring_whitespace


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
        purpose="There is no purpose",
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
        suppression_and_disclosure="Suppression and disclosure",
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

    assert page.h1.text.strip() == "Test Measure Page"
    assert_strings_match_ignoring_whitespace(
        page.find("div", attrs={"id": "data-source-1-publisher_id"}).text,
        "Source data published by Department for Work and Pensions",
    )
    assert_strings_match_ignoring_whitespace(
        page.find("div", attrs={"id": "area_covered"}).text, "Areas covered England"
    )
    assert_strings_match_ignoring_whitespace(
        page.find("div", attrs={"id": "lowest_level_of_geography_id"}).text, "Geographic breakdown UK"
    )
    assert_strings_match_ignoring_whitespace(
        page.find("div", attrs={"id": "time_covered"}).text, "Time period covered 4 months"
    )
    assert_strings_match_ignoring_whitespace(
        page.find("div", attrs={"id": "need_to_know"}).text, "Things you need to know Need to know this"
    )
    assert_strings_match_ignoring_whitespace(
        page.find("div", attrs={"id": "measure_summary"}).text, "What the data measures Unemployment measure summary"
    )
    assert_strings_match_ignoring_whitespace(
        page.find("div", attrs={"id": "ethnicity_definition_summary"}).text,
        "The ethnic categories used in this data This is a summary of ethnicity definitions",
    )
    assert_strings_match_ignoring_whitespace(
        page.find("div", attrs={"id": "methodology"}).text, "Methodology how we measure unemployment"
    )
    assert_strings_match_ignoring_whitespace(
        page.find("div", attrs={"id": "suppression_and_disclosure"}).text,
        "Suppression rules and disclosure control (optional) Suppression and disclosure",
    )
    assert_strings_match_ignoring_whitespace(
        page.find("div", attrs={"id": "data-source-1-source-url"}).text, "Link to data source http://dwp.gov.uk"
    )
    assert_strings_match_ignoring_whitespace(
        page.find("div", attrs={"id": "data-source-1-title"}).text, "Title of data source DWP Stats"
    )
    assert_strings_match_ignoring_whitespace(
        page.find("div", attrs={"id": "data-source-1-type_of_data"}).text, "Type of data Survey data"
    )
    assert_strings_match_ignoring_whitespace(
        page.find("div", attrs={"id": "data-source-1-type_of_statistic_id"}).text, "Type of statistic National"
    )
    assert_strings_match_ignoring_whitespace(
        page.find("div", attrs={"id": "data-source-1-publisher_id"}).text,
        "Source data published by Department for Work and Pensions",
    )
    assert_strings_match_ignoring_whitespace(
        page.find("div", attrs={"id": "data-source-1-publication_date"}).text,
        "Source data publication date 15th May 2017",
    )
    assert_strings_match_ignoring_whitespace(
        page.find("div", attrs={"id": "data-source-1-note_on_corrections_or_updates"}).text,
        "Corrections or updates (optional) Note on corrections or updates",
    )
    assert_strings_match_ignoring_whitespace(
        page.find("div", attrs={"id": "data-source-1-frequency_of_release_id"}).text,
        "How often is the source data published? Quarterly",
    )
    assert_strings_match_ignoring_whitespace(
        page.find("div", attrs={"id": "data-source-1-purpose"}).text, "Purpose of data source There is no purpose"
    )


def test_view_topic_page(test_app_client, logged_in_rdu_user):
    topic = TopicFactory(title="Test topic page", short_title="Testing")
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

    sandbox_topic = TopicFactory(slug=TESTING_SPACE_SLUG, title="Test sandbox topic")
    resp = test_app_client.get(url_for("static_site.topic", topic_slug=sandbox_topic.slug))

    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
    assert page.h1.text.strip() == "Test sandbox topic"


@pytest.mark.parametrize(
    "summary, description, expected_social_description",
    (
        ("Unemployment Summary\n * This is a summary bullet", None, "This is a summary bullet"),
        (
            "Unemployment Summary\n * This is a summary bullet",
            "This is the short description",
            "This is the short description",
        ),
    ),
)
def test_measure_page_social_sharing(
    app, test_app_client, logged_in_rdu_user, summary, description, expected_social_description
):
    measure_version = MeasureVersionFactory(title="Test Measure Page", summary=summary, description=description)
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
        "og:image": app.config["RDU_SITE"] + "/static/assets/images/govuk-opengraph-image.png",
        "og:description": expected_social_description,
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

    things_to_know = page.select_one("#things-you-need-to-know summary")
    assert things_to_know.text.strip() == "Things you need to know"

    what_measured = page.select_one("#what-the-data-measures summary")
    assert what_measured.text.strip() == "What the data measures"

    categories_used = page.select_one("#the-ethnic-categories-used-in-this-data summary")
    assert categories_used.text.strip() == "The ethnic categories used in this data"

    # methodology section
    methodology = page.find("h2", attrs={"id": "methodology"})
    assert methodology.text.strip() == "2. Methodology"
    methodology_headings = methodology.parent.parent.find_all("h3")
    assert methodology_headings[0].text.strip() == "Suppression rules and disclosure control"
    assert methodology_headings[1].text.strip() == "Rounding"
    assert methodology_headings[2].text.strip() == "Related publications"

    data_source_heading = page.find("h2", attrs={"id": "data-sources"})
    assert data_source_heading.text.strip() == "3. Data sources"
    data_source_subheadings = data_source_heading.parent.find_all("h3")
    assert data_source_subheadings[0].text.strip() == "Source"
    assert data_source_subheadings[1].text.strip() == "Type of data"
    assert data_source_subheadings[2].text.strip() == "Type of statistic"
    assert data_source_subheadings[3].text.strip() == "Publisher"
    assert data_source_subheadings[4].text.strip() == "Note on corrections or updates"
    assert data_source_subheadings[5].text.strip() == "Publication frequency"
    assert data_source_subheadings[6].text.strip() == "Purpose of data source"

    download_the_data = page.find("h2", attrs={"id": "download-the-data"})
    assert download_the_data
    assert download_the_data.text.strip() == "4. Download the data"


@pytest.mark.parametrize(["number_of_topics", "row_counts"], ((1, (1,)), (3, (3,)), (5, (3, 2)), (9, (3, 3, 3))))
def test_homepage_topics_display_in_rows_with_three_columns(
    number_of_topics, row_counts, test_app_client, logged_in_rdu_user
):
    for i in range(number_of_topics):
        topic = TopicFactory(slug=f"topic-{i}", title=f"Test topic page #{i}", short_title=f"Testing #{i}")
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

    for i in range(number_of_topics):
        assert page.select(".topic a")[i].text.strip() == f"Testing #{i}"


@pytest.mark.parametrize(
    "measure_published, static_mode, topic_should_be_visible",
    ((True, True, True), (True, False, True), (False, True, False), (False, False, True)),
)
def test_homepage_only_shows_topics_with_published_measures_for_site_type(
    measure_published, static_mode, topic_should_be_visible, test_app_client, logged_in_rdu_user
):
    MeasureVersionFactory(
        status="APPROVED" if measure_published else "DRAFT", measure__subtopics__topic__title="Test topic page"
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


def test_topic_meta_description(test_app_client, logged_in_rdu_user):
    TopicFactory(slug="test-topic", meta_description="I'm a description sentence for search engines.")

    resp = test_app_client.get(url_for("static_site.topic", topic_slug="test-topic"))
    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")

    assert resp.status_code == 200

    meta_description = page.findAll("meta", property="description")
    assert len(meta_description) == 1, f"Missing meta description on topic page"
    assert meta_description[0].get("content") == "I'm a description sentence for search engines."


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
    @pytest.mark.parametrize(
        "static_mode, expected_url",
        (
            ("yes", "/topic/subtopic/measure/latest/downloads/dimension-title-table.csv"),
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
            dimensions__title="dimension-title",
            dimensions__dimension_chart__chart_object=chart,
            dimensions__dimension_table__table_object=simple_table(),
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
            ("yes", "/topic/subtopic/measure/latest/downloads/dimension-title.csv"),
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
            dimensions__title="dimension-title",
            dimensions__dimension_chart__chart_object=chart,
            dimensions__dimension_table__table_object=simple_table(),
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
            ("yes", "/topic/subtopic/measure/1.0/downloads/test-measure-page-data.csv"),
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
            dimensions__dimension_chart__chart_object=chart,
            dimensions__dimension_table__table_object=simple_table(),
            uploads__guid="test-download",
            uploads__title="Test measure page data",
            uploads__file_name="test-measure-page-data.csv",
        )
        resp = test_app_client.get("/topic/subtopic/measure/latest", follow_redirects=False)
        page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
        data_links = page.findAll("a", href=True, text=re.compile(r"Test measure page data\s+-\s+Spreadsheet"))
        assert len(data_links) == 1
        assert data_links[0].attrs["href"] == expected_url

    def test_later_version_shows_links_to_earlier_versions(self, test_app_client, logged_in_admin_user):
        # GIVEN a page with a later published version
        measure = MeasureFactory()
        # Published version 1.0
        measure_1_0 = MeasureVersionFactory(
            measure=measure, status="APPROVED", latest=False, version="1.0", published_at=datetime.datetime(2018, 3, 29)
        )
        # Published version 1.1
        measure_1_1 = MeasureVersionFactory(
            measure=measure, status="APPROVED", latest=False, version="1.1", published_at=datetime.datetime(2019, 3, 29)
        )
        # Latest published version 2.0
        measure_2_0 = MeasureVersionFactory(measure=measure, status="APPROVED", latest=True, version="2.0")

        measure_1_0_url = url_for(
            "static_site.measure_version",
            topic_slug=measure_1_0.measure.subtopic.topic.slug,
            subtopic_slug=measure_1_0.measure.subtopic.slug,
            measure_slug=measure_1_0.measure.slug,
            version=measure_1_0.version,
        )
        measure_1_1_url = url_for(
            "static_site.measure_version",
            topic_slug=measure_1_1.measure.subtopic.topic.slug,
            subtopic_slug=measure_1_1.measure.subtopic.slug,
            measure_slug=measure_1_1.measure.slug,
            version=measure_1_1.version,
        )
        measure_2_0_url = url_for(
            "static_site.measure_version",
            topic_slug=measure_2_0.measure.subtopic.topic.slug,
            subtopic_slug=measure_2_0.measure.subtopic.slug,
            measure_slug=measure_2_0.measure.slug,
            version=measure_2_0.version,
        )

        # WHEN we get the latest measure page
        resp = test_app_client.get(measure_2_0_url)

        # THEN it should contain a link to the latest minor version of the earlier published version
        assert resp.status_code == 200
        page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
        measure_1_1_links = page.find_all("a", attrs={"href": measure_1_1_url})
        assert len(measure_1_1_links) == 1
        assert measure_1_1_links[0].text == "29 March 2019"

        # AND should not contain a link to the superseded earlier version
        measure_1_0_links = page.find_all("a", attrs={"href": measure_1_0_url})
        assert len(measure_1_0_links) == 0

    def test_version_with_factual_error(self, test_app_client, logged_in_rdu_user):

        # GIVEN a 1.0 measure which contains factual errors
        measure = MeasureFactory()

        measure_1_0 = MeasureVersionFactory.create(
            measure=measure, status="APPROVED", version="1.0"
        )

        MeasureVersionFactory.create(
            measure=measure, status="APPROVED", version="1.1",update_corrects_data_mistake=True
        )

        measure_1_0_url = url_for(
            "static_site.measure_version",
            topic_slug=measure_1_0.measure.subtopic.topic.slug,
            subtopic_slug=measure_1_0.measure.subtopic.slug,
            measure_slug=measure_1_0.measure.slug,
            version=measure_1_0.version,
        )

        # WHEN we get the 1.0 measure page
        resp = test_app_client.get(measure_1_0_url)

        assert resp.status_code == 200

        page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")

        # THEN it should contain a banner explaining that the page contains an error
        assert 'This page contains a factual mistake. Details can be found on the corrected page.' in page.get_text()


    def test_version_with_factual_corrections(self, test_app_client, logged_in_rdu_user):

        # GIVEN a 1.0 measure which contains factual errors
        measure = MeasureFactory()

        MeasureVersionFactory.create(
            measure=measure, status="APPROVED", version="1.0"
        )

        measure_1_1 = MeasureVersionFactory.create(
            measure=measure, status="APPROVED", version="1.1",update_corrects_data_mistake=True
        )

        measure_1_1_url = url_for(
            "static_site.measure_version",
            topic_slug=measure_1_1.measure.subtopic.topic.slug,
            subtopic_slug=measure_1_1.measure.subtopic.slug,
            measure_slug=measure_1_1.measure.slug,
            version=measure_1_1.version,
        )

        # WHEN we get the 1.1 measure page
        resp = test_app_client.get(measure_1_1_url)

        assert resp.status_code == 200

        page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")

        # THEN it should contain a banner explaining that the page contains corrections
        assert 'This page corrects mistakes in a previous version. See details.' in page.get_text()


class TestCorrections:
    def setup(self):
        self.measure_version_1 = MeasureVersionFactory.create(
            version="1.0",
            status="APPROVED",
            update_corrects_data_mistake=False,
            title="Measure 1 version 1.0",
            published_at=datetime.datetime(2000, 1, 1),
        )
        MeasureVersionFactory.create(
            version="1.1",
            status="APPROVED",
            update_corrects_data_mistake=True,
            title="Measure 1 version 1.1",
            published_at=datetime.datetime(2001, 1, 1),
            measure=self.measure_version_1.measure,
        )

        self.measure_version_2 = MeasureVersionFactory.create(
            version="1.0",
            status="APPROVED",
            update_corrects_data_mistake=False,
            title="Measure 2 version 1.0",
            published_at=datetime.datetime(2002, 1, 1),
        )
        MeasureVersionFactory.create(
            version="1.1",
            status="APPROVED",
            update_corrects_data_mistake=True,
            title="Measure 2 version 1.1",
            published_at=datetime.datetime(2003, 1, 1),
            measure=self.measure_version_2.measure,
        )
        MeasureVersionFactory.create(
            version="1.2",
            status="APPROVED",
            update_corrects_data_mistake=False,
            title="Measure 2 version 1.2",
            published_at=datetime.datetime(2004, 1, 1),
            measure=self.measure_version_2.measure,
        )

    def test_corrections_listed_in_reverse_chronological_order(self, test_app_client, logged_in_rdu_user):
        resp = test_app_client.get("/corrections", follow_redirects=False)
        page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")

        corrected_measure_versions = page.findAll("div", {"class": "corrected-measure-version"})

        assert corrected_measure_versions[0].find("a").text.strip() == "Measure 2 version 1.1"
        assert corrected_measure_versions[1].find("a").text.strip() == "Measure 1 version 1.1"

    def test_latest_published_version_uses_latest_reference_rather_than_numerical_version_if_no_later_versions(
        self, test_app_client, logged_in_rdu_user
    ):
        resp = test_app_client.get("/corrections", follow_redirects=False)
        page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")

        corrected_measure_versions = page.findAll("div", {"class": "corrected-measure-version"})

        assert corrected_measure_versions[0].find("a").attrs["href"].endswith("1.2")
        assert corrected_measure_versions[1].find("a").attrs["href"].endswith("latest")
