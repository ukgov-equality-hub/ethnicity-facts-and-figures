#!/usr/bin/env python

from application import db
from application.cms.models import Measure, Subtopic, Topic
from application.config import Config
from application.factory import create_app
from application.redirects.models import Redirect
from datetime import datetime
from slugify import slugify
import sys

sys.path.insert(0, ".")  # noqa


new_grouping = {
    "alcohol-smoking-and-drug-use": [
        "harmful-and-probable-dependent-drinking-in-adults",
        "adult-smokers",
        "cigarette-smoking-among-15-year-olds",
        "illicit-drug-use-among-adults",
        "drug-dependency-in-adults",
    ],
    "diet-and-exercise": [
        "healthy-eating-of-5-a-day-among-15-year-olds",
        "healthy-eating-of-5-a-day-among-adults",
        "physical-activity",
        "physical-inactivity",
        "overweight-adults",
        "overweight-children",
    ],
    "wellbeing": [
        "well-being-anxiety-yesterday",
        "well-being-happiness-yesterday",
        "well-being-life-satisfaction",
        "well-being-how-worthwhile-people-feel-the-things-they-do-in-their-life-are",
    ],
    "mental-health": [
        "prevalence-of-adhd-among-adults",
        "adults-screening-positive-for-bipolar-disorder",
        "adults-experiencing-common-mental-disorders",
        "detentions-under-the-mental-health-act",
        "outcomes-for-treatment-for-anxiety-and-depression",
        "prevalence-of-personality-disorder-in-adults",
        "adults-experiencing-a-psychotic-disorder",
        "adults-with-post-traumatic-stress-disorder-ptsd-in-the-month-prior-to-survey",
        "adults-reporting-suicidal-thoughts-attempts-and-self-harm",
        "adults-receiving-treatment-for-mental-or-emotional-problems",
        "adults-using-nhs-funded-mental-health-and-learning-disability-services",
    ],
    "physical-health": [
        "absence-of-tooth-decay-in-5-year-olds",
        "organ-donation-consent",
        "cancer-diagnosis-at-an-early-stage",
        "health-related-quality-of-life-for-people-aged-65-and-over",
        "hiv-infection-with-late-diagnosis",
    ],
    "patient-experience": [
        "access-to-nhs-dental-services",
        "inpatient-satisfaction-with-hospital-care",
        "patient-experience-of-primary-care-gp-services",
        "patient-satisfaction-with-gp-out-of-hours-services",
        "patient-satisfaction-with-nhs-dental-services",
        "satisfaction-with-access-to-gp-services",
    ],
    "social-care": ["adoptions"],
}

subtopic_title_mappings = {
    "Access to treatment": "Social care",
    "Exercise and activity": "Diet and exercise",
    "Patient experiences": "Patient experience",
    "Patient outcomes": "Physical health",
    "Physical and mental health": "Mental health",
    "Preventing illness": "Alcohol, smoking and drug use",
}

subtopic_new_order = [
    "Alcohol, smoking and drug use",
    "Diet and exercise",
    "Wellbeing",
    "Mental health",
    "Physical health",
    "Patient experience",
    "Social care",
]

redirects = {
    "health/access-to-treatment": "health/social-care",
    "health/exercise-and-activity": "health/diet-and-exercise",
    "health/patient-experiences": "health/patient-experience",
    "health/patient-outcomes": "health/physical-health",
    "health/physical-and-mental-health": "health/mental-health",
    "health/preventing-illness": "health/alcohol-smoking-and-drug-use",
}


def create_wellbeing_subtopic():
    print("+ Creating 'Wellbeing' subtopic")
    new_title = "Wellbeing"
    health = Topic.query.filter_by(title="Health").one()
    wellbeing = Subtopic(slug=slugify(new_title), title=new_title, position=0, topic=health)
    db.session.add(wellbeing)
    db.session.flush()


def rename_health_subtopics():
    print("+ Renaming subtopics")
    for before, after in subtopic_title_mappings.items():
        s = Subtopic.query.filter_by(title=before).one()
        s.title = after
        s.slug = slugify(after)

    db.session.flush()


def reorder_subtopics():
    print("+ Reordering sutopics under Health")
    for index, subtopic_title in enumerate(subtopic_new_order, start=0):
        s = Subtopic.query.filter_by(title=subtopic_title).one()
        s.position = index

    db.session.flush()


def redistribute_measures():
    print("+ Redistributing measures")
    for subtopic_slug, measure_slugs in new_grouping.items():
        subtopic = Subtopic.query.filter_by(slug=subtopic_slug).one()
        for measure_slug in measure_slugs:
            measure = Measure.query.filter_by(slug=measure_slug).order_by(Measure.id.desc()).first()
            if measure is not None:
                measure.subtopics = [subtopic]

    db.session.flush()


def reorder_measures_in_subtopics():
    print("+ Reordering measures within subtopics")
    for subtopic_slug, measure_slugs in new_grouping.items():
        for index, measure_slug in enumerate(measure_slugs, start=0):
            measure = Measure.query.filter_by(slug=measure_slug).order_by(Measure.id.desc()).first()
            if measure is not None:
                measure.position = index

    db.session.flush()


def add_redirects():
    print("+ Adding redirects")
    for from_uri, to_uri in redirects.items():
        new_redirect = Redirect(created=datetime.utcnow(), from_uri=from_uri, to_uri=to_uri)
        db.session.add(new_redirect)

    db.session.flush()


if __name__ == "__main__":
    app = create_app(Config())
    with app.app_context():
        create_wellbeing_subtopic()
        rename_health_subtopics()
        reorder_subtopics()
        redistribute_measures()
        reorder_measures_in_subtopics()
        add_redirects()
        db.session.commit()
