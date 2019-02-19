from application.data.charts import ChartObjectDataBuilder
from application.data.tables import TableObjectDataBuilder, TableObjectTableBuilder


class DimensionObjectBuilder:
    """
    Creates an object from table database entries that can be processed using file writers
    """

    def __init__(self):
        self.data_table = [[]]
        self.context = []

    @staticmethod
    def build(dimension):
        dimension_object = {"context": DimensionObjectBuilder.get_context(dimension)}

        if dimension.table:
            dimension_object["table"] = TableObjectDataBuilder.build(dimension.table)

        if dimension.chart:
            dimension_object["chart"] = ChartObjectDataBuilder.build(dimension.chart)

        if dimension.table:
            dimension_object["tabular"] = TableObjectTableBuilder.build(dimension.table)

        return dimension_object

    @staticmethod
    def get_context(dimension):
        title, source_url, publisher, publication_date = "", "", "", ""

        if dimension.page.primary_data_source:
            title = dimension.page.primary_data_source.title
            source_url = dimension.page.primary_data_source.source_url

            if dimension.page.primary_data_source.publisher:
                publisher = dimension.page.primary_data_source.publisher.name

            publication_date = dimension.page.primary_data_source.publication_date

        return {
            "measure": dimension.page.title,
            "dimension": dimension.title,
            "dimension_slug": "%s/%s" % (dimension.page.measure.slug, dimension.guid)
            if dimension.page.measure.slug
            else "",
            "guid": dimension.guid,
            "measure_guid": dimension.page.guid if dimension.page.guid else "",
            "measure_slug": dimension.page.measure.slug if dimension.page.measure.slug else "",
            "time_period": dimension.time_period if dimension.time_period else "",
            "location": dimension.page.format_area_covered(),
            "title": title,
            "source_url": source_url,
            "publisher": publisher,
            "publication_date": publication_date,
        }
