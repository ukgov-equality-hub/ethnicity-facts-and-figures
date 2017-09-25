/**
 * Created by Tom.Ridd on 08/05/2017.
 */
const defaultParentColor = '#2B8CC4';
const defaultChildColor = '#B3CBD9';
var VERSION = '1.1'; // panel charts include sort option

function barchartObject(data, primary_column, secondary_column, parent_column, order_column,
                        chart_title, x_axis_label, y_axis_label, number_format) {
    var dataRows = _.clone(data);
    var headerRow = dataRows.shift();
    if(isSimpleBarchart(secondary_column)) {
        return barchartSingleObject(headerRow, dataRows, primary_column, parent_column, order_column, chart_title, x_axis_label, y_axis_label, number_format);
    } else {
        return barchartDoubleObject(headerRow, dataRows, primary_column, secondary_column, parent_column, order_column, chart_title, x_axis_label, y_axis_label, number_format);
    }
}

function isSimpleBarchart(column_name) {
    return column_name === '[None]' || column_name === null;
}

function barchartSingleObject(headerRow, dataRows, category_column, parent_column, order_column, chart_title, x_axis_label, y_axis_label, number_format) {
    var indices = getIndices(headerRow, category_column, null, parent_column, order_column);

    var categories = uniqueCategories(dataRows, indices['category'], indices['order']);
    var values = _.map(categories, function(category) {
        return valueForCategory(dataRows, indices['category'], indices['value'], indices['parent'], category);
    });

    var parents = [];
    if(indices['parent'] !== null) {
        parents = _.unique(_.map(dataRows, function(row) { return row[indices['parent']]; }));
    }

    return {
        'type':'bar',
        'title':{'text':chart_title},
        'parent_child': indices['parent'] !== null,
        'xAxis':{'title':{'text':x_axis_label}, 'categories':categories},
        'yAxis':{'title':{'text':y_axis_label}},
        'series': [{'name':category_column, 'data': values}],
        'number_format':number_format,
        'parents':parents,
        'version':VERSION
    };
}

function barchartDoubleObject(headerRow, dataRows, category1, category2, parent_column, order_column, chart_title, x_axis_label, y_axis_label, number_format) {
    var indices = getIndices(headerRow, category1, category2, parent_column, order_column);

    var categories = uniqueCategories(dataRows, indices['category'], indices['order']);

    var series = uniqueDataInColumnMaintainOrder(dataRows, indices['secondary']);

    var seriesData = [];
    series.forEach(function(s){
        var seriesRows = _.filter(dataRows, function(row) { return row[indices['secondary']] === s;});
        var values = [];
        _.forEach(categories, function(category) {
            values.push(valueForCategory(seriesRows, indices['category'], indices['value'], indices['parent'], category));
        });
        seriesData.push({'name':s, 'data': values});
    });

    return {
        'type':'bar',
        'title':{'text': chart_title},
        'xAxis':{'title':{'text':x_axis_label}, 'categories':categories},
        'yAxis':{'title':{'text':y_axis_label}},
        'series': sortChartSeries(seriesData),
        'number_format':number_format,
        'version':VERSION
    };
}

function panelBarchartObject(data, category_column, panel_column, chart_title, x_axis_label, y_axis_label, number_format, category_order_column, panel_order_column) {
    var dataRows = _.clone(data);
    var headerRow = dataRows.shift();

    var indices = getIndices(headerRow, category_column, panel_column, null, category_order_column);
    var categories = uniqueCategories(dataRows, indices['category'], indices['order']);

    var panelValues = null;
    if(isUndefinedOrNull(panel_order_column) || panel_order_column === '[None]') {
        panelValues = uniqueDataInColumnMaintainOrder(dataRows, indices['secondary']);
    } else {
        panelValues = uniqueDataInColumn(dataRows, indices['secondary'], panel_order_column)
    }

    var panels = panelValues.map(function(panelValue) {
        var panelRows = _.filter(dataRows, function(row) { return row[indices['secondary']] === panelValue;});

        var values = categories.map(function(category) {
           return valueForCategory(panelRows, indices['category'], indices['value'], indices['parent'], category);
        });

        return {
            'type':'small_bar',
            'title':{'text':panelValue},
            'xAxis':{'title':{'text':x_axis_label}, 'categories':categories},
            'yAxis':{'title':{'text':y_axis_label}},
            'series': [{'name':category_column, 'data': values}],
            'number_format':number_format
        };
    });

    return {
        'type': 'panel_bar_chart',
        'title': {'text': chart_title},
        'xAxis': {'title': {'text': x_axis_label}, 'categories': categories},
        'yAxis': {'title': {'text': y_axis_label}},
        'panels': panels,
        'version':VERSION
    }
}


function linechartObject(data, categories_column, series_column, chart_title, x_axis_label, y_axis_label, number_format, series_order_column) {
    var dataRows = _.clone(data);
    var headerRow = dataRows.shift();
    var series_order_column_name = series_order_column === '[None]' ? null : series_order_column;

    var indices = getIndices(headerRow, categories_column, series_column, null, null, series_order_column_name);
    var categories = uniqueDataInColumnMaintainOrder(dataRows, indices['category']);
    var seriesNames = uniqueDataInColumnMaintainOrder(dataRows, indices['secondary']);

    /*
    This is going to require some major refactoring down line
    For now we are going to compromise with a degree of code ugliness, build tests, and then get to beautification
     */
    var series_index = indices['secondary'];
    var series_order_index = indices['custom'];
    if (series_order_index) {
        var order_values = _.map(seriesNames, function(series) {
            var index = _.findIndex(dataRows, function(row) {
                return row[series_index] === series;
            });
            return dataRows[index][series_order_index];
        });
        seriesNames = _.map(_.sortBy(_.zip(seriesNames, order_values), function(pair) { return pair[1]; }), function(pair) { return pair[0]; });
    }

    var chartSeries = [];
    _.forEach(seriesNames, function(seriesName) {
        var values = [];
        _.forEach(categories, function(category) {
            values.push(valueForCategoryAndSeries(dataRows, indices['category'], category, indices['secondary'], seriesName, indices['value']));
        });
        chartSeries.push({'name':seriesName, 'data':values});
    });

    return {
        'type':'line',
        'title':{'text':chart_title},
        'xAxis':{'title':{'text':x_axis_label}, 'categories':categories},
        'yAxis':{'title':{'text':y_axis_label}},
        'series': sortChartSeries(chartSeries),
        'number_format':number_format,
        'version':VERSION};
}

function panelLinechartObject(data, x_axis_column, panel_column, chart_title, x_axis_label, y_axis_label, number_format) {
    var dataRows = _.clone(data);
    var headerRow = dataRows.shift();
    var indices = getIndices(headerRow, panel_column, x_axis_column, null, null);

    var panelNames = uniqueDataInColumn(dataRows, indices['category']);
    var xAxisNames = uniqueDataInColumn(dataRows, indices['secondary']);

    var panelCharts = _.map(panelNames, function(panelName) {
            var values = _.map(xAxisNames, function(category) {
                 return valueForCategoryAndSeries(dataRows, indices['secondary'], category, indices['category'], panelName, indices['value']);
            });

            return {'type':'line',
                'title':{'text':panelName},
                'xAxis':{'title':{'text':x_axis_label}, 'categories':xAxisNames},
                'yAxis':{'title':{'text':y_axis_label}},
                'series': [{'name':panelName, 'data':values}],
                'number_format':number_format
            };
        });

    return {
        'type':'panel_line_chart',
        'title':{'text':chart_title},
        'panels': panelCharts,
        'number_format':number_format,
        'version':VERSION
    };
}


function componentChartObject(data, grouping_column, series_column, chart_title, x_axis_label, y_axis_label, number_format, row_order_column, series_order_column) {

    var dataRows = _.clone(data);
    var headerRow = dataRows.shift();
    var indices = getIndices(headerRow, grouping_column, series_column, null, row_order_column, series_order_column);

    var groups = null;
    if(isUndefinedOrNull(row_order_column) || row_order_column === '[None]') {
        groups = uniqueDataInColumnMaintainOrder(dataRows, indices['category']);
    } else {
        groups = uniqueDataInColumnOrdered(dataRows, indices['category'], indices['order']);
    }

    var seriesNames = null;
    if(isUndefinedOrNull(series_order_column) || series_order_column === '[None]') {
        seriesNames = uniqueDataInColumnMaintainOrder(dataRows, indices['secondary']).reverse();
    } else {
        seriesNames = uniqueDataInColumnOrdered(dataRows, indices['secondary'], indices['custom']).reverse();
    }

    var chartSeries = seriesNames.map(function(seriesName)
    {
        var values = groups.map(function(group) {
            return valueForCategoryAndSeries(dataRows, indices['category'], group, indices['secondary'], seriesName, indices['value'])
        });
        return {'name': seriesName, 'data': values};
    });

    return {
        'type':'component',
        'title':{'text':chart_title},
        'xAxis':{'title':{'text':x_axis_label}, 'categories':groups},
        'yAxis':{'title':{'text':y_axis_label}},
        'series': chartSeries,
        'number_format':number_format,
        'version':VERSION
    };
}


function uniqueCategories(dataRows, categoryIndex, orderIndex) {

    if(orderIndex) {
        return uniqueDataInColumnOrdered(dataRows, categoryIndex, orderIndex);
    } else {
        return uniqueDataInColumnMaintainOrder(dataRows, categoryIndex);
    }
}

function valueForCategory(dataRows, categoryIndex, valueIndex, parentIndex, categoryValue) {

    var rows = dataRows.filter(function(row) { return row[categoryIndex] === categoryValue });
    if(rows.length === 0) {
        return {y: 0, category: categoryValue};
    } else {
        var row = rows[0];
        if(row[categoryIndex] === categoryValue) {
            var valueIsNumeric = isNumber(row[valueIndex]);
            if(parentIndex) {
                var parentValue = row[parentIndex];
                var relationships = {is_parent:parentValue === categoryValue,
                    is_child: parentValue !== categoryValue, parent:parentValue};
                if(relationships['is_parent']){
                    return {
                        y: valueIsNumeric ? parseFloat(row[valueIndex]) : 0,
                        relationships: relationships,
                        category: row[categoryIndex],
                        color: defaultParentColor,
                        text: valueIsNumeric ? 'number' : row[valueIndex]
                    };
                } else {
                    return {
                        y: valueIsNumeric ? parseFloat(row[valueIndex]) : 0,
                        relationships: relationships,
                        category: row[categoryIndex],
                        color: defaultChildColor,
                        text: valueIsNumeric ? 'number' : row[valueIndex]
                    };
                }
            } else {
                return {y: valueIsNumeric ? parseFloat(row[valueIndex]) : 0,
                    category: row[categoryIndex],
                    text: valueIsNumeric ? 'number' : row[valueIndex]};
            }
        }
    }
}

function isNumber(value) {
    return !isNaN(parseFloat(value));
}

function valueForCategoryAndSeries(dataRows, categoryIndex, categoryValue, seriesIndex, seriesValue, valueIndex) {

    var rows = _.filter(dataRows, function(row) { return row[categoryIndex] === categoryValue && row[seriesIndex] === seriesValue });
    return rows.length > 0 ? parseFloat(rows[0][valueIndex]) : 0;
}

function sortChartSeries(serieses) {

    // check if these series are numerically sortable
    var invalidSerieses = serieses.filter(function(series) {
       return isNaN(toNumberSortValue(series.name))
    });
    if(invalidSerieses.length > 0) { return serieses; }

    // if series sortable assign a sort value
    serieses.forEach(function (series) {
        series.name_value = toNumberSortValue(series.name);
    });

    // return the sorted series
    return _.sortBy(serieses, function (series) {
        return series.name_value;
    })
}

function toNumberSortValue(value) {
    var floatVal = parseFloat(value);
    if(isNaN(floatVal)) {
    return parseFloat(value.substring(1));
    } else {
    return floatVal;
    }
}

function isUndefinedOrNull(value) {
    return value === undefined || value === null;
}

function getIndices(headerRow, category_column, secondary_column, parent_column, order_column, custom_column) {
    var headersLower = _.map(headerRow, function(item) { return item.toLowerCase();});

    var category = isUndefinedOrNull(category_column) ? null: headersLower.indexOf(category_column.toLowerCase());
    var order = isUndefinedOrNull(order_column) ? category : headersLower.indexOf(order_column.toLowerCase());
    var parent = isUndefinedOrNull(parent_column) ? null: headersLower.indexOf(parent_column.toLowerCase());
    var secondary = isUndefinedOrNull(secondary_column) ? null: headersLower.indexOf(secondary_column.toLowerCase());
    var custom = isUndefinedOrNull(custom_column) ? null: headersLower.indexOf(custom_column.toLowerCase());

    return {
        'category': category >= 0 ? category : null,
        'order': order >= 0 ? order : null,
        'secondary': secondary >= 0 ? secondary : null,
        'value': headersLower.indexOf('value'),
        'parent': parent >= 0 ? parent : null,
        'custom': custom >= 0 ? custom : null
    };
}

// If we're running under Node - required for testing
if(typeof exports !== 'undefined') {
    var _ = require('../vendor/underscore-min');
    var dataTools = require('./rd-data-tools');
    var uniqueDataInColumnMaintainOrder = dataTools.uniqueDataInColumnMaintainOrder;

    exports.barchartObject = barchartObject;
    exports.linechartObject = linechartObject;
    exports.componentChartObject = componentChartObject;
    exports.panelLinechartObject = panelLinechartObject;
    exports.panelBarchartObject = panelBarchartObject;
}
