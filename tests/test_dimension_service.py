from application.cms.models import Dimension
from application.cms.dimension_service import DimensionService

dimension_service = DimensionService()


def test_create_dimension_on_measure_page(stub_measure_page):

    assert not Dimension.query.all()
    assert stub_measure_page.dimensions.count() == 0

    dimension_service.create_dimension(stub_measure_page,
                                       title='test-dimension',
                                       time_period='time_period',
                                       summary='summary',
                                       ethnicity_category='')

    db_dimension = Dimension.query.all()[0]
    assert stub_measure_page.dimensions[0].guid == db_dimension.guid
    assert stub_measure_page.dimensions[0].title == db_dimension.title


def test_delete_dimension_from_measure_page(stub_measure_page):

    assert not Dimension.query.all()
    assert stub_measure_page.dimensions.count() == 0

    dimension_service.create_dimension(stub_measure_page,
                                       title='test-dimension',
                                       time_period='time_period',
                                       summary='summary', ethnicity_category='')

    db_dimension = Dimension.query.all()[0]
    assert stub_measure_page.dimensions[0].guid == db_dimension.guid

    dimension_service.delete_dimension(stub_measure_page, db_dimension.guid)
    assert not Dimension.query.all()
    assert stub_measure_page.dimensions.count() == 0


def test_update_dimension(stub_measure_page):
    assert not Dimension.query.all()
    assert stub_measure_page.dimensions.count() == 0

    dimension = dimension_service.create_dimension(stub_measure_page,
                                                   title='test-dimension',
                                                   time_period='time_period',
                                                   summary='summary', ethnicity_category='')

    update_data = {'title': 'updated-title', 'time_period': 'updated_time_period'}

    dimension_service.update_dimension(dimension, update_data)

    updated_dimension = stub_measure_page.dimensions[0]
    assert dimension.guid == updated_dimension.guid
    assert updated_dimension.title == 'updated-title'
    assert updated_dimension.time_period == 'updated_time_period'


def test_add_chart_to_dimension(stub_measure_page):
    assert not Dimension.query.all()
    assert stub_measure_page.dimensions.count() == 0

    dimension = dimension_service.create_dimension(stub_measure_page,
                                                   title='test-dimension',
                                                   time_period='time_period',
                                                   summary='summary', ethnicity_category='')

    chart = {"chart_is_just_a": "dictionary"}

    update_data = {'chart': chart}

    dimension_service.update_dimension(dimension, update_data)

    updated_dimension = stub_measure_page.dimensions[0]
    assert dimension.guid == updated_dimension.guid
    assert updated_dimension.chart
    assert updated_dimension.chart == chart


def test_add_table_to_dimension(stub_measure_page):
    assert not Dimension.query.all()
    assert stub_measure_page.dimensions.count() == 0

    dimension = dimension_service.create_dimension(stub_measure_page,
                                                   title='test-dimension',
                                                   time_period='time_period',
                                                   summary='summary', ethnicity_category='')

    table = {"table_is_just_a": "dictionary"}

    update_data = {'table': table}

    dimension_service.update_dimension(dimension, update_data)

    updated_dimension = stub_measure_page.dimensions[0]
    assert dimension.guid == updated_dimension.guid
    assert updated_dimension.table
    assert updated_dimension.table == table


def test_delete_chart_from_dimension(stub_measure_page):
    assert not Dimension.query.all()
    assert stub_measure_page.dimensions.count() == 0

    dimension = dimension_service.create_dimension(stub_measure_page,
                                                   title='test-dimension',
                                                   time_period='time_period',
                                                   summary='summary', ethnicity_category='')

    chart = {"chart_is_just_a": "dictionary"}
    update_data = {'chart': chart}
    dimension_service.update_dimension(dimension, update_data)
    updated_dimension = stub_measure_page.dimensions[0]
    assert updated_dimension.chart

    dimension_service.delete_chart(updated_dimension)
    assert not updated_dimension.chart


def test_delete_table_from_dimension(stub_measure_page):
    assert not Dimension.query.all()
    assert stub_measure_page.dimensions.count() == 0

    dimension = dimension_service.create_dimension(stub_measure_page,
                                                   title='test-dimension',
                                                   time_period='time_period',
                                                   summary='summary', ethnicity_category='')

    table = {"table_is_just_a": "dictionary"}
    update_data = {'table': table}
    dimension_service.update_dimension(dimension, update_data)
    updated_dimension = stub_measure_page.dimensions[0]
    assert updated_dimension.table

    dimension_service.delete_table(updated_dimension)
    assert not updated_dimension.table


def test_add_or_update_dimensions_to_measure_page_preserves_order(stub_measure_page):

    assert not Dimension.query.all()
    assert stub_measure_page.dimensions.count() == 0

    d1 = dimension_service.create_dimension(stub_measure_page,
                                            title='test-dimension-1',
                                            time_period='time_period',
                                            summary='summary', ethnicity_category='')

    d2 = dimension_service.create_dimension(stub_measure_page,
                                            title='test-dimension-2',
                                            time_period='time_period',
                                            summary='summary', ethnicity_category='')

    assert stub_measure_page.dimensions[0].title == d1.title
    assert d1.position == 0
    assert stub_measure_page.dimensions[0].position == d1.position

    assert stub_measure_page.dimensions[1].title == 'test-dimension-2'
    assert d2.position == 1
    assert stub_measure_page.dimensions[1].position == d2.position

    # after update. positions should not have changed
    dimension_service.update_dimension(d1, {'summary': 'updated summary'})
    assert d1.summary == 'updated summary'
    assert d1.position == 0
    assert d2.position == 1
