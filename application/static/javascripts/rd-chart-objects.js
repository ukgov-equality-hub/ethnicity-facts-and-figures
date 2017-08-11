/**
 * Created by Tom.Ridd on 08/05/2017.
 */
const defaultParentColor = '#054462';
const defaultChildColor = '#6da8d6';


function barchartObject(data, primary_column, secondary_column, parent_column, order_column,
                        chart_title, x_axis_label, y_axis_label, number_format) {
    var dataRows = _.clone(data);
    var headerRow = dataRows.shift();
    console.log('parent column', parent_column);
    if(secondary_column === '[None]') {
        return barchartSingleObject(headerRow, dataRows, primary_column, parent_column, order_column, chart_title, x_axis_label, y_axis_label, number_format);
    } else {
        return barchartDoubleObject(headerRow, dataRows, primary_column, secondary_column, parent_column, order_column, chart_title, x_axis_label, y_axis_label, number_format);
    }
}

function barchartSingleObject(headerRow, dataRows, category_column, parent_column, order_column, chart_title, x_axis_label, y_axis_label, number_format) {
    var indices = getIndices(headerRow, category_column, null, parent_column, order_column);

    var categories = uniqueCategories(dataRows, indices['category'], indices['order']);
    var values = _.map(categories, function(category) {
        return valueForCategory(dataRows, indices['category'], indices['value'], indices['parent'], category);
    });



    var chart = {
        'type':'bar',
        'title':{'text':chart_title},
        'parent_child': indices['parent'] !== null,
        'xAxis':{'title':{'text':x_axis_label}, 'categories':categories},
        'yAxis':{'title':{'text':y_axis_label}},
        'series': [{'name':category_column, 'data': values}],
        'number_format':number_format
    };
    console.log(chart);
    return chart;
}

function barchartDoubleObject(headerRow, dataRows, category1, category2, parent_column, order_column, chart_title, x_axis_label, y_axis_label, number_format) {
    var indices = getIndices(headerRow, category1, category2, parent_column, order_column);

    var categories = uniqueCategories(dataRows, indices['category'], indices['order'])

    var series = uniqueDataInColumnMaintainOrder(dataRows, indices['secondary']);

    var seriesData = [];
    for(var s in series) {
        var seriesRows = _.filter(dataRows, function(row) { return row[indices['secondary']] === series[s];});
        var values = [];
        for(var c in categories) {
            values.push(valueForCategory(seriesRows, indices['category'], indices['value'], categories[c]));
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

    var indices = getIndices(headerRow, category_column, panel_column, null, null);
    var categories = uniqueCategories(dataRows, indices['category'], indices['order']);
    var panelValues = uniqueDataInColumnMaintainOrder(dataRows, indices['secondary']);

    var panels = [];
    for(var p in panelValues) {
        var panelRows = _.filter(dataRows, function(row) { return row[indices['secondary']] === panelValues[p];});
        var values = [];
        for(var c in categories) {
            values.push(valueForCategory(panelRows, indices['category'], indices['value'], categories[c]));
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


function linechartObject(data, categories_column, series_column, chart_title, x_axis_label, y_axis_label, number_format) {
    var dataRows = _.clone(data);
    var headerRow = dataRows.shift();

    var indices = getIndices(headerRow, categories_column, series_column, null, null);
    var categories = uniqueDataInColumnMaintainOrder(dataRows, indices['category']);
    var seriesNames = uniqueDataInColumnMaintainOrder(dataRows, indices['secondary']);

    var chartSeries = [];
    for(s in seriesNames) {
        var seriesName = seriesNames[s];
        var values = [];
        for(var c in categories) {
            var category = categories[c];
            values.push(valueForCategoryAndSeries(dataRows, indices['category'], category, indices['secondary'], seriesName, indices['value']));
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
    var indices = getIndices(headerRow, panel_column, x_axis_column, null, null);

    var panelNames = uniqueDataInColumn(dataRows, indices['category']);
    var xAxisNames = uniqueDataInColumn(dataRows, indices['secondary']);

    var panelCharts = [];
    for(var p in panelNames) {
        var panelName = panelNames[p];
        var values = [];
        for(var c in xAxisNames) {
            var category = xAxisNames[c];
            values.push(valueForCategoryAndSeries(dataRows, indices['secondary'], category, indices['category'], panelName, indices['value']));
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


function componentChartObject(data, grouping_column, series_column, chart_title, x_axis_label, y_axis_label, number_format) {


    var dataRows = _.clone(data);
    var headerRow = dataRows.shift();
    var indices = getIndices(headerRow, grouping_column, series_column, null, null);

    var groups = uniqueDataInColumnMaintainOrder(dataRows, indices['category']);
    var seriesNames = uniqueDataInColumnMaintainOrder(dataRows, indices['secondary']).reverse();

    var chartSeries = [];
    for(var s in seriesNames) {
        var seriesName = seriesNames[s];
        var values = [];
        for(var g in groups) {
            var group = groups[g];
            values.push(valueForCategoryAndSeries(dataRows, indices['category'], group, indices['secondary'], seriesName, indices['value']));
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


function uniqueCategories(dataRows, categoryIndex, orderIndex) {

    if(orderIndex) {
        return uniqueDataInColumnOrdered(dataRows, categoryIndex, orderIndex);
    } else {
        return uniqueDataInColumnMaintainOrder(dataRows, categoryIndex);
    }
}

function valueForCategory(dataRows, categoryIndex, valueIndex, parentIndex, categoryValue) {

    for(var r in dataRows) {
        if(dataRows[r][categoryIndex] === categoryValue) {
            console.log('parentIndex', parentIndex);
            if(parentIndex) {
                var parentValue = dataRows[r][parentIndex];
                var relationships = {is_parent:parentValue === categoryValue,
                    is_child: parentValue !== categoryValue, parent:parentValue};
                if(relationships['is_parent']){
                    return {
                        y: parseFloat(dataRows[r][valueIndex]),
                        relationships: relationships,
                        category: dataRows[r][categoryIndex],
                        color: defaultParentColor
                    };

                } else {
                    return {
                        y: parseFloat(dataRows[r][valueIndex]),
                        relationships: relationships,
                        category: dataRows[r][categoryIndex],
                        color: defaultChildColor
                    };
                }
            } else {
                return {y: parseFloat(dataRows[r][valueIndex]), category: dataRows[r][categoryIndex]};
            }
        }
    }
    return {y: 0, category: categoryValue};
}

function valueForCategoryAndSeries(dataRows, categoryIndex, categoryValue, seriesIndex, seriesValue, valueIndex) {
    for(var r in dataRows) {
        if((dataRows[r][categoryIndex] === categoryValue) && (dataRows[r][seriesIndex] === seriesValue)) {
            return parseFloat(dataRows[r][valueIndex]);
        }
    }
    return 0;
}

function sortChartSeries(serieses) {
    // check if these series are numerically sortable
    for(var s in serieses) {
        var sort_value = toNumberSortValue(serieses[s].name);
        if(isNaN(sort_value)){
            // if not numeric return original series
            return serieses;
        }
    }
    // if series sortable assign a sort value
    for(var s in serieses) {
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

function getIndices(headerRow, category_column, secondary_column, parent_column, order_column) {
    var headersLower = _.map(headerRow, function(item) { return item.toLowerCase();});

    var category = category_column === null ? null: headersLower.indexOf(category_column.toLowerCase());
    var order = order_column  === null ? category : headersLower.indexOf(order_column.toLowerCase());
    var parent = parent_column  === null ? null: headersLower.indexOf(parent_column.toLowerCase());
    var secondary = secondary_column  === null ? null: headersLower.indexOf(secondary_column.toLowerCase());

    return {
        'category': category >= 0 ? category : null,
        'order': order >= 0 ? order : null,
        'secondary': secondary >= 0 ? secondary : null,
        'value': headersLower.indexOf('value'),
        'parent': parent >= 0 ? parent : null
    };
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

    var sortIndex = findSortColumnForSimple(columnIndex, headerRow, data_column_indices);

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

function findGroupedData(group_values, dataRows, group_column_index, columnIndex, hasParentChild, parentIndex, sortIndex, data_column_indices) {
    // generate series from rows

    // begin
    var group_series = _.map(group_values, function (group) {

        // get rows
        var group_data = _.filter(dataRows, function (dataRow) {
            return dataRow[group_column_index] === group;
        });
        var group_data_items = _.map(group_data, function (item) {
            var relationships = {
                'is_parent': false,
                'is_child': false,
                'parent': item[columnIndex]
            };
            if (hasParentChild) {
                var parent = item[parentIndex];
                var child = item[columnIndex];
                relationships = {
                    'is_parent': parent === child,
                    'is_child': parent !== child,
                    'parent': parent
                }
            }
            return {
                'category': item[columnIndex],
                'relationships': relationships,
                'order': item[sortIndex],
                'values': _.map(data_column_indices, function (i) {
                    return item[i]
                })
            }
        });
        return {'group': group, 'data': group_data_items};
    });

    // sort by order
    group_series = _.map(group_series, function (group) {
        group.data = _.sortBy(group.data, function(item) { return item['order'];});
        return group;
    });

    return group_series;
}

function transformGroupedDataToRows(original_obj) {
    var rows = _.map(original_obj.groups[0].data, function (item) {
        return item.category;
    });
    var data = _.map(rows, function (row) {
        var row_item = null;
        var values = _.flatten(_.map(original_obj.groups, function (group) {
            row_item = _.findWhere(group.data, {'category': row});
            return row_item.values;
        }));
        return {
            'category': row, 'relationships': row_item['relationships'], 'parent': row_item['parent'],
            'order': row_item['order'], 'values': values
        };
    });
    data = _.sortBy(data, function (item) {
        return item['order'];
    });
    return data;
}

function groupedTable(data, title, subtitle, footer,  category_column, parent_column, group_column, data_columns, order_column, column_captions) {
    var dataRows = _.clone(data);
    var headerRow = dataRows.shift();
    var columnIndex = headerRow.indexOf(category_column);
    var data_column_indices = _.map(data_columns, function(data_column) { return headerRow.indexOf(data_column); });
    var group_column_index = headerRow.indexOf(group_column);
    var category_column_index = headerRow.indexOf(category_column);

    var categories = uniqueDataInColumnMaintainOrder(dataRows, category_column_index);
    var group_category_labels = uniqueDataInColumnMaintainOrder(dataRows, group_column_index);
    var sortIndex = findSortColumnForGroups(order_column, categories, category_column_index, headerRow, dataRows);

    var parentIndex = columnIndex;
    var hasParentChild = false;
    if(parent_column && parent_column !== '[None]') {
        parentIndex = headerRow.indexOf(parent_column);
        hasParentChild = true;
    }

    var group_series = findGroupedData(group_category_labels, dataRows, group_column_index, columnIndex, hasParentChild, parentIndex, sortIndex, data_column_indices);

    var original_obj = {
        'type':'grouped',
        'category': category_column,
        'title':{'text':'Grouped Table'},
        'header': title,
        'columns':column_captions,
        'groups': group_series};

    var group_columns = _.map(original_obj.groups, function (group) {
        return group.group;
    });

    var data_by_rows = transformGroupedDataToRows(original_obj, data);

    return {
        'group_columns': group_columns,
        'type':'grouped',
        'category': category_column,
        'columns': column_captions,
        'data': data_by_rows,
        'header':title,
        'subtitle':subtitle,
        'footer':footer,
        'groups': group_series,
        'parent_child': hasParentChild
    };
}

function findSortColumnForSimple(order_column, headerRow, dataRows) {

    if (order_column !== '[None]') {
        return headerRow.indexOf(order_column);
    } else {
        headerRow.push('Sort Column');
        for(var row in dataRows) {
            dataRows[row].push(row);
        }
        return headerRow.length - 1;
    }
}

function findSortColumnForGroups(order_column, categories, category_index, headerRow, dataRows) {
    if (order_column !== '[None]') {
        return headerRow.indexOf(order_column);
    } else {
        headerRow.push('Sort Column');
        _.forEach(dataRows, function (row) {
            var group = row[category_index];
            row.push(categories.indexOf(group));
        });
        return headerRow.length - 1;
    }
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
