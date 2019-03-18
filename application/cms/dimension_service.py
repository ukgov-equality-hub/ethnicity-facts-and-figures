from flask import current_app
from sqlalchemy.orm.exc import NoResultFound

from application import db
from application.cms.exceptions import (
    DimensionNotFoundException,
    DimensionAlreadyExists,
    PageUnEditable,
    ClassificationFinderClassificationNotFoundException,
)
from application.cms.models import Dimension, Chart, Table
from application.cms.service import Service
from application.data.ethnicity_classification_matcher import EthnicityClassificationMatcher, BuilderClassification
from application.utils import create_guid


class DimensionService(Service):
    def __init__(self):
        super().__init__()

    def create_dimension(self, measure_version, title, time_period, summary):

        guid = create_guid(title)

        if not self.check_dimension_title_unique(measure_version, title):
            raise DimensionAlreadyExists()
        else:
            self.logger.info("Dimension with guid %s does not exist ok to proceed", guid)

            dimension = Dimension(
                guid=guid,
                title=title,
                time_period=time_period,
                summary=summary,
                measure_version=measure_version,
                position=measure_version.dimensions.count(),
            )

            measure_version.dimensions.append(dimension)
            db.session.commit()

            return measure_version.get_dimension(dimension.guid)

    # This does some pre-processing of form data submitted by chart and table builders
    # It also sets the flag update_classification=True when update_dimension is called, to
    # trigger reclassification of the dimension based on the updated chart or table
    def update_dimension_chart_or_table(self, dimension, post_data):
        data = {}
        if "chartObject" in post_data:
            data["chart"] = post_data["chartObject"]
            data["chart_2_source_data"] = post_data["source"]

        if "tableObject" in post_data:
            data["table"] = post_data["tableObject"]
            data["table_2_source_data"] = post_data["source"]

        if "classificationCode" in post_data:
            if post_data["classificationCode"] == "custom":
                data["use_custom"] = True
                data["classification_code"] = post_data["customClassification"]["code"]
                data["has_parents"] = post_data["customClassification"]["hasParents"]
                data["has_all"] = post_data["customClassification"]["hasAll"]
                data["has_unknown"] = post_data["customClassification"]["hasUnknown"]
            else:
                data["use_custom"] = False
                data["classification_code"] = post_data["classificationCode"]

        if "ethnicityValues" in post_data:
            data["ethnicity_values"] = post_data["ethnicityValues"]

        self.update_dimension(dimension, data, update_classification=True)

    def set_dimension_positions(self, dimension_positions):
        for item in dimension_positions:
            try:
                dimension = Dimension.query.filter_by(guid=item["guid"]).one()
                dimension.position = item["index"]
            except NoResultFound as e:
                self.logger.exception(e)
                raise DimensionNotFoundException()
        if db.session.dirty:
            db.session.commit()

    def delete_dimension(self, page, guid):
        if page.not_editable():
            message = 'Error updating page "{}" - only pages in DRAFT or REJECT can be edited'.format(page.title)
            self.logger.error(message)
            raise PageUnEditable(message)

        dimension = page.get_dimension(guid)

        db.session.delete(dimension)
        db.session.commit()

    @staticmethod
    def get_dimension_with_guid(guid):
        try:
            return Dimension.query.filter_by(guid=guid).one()
        except NoResultFound:
            raise DimensionNotFoundException()

    @staticmethod
    def check_dimension_title_unique(measure_version, title):
        try:
            Dimension.query.filter_by(measure_version=measure_version, title=title).one()
            return False
        except NoResultFound:
            return True

    def update_dimension(self, dimension, data, update_classification=False):  # noqa: C901 (complexity)
        dimension.title = data["title"] if "title" in data else dimension.title
        dimension.time_period = data["time_period"] if "time_period" in data else dimension.time_period
        dimension.summary = data["summary"] if "summary" in data else dimension.summary
        if "chart" in data:
            if dimension.dimension_chart is None:
                dimension.dimension_chart = Chart()
            dimension.dimension_chart.chart_object = data["chart"]
        if "table" in data:
            if dimension.dimension_table is None:
                dimension.dimension_table = Table()
            dimension.dimension_table.table_object = data["table"]

        if (
            dimension.dimension_chart
            and dimension.dimension_chart.chart_object
            and data.get("chart_2_source_data") is not None
        ):
            chart_options = data.get("chart_2_source_data").get("chartOptions")
            for key, val in chart_options.items():
                if val is None:
                    chart_options[key] = "[None]"
            data["chart_2_source_data"]["chartOptions"] = chart_options
            dimension.dimension_chart.settings_and_source_data = data.get("chart_2_source_data")
            if data["use_custom"] is False:
                self.__set_chart_dimension_classification_through_builder(dimension, data)
            else:
                self.__set_chart_custom_dimension_classification(dimension, data)

        if (
            dimension.dimension_table
            and dimension.dimension_table.table_object
            and data.get("table_2_source_data") is not None
        ):
            table_options = data.get("table_2_source_data").get("tableOptions")
            for key, val in table_options.items():
                if val is None:
                    table_options[key] = "[None]"
            data["table_2_source_data"]["tableOptions"] = table_options
            dimension.dimension_table.settings_and_source_data = data.get("table_2_source_data")
            if data["use_custom"] is False:
                self.__set_table_dimension_classification_through_builder(dimension, data)
            else:
                self.__set_table_custom_dimension_classification(dimension, data)

        dimension.set_updated_at()

        # This should be True if the update has come in from chart or table builder
        # but False if the dimension metadata form has been submitted with no update to chart or table
        if update_classification:
            dimension.update_dimension_classification_from_chart_or_table()

        db.session.commit()

    def __set_table_dimension_classification_through_builder(self, dimension, data):
        code_from_builder, ethnicity_values = DimensionService.__get_builder_classification_data(data)

        if code_from_builder:
            try:
                classification = DimensionService.__get_classification_from_request(code_from_builder, ethnicity_values)
                self.__set_table_dimension_classification(dimension, classification)
            except ClassificationFinderClassificationNotFoundException:
                self.logger.error(
                    "Error: Could not match table builder classification '{}' with a known classification"
                )

    def __set_table_custom_dimension_classification(self, dimension, data):

        classification = self.__get_classification_from_custom_request(
            code_from_builder=data["classification_code"],
            has_parents=data["has_parents"],
            has_all=data["has_all"],
            has_unknown=data["has_unknown"],
        )
        self.__set_table_dimension_classification(dimension, classification)

    def __set_table_dimension_classification(self, dimension, classification):
        table = dimension.dimension_table or Table()

        table.classification_id = classification.classification_id
        table.includes_parents = classification.includes_parents
        table.includes_all = classification.includes_all
        table.includes_unknown = classification.includes_unknown

        db.session.add(table)
        db.session.flush()  # Flush to DB will generate PK if it's a newly-created instance

        dimension.dimension_table = table

        db.session.commit()

    @staticmethod
    def __get_classification_from_request(code_from_builder, ethnicity_values):
        classification_finder = DimensionService.__get_classification_matcher()
        classification = classification_finder.get_classification_from_builder_values(
            code_from_builder, ethnicity_values
        )
        return classification

    @staticmethod
    def __get_classification_from_custom_request(code_from_builder, has_parents, has_all, has_unknown):
        classification_matcher = DimensionService.__get_classification_matcher()
        builder_classification = BuilderClassification(
            code_from_builder, has_parents=has_parents, has_all=has_all, has_unknown=has_unknown
        )
        classification = classification_matcher.convert_builder_classification_to_classification(builder_classification)
        return classification

    @staticmethod
    def __get_classification_matcher():
        return EthnicityClassificationMatcher(
            ethnicity_standardiser=current_app.classification_finder.standardiser,
            ethnicity_classification_collection=current_app.classification_finder.classification_collection,
        )

    def __set_chart_dimension_classification_through_builder(self, dimension, data):
        code_from_builder, ethnicity_values = DimensionService.__get_builder_classification_data(data)

        try:
            classification = DimensionService.__get_classification_from_request(code_from_builder, ethnicity_values)
            self.__set_chart_dimension_classification(dimension, classification)

        except ClassificationFinderClassificationNotFoundException:
            self.logger.error("Error: Could not match chart builder classification '{}' with a known classification")

    def __set_chart_custom_dimension_classification(self, dimension, data):

        classification = self.__get_classification_from_custom_request(
            code_from_builder=data["classification_code"],
            has_parents=data["has_parents"],
            has_all=data["has_all"],
            has_unknown=data["has_unknown"],
        )
        self.__set_chart_dimension_classification(dimension, classification)

    def __set_chart_dimension_classification(self, dimension, classification):
        chart = dimension.dimension_chart or Chart()

        chart.classification_id = classification.classification_id
        chart.includes_parents = classification.includes_parents
        chart.includes_all = classification.includes_all
        chart.includes_unknown = classification.includes_unknown

        db.session.add(chart)
        db.session.flush()  # Flush to DB will generate PK if it's a newly-created instance

        dimension.dimension_chart = chart

        db.session.commit()

    @staticmethod
    def __get_builder_classification_data(data):
        if "classification_code" not in data or data["classification_code"] == "":
            return None, None

        code_from_builder = data["classification_code"]
        if "ethnicity_values" in data and data["ethnicity_values"] != "":
            ethnicity_values = data["ethnicity_values"]
        else:
            ethnicity_values = []

        return code_from_builder, ethnicity_values


dimension_service = DimensionService()
