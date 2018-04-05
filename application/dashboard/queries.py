from application.cms.models import DimensionCategorisation, Page, Dimension, Categorisation, CategorisationValue

'''
The model that links Dimensions to Values is complicated

The Categorisation - Value model
    A categorisation is a list of values (i.e. Bangladeshi, Indian, Pakistani, Black, ...)
    A categorisation may also have broad "parent" categories (i.e. Asian, Black, Mixed, ...)

Dimensions - Categorisation model
    All dimensions are linked to a categorisation by the DimensionCategorisation table
    The .includes_parents property specifies whether "parent" data has been included
'''


def query_dimensions_with_categorisation_link_to_value(value):
    '''
    Find all dimensions that are linked to a value

    :param value: a string value i.e. Black
    :return: a query
    '''
    as_child = query_dimensions_linked_to_value_as_standard(value)
    as_parent = query_dimensions_linked_to_value_as_parent(value)

    return as_child.union(as_parent).distinct()


def query_dimensions_linked_to_value_as_standard(value):
    '''
    Find all dimensions that are linked to a value as a standard value of it's categorisation

    :param value: a string value i.e. Black
    :return: a query
    '''
    import sqlalchemy as sa
    from application import db

    query = db.session.query(
        Page.guid.label('page_guid'),
        Page.version.label('page_version'),
        Dimension.guid.label('dimension_guid')
    ).join(Dimension) \
        .join(DimensionCategorisation) \
        .join(Categorisation) \
        .join((CategorisationValue, Categorisation.values)) \
        .filter(Page.latest == sa.text('TRUE'),
                CategorisationValue.value == value) \
        .order_by(Categorisation.id)

    return query


def query_dimensions_linked_to_value_as_parent(value):
    '''
    Find all dimensions that are linked to a value as a parent value of it's categorisation

    :param value: a string value i.e. Black
    :return: a query
    '''
    import sqlalchemy as sa
    from application import db

    query = db.session.query(
        Page.guid.label('page_guid'),
        Page.version.label('page_version'),
        Dimension.guid.label('dimension_guid')
    ).join(Dimension) \
        .join(DimensionCategorisation) \
        .join(Categorisation) \
        .join((CategorisationValue, Categorisation.parent_values)) \
        .filter(Page.latest == sa.text('TRUE'),
                CategorisationValue.value == value,
                DimensionCategorisation.includes_parents == sa.text('TRUE')) \
        .order_by(Categorisation.id)

    return query
