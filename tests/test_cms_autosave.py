import pytest
from flask import url_for


class TestCMSAutosave():

    def test_edit_and_preview_page_should_load(
        self, test_app_client, mock_user, stub_topic_page, stub_subtopic_page, stub_measure_page
    ):
        with test_app_client.session_transaction() as session:
            session['user_id'] = mock_user.id
        url = url_for('cms.edit_and_preview_measure_page',
                      topic=stub_topic_page.guid,
                      subtopic=stub_subtopic_page.guid,
                      measure=stub_measure_page.guid,
                      version=stub_measure_page.version,
                      )
        response = test_app_client.get(url)
        assert response.status_code == 200

    @pytest.mark.parametrize("url, expected_result", [
        ("/cms/topic_test/subtopic_example/test-measure-page/1.0/edit_and_preview", 200),
        ("/cms/WRONG_topic_test/subtopic_example/test-measure-page/1.0/edit_and_preview", 404),
        ("/cms/topic_test/WRONG_subtopic_example/test-measure-page/1.0/edit_and_preview", 404)
    ])
    def test_topic_and_subtopic_should_belong_to_page_or_404(
            self, test_app_client, mock_user, stub_topic_page, stub_subtopic_page,
            stub_measure_page, url, expected_result,
    ):
        with test_app_client.session_transaction() as session:
            session['user_id'] = mock_user.id

        response = test_app_client.get(url)
        assert response.status_code == expected_result
