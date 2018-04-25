import datetime
import json

from flask import url_for
from bs4 import BeautifulSoup

from application.cms.forms import MeasurePageForm
from application.cms.models import Page
from application.cms.page_service import PageService
from application.sitebuilder.models import Build


def test_create_measure_page(test_app_client,
                             mock_user,
                             stub_topic_page,
                             stub_subtopic_page,
                             stub_measure_data,
                             stub_frequency,
                             stub_geography):

    with test_app_client.session_transaction() as session:
        session['user_id'] = mock_user.id

    form = MeasurePageForm(**stub_measure_data)

    resp = test_app_client.post(url_for('cms.create_measure_page',
                                topic=stub_topic_page.guid,
                                subtopic=stub_subtopic_page.guid),
                                data=form.data,
                                follow_redirects=True)

    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode('utf-8'), 'html.parser')
    assert page.find('div', class_="alert-box").span.string == 'created page %s' % stub_measure_data['title']


def test_reject_page(app,
                     test_app_client,
                     mock_user,
                     stub_topic_page,
                     stub_subtopic_page,
                     stub_measure_page):
    with test_app_client.session_transaction() as session:
        session['user_id'] = mock_user.id
    test_app_client.get(url_for('cms.reject_page',
                                topic=stub_topic_page.guid,
                                subtopic=stub_subtopic_page.guid,
                                measure=stub_measure_page.guid,
                                version=stub_measure_page.version,
                                follow_redirects=True))
    page_service = PageService()
    page_service.init_app(app)
    page = page_service.get_page(stub_measure_page.guid)
    assert page.status == 'REJECTED'


def test_admin_user_can_publish_page_in_dept_review(app,
                                                    db,
                                                    db_session,
                                                    test_app_client,
                                                    mock_admin_user,
                                                    stub_topic_page,
                                                    stub_subtopic_page,
                                                    stub_measure_page,
                                                    mock_request_build,
                                                    mock_page_service_mark_page_published):

    with test_app_client.session_transaction() as session:
        session['user_id'] = mock_admin_user.id

    stub_measure_page.status = 'DEPARTMENT_REVIEW'
    db.session.add(stub_measure_page)
    db.session.commit()

    response = test_app_client.get(url_for('cms.publish',
                                           topic=stub_topic_page.guid,
                                           subtopic=stub_subtopic_page.guid,
                                           measure=stub_measure_page.guid,
                                           version=stub_measure_page.version),
                                   follow_redirects=True)

    assert response.status_code == 200
    mock_request_build.assert_called_once()
    mock_page_service_mark_page_published.assert_called_once_with(stub_measure_page)

    page_service = PageService()
    page_service.init_app(app)
    page = page_service.get_page(stub_measure_page.guid)
    assert page.status == 'APPROVED'
    assert page.last_updated_by == mock_admin_user.email
    assert page.published_by == mock_admin_user.email
    assert page.publication_date == datetime.date.today()

    page = BeautifulSoup(response.data.decode('utf-8'), 'html.parser')
    assert page.find('div', class_="alert-box").span.string == 'Sent page "Test Measure Page" to APPROVED'  # noqa


def test_admin_user_can_not_publish_page_not_in_department_review(app,
                                                                  db,
                                                                  db_session,
                                                                  test_app_client,
                                                                  mock_admin_user,
                                                                  stub_topic_page,
                                                                  stub_subtopic_page,
                                                                  stub_measure_page,
                                                                  mock_request_build):

    with test_app_client.session_transaction() as session:
        session['user_id'] = mock_admin_user.id

    assert stub_measure_page.status == 'DRAFT'

    response = test_app_client.get(url_for('cms.publish',
                                           topic=stub_topic_page.guid,
                                           subtopic=stub_subtopic_page.guid,
                                           measure=stub_measure_page.guid,
                                           version=stub_measure_page.version),
                                   follow_redirects=True)

    assert response.status_code == 400

    page_service = PageService()
    page_service.init_app(app)
    page = page_service.get_page(stub_measure_page.guid)
    assert page.status == 'DRAFT'

    stub_measure_page.status = 'INTERNAL_REVIEW'
    db.session.add(stub_measure_page)
    db.session.commit()

    response = test_app_client.get(url_for('cms.publish',
                                           topic=stub_topic_page.guid,
                                           subtopic=stub_subtopic_page.guid,
                                           measure=stub_measure_page.guid,
                                           version=stub_measure_page.version),
                                   follow_redirects=True)

    assert response.status_code == 400
    assert mock_request_build.call_count == 0

    page_service = PageService()
    page_service.init_app(app)
    page = page_service.get_page(stub_measure_page.guid)
    assert page.status == 'INTERNAL_REVIEW'


def test_non_admin_user_can_not_publish_page_in_dept_review(app,
                                                            db,
                                                            db_session,
                                                            test_app_client,
                                                            mock_user,
                                                            stub_topic_page,
                                                            stub_subtopic_page,
                                                            stub_measure_page):

    with test_app_client.session_transaction() as session:
        session['user_id'] = mock_user.id

    stub_measure_page.status = 'DEPARTMENT_REVIEW'
    db.session.add(stub_measure_page)
    db.session.commit()

    response = test_app_client.get(url_for('cms.publish',
                                           topic=stub_topic_page.guid,
                                           subtopic=stub_subtopic_page.guid,
                                           measure=stub_measure_page.guid,
                                           version=stub_measure_page.version),
                                   follow_redirects=True)

    assert response.status_code == 403

    page_service = PageService()
    page_service.init_app(app)
    page = page_service.get_page(stub_measure_page.guid)
    assert page.status == 'DEPARTMENT_REVIEW'


def test_admin_user_can_unpublish_page(app,
                                       db,
                                       db_session,
                                       test_app_client,
                                       mock_admin_user,
                                       stub_topic_page,
                                       stub_subtopic_page,
                                       stub_measure_page,
                                       mock_request_build):

    with test_app_client.session_transaction() as session:
        session['user_id'] = mock_admin_user.id

    stub_measure_page.status = 'APPROVED'
    db.session.add(stub_measure_page)
    db.session.commit()

    response = test_app_client.get(url_for('cms.unpublish_page',
                                           topic=stub_topic_page.guid,
                                           subtopic=stub_subtopic_page.guid,
                                           measure=stub_measure_page.guid,
                                           version=stub_measure_page.version),
                                   follow_redirects=True)

    assert response.status_code == 200
    mock_request_build.assert_called_once()

    page_service = PageService()
    page_service.init_app(app)
    page = page_service.get_page(stub_measure_page.guid)
    assert page.status == 'UNPUBLISH'
    assert page.unpublished_by == mock_admin_user.email


def test_non_admin_user_can_not_unpublish_page(app,
                                               db,
                                               db_session,
                                               test_app_client,
                                               mock_user,
                                               stub_topic_page,
                                               stub_subtopic_page,
                                               stub_measure_page,
                                               mock_request_build):

    with test_app_client.session_transaction() as session:
        session['user_id'] = mock_user.id

    stub_measure_page.status = 'APPROVED'
    db.session.add(stub_measure_page)
    db.session.commit()

    response = test_app_client.get(url_for('cms.unpublish_page',
                                           topic=stub_topic_page.guid,
                                           subtopic=stub_subtopic_page.guid,
                                           measure=stub_measure_page.guid,
                                           version=stub_measure_page.version),
                                   follow_redirects=True)

    assert response.status_code == 403
    assert mock_request_build.call_count == 0

    page_service = PageService()
    page_service.init_app(app)
    page = page_service.get_page(stub_measure_page.guid)
    assert page.status == 'APPROVED'


def test_admin_user_can_see_publish_unpublish_buttons_on_edit_page(app,
                                                                   db,
                                                                   db_session,
                                                                   test_app_client,
                                                                   mock_admin_user,
                                                                   stub_topic_page,
                                                                   stub_subtopic_page,
                                                                   stub_measure_page):

    with test_app_client.session_transaction() as session:
        session['user_id'] = mock_admin_user.id

    stub_measure_page.status = 'DEPARTMENT_REVIEW'
    db.session.add(stub_measure_page)
    db.session.commit()

    response = test_app_client.get(url_for('cms.edit_measure_page',
                                           topic=stub_topic_page.guid,
                                           subtopic=stub_subtopic_page.guid,
                                           measure=stub_measure_page.guid,
                                           version=stub_measure_page.version),
                                   follow_redirects=True)

    page = BeautifulSoup(response.data.decode('utf-8'), 'html.parser')
    assert page.find_all('a', class_="button")[-1].text.strip().lower() == 'approve for publishing'

    stub_measure_page.status = 'APPROVED'
    db.session.add(stub_measure_page)
    db.session.commit()

    response = test_app_client.get(url_for('cms.edit_measure_page',
                                           topic=stub_topic_page.guid,
                                           subtopic=stub_subtopic_page.guid,
                                           measure=stub_measure_page.guid,
                                           version=stub_measure_page.version),
                                   follow_redirects=True)

    page = BeautifulSoup(response.data.decode('utf-8'), 'html.parser')
    assert page.find_all('a', class_="button")[-1].text.strip().lower() == 'unpublish'


def test_internal_user_can_not_see_publish_unpublish_buttons_on_edit_page(app,
                                                                          db,
                                                                          db_session,
                                                                          test_app_client,
                                                                          mock_user,
                                                                          stub_topic_page,
                                                                          stub_subtopic_page,
                                                                          stub_measure_page):

    with test_app_client.session_transaction() as session:
        session['user_id'] = mock_user.id

    stub_measure_page.status = 'DEPARTMENT_REVIEW'
    db.session.add(stub_measure_page)
    db.session.commit()

    response = test_app_client.get(url_for('cms.edit_measure_page',
                                           topic=stub_topic_page.guid,
                                           subtopic=stub_subtopic_page.guid,
                                           measure=stub_measure_page.guid,
                                           version=stub_measure_page.version),
                                   follow_redirects=True)

    page = BeautifulSoup(response.data.decode('utf-8'), 'html.parser')
    assert page.find_all('a', class_="button")[-1].text.strip().lower() == 'reject'

    stub_measure_page.status = 'APPROVED'
    db.session.add(stub_measure_page)
    db.session.commit()

    response = test_app_client.get(url_for('cms.edit_measure_page',
                                           topic=stub_topic_page.guid,
                                           subtopic=stub_subtopic_page.guid,
                                           measure=stub_measure_page.guid,
                                           version=stub_measure_page.version),
                                   follow_redirects=True)

    page = BeautifulSoup(response.data.decode('utf-8'), 'html.parser')
    assert page.find_all('a', class_="button")[-1].text.strip().lower() == 'edit / create new version'


def test_order_measures_in_subtopic(app, db, db_session, test_app_client, mock_user, stub_subtopic_page):
    ids = [0, 1, 2, 3, 4]
    reversed_ids = ids[::-1]
    for i in ids:
        stub_subtopic_page.children.append(Page(guid=str(i), version='1.0', position=i))

    db.session.add(stub_subtopic_page)
    db.session.commit()

    assert stub_subtopic_page.children[0].guid == '0'
    assert stub_subtopic_page.children[1].guid == '1'
    assert stub_subtopic_page.children[2].guid == '2'
    assert stub_subtopic_page.children[3].guid == '3'
    assert stub_subtopic_page.children[4].guid == '4'

    with test_app_client.session_transaction() as session:
        session['user_id'] = mock_user.id

    updates = []
    for position, id in enumerate(reversed_ids):
        updates.append({"position": position, "guid": str(id), "subtopic": stub_subtopic_page.guid})

    resp = test_app_client.post(url_for('cms.set_measure_order'),
                                data=json.dumps({"positions": updates}),
                                content_type='application/json')

    assert resp.status_code == 200

    page_service = PageService()
    page_service.init_app(app)
    udpated_page = page_service.get_page(stub_subtopic_page.guid)

    assert udpated_page.children[0].guid == '4'
    assert udpated_page.children[1].guid == '3'
    assert udpated_page.children[2].guid == '2'
    assert udpated_page.children[3].guid == '1'
    assert udpated_page.children[4].guid == '0'


def test_reorder_measures_triggers_build(app, db, db_session, test_app_client, mock_user, stub_subtopic_page):
    ids = [0, 1]
    reversed_ids = ids[::-1]
    for i in ids:
        stub_subtopic_page.children.append(Page(guid=str(i), version='1.0', position=i))

    db.session.add(stub_subtopic_page)
    db.session.commit()

    builds = Build.query.all()

    assert len(builds) == 0

    with test_app_client.session_transaction() as session:
        session['user_id'] = mock_user.id

    updates = []
    for position, id in enumerate(reversed_ids):
        updates.append({"position": position, "guid": str(id), "subtopic": stub_subtopic_page.guid})

    resp = test_app_client.post(url_for('cms.set_measure_order'),
                                data=json.dumps({"positions": updates}),
                                content_type='application/json')

    assert resp.status_code == 200

    builds = Build.query.all()

    assert len(builds) == 1


def test_order_measures_in_subtopic_sets_order_on_all_versions(app,
                                                               db,
                                                               db_session,
                                                               test_app_client,
                                                               mock_user,
                                                               stub_subtopic_page):

    stub_subtopic_page.children.append(Page(guid='0', version='1.0', position=0))
    stub_subtopic_page.children.append(Page(guid='0', version='1.1', position=0))
    stub_subtopic_page.children.append(Page(guid='0', version='2.0', position=0))
    stub_subtopic_page.children.append(Page(guid='1', version='1.0', position=0))
    stub_subtopic_page.children.append(Page(guid='1', version='2.0', position=0))

    db.session.add(stub_subtopic_page)
    db.session.commit()

    assert stub_subtopic_page.children[0].guid == '0'
    assert stub_subtopic_page.children[1].guid == '0'
    assert stub_subtopic_page.children[2].guid == '0'
    assert stub_subtopic_page.children[3].guid == '1'
    assert stub_subtopic_page.children[4].guid == '1'

    with test_app_client.session_transaction() as session:
        session['user_id'] = mock_user.id

    updates = [{"position": 0, "guid": '1', "subtopic": stub_subtopic_page.guid},
               {"position": 1, "guid": '0', "subtopic": stub_subtopic_page.guid}]

    resp = test_app_client.post(url_for('cms.set_measure_order'),
                                data=json.dumps({"positions": updates}),
                                content_type='application/json')

    assert resp.status_code == 200

    page_service = PageService()
    page_service.init_app(app)
    udpated_page = page_service.get_page(stub_subtopic_page.guid)

    assert udpated_page.children[0].guid == '1'
    assert udpated_page.children[1].guid == '1'
    assert udpated_page.children[2].guid == '0'
    assert udpated_page.children[3].guid == '0'
    assert udpated_page.children[4].guid == '0'


def test_view_edit_measure_page(test_app_client, mock_user, stub_topic_page, stub_subtopic_page, stub_measure_page):

    with test_app_client.session_transaction() as session:
        session['user_id'] = mock_user.id

    resp = test_app_client.get(url_for('cms.edit_measure_page',
                                       topic=stub_topic_page.guid,
                                       subtopic=stub_subtopic_page.guid,
                                       measure=stub_measure_page.guid,
                                       version=stub_measure_page.version))

    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode('utf-8'), 'html.parser')

    assert page.h1.text.strip() == 'Edit measure'

    title = page.find('input', attrs={'id': 'title'})
    assert title
    assert title.attrs.get('value') == 'Test Measure Page'

    subtopic = page.find('select', attrs={'id': 'subtopic'})
    assert subtopic
    assert subtopic.find('option', selected=True).attrs.get('value') == 'subtopic_example'

    time_covered = page.find('input', attrs={'id': 'time_covered'})
    assert time_covered
    assert time_covered.attrs.get('value') == '4 months'

    assert len(page.find_all('input', class_='country')) == 4

    # TODO lowest level of geography

    # Data sources
    source_text = page.find('input', attrs={'id': 'source_text'})
    assert source_text
    assert source_text.attrs.get('value') == 'DWP Stats'

    # TODO publisher/dept source

    source_url = page.find('input', attrs={'id': 'source_url'})
    assert source_url
    assert source_url.attrs.get('value') == 'http://dwp.gov.uk'

    published_date = page.find('input', attrs={'id': 'published_date'})
    assert published_date
    assert published_date.attrs.get('value') == '15th May 2017'

    # TODO frequency of release

    suppression_and_disclosure = page.find('textarea', attrs={'id': 'suppression_and_disclosure'})
    assert suppression_and_disclosure
    assert suppression_and_disclosure.text == 'Suppression rules and disclosure control'

    label_suppression_and_disclosure = page.find('label', attrs={'for': 'suppression_and_disclosure'})
    assert label_suppression_and_disclosure.text == 'Suppression rules and disclosure control'

    contact_name = page.find('input', attrs={'id': 'contact_name'})
    assert contact_name
    assert contact_name.attrs.get('value') == 'Jane Doe'

    contact_email = page.find('input', attrs={'id': 'contact_email'})
    assert contact_email
    assert contact_email.attrs.get('value') == 'janedoe@example.com'

    contact_phone = page.find('input', attrs={'id': 'contact_phone'})
    assert contact_phone
    assert contact_phone.attrs.get('value') == ''

    summary = page.find('textarea', attrs={'id': 'summary'})
    assert summary
    assert summary.text == 'Unemployment Summary'

    need_to_know = page.find('textarea', attrs={'id': 'need_to_know'})
    assert need_to_know
    assert need_to_know.text == 'Need to know this'

    measure_summary = page.find('textarea', attrs={'id': 'measure_summary'})
    assert measure_summary
    assert measure_summary.text == 'Unemployment measure summary'

    ethnicity_definition_summary = page.find('textarea', attrs={'id': 'ethnicity_definition_summary'})
    assert ethnicity_definition_summary
    assert ethnicity_definition_summary.text == 'Ethnicity information'

    data_source_purpose = page.find('textarea', attrs={'id': 'data_source_purpose'})
    assert data_source_purpose
    assert data_source_purpose.text == 'Data source purpose'

    methodology = page.find('textarea', attrs={'id': 'methodology'})
    assert methodology
    assert methodology.text == 'how we measure unemployment'

    estimation = page.find('textarea', attrs={'id': 'estimation'})
    assert estimation
    assert estimation.text == 'X people are unemployed'

    related_publications = page.find('textarea', attrs={'id': 'related_publications'})
    assert related_publications
    assert related_publications.text == 'Related publications'

    qmi_url = page.find('input', attrs={'id': 'qmi_url'})
    assert qmi_url
    assert qmi_url.attrs.get('value') == 'http://www.quality-street.gov.uk'

    further_technical_information = page.find('textarea', attrs={'id': 'further_technical_information'})
    assert further_technical_information
    assert further_technical_information.text == 'Further technical information'
