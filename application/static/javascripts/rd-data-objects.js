/**
 * Created by Tom.Ridd on 08/05/2017.
 */


function barchartObject(data, primary_column, secondary_column, parent_column, order_column,
                        chart_title, x_axis_label, y_axis_label, number_format) {
    dataRows = _.clone(data);
    headerRow = dataRows.shift();

    if(secondary_column === '[None]') {
        return barchartSingleObject(headerRow, dataRows, primary_column, parent_column, order_column, chart_title, x_axis_label, y_axis_label, number_format);
    } else {
        return barchartDoubleObject(headerRow, dataRows, primary_column, secondary_column, parent_column, order_column, chart_title, x_axis_label, y_axis_label, number_format);
    }
}

function barchartSingleObject(headerRow, dataRows, category_column, parent_column, order_column, chart_title, x_axis_label, y_axis_label, number_format) {
    var valueIndex = headerRow.indexOf('Value');
    var categoryIndex = headerRow.indexOf(category_column);
    var orderIndex = headerRow.indexOf(order_column);
    var parentIndex = headerRow.indexOf(parent_column)

    var categories = uniqueCategories(dataRows, categoryIndex, orderIndex);
    var values = _.map(categories, function(category) {
        return valueFromDatasetForCategory(dataRows, categoryIndex, valueIndex, category);
    });

    return {
        'type':'bar',
        'title':{'text':chart_title},
        'xAxis':{'title':{'text':x_axis_label}, 'categories':categories},
        'yAxis':{'title':{'text':y_axis_label}},
        'series': [{'name':category_column, 'data': values}],
        'number_format':number_format
    }
}


function valueFromDatasetForCategory(dataRows, categoryIndex, valueIndex, category) {
    var valueRow = _.find(dataRows, function(row) {
        return row[categoryIndex] === category;
    });
    return parseFloat(valueRow[valueIndex]);
}
function valueForCategory(dataRows, categoryIndex, valueIndex, categoryValue, chart_title, x_axis_label, y_axis_label) {
    for(r in dataRows) {
        if(dataRows[r][categoryIndex] === categoryValue) {
            return parseFloat(dataRows[r][valueIndex]);
        }
    }
    return 0;
}

function barchartDoubleObject(headerRow, dataRows, category1, category2, parent_column, order_column, chart_title, x_axis_label, y_axis_label, number_format) {
    var valueIndex = headerRow.indexOf('Value');
    var categoryIndex = headerRow.indexOf(category1);
    var parentIndex = headerRow.indexOf(parent_column);
    var orderIndex = headerRow.indexOf(order_column);

    var categories = uniqueCategories(dataRows, categoryIndex, orderIndex)

    var seriesIndex = headerRow.indexOf(category2);
    var series = uniqueDataInColumnMaintainOrder(dataRows, seriesIndex);

    var seriesData = [];
    for(var s in series) {
        var seriesRows = _.filter(dataRows, function(row) { return row[seriesIndex] === series[s];});
        var values = [];
        for(var c in categories) {
            values.push(valueForCategory(seriesRows, categoryIndex, valueIndex, categories[c]));
        }
        seriesData.push({'name':series[s], 'data': values});
    }

    return {
        'type':'bar',
        'title':{'text': chart_title},
        'xAxis':{'title':{'text':x_axis_label}, 'categories':categories},
        'yAxis':{'title':{'text':y_axis_label}},
        'series': sortChartSeries(seriesData),
        'number_format':number_format};
}

function panelBarchartObject(data, category_column, panel_column, chart_title, x_axis_label, y_axis_label, number_format) {
    var dataRows = _.clone(data);
    var headerRow = dataRows.shift();

    var valueIndex = headerRow.indexOf('Value');
    var categoryIndex = headerRow.indexOf(category_column);
    var parentIndex = headerRow.indexOf(parent_column);
    var orderIndex = headerRow.indexOf(order_column);

    var categories = uniqueCategories(dataRows, categoryIndex, orderIndex)

    var panelIndex = headerRow.indexOf(panel_column);
    var panelValues = uniqueDataInColumnMaintainOrder(dataRows, panelIndex);

    var panels = [];
    for(var p in panelValues) {
        var panelRows = _.filter(dataRows, function(row) { return row[panelIndex] === panelValues[p];});
        var values = [];
        for(var c in categories) {
            values.push(valueForCategory(panelRows, categoryIndex, valueIndex, categories[c]));
        }
        panels.push({
            'type':'small_bar',
            'title':{'text':panelValues[p]},
            'xAxis':{'title':{'text':x_axis_label}, 'categories':categories},
            'yAxis':{'title':{'text':y_axis_label}},
            'series': [{'name':category_column, 'data': values}],
            'number_format':number_format
        });
    }

    return {
        'type': 'panel_bar_chart',
        'title': {'text': chart_title},
        'xAxis': {'title': {'text': x_axis_label}, 'categories': categories},
        'yAxis': {'title': {'text': y_axis_label}},
        'panels': panels
    }
}

function uniqueCategories(dataRows, categoryIndex, orderIndex) {

    if(orderIndex) {
        return uniqueDataInColumnOrdered(dataRows, categoryIndex, orderIndex);
    } else {
        return uniqueDataInColumnMaintainOrder(dataRows, categoryIndex);
    }
}

function uniqueDataInColumn(data, index) {
    var values = _.map(data.slice(start = 0), function(item) {
        return item[index]; });
    return _.uniq(values).sort();
}

function uniqueDataInColumnOrdered(data, index, order_column) {
    // Sort by the specified column
    var sorted = _.sortBy(data, function (item) {
        return item[order_column];
    });
    // Pull out unique items
    var values = _.map(sorted, function(item) { return item[index];});
    return _.uniq(values);
}

function uniqueDataInColumnMaintainOrder(data, index) {
    var values = [];
    var used = {};
    _.forEach(data, function (item) {
        if(!(item[index] in used)) {
            values.push(item[index]);
            used[item[index]] = 1;
        }
    });
    return values;
}

function linechartObject(data, categories_column, series_column, chart_title, x_axis_label, y_axis_label, number_format) {
    dataRows = _.clone(data);
    headerRow = dataRows.shift();

    valueIndex = headerRow.indexOf('Value');
    categoryIndex = headerRow.indexOf(categories_column);
    categories = uniqueDataInColumnMaintainOrder(dataRows, categoryIndex);

    seriesIndex = headerRow.indexOf(series_column);
    seriesNames = uniqueDataInColumnMaintainOrder(dataRows, seriesIndex);

    chartSeries = [];
    for(s in seriesNames) {
        seriesName = seriesNames[s];
        values = [];
        for(c in categories) {
            category = categories[c];
            values.push(valueForCategoryAndSeries(dataRows, categoryIndex, category, seriesIndex, seriesName, valueIndex));
        }
        chartSeries.push({'name':seriesName, 'data':values});
    }

    return {
        'type':'line',
        'title':{'text':chart_title},
        'xAxis':{'title':{'text':x_axis_label}, 'categories':categories},
        'yAxis':{'title':{'text':y_axis_label}},
        'series': sortChartSeries(chartSeries),
        'number_format':number_format};
}

function panelLinechartObject(data, x_axis_column, panel_column, chart_title, x_axis_label, y_axis_label, number_format) {
    var dataRows = _.clone(data);
    var headerRow = dataRows.shift();

    var valueIndex = headerRow.indexOf('Value');

    var panelIndex = headerRow.indexOf(panel_column);
    var panelNames = uniqueDataInColumn(dataRows, panelIndex);

    var xAxisIndex = headerRow.indexOf(x_axis_column);
    var xAxisNames = uniqueDataInColumn(dataRows, xAxisIndex);

    var panelCharts = [];
    for(var p in panelNames) {
        var panelName = panelNames[p];
        var values = [];
        for(var c in xAxisNames) {
            var category = xAxisNames[c];
            values.push(valueForCategoryAndSeries(dataRows, xAxisIndex, category, panelIndex, panelName, valueIndex));
        }
        panelCharts.push({'type':'line',
            'title':{'text':panelName},
            'xAxis':{'title':{'text':x_axis_label}, 'categories':xAxisNames},
            'yAxis':{'title':{'text':y_axis_label}},
            'series': [{'name':panelName, 'data':values}],
            'number_format':number_format
        });
    }

    return {
        'type':'panel_line_chart',
        'title':{'text':chart_title},
        'panels': panelCharts,
        'number_format':number_format
    };
}

function valueForCategoryAndSeries(dataRows, categoryIndex, categoryValue, seriesIndex, seriesValue, valueIndex) {
    for(r in dataRows) {
        if((dataRows[r][categoryIndex] === categoryValue) && (dataRows[r][seriesIndex] === seriesValue)) {
            return parseFloat(dataRows[r][valueIndex]);
        }
    }
    return 0;
}

function sortChartSeries(serieses) {
    // check if these series are numerically sortable
    for(s in serieses) {
        var sort_value = toNumberSortValue(serieses[s].name);
        if(isNaN(sort_value)){
            // if not numeric return original series
            return serieses;
        }
    }
    // if series sortable assign a sort value
    for(s in serieses) {
        serieses[s].name_value = toNumberSortValue(serieses[s].name);
    }
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



function componentChartObject(data, grouping_column, series_column, chart_title, x_axis_label, y_axis_label, number_format) {
    dataRows = _.clone(data);
    headerRow = dataRows.shift();

    valueIndex = headerRow.indexOf('Value');
    groupingIndex = headerRow.indexOf(grouping_column);
    groups = uniqueDataInColumnMaintainOrder(dataRows, groupingIndex);

    seriesIndex = headerRow.indexOf(series_column);
    seriesNames = uniqueDataInColumnMaintainOrder(dataRows, seriesIndex);
    seriesNames = seriesNames.reverse()

    chartSeries = [];
    for(s in seriesNames) {
        seriesName = seriesNames[s];
        values = [];
        for(g in groups) {
            group = groups[g];
            values.push(valueForCategoryAndSeries(dataRows, groupingIndex, group, seriesIndex, seriesName, valueIndex));
        }
        chartSeries.push({'name':seriesName, 'data':values});
    }

    return {
        'type':'component',
        'title':{'text':chart_title},
        'xAxis':{'title':{'text':x_axis_label}, 'categories':groups},
        'yAxis':{'title':{'text':y_axis_label}},
        'series': chartSeries,
        'number_format':number_format};
}


function simpleTableObject(data, title, subtitle, footer, row_column, parent_column, group_column, order_column, data_columns, column_captions) {
    var table = null;
    if(group_column === '[None]') {
        table = simpleTable(data, title, subtitle, footer, row_column, parent_column, data_columns, order_column, column_captions);
    } else {
        table = groupedTable(data, title, subtitle, footer, row_column, parent_column, group_column, data_columns, order_column, column_captions);
    }
    return preProcessTableObject(table);
}

function simpleTable(data, title, subtitle, footer, category_column, parent_column, data_columns, order_column, column_captions) {
    var dataRows = _.clone(data);

    var headerRow = dataRows.shift();

    var columnIndex = headerRow.indexOf(category_column);
    var data_column_indices = _.map(data_columns, function(data_column) { return headerRow.indexOf(data_column); });

    var sortIndex = columnIndex;
    if(order_column !== '[None]') {
        sortIndex = headerRow.indexOf(order_column);
    }

    var parentIndex = columnIndex;
    var hasParentChild = false;
    if(parent_column !== '[None]') {
        parentIndex = headerRow.indexOf(parent_column);
        hasParentChild = true;
    }

    var data = _.map(dataRows, function(item) {
        // return {'category':item[columnIndex], 'parent':item[parentIndex], 'order': item[sortIndex], 'values':_.map(data_column_indices, function(i) { return item[i]})};
        var relationships = {
                'is_parent':false,
                'is_child':false,
                'parent':item[columnIndex]
        };
        if(hasParentChild) {
            var parent = item[parentIndex];
            var child = item[columnIndex];
            relationships = {
                'is_parent': parent === child,
                'is_child': parent !== child,
                'parent': parent
            }
        }

        return {'category':item[columnIndex], 'relationships':relationships, 'order': item[sortIndex], 'values':_.map(data_column_indices, function(i) { return item[i]})};
    });
    data = _.sortBy(data, function(item) { return item['order'];});

    return {
        'type':'simple',
        'parent_child': hasParentChild,
        'header': title,
        'subtitle' :subtitle,
        'footer' :footer,
        'category':category_column,
        'columns': column_captions,
        'data': data};
}

function groupedTable(data, title, subtitle, footer,  category_column, parent_column, group_column, data_columns, order_column, column_captions) {
    var dataRows = _.clone(data);
    var headerRow = dataRows.shift();

    var columnIndex = headerRow.indexOf(category_column);
    var data_column_indices = _.map(data_columns, function(data_column) { return headerRow.indexOf(data_column); });

    var group_column_index = headerRow.indexOf(group_column);
    var group_values = uniqueDataInColumnMaintainOrder(dataRows, group_column_index);

    var sortIndex = columnIndex;
    if(order_column !== '[None]') {
        sortIndex = headerRow.indexOf(order_column);
    }

    var parentIndex = columnIndex;
    var hasParentChild = false;
    if(parent_column && parent_column !== '[None]') {
        parentIndex = headerRow.indexOf(parent_column);
        hasParentChild = true;
    }

    var group_series = _.map(group_values, function(group) {
        var group_data = _.filter(dataRows, function(item) { return item[group_column_index] === group;});
        var group_data_items = _.map(group_data, function(item) {
            var relationships = {
                'is_parent':false,
                'is_child':false,
                'parent':item[columnIndex]
            };
            if(hasParentChild) {
                var parent = item[parentIndex];
                var child = item[columnIndex];
                relationships = {
                    'is_parent': parent === child,
                    'is_child': parent !== child,
                    'parent': parent
                }
            }
            return {'category':item[columnIndex], 'relationships':relationships, 'order':item[sortIndex], 'values':_.map(data_column_indices, function(i) { return item[i]})}

            // return {'category':item[columnIndex], 'parent':item[parentIndex], 'order':item[sortIndex], 'values':_.map(data_column_indices, function(i) { return item[i]})}
        });
        return {'group':group, 'data':group_data_items};
    });
    var original_obj = {
        'type':'grouped',
        'category': category_column,
        'title':{'text':'Grouped Table'},
        'header': title,
        'columns':column_captions,
        'groups': group_series};

    var group_columns = [''];

    _.forEach(original_obj.groups, function (group) {
        group_columns.push(group.group);
    });

    var data = [];
    var rows = _.map(original_obj.groups[0].data, function(item) { return item.category; });
    _.forEach(rows, function(row) {
        var values = [];
        var sortValue = '';
        var parentValue = '';
        var relationships = {};
        _.forEach(original_obj.groups, function(group) {
            row_item = _.findWhere(group.data, {'category':row});
            sortValue = row_item['order'];
            parentValue = row_item['parent'];
            relationships = row_item['relationships'];
            _.forEach(row_item.values, function(cell) {
                values.push(cell);
            })
        });

        data.push({'category': row, 'relationships': relationships, 'parent': parentValue, 'order':sortValue, 'values':values});
    });

    data = _.sortBy(data, function(item) { return item['order'];});
    group_series = _.map(group_series, function (group) {
        group.data = _.sortBy(group.data, function(item) { return item['order'];})
        return group;
    });

    return {
        'group_columns': group_columns,
        'type':'grouped',
        'category': category_column,
        'columns': column_captions,
        'data': data,
        'header':title,
        'subtitle':subtitle,
        'footer':footer,
        'groups': group_series,
        'parent_child': hasParentChild
    };
}

function columnDecimalPlaces(tableObject) {
    var dps = [];
    // iterate through columns
    for(var i in tableObject.data[0].values) {

        // gather all the data for that column
        var series = _.map(tableObject.data, function(item) {
            return item.values[i];
        });
        dps.push(seriesDecimalPlaces(series));
    }
    return dps;
}

function columnCouldBeAYear(tableObject) {
    var years = [];

    // iterate through columns
    for(var i in tableObject.data[0].values) {

        // gather all the data for that column
        var series = _.map(tableObject.data, function(item) { return item.values[i]; });
        years.push(seriesCouldBeYear(series));
    }
    return years;
}

function groupedTableDecimalPlaces(tableObject) {
    var dps = [];
    // iterate through columns
    for(var c in tableObject.groups[0].data[0].values) {

        // gather all data for a column
        var series = _.flatten(
            _.map(tableObject.groups, function(group) {
                return _.map(group.data, function(item) {
                    return item.values[c];
            })
        }));
        dps.push(seriesDecimalPlaces(series));
    }
    return dps;
}

function groupedTableCouldBeAYear(tableObject) {
    var years = [];
    // iterate through columns
    for(var c in tableObject.groups[0].data[0].values) {

        // gather all data for a column
        var series = _.flatten(
            _.map(tableObject.groups, function(group) {
                return _.map(group.data, function(item) {
                    return item.values[c];
            })
        }));
        years.push(seriesCouldBeYear(series));
    }
    return years;
}

function preProcessTableObject(tableObject) {
    if(tableObject.type === 'simple') {
        preProcessSimpleTableObject(tableObject);
    } else if(tableObject.type === 'grouped') {
        preProcessGroupedTableObject(tableObject);
    }
    return tableObject;
}

function preProcessSimpleTableObject(tableObject) {
    var columnDps = columnDecimalPlaces(tableObject);
    var couldBeYear = columnCouldBeAYear(tableObject);

    tableObject.data = _.map(tableObject.data, function(item) {
        item.values = _.map(_.zip(item.values, columnDps, couldBeYear), function(cellTuple) {
            if(cellTuple[2] === false) {
                return formatNumberWithDecimalPlaces(cellTuple[0], cellTuple[1]);
            } else {
                return cellTuple[0];
            }
        });
        return item;
    });
}

function preProcessGroupedTableObject(tableObject) {
    var columnDps = groupedTableDecimalPlaces(tableObject);
    var couldBeYear = groupedTableCouldBeAYear(tableObject);


    tableObject.groups = _.map(tableObject.groups, function(group) {
        group.data = _.map(group.data, function(item) {
           item.values = _.map(_.zip(item.values, columnDps, couldBeYear), function(cellTuple) {
                if(cellTuple[2] === false) {
                    return formatNumberWithDecimalPlaces(cellTuple[0], cellTuple[1]);
                } else {
                    return cellTuple[0];
                }
            });
            return item;
        });
        return group;
    });

    // update tableObject data
    tableObject.data = [];
    // for each row
    for(var rowNo in tableObject.groups[0].data) {
        // grab a prototype cell
        var row = _.clone(tableObject.groups[0].data[rowNo]);
        // fill it with all contents across the groups
        row.values = _.flatten(_.map(tableObject.groups, function(group) {
            return group.data[rowNo].values;
        }));
        // add to the data
        tableObject.data.push(row)
    }


    var items = _.sortBy(tableObject.groups[0].data, function(item) { return item.order; });
    var rows = _.map(items, function(item) { return item.category; });
    _.forEach(rows, function(row) {
        var row_html = '<tr><th>' + row + '</th>';
        _.forEach(tableObject.groups, function(group) {
            var row_item = _.findWhere(group.data, {'category':row});
            _.forEach(_.zip(row_item.values, columnDps, couldBeYear), function(cellValues) {
                if(cellValues[2]) {
                    row_html = row_html + '<td>' + cellValues[0] + '</td>';
                } else {
                    row_html = row_html + '<td>' + formatNumberWithDecimalPlaces(cellValues[0], cellValues[1]) + '</td>';
                }
            })
        });
    });
}