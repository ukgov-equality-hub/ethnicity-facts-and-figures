from flask import render_template, request, current_app, flash
from flask_login import login_required, current_user

from application.auth.models import UPDATE_MEASURE
from application.cms import cms_blueprint
from application.cms.exceptions import (
    PageExistsException,
    StaleUpdateException,
    PageUnEditable
)
from application.cms.models import (
    FrequencyOfRelease,
    TypeOfStatistic,
    LowestLevelOfGeography,
    Organisation,
)
from application.cms.page_service import page_service
from application.cms.views import _diff_updates
from application.cms_autosave.forms import MeasurePageAutosaveForm
from application.utils import user_has_access, user_can


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/<version>/edit_and_preview', methods=['GET', 'POST'])
@login_required
@user_has_access
@user_can(UPDATE_MEASURE)
def edit_and_preview_measure_page(topic, subtopic, measure, version):

    topic_page, subtopic_page, measure_page = page_service.get_measure_page_hierarchy(
        topic, subtopic, measure, version)

    form = MeasurePageAutosaveForm(
        obj=measure_page,
        frequency_choices=FrequencyOfRelease,
        type_of_statistic_choices=TypeOfStatistic,
        lowest_level_of_geography_choices=LowestLevelOfGeography,
    )

    saved = False
    if form.validate_on_submit():
        try:
            # this subtopic stuff is a bit stupid but they insist in loading more nonsense into this form
            # the original design was move was a separate activity not bundled up with edit
            form_data = form.data
            form_data['subtopic'] = request.form.get('subtopic', None)
            page_service.update_page(page, data=form_data, last_updated_by=current_user.email)
            message = 'Updated page "{}"'.format(measure_page.title)
            current_app.logger.info(message)
            flash(message, 'info')
            saved = True
        except PageExistsException as e:
            current_app.logger.info(e)
            flash(str(e), 'error')
            form.title.data = measure_page.title
        except StaleUpdateException as e:
            current_app.logger.error(e)
            diffs = _diff_updates(form, measure_page)
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
        'measure': measure_page,
        'available_actions': measure_page.available_actions(),
        'organisations_by_type': Organisation.select_options_by_type(),
    }
    return render_template(
        "cms_autosave/edit_and_preview_measure.html", **context
    )
