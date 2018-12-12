from datetime import datetime
from bs4 import BeautifulSoup
from flask import url_for
import re

import pytest

from application.cms.models import MeasureVersion
from application.cms.page_service import PageService

page_service = PageService()


def test_rdu_user_can_see_page_if_not_shared(
    test_app_client, db_session, mock_rdu_user, stub_topic_page, stub_subtopic_page, stub_measure_page
):
    assert stub_measure_page.shared_with == []
    assert mock_rdu_user.pages == []

    with test_app_client.session_transaction() as session:
        session["user_id"] = mock_rdu_user.id

    resp = test_app_client.get(
        url_for(
            "static_site.measure_page",
            topic_uri=stub_topic_page.uri,
            subtopic_uri=stub_subtopic_page.uri,
            measure_uri=stub_measure_page.uri,
            version=stub_measure_page.version,
        )
    )

    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
    assert page.h1.text.strip() == "Test Measure Page"


def test_departmental_user_cannot_see_page_unless_shared(
    test_app_client, db_session, mock_dept_user, stub_topic_page, stub_subtopic_page, stub_measure_page
):
    with test_app_client.session_transaction() as session:
        session["user_id"] = mock_dept_user.id

    assert stub_measure_page.shared_with == []
    assert mock_dept_user.pages == []

    resp = test_app_client.get(
        url_for(
            "static_site.measure_page",
            topic_uri=stub_topic_page.uri,
            subtopic_uri=stub_subtopic_page.uri,
            measure_uri=stub_measure_page.uri,
            version=stub_measure_page.version,
        )
    )

    assert resp.status_code == 403

    stub_measure_page.shared_with.append(mock_dept_user)
    db_session.session.add(stub_measure_page)
    db_session.session.commit()

    resp = test_app_client.get(
        url_for(
            "static_site.measure_page",
            topic_uri=stub_topic_page.uri,
            subtopic_uri=stub_subtopic_page.uri,
            measure_uri=stub_measure_page.uri,
            version=stub_measure_page.version,
        )
    )

    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
    assert page.h1.text.strip() == "Test Measure Page"

    stub_measure_page.shared_with = []
    mock_dept_user.pages = []
    db_session.session.add(mock_dept_user)
    db_session.session.add(stub_measure_page)
    db_session.session.commit()


def test_get_file_download_returns_404(
    test_app_client, mock_rdu_user, stub_topic_page, stub_subtopic_page, stub_measure_page
):
    with test_app_client.session_transaction() as session:
        session["user_id"] = mock_rdu_user.id

    resp = test_app_client.get(
        url_for(
            "static_site.measure_page_file_download",
            topic_uri=stub_topic_page.uri,
            subtopic_uri=stub_subtopic_page.uri,
            measure_uri=stub_measure_page.uri,
            version=stub_measure_page.version,
            filename="nofile.csv",
        )
    )

    assert resp.status_code == 404


def test_view_export_page(
    test_app_client, db_session, mock_rdu_user, stub_topic_page, stub_subtopic_page, stub_measure_page
):
    with test_app_client.session_transaction() as session:
        session["user_id"] = mock_rdu_user.id

    assert stub_measure_page.status == "DRAFT"

    resp = test_app_client.get(
        url_for(
            "static_site.measure_page_markdown",
            topic_uri=stub_topic_page.uri,
            subtopic_uri=stub_subtopic_page.uri,
            measure_uri=stub_measure_page.uri,
            version=stub_measure_page.version,
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


def test_view_topic_page(test_app_client, mock_rdu_user, stub_topic_page):
    with test_app_client.session_transaction() as session:
        session["user_id"] = mock_rdu_user.id

    resp = test_app_client.get(url_for("static_site.topic", topic_uri=stub_topic_page.uri))

    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
    assert page.h1.text.strip() == "Test topic page"


def test_view_topic_page_contains_reordering_javascript_for_admin_user_only(
    test_app_client, mock_rdu_user, mock_admin_user, stub_topic_page
):
    import re

    with test_app_client.session_transaction() as session:
        session["user_id"] = mock_admin_user.id

    resp = test_app_client.get(url_for("static_site.topic", topic_uri=stub_topic_page.uri))

    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
    assert page.h1.text.strip() == "Test topic page"
    assert len(page.find_all("script", text=re.compile("setupReorderableTables"))) == 1

    with test_app_client.session_transaction() as session:
        session["user_id"] = mock_rdu_user.id

    resp = test_app_client.get(url_for("static_site.topic", topic_uri=stub_topic_page.uri))

    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
    assert page.h1.text.strip() == "Test topic page"
    assert len(page.find_all("script", text=re.compile("setupReorderableTables"))) == 0


def test_view_topic_page_in_static_mode_does_not_contain_reordering_javascript(
    test_app_client, mock_admin_user, stub_topic_page
):
    import re

    with test_app_client.session_transaction() as session:
        session["user_id"] = mock_admin_user.id

    resp = test_app_client.get(url_for("static_site.topic", topic_uri=stub_topic_page.uri))

    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
    assert page.h1.text.strip() == "Test topic page"
    assert len(page.find_all("script", text=re.compile("setupReorderableTables"))) == 1

    resp = test_app_client.get(url_for("static_site.topic", topic_uri=stub_topic_page.uri, static_mode=True))

    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
    assert page.h1.text.strip() == "Test topic page"
    assert len(page.find_all("script", text=re.compile("setupReorderableTables"))) == 0


def test_view_index_page_only_contains_one_topic(
    test_app_client, mock_rdu_user, stub_home_page, stub_topic_page, stub_published_measure_page
):
    with test_app_client.session_transaction() as session:
        session["user_id"] = mock_rdu_user.id

    resp = test_app_client.get(url_for("static_site.index"))

    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
    assert page.h1.text.strip() == "Ethnicity facts and figures"
    topics = page.find_all("div", class_="topic")
    assert len(topics) == 1
    assert topics[0].find("a").text.strip() == stub_topic_page.title


def test_view_sandbox_topic(test_app_client, mock_rdu_user, stub_sandbox_topic_page):
    with test_app_client.session_transaction() as session:
        session["user_id"] = mock_rdu_user.id

    resp = test_app_client.get(url_for("static_site.topic", topic_uri=stub_sandbox_topic_page.uri))

    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
    assert page.h1.text.strip() == "Test sandbox topic page"


def test_measure_page_social_sharing(
    app, test_app_client, mock_rdu_user, stub_topic_page, stub_subtopic_page, stub_measure_page
):
    with test_app_client.session_transaction() as session:
        session["user_id"] = mock_rdu_user.id

    resp = test_app_client.get(
        url_for(
            "static_site.measure_page",
            topic_uri=stub_topic_page.uri,
            subtopic_uri=stub_subtopic_page.uri,
            measure_uri=stub_measure_page.uri,
            version=stub_measure_page.version,
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


def test_view_measure_page(test_app_client, mock_rdu_user, stub_topic_page, stub_subtopic_page, stub_measure_page):
    with test_app_client.session_transaction() as session:
        session["user_id"] = mock_rdu_user.id

    resp = test_app_client.get(
        url_for(
            "static_site.measure_page",
            topic_uri=stub_topic_page.uri,
            subtopic_uri=stub_subtopic_page.uri,
            measure_uri=stub_measure_page.uri,
            version=stub_measure_page.version,
        )
    )

    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")

    assert page.h1.text.strip() == stub_measure_page.title

    # check metadata
    metadata_titles = page.find("div", class_="metadata").find_all("dt")
    assert len(metadata_titles) == 5
    assert metadata_titles[0].text == "Department:"
    assert metadata_titles[1].text == "Published:"
    assert metadata_titles[2].text == "Source:"
    assert metadata_titles[3].text == "Area covered:"
    assert metadata_titles[4].text == "Time period:"

    metadata_values = page.find("div", class_="metadata").find_all("dd")
    assert len(metadata_titles) == 5
    assert metadata_values[0].text.strip() == "Department for Work and Pensions"
    assert metadata_values[1].text.strip() == datetime.now().date().strftime("%d %B %Y").lstrip("0")
    assert metadata_values[2].text.strip() == "DWP Stats"
    assert metadata_values[3].text.strip() == "England"
    assert metadata_values[4].text.strip() == "4 months"

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
    number_of_topics, row_counts, test_app_client, mock_rdu_user, stub_home_page, db_session
):
    with test_app_client.session_transaction() as session:
        session["user_id"] = mock_rdu_user.id

    MeasureVersion.query.filter(MeasureVersion.page_type == "topic").delete()
    db_session.session.commit()

    for i in range(number_of_topics):
        topic = MeasureVersion(
            guid=f"topic_{i}",
            parent_guid="homepage",
            page_type="topic",
            uri=f"topic-{i}",
            status="DRAFT",
            title=f"Test topic page #{i}",
            version="1.0",
        )
        subtopic = MeasureVersion(
            guid=f"subtopic_{i}",
            parent_guid=f"topic_{i}",
            page_type="subtopic",
            uri=f"subtopic-{i}",
            status="DRAFT",
            title=f"Test subtopic page #{i}",
            version="1.0",
        )
        measure = MeasureVersion(
            guid=f"measure_{i}",
            parent_guid=f"topic_{i}",
            page_type="measure",
            uri=f"measure-{i}",
            status="APPROVED",
            published=True,
            title=f"Test measure page #{i}",
            version="1.0",
        )

        topic.children = [subtopic]
        subtopic.children = [measure]

        db_session.session.add(topic)
        db_session.session.add(subtopic)
        db_session.session.add(measure)
        db_session.session.commit()

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
    measure_published,
    static_mode,
    topic_should_be_visible,
    test_app_client,
    mock_rdu_user,
    stub_measure_page,
    db_session,
):
    with test_app_client.session_transaction() as session:
        session["user_id"] = mock_rdu_user.id

    stub_measure_page.published = measure_published
    db_session.session.add(stub_measure_page)
    db_session.session.commit()

    resp = test_app_client.get(url_for("static_site.index", static_mode=static_mode))
    assert resp.status_code == 200

    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")

    assert bool(page(string=re.compile("Test topic page"))) is topic_should_be_visible


@pytest.mark.parametrize(
    "measure_published, static_mode, subtopic_should_be_visible",
    ((True, True, True), (True, False, True), (False, True, False), (False, False, True)),
)
def test_topic_page_only_shows_subtopics_with_published_measures_for_static_site_build(
    measure_published,
    static_mode,
    subtopic_should_be_visible,
    test_app_client,
    mock_rdu_user,
    stub_measure_page,
    db_session,
):
    with test_app_client.session_transaction() as session:
        session["user_id"] = mock_rdu_user.id

    stub_measure_page.published = measure_published
    db_session.session.add(stub_measure_page)
    db_session.session.commit()

    resp = test_app_client.get(url_for("static_site.topic", topic_uri="test", static_mode=static_mode))
    assert resp.status_code == 200

    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")

    assert bool(page(string=re.compile("Test subtopic page"))) is subtopic_should_be_visible


@pytest.mark.parametrize(
    "measure_shared, measure_published, subtopic_should_be_visible",
    ((True, True, True), (True, False, True), (False, True, True), (False, False, False)),
)
def test_topic_page_only_shows_subtopics_with_shared_or_published_measures_for_dept_user_type(
    measure_shared,
    measure_published,
    subtopic_should_be_visible,
    test_app_client,
    mock_dept_user,
    stub_measure_page,
    db_session,
):
    with test_app_client.session_transaction() as session:
        session["user_id"] = mock_dept_user.id

    if measure_shared:
        stub_measure_page.shared_with.append(mock_dept_user)
        db_session.session.add(stub_measure_page)

    stub_measure_page.published = measure_published
    db_session.session.add(stub_measure_page)
    db_session.session.commit()

    resp = test_app_client.get(url_for("static_site.topic", topic_uri="test"))
    assert resp.status_code == 200

    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")

    assert bool(page(string=re.compile("Test subtopic page"))) is subtopic_should_be_visible


@pytest.mark.parametrize("user_type, empty_subtopic_should_be_visible", (("DEPT", False), ("RDU", True)))
def test_topic_page_only_shows_empty_subtopics_if_user_can_create_a_measure(
    user_type, empty_subtopic_should_be_visible, test_app_client, mock_rdu_user, mock_dept_user, stub_subtopic_page
):
    with test_app_client.session_transaction() as session:
        session["user_id"] = mock_dept_user.id if user_type == "DEPT" else mock_rdu_user.id

    resp = test_app_client.get(url_for("static_site.topic", topic_uri="test"))
    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")

    assert resp.status_code == 200
    assert bool(page(string=re.compile("Test subtopic page"))) is empty_subtopic_should_be_visible


def test_measure_page_share_links_do_not_contain_double_slashes_between_domain_and_path(
    test_app_client, db_session, mock_rdu_user, stub_topic_page, stub_subtopic_page, stub_measure_page
):
    assert stub_measure_page.shared_with == []
    assert mock_rdu_user.pages == []

    with test_app_client.session_transaction() as session:
        session["user_id"] = mock_rdu_user.id

    resp = test_app_client.get(
        url_for(
            "static_site.measure_page",
            topic_uri=stub_topic_page.uri,
            subtopic_uri=stub_subtopic_page.uri,
            measure_uri=stub_measure_page.uri,
            version=stub_measure_page.version,
        )
    )

    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")

    share_links = page.find("div", {"class": "share"}).findChildren("a")

    for share_link in share_links:
        assert (
            "https%3A//www.ethnicity-facts-figures.service.gov.uk/test/example/test-measure-page/latest"
            in share_link["href"]
        )


def test_latest_version_does_not_add_noindex_for_robots(
    app,
    db,
    db_session,
    test_app_client,
    mock_admin_user,
    stub_topic_page,
    stub_subtopic_page,
    stub_measure_page_one_of_three,
    stub_measure_page_two_of_three,
):
    # GIVEN the latest version of a page
    latest_version_of_page = stub_measure_page_two_of_three
    # WHEN we get the rendered template
    with test_app_client.session_transaction() as session:
        session["user_id"] = mock_admin_user.id
    from flask import url_for

    resp = test_app_client.get(
        url_for(
            "static_site.measure_page",
            topic_uri=stub_topic_page.uri,
            subtopic_uri=stub_subtopic_page.uri,
            measure_uri=latest_version_of_page.uri,
            version=latest_version_of_page.version,
        )
    )
    # THEN it should not contain a noindex tag
    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
    robots_tags = page.find_all("meta", attrs={"name": "robots"}, content=lambda value: value and "noindex" in value)
    assert len(robots_tags) == 0


def test_latest_version_does_not_add_noindex_for_robots_when_newer_draft_exists(
    app,
    db,
    db_session,
    test_app_client,
    mock_admin_user,
    stub_topic_page,
    stub_subtopic_page,
    stub_measure_page_one_of_three,
    stub_measure_page_two_of_three,
    stub_measure_page_three_of_three,
):
    # GIVEN the latest version of a page and a newer draft (ie the stub_measure_page_three_of_three fixture)
    latest_published_version_of_page = stub_measure_page_two_of_three

    # WHEN we get the rendered template
    with test_app_client.session_transaction() as session:
        session["user_id"] = mock_admin_user.id
    from flask import url_for

    resp = test_app_client.get(
        url_for(
            "static_site.measure_page",
            topic_uri=stub_topic_page.uri,
            subtopic_uri=stub_subtopic_page.uri,
            measure_uri=latest_published_version_of_page.uri,
            version=latest_published_version_of_page.version,
        )
    )
    # THEN it should not contain a noindex tag
    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
    robots_tags = page.find_all("meta", attrs={"name": "robots"}, content=lambda value: value and "noindex" in value)
    assert len(robots_tags) == 0


def test_previous_version_adds_noindex_for_robots(
    app,
    db,
    db_session,
    test_app_client,
    mock_admin_user,
    stub_topic_page,
    stub_subtopic_page,
    stub_measure_page_one_of_three,
    stub_measure_page_two_of_three,
):
    # GIVEN a page with a later published version
    outdated_page = stub_measure_page_one_of_three
    # WHEN we get the rendered template
    with test_app_client.session_transaction() as session:
        session["user_id"] = mock_admin_user.id
    from flask import url_for

    resp = test_app_client.get(
        url_for(
            "static_site.measure_page",
            topic_uri=stub_topic_page.uri,
            subtopic_uri=stub_subtopic_page.uri,
            measure_uri=outdated_page.uri,
            version=outdated_page.version,
        )
    )
    # THEN it should contain a noindex tag
    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
    robots_tags = page.find_all("meta", attrs={"name": "robots"}, content=lambda value: value and "noindex" in value)
    assert len(robots_tags) == 1
