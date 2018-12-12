from application.cms.models import DimensionClassification, MeasureVersion, Dimension, Classification, Ethnicity

"""
The model that links Dimensions to Values is complicated

The Classification - Value model
    A categorisation is a list of values (i.e. Bangladeshi, Indian, Pakistani, Black, ...)
    A categorisation may also have broad "parent" categories (i.e. Asian, Black, Mixed, ...)

Dimensions - Classification model
    All dimensions are linked to a categorisation by the DimensionClassification table
    The .includes_parents property specifies whether "parent" data has been included
"""


def query_dimensions_with_categorisation_link_to_values():
    as_child = query_dimensions_linked_to_values_as_standard()
    as_parent = query_dimensions_linked_to_values_as_parent()

    return as_child.union(as_parent).distinct().order_by("page_position", "dimension_position")


def query_dimensions_linked_to_values_as_standard():
    """
    Find all dimensions and value links through standard relationships

    :return: a query
    """
    import sqlalchemy as sa
    from application import db

    query = (
        db.session.query(
            MeasureVersion.parent_guid.label("subtopic_guid"),
            MeasureVersion.guid.label("page_guid"),
            MeasureVersion.title.label("page_title"),
            MeasureVersion.version.label("page_version"),
            MeasureVersion.uri.label("page_uri"),
            MeasureVersion.position.label("page_position"),
            Dimension.guid.label("dimension_guid"),
            Dimension.title.label("dimension_title"),
            Dimension.position.label("dimension_position"),
            Classification.title.label("categorisation"),
            Ethnicity.value.label("value"),
            Ethnicity.position.label("value_position"),
        )
        .join(Dimension)
        .join(DimensionClassification)
        .join(Classification)
        .join((Ethnicity, Classification.ethnicities))
        .filter(MeasureVersion.latest == sa.text("TRUE"))
    )

    return query


def query_dimensions_linked_to_values_as_parent():
    """
    Find all dimension and value links through parent relationships

    :return: a query
    """
    import sqlalchemy as sa
    from application import db

    query = (
        db.session.query(
            MeasureVersion.parent_guid.label("subtopic_guid"),
            MeasureVersion.guid.label("page_guid"),
            MeasureVersion.title.label("page_title"),
            MeasureVersion.version.label("page_version"),
            MeasureVersion.uri.label("page_uri"),
            MeasureVersion.position.label("page_position"),
            Dimension.guid.label("dimension_guid"),
            Dimension.title.label("dimension_title"),
            Dimension.position.label("dimension_position"),
            Classification.title.label("categorisation"),
            Ethnicity.value.label("value"),
            Ethnicity.position.label("value_position"),
        )
        .join(Dimension)
        .join(DimensionClassification)
        .join(Classification)
        .join((Ethnicity, Classification.parent_values))
        .filter(MeasureVersion.latest == sa.text("TRUE"), DimensionClassification.includes_parents == sa.text("TRUE"))
    )

    return query


def query_dimensions_with_categorisation_link_to_value(value):
    """
    Find all dimensions that are linked to a value

    :param value: a string value i.e. Black
    :return: a query
    """
    as_child = query_dimensions_linked_to_value_as_standard(value)
    as_parent = query_dimensions_linked_to_value_as_parent(value)

    return as_child.union(as_parent).distinct().order_by("page_position", "dimension_position")


def query_dimensions_linked_to_value_as_standard(value):
    """
    Find all dimensions that are linked to a value as a standard value of it's categorisation

    :param value: a string value i.e. Black
    :return: a query
    """
    import sqlalchemy as sa
    from application import db

    query = (
        db.session.query(
            MeasureVersion.parent_guid.label("subtopic_guid"),
            MeasureVersion.guid.label("page_guid"),
            MeasureVersion.title.label("page_title"),
            MeasureVersion.version.label("page_version"),
            MeasureVersion.uri.label("page_uri"),
            MeasureVersion.position.label("page_position"),
            Dimension.guid.label("dimension_guid"),
            Dimension.title.label("dimension_title"),
            Dimension.position.label("dimension_position"),
        )
        .join(Dimension)
        .join(DimensionClassification)
        .join(Classification)
        .join((Ethnicity, Classification.ethnicities))
        .filter(MeasureVersion.latest == sa.text("TRUE"), Ethnicity.value == value)
    )

    return query


def query_dimensions_linked_to_value_as_parent(value):
    """
    Find all dimensions that are linked to a value as a parent value of it's categorisation

    :param value: a string value i.e. Black
    :return: a query
    """
    import sqlalchemy as sa
    from application import db

    query = (
        db.session.query(
            MeasureVersion.parent_guid.label("subtopic_guid"),
            MeasureVersion.guid.label("page_guid"),
            MeasureVersion.title.label("page_title"),
            MeasureVersion.version.label("page_version"),
            MeasureVersion.uri.label("page_uri"),
            MeasureVersion.position.label("page_position"),
            Dimension.guid.label("dimension_guid"),
            Dimension.title.label("dimension_title"),
            Dimension.position.label("dimension_position"),
        )
        .join(Dimension)
        .join(DimensionClassification)
        .join(Classification)
        .join((Ethnicity, Classification.parent_values))
        .filter(
            MeasureVersion.latest == sa.text("TRUE"),
            Ethnicity.value == value,
            DimensionClassification.includes_parents == sa.text("TRUE"),
        )
    )

    return query
