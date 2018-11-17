from application.data.charts import ChartObjectDataBuilder
from application.data.tables import TableObjectDataBuilder, TableObjectTableBuilder
from application.cms.models import Dimension
from typing import Any
from typing import Dict
from typing import Union


class DimensionObjectBuilder:
    """
    Creates an object from table database entries that can be processed using file writers
    """

    def __init__(self) -> None:
        self.data_table = [[]]
        self.context = []

    @staticmethod
    def build(dimension: Dimension) -> Union[Dict[str, Dict[str, Any]], Dict[str, Dict[str, str]]]:
        dimension_object = {"context": DimensionObjectBuilder.get_context(dimension)}

        if dimension.table:
            dimension_object["table"] = TableObjectDataBuilder.build(dimension.table)

        if dimension.chart:
            dimension_object["chart"] = ChartObjectDataBuilder.build(dimension.chart)

        if dimension.table:
            dimension_object["tabular"] = TableObjectTableBuilder.build(dimension.table)

        return dimension_object

    @staticmethod
    def get_context(dimension: Dimension) -> Dict[str, str]:
        return {
            "measure": dimension.page.title,
            "dimension": dimension.title,
            "dimension_uri": "%s/%s" % (dimension.page.uri, dimension.guid) if dimension.page.uri else "",
            "guid": dimension.guid,
            "measure_guid": dimension.page.guid if dimension.page.guid else "",
            "measure_uri": dimension.page.uri if dimension.page.uri else "",
            "time_period": dimension.time_period if dimension.time_period else "",
            "location": dimension.page.format_area_covered(),
            "source_text": dimension.page.source_text if dimension.page.source_text else "",
            "source_url": dimension.page.source_url if dimension.page.source_url else "",
            "department": dimension.page.department_source.name if dimension.page.department_source else "",
            "publication_date": dimension.page.published_date if dimension.page.published_date else "",
        }
