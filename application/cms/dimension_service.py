from flask import current_app
from sqlalchemy import null
from sqlalchemy.orm.exc import NoResultFound

from application import db
from application.cms.classification_service import classification_service
from application.cms.dimension_classification_service import ClassificationLink, dimension_classification_service
from application.cms.exceptions import (
    DimensionNotFoundException,
    DimensionAlreadyExists,
    PageUnEditable,
    ClassificationFinderClassificationNotFoundException,
)
from application.cms.models import Dimension
from application.cms.service import Service
from application.data.ethnicity_classification_link_builder import EthnicityClassificationLinkBuilder
from application.utils import create_guid


class DimensionService(Service):
    def __init__(self):
        super().__init__()

    def create_dimension(
        self,
        page,
        title,
        time_period,
        summary,
        ethnicity_classification_id,
        include_parents=False,
        include_all=False,
        include_unknown=False,
    ):

        guid = create_guid(title)

        if not self.check_dimension_title_unique(page, title):
            raise DimensionAlreadyExists()
        else:
            self.logger.info("Dimension with guid %s does not exist ok to proceed", guid)

            db_dimension = Dimension(
                guid=guid,
                title=title,
                time_period=time_period,
                summary=summary,
                page=page,
                position=page.dimensions.count(),
            )

            page.dimensions.append(db_dimension)
            db.session.add(page)
            db.session.commit()

            if ethnicity_classification_id and ethnicity_classification_id != "":
                link = ClassificationLink(
                    classification_id=ethnicity_classification_id,
                    includes_all=include_all,
                    includes_parents=include_parents,
                    includes_unknown=include_unknown,
                )
                dimension_classification_service.set_table_classification_on_dimension(db_dimension, link)

            return page.get_dimension(db_dimension.guid)

    # TODO can this roll up into update dimension?
    def update_measure_dimension(self, dimension, post_data):
        data = {}
        if "chartObject" in post_data:
            data["chart"] = post_data["chartObject"]

            if "chartBuilderVersion" in post_data and post_data["chartBuilderVersion"] > 1:
                data["chart_2_source_data"] = post_data["source"]
                data["chart_builder_version"] = 2
            else:
                data["chart_source_data"] = post_data["source"]
                data["chart_builder_version"] = 1

        if "tableObject" in post_data:
            data["table"] = post_data["tableObject"]

            if "tableBuilderVersion" in post_data and post_data["tableBuilderVersion"] > 1:
                data["table_2_source_data"] = post_data["source"]
                data["table_builder_version"] = 2
            else:
                data["table_source_data"] = post_data["source"]
                data["table_builder_version"] = 1

        if "classificationCode" in post_data:
            data["classification_code"] = post_data["classificationCode"]

        if "ethnicityValues" in post_data:
            data["ethnicity_values"] = post_data["ethnicityValues"]

        self.update_dimension(dimension, data)

    def set_dimension_positions(self, dimension_positions):
        for item in dimension_positions:
            try:
                dimension = Dimension.query.filter_by(guid=item["guid"]).one()
                dimension.position = item["index"]
                db.session.add(dimension)
            except NoResultFound as e:
                self.logger.exception(e)
                raise DimensionNotFoundException()
        if db.session.dirty:
            db.session.commit()

    def delete_dimension(self, page, guid):
        if page.not_editable():
            message = 'Error updating page "{}" - only pages in DRAFT or REJECT can be edited'.format(page.guid)
            self.logger.error(message)
            raise PageUnEditable(message)

        dimension = page.get_dimension(guid)

        db.session.delete(dimension)
        db.session.commit()

    @staticmethod
    def get_dimension_with_guid(guid):
        try:
            return Dimension.query.filter_by(guid=guid).one()
        except NoResultFound as e:
            raise DimensionNotFoundException()

    @staticmethod
    def delete_chart(dimension):
        dimension.chart = null()
        dimension.chart_source_data = null()
        dimension.chart_2_source_data = null()
        db.session.add(dimension)
        db.session.commit()
        dimension_classification_service.remove_chart_classification_on_dimension(dimension, "Ethnicity")

    @staticmethod
    def delete_table(dimension):
        dimension.table = null()
        dimension.table_source_data = null()
        dimension.table_2_source_data = null()
        db.session.add(dimension)
        db.session.commit()
        dimension_classification_service.remove_table_classification_on_dimension(dimension, "Ethnicity")

    @staticmethod
    def check_dimension_title_unique(page, title):
        try:
            Dimension.query.filter_by(page=page, title=title).one()
            return False
        except NoResultFound as e:
            return True

    def update_dimension(self, dimension, data):
        dimension.title = data["title"] if "title" in data else dimension.title
        dimension.time_period = data["time_period"] if "time_period" in data else dimension.time_period
        dimension.summary = data["summary"] if "summary" in data else dimension.summary
        dimension.chart = data["chart"] if "chart" in data else dimension.chart
        dimension.table = data["table"] if "table" in data else dimension.table
        dimension.chart_builder_version = (
            data["chart_builder_version"] if "chart_builder_version" in data else dimension.chart_builder_version
        )
        dimension.table_builder_version = (
            data["table_builder_version"] if "table_builder_version" in data else dimension.table_builder_version
        )

        if dimension.chart and data.get("chart_source_data") is not None:
            chart_options = data.get("chart_source_data").get("chartOptions")
            for key, val in chart_options.items():
                if val is None:
                    chart_options[key] = "[None]"
            data["chart_source_data"]["chartOptions"] = chart_options
            dimension.chart_source_data = data.get("chart_source_data")

        if dimension.chart and data.get("chart_2_source_data") is not None:
            chart_options = data.get("chart_2_source_data").get("chartOptions")
            for key, val in chart_options.items():
                if val is None:
                    chart_options[key] = "[None]"
            data["chart_2_source_data"]["chartOptions"] = chart_options
            dimension.chart_2_source_data = data.get("chart_2_source_data")
            self.__set_chart_dimension_classification_through_builder(dimension, data)

        if dimension.table and data.get("table_source_data") is not None:
            table_options = data.get("table_source_data").get("tableOptions")
            for key, val in table_options.items():
                if val is None:
                    table_options[key] = "[None]"
            data["table_source_data"]["tableOptions"] = table_options
            dimension.table_source_data = data.get("table_source_data")

        if dimension.table and data.get("table_2_source_data") is not None:
            table_options = data.get("table_2_source_data").get("tableOptions")
            for key, val in table_options.items():
                if val is None:
                    table_options[key] = "[None]"
            data["table_2_source_data"]["tableOptions"] = table_options
            dimension.table_2_source_data = data.get("table_2_source_data")
            self.__set_table_dimension_classification_through_builder(dimension, data)

        db.session.add(dimension)
        db.session.commit()

    def __set_table_dimension_classification_through_builder(self, dimension, data):
        code_from_builder, ethnicity_values = DimensionService.__get_builder_classification_data(data)

        if code_from_builder:
            try:
                link = DimensionService.__get_requested_link(code_from_builder, ethnicity_values)
                dimension_classification_service.set_table_classification_on_dimension(dimension, link)
            except ClassificationFinderClassificationNotFoundException:
                self.logger.error("Error: Could not match external classification '{}' with a known classification")

    @staticmethod
    def __get_requested_link(code_from_builder, ethnicity_values):
        link_builder = EthnicityClassificationLinkBuilder(
            ethnicity_standardiser=current_app.classification_finder.standardiser,
            ethnicity_classification_collection=current_app.classification_finder.classification_collection,
            classification_service=classification_service,
        )
        link = link_builder.build_internal_classification_link(
            code_from_builder=code_from_builder, values_from_builder=ethnicity_values
        )
        return link

    def __set_chart_dimension_classification_through_builder(self, dimension, data):
        code_from_builder, ethnicity_values = DimensionService.__get_builder_classification_data(data)

        try:
            link = DimensionService.__get_requested_link(code_from_builder, ethnicity_values)
            dimension_classification_service.set_chart_classification_on_dimension(dimension, link)
        except ClassificationFinderClassificationNotFoundException:
            self.logger.error("Error: Could not match external classification '{}' with a known classification")

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
