from flask import abort, render_template
from flask_login import login_required

from application.auth.models import UPDATE_MEASURE
from application.cms import cms_blueprint
from application.cms.exceptions import PageNotFoundException
from application.cms.page_service import page_service
from application.utils import user_has_access, user_can


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/<version>/edit_and_preview', methods=['GET', 'POST'])
@user_can(UPDATE_MEASURE)
@user_has_access
@login_required
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

    context = {
        #  'form': form,
        'topic': topic_page,
        'subtopic': subtopic_page,
        'measure': page,
        # 'status': current_status,
        'available_actions': page.available_actions(),
        # 'next_approval_state': approval_state if 'APPROVE' in available_actions else None,
        # 'diffs': diffs,
        # 'organisations_by_type': Organisation.select_options_by_type(),
        # 'topics': topics
    }
    return render_template(
        "cms_autosave/edit_and_preview_measure.html", **context
    )
