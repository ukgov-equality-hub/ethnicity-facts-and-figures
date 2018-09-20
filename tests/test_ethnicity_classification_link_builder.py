from application.cms.dimension_classification_service import ClassificationLink
from application.data.standardisers.ethnicity_classification_link_builder import EthnicityClassificationLinkBuilder


def test_build_classification_returns_a_classification_link():
    # given a builder
    builder = EthnicityClassificationLinkBuilder("test", [])

    # when we build
    link = builder.build_classification_link()

    # then we have a classification link
    assert isinstance(link, ClassificationLink)


def test_build_classification_returns_a_classification_link():
    # given a builder
    builder = EthnicityClassificationLinkBuilder("test", [])

    # when we build
    link = builder.build_classification_link()

    # then we have a classification link
    assert isinstance(link, ClassificationLink)
