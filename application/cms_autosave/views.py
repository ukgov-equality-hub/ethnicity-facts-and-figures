from flask import abort, render_template, request, current_app, flash
from flask_login import login_required, current_user

from application.auth.models import UPDATE_MEASURE
from application.cms import cms_blueprint
from application.cms.exceptions import PageNotFoundException, PageExistsException, StaleUpdateException, PageUnEditable
from application.cms.page_service import page_service
from application.cms.views import _diff_updates
from application.cms_autosave.forms import MeasurePageAutosaveForm
from application.utils import user_has_access, user_can

from application.cms.models import (
    FrequencyOfRelease,
    TypeOfStatistic,
    LowestLevelOfGeography,
    Organisation
)


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/<version>/edit_and_preview', methods=['GET', 'POST'])
@login_required
@user_has_access
@user_can(UPDATE_MEASURE)
def edit_and_preview_measure_page(topic, subtopic, measure, version):

    try:
        subtopic_page = page_service.get_page(subtopic)
        topic_page = page_service.get_page(topic)
        page = page_service.get_page_with_version(measure, version)
    except PageNotFoundException:
        abort(404)

    # Check the topic and subtopics in the URL are the right ones for the measure
    if page.parent != subtopic_page or page.parent.parent != topic_page:
        abort(404)

    if request.method == 'POST':
        print(f"POSTED FORM DATA:\n{request.form}")
        areas_covered = request.form.getlist('area_covered')
    form = MeasurePageAutosaveForm(
        obj=page,
        frequency_choices=FrequencyOfRelease,
        type_of_statistic_choices=TypeOfStatistic,
        lowest_level_of_geography_choices=LowestLevelOfGeography
    )

    saved = False
    if form.validate_on_submit():
        try:
            # this subtopic stuff is a bit stupid but they insist in loading more nonsense into this form
            # the original design was move was a separate activity not bundled up with edit
            form_data = form.data
            form_data['subtopic'] = request.form.get('subtopic', None)
            page_service.update_page(page, data=form_data, last_updated_by=current_user.email)
            message = 'Updated page "{}"'.format(page.title)
            current_app.logger.info(message)
            flash(message, 'info')
            saved = True
        except PageExistsException as e:
            current_app.logger.info(e)
            flash(str(e), 'error')
            form.title.data = page.title
        except StaleUpdateException as e:
            current_app.logger.error(e)
            diffs = _diff_updates(form, page)
            if diffs:
                flash('Your update will overwrite the latest content. Resolve the conflicts below', 'error')
            else:
                flash('Your update will overwrite the latest content. Reload this page', 'error')
        except PageUnEditable as e:
            current_app.logger.info(e)
            flash(str(e), 'error')

    context = {
        'form': form,
        'topic': topic_page,
        'subtopic': subtopic_page,
        'measure': page,
        # 'status': current_status,
        'available_actions': page.available_actions(),
        # 'next_approval_state': approval_state if 'APPROVE' in available_actions else None,
        # 'diffs': diffs,
        'organisations_by_type': Organisation.select_options_by_type(),
        # 'topics': topics
    }
    return render_template(
        "cms_autosave/edit_and_preview_measure.html", **context
    )

# @cms_blueprint.route('/<topic>/<subtopic>/<measure>/<version>/edit', methods=['GET', 'POST'])
# @login_required
# @user_has_access
# def edit_measure_page(topic, subtopic, measure, version):
#     diffs = {}
#     try:
#         subtopic_page = page_service.get_page(subtopic)
#         topic_page = page_service.get_page(topic)
#         page = page_service.get_page_with_version(measure, version)
#
#         topics = page_service.get_pages_by_type('topic')
#         topics.sort(key=lambda page: page.title)
#
#     except PageNotFoundException:
#         abort(404)
#
#     if page.type_of_data is not None:
#         administrative_data = True if TypeOfData.ADMINISTRATIVE in page.type_of_data else False
#         survey_data = True if TypeOfData.SURVEY in page.type_of_data else False
#     else:
#         administrative_data = survey_data = False
#
#     if page.secondary_source_1_type_of_data is not None:
#         secondary_source_1_administrative_data = True if TypeOfData.ADMINISTRATIVE in page.secondary_source_1_type_of_data else False  # noqa
#         secondary_source_1_survey_data = True if TypeOfData.SURVEY in page.secondary_source_1_type_of_data else False  # noqa
#     else:
#         secondary_source_1_administrative_data = secondary_source_1_survey_data = False
#
#     if page.area_covered is not None:
#         if UKCountry.UK in page.area_covered:
#             england = wales = scotland = northern_ireland = True
#         else:
#             england = True if UKCountry.ENGLAND in page.area_covered else False
#             wales = True if UKCountry.WALES in page.area_covered else False
#             scotland = True if UKCountry.SCOTLAND in page.area_covered else False
#             northern_ireland = True if UKCountry.NORTHERN_IRELAND in page.area_covered else False
#     else:
#         england = wales = scotland = northern_ireland = False
#
#     form = MeasurePageForm(obj=page,
#                            administrative_data=administrative_data,
#                            survey_data=survey_data,
#                            secondary_source_1_administrative_data=secondary_source_1_administrative_data,
#                            secondary_source_1_survey_data=secondary_source_1_survey_data,
#                            frequency_choices=FrequencyOfRelease,
#                            type_of_statistic_choices=TypeOfStatistic,
#                            england=england,
#                            wales=wales,
#                            scotland=scotland,
#                            northern_ireland=northern_ireland,
#                            lowest_level_of_geography_choices=LowestLevelOfGeography)
#
#     # Temporary to work out issue with data deletions
#     if request.method == 'GET':
#         message = 'EDIT MEASURE: GET form for page edit: %s' % form.data
#     if request.method == 'POST':
#         message = 'EDIT MEASURE: POST form for page edit: %s' % form.data
#     current_app.logger.info(message)
#
#     if 'save-and-review' in request.form:
#         form.frequency_id.validators = [Optional()]
#
#     saved = False
#     if form.validate_on_submit():
#         try:
#             # this subtopic stuff is a bit stupid but they insist in loading more nonsense into this form
#             # the original design was move was a separate activity not bundled up with edit
#             form_data = form.data
#             form_data['subtopic'] = request.form.get('subtopic', None)
#             page_service.update_page(page, data=form_data, last_updated_by=current_user.email)
#             message = 'Updated page "{}"'.format(page.title)
#             current_app.logger.info(message)
#             flash(message, 'info')
#             saved = True
#         except PageExistsException as e:
#             current_app.logger.info(e)
#             flash(str(e), 'error')
#             form.title.data = page.title
#         except StaleUpdateException as e:
#             current_app.logger.error(e)
#             diffs = _diff_updates(form, page)
#             if diffs:
#                 flash('Your update will overwrite the latest content. Resolve the conflicts below', 'error')
#             else:
#                 flash('Your update will overwrite the latest content. Reload this page', 'error')
#         except PageUnEditable as e:
#             current_app.logger.info(e)
#             flash(str(e), 'error')
#
#     if form.errors:
#         message = 'This page could not be saved. Please check for errors below'
#         flash(message, 'error')
#
#     current_status = page.status
#     available_actions = page.available_actions()
#     if 'APPROVE' in available_actions:
#         numerical_status = page.publish_status(numerical=True)
#         approval_state = publish_status.inv[(numerical_status + 1) % 6]
#
#     if saved and 'save-and-review' in request.form:
#         return redirect(url_for('cms.send_to_review',
#                                 topic=page.parent.parent.guid,
#                                 subtopic=page.parent.guid,
#                                 measure=page.guid,
#                                 version=page.version))
#     elif saved:
#         return redirect(url_for('cms.edit_measure_page',
#                                 topic=page.parent.parent.guid,
#                                 subtopic=page.parent.guid,
#                                 measure=page.guid,
#                                 version=page.version))
#     context = {
#         'form': form,
#         'topic': page.parent.parent,
#         'subtopic': page.parent,
#         'measure': page,
#         'status': current_status,
#         'available_actions': available_actions,
#         'next_approval_state': approval_state if 'APPROVE' in available_actions else None,
#         'diffs': diffs,
#         'organisations_by_type': Organisation.select_options_by_type(),
#         'topics': topics
#     }
#
#     return render_template("cms/edit_measure_page.html", **context)
