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

function uniqueCategories(dataRows, categoryIndex, orderIndex) {

    if(orderIndex) {
        return uniqueDataInColumnOrdered(dataRows, categoryIndex, orderIndex);
    } else {
        return uniqueDataInColumn(dataRows, categoryIndex);
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
    categories = uniqueDataInColumn(dataRows, categoryIndex);

    seriesIndex = headerRow.indexOf(series_column);
    seriesNames = uniqueDataInColumn(dataRows, seriesIndex);

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
    groups = uniqueDataInColumn(dataRows, groupingIndex);

    seriesIndex = headerRow.indexOf(series_column);
    seriesNames = uniqueDataInColumn(dataRows, seriesIndex);

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
    if(group_column === '[None]') {
        return simpleTable(data, title, subtitle, footer, row_column, parent_column, data_columns, order_column, column_captions);
    } else {
        return groupedTable(data, title, subtitle, footer, row_column, parent_column, group_column, data_columns, order_column, column_captions);
    }
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
        return {'category':item[columnIndex], 'parent':item[parentIndex], 'order': item[sortIndex], 'values':_.map(data_column_indices, function(i) { return item[i]})};
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
    var group_values = uniqueDataInColumn(dataRows, group_column_index);

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

    var group_series = _.map(group_values, function(group) {
        var group_data = _.filter(dataRows, function(item) { return item[group_column_index] === group;});
        var group_data_items = _.map(group_data, function(item) {
            return {'category':item[columnIndex], 'parent':item[parentIndex], 'order':item[sortIndex], 'values':_.map(data_column_indices, function(i) { return item[i]})}
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
        _.forEach(original_obj.groups, function(group) {
            row_item = _.findWhere(group.data, {'category':row});
            sortValue = row_item['order'];
            parentValue = row_item['parent'];
            _.forEach(row_item.values, function(cell) {
                values.push(cell);
            })
        });
        data.push({'category': row, 'parent': parentValue, 'order':sortValue, 'values':values});
    });
    data = _.sortBy(data, function(item) { return item['order'];});


    return {
        'group_columns': group_columns,
        'type':'grouped',
        'category': category_column,
        'columns': column_captions,
        'data': data,
        'header':title,
        'subtitle':subtitle,
        'footer':footer,
        'groups': group_series
    };
}