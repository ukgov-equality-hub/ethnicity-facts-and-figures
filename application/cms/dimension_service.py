from flask import current_app
from sqlalchemy import null
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
from application.data.ethnicity_classification_link_builder import (
    EthnicityClassificationLinkBuilder,
    ExternalClassificationFinderLink,
)
from application.utils import create_guid


class DimensionService(Service):
    def __init__(self):
        super().__init__()

    def create_dimension(self, page, title, time_period, summary):

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

        chart_id = dimension.chart_id
        dimension.chart_id = None

        db.session.add(dimension)
        db.session.commit()

        chart = Chart.query.get(chart_id)
        db.session.delete(chart)
        db.session.commit()

        dimension.update_dimension_classification_from_chart_or_table()

    @staticmethod
    def delete_table(dimension):
        dimension.table = null()
        dimension.table_source_data = null()
        dimension.table_2_source_data = null()

        table_id = dimension.table_id
        dimension.table_id = None

        db.session.add(dimension)
        db.session.commit()

        table = Table.query.get(table_id)
        db.session.delete(table)
        db.session.commit()

        dimension.update_dimension_classification_from_chart_or_table()

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
            if data["use_custom"] is False:
                self.__set_chart_dimension_classification_through_builder(dimension, data)
            else:
                self.__set_chart_custom_dimension_classification(dimension, data)

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
            if data["use_custom"] is False:
                self.__set_table_dimension_classification_through_builder(dimension, data)
            else:
                self.__set_table_custom_dimension_classification(dimension, data)

        dimension.update_dimension_classification_from_chart_or_table()

        db.session.add(dimension)
        db.session.commit()

    def __set_table_dimension_classification_through_builder(self, dimension, data):
        code_from_builder, ethnicity_values = DimensionService.__get_builder_classification_data(data)

        if code_from_builder:
            try:
                link = DimensionService.__get_internal_link_from_request(code_from_builder, ethnicity_values)

                table = Table.query.filter_by(id=dimension.table_id).first() or Table()

                table.classification_id = code_from_builder
                table.includes_parents = link.includes_parents
                table.includes_all = link.includes_all
                table.includes_unknown = link.includes_unknown

                db.session.add(table)
                db.session.commit()

                dimension.table_id = table.id

                db.session.add(dimension)
                db.session.commit()

            except ClassificationFinderClassificationNotFoundException:
                self.logger.error("Error: Could not match external classification '{}' with a known classification")

    def __set_table_custom_dimension_classification(self, dimension, data):

        link = self.__get_internal_link_from_custom_request(
            code_from_builder=data["classification_code"],
            has_parents=data["has_parents"],
            has_all=data["has_all"],
            has_unknown=data["has_unknown"],
        )
        table = Table.query.filter_by(id=dimension.table_id).first() or Table()

        table.classification_id = link.classification_id
        table.includes_parents = link.includes_parents
        table.includes_all = link.includes_all
        table.includes_unknown = link.includes_unknown

        db.session.add(table)
        db.session.commit()

        dimension.table_id = table.id

        db.session.add(dimension)
        db.session.commit()

    @staticmethod
    def __get_internal_link_from_request(code_from_builder, ethnicity_values):
        link_builder = DimensionService.__get_link_builder()
        link = link_builder.build_internal_classification_link(code_from_builder, ethnicity_values)
        return link

    @staticmethod
    def __get_internal_link_from_custom_request(code_from_builder, has_parents, has_all, has_unknown):
        link_builder = DimensionService.__get_link_builder()
        external_link = ExternalClassificationFinderLink(
            code_from_builder, has_parents=has_parents, has_all=has_all, has_unknown=has_unknown
        )
        internal_link = link_builder.convert_external_link(external_link)
        return internal_link

    @staticmethod
    def __get_link_builder():
        return EthnicityClassificationLinkBuilder(
            ethnicity_standardiser=current_app.classification_finder.standardiser,
            ethnicity_classification_collection=current_app.classification_finder.classification_collection,
        )

    def __set_chart_dimension_classification_through_builder(self, dimension, data):
        code_from_builder, ethnicity_values = DimensionService.__get_builder_classification_data(data)

        try:
            link = DimensionService.__get_internal_link_from_request(code_from_builder, ethnicity_values)

            chart = Chart.query.filter_by(id=dimension.chart_id).first() or Chart()

            chart.classification_id = code_from_builder
            chart.includes_parents = link.includes_parents
            chart.includes_all = link.includes_all
            chart.includes_unknown = link.includes_unknown

            db.session.add(chart)
            db.session.commit()

            dimension.chart_id = chart.id

            db.session.add(dimension)
            db.session.commit()

        except ClassificationFinderClassificationNotFoundException:
            self.logger.error("Error: Could not match external classification '{}' with a known classification")

    def __set_chart_custom_dimension_classification(self, dimension, data):

        link = self.__get_internal_link_from_custom_request(
            code_from_builder=data["classification_code"],
            has_parents=data["has_parents"],
            has_all=data["has_all"],
            has_unknown=data["has_unknown"],
        )
        chart = Chart.query.filter_by(id=dimension.chart_id).first() or Chart()

        chart.classification_id = link.classification_id
        chart.includes_parents = link.includes_parents
        chart.includes_all = link.includes_all
        chart.includes_unknown = link.includes_unknown

        db.session.add(chart)
        db.session.commit()

        dimension.chart_id = chart.id

        db.session.add(dimension)
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
