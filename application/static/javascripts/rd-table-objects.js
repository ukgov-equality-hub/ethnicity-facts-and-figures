/**
 * Created by Tom.Ridd on 25/07/2017.
 */


function buildTableObject(data, title, subtitle, footer, row_column, parent_column, group_column, order_column, data_columns, column_captions, first_column_caption, group_order_column) {
    var table = null;
    if(!group_column || group_column === '[None]') {
        table = simpleTable(data, title, subtitle, footer, row_column, parent_column, data_columns, order_column, column_captions, first_column_caption);
    } else {
        table = groupedTable(data, title, subtitle, footer, row_column, parent_column, group_column, data_columns, order_column, column_captions, first_column_caption, group_order_column);
    }
    return preProcessTableObject(table);
}

function simpleTable(data, title, subtitle, footer, category_column, parent_column, data_columns, order_column, column_captions, first_column_caption) {
    var dataRows = _.clone(data);

    var headerRow = dataRows.shift();

    var columnIndex = headerRow.indexOf(category_column);
    var data_column_indices = _.map(data_columns, function(data_column) { return headerRow.indexOf(data_column); });

    var parentIndex = columnIndex;
    var hasParentChild = false;
    if(parent_column && parent_column !== '[None]') {
        parentIndex = headerRow.indexOf(parent_column);
        hasParentChild = true;
    }

    if(order_column && order_column !== '[None]') {
        var sortIndex = headerRow.indexOf(order_column);
    }

    var tableData = _.map(dataRows, function(item, index) {
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

        var values = _.map(data_column_indices, function (i) { return item[i]; });
        var sortValues = _.map(values, function (value) { return numVal(value); });

        if(sortIndex) {
            return {
                'category': item[columnIndex],
                'relationships': relationships,
                'order': item[sortIndex],
                'values': values,
                'sort_values': sortValues
            };
        } else {
            return {
                'category': item[columnIndex],
                'relationships': relationships,
                'order': index,
                'values': values,
                'sort_values': sortValues
            };
        }
    });


    tableData = _.sortBy(tableData, function(item) { return item['order'];});

    var first_column = first_column_caption == null ? category_column : first_column_caption;

    return {
        'type':'simple',
        'parent_child': hasParentChild,
        'header': title,
        'subtitle' :subtitle,
        'footer' :footer,
        'category':category_column,
        'columns': column_captions,
        'data': tableData,
        'category_caption': first_column
    };
}

function groupedTable(data, title, subtitle, footer,  category_column, parent_column, group_column, data_columns, order_column, column_captions, first_column_caption, group_order_column) {
    const DEFAULT_SORT = -2;

    var dataRows = _.clone(data);
    var headerRow = dataRows.shift();

    var columnIndex = headerRow.indexOf(category_column);
    var data_column_indices = _.map(data_columns, function(data_column) { return headerRow.indexOf(data_column); });

    var group_column_index = headerRow.indexOf(group_column);
    var group_values = uniqueDataInColumnMaintainOrder(dataRows, group_column_index);

    if(group_order_column && group_order_column !== '[None]') {
        var group_order_index = headerRow.indexOf(group_order_column);
        var order_values = _.map(group_values, function(item) {
           var index = _.findIndex(dataRows, function(row) {
               return row[group_column_index] === item;
           });
           return dataRows[index][group_order_index];
        });

        group_values = _.map(_.sortBy(_.zip(group_values, order_values), function(pair) { return pair[1]; }), function(pair) { return pair[0]; });
    }

    var sortIndex = DEFAULT_SORT;
    if (order_column === null) {
        sortIndex = columnIndex;
    } else if(order_column !== '[None]') {
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
        var group_data_items = _.map(group_data, function(item, index) {
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
            var sort_val = sortIndex === DEFAULT_SORT ? index : item[sortIndex];
            var values = _.map(data_column_indices, function(i) { return item[i]});
            var sortValues = _.map(values, function(value) { return numVal(value); });
            return {'category':item[columnIndex], 'relationships':relationships, 'order':sort_val, 'values': values, 'sort_values': sortValues}
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

    var dataVals = [];
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

        var sortValues = [];
        _.forEach(values, function(val) { sortValues.push(numVal(val)); });

        dataVals.push({'category': row, 'relationships': relationships, 'parent': parentValue, 'order':sortValue, 'values':values, 'sort_values':sortValues});
    });

    dataVals = _.sortBy(dataVals, function(item) { return item['order'];});
    group_series = _.map(group_series, function (group) {
        group.data = _.sortBy(group.data, function(item) { return item['order'];});
        return group;
    });

    var first_column = first_column_caption == null ? category_column : first_column_caption;

    return {
        'group_columns': group_columns,
        'type':'grouped',
        'category': category_column,
        'group_column': group_column,
        'columns': column_captions,
        'data': dataVals,
        'header':title,
        'subtitle':subtitle,
        'footer':footer,
        'groups': group_series,
        'parent_child': hasParentChild,
        'category_caption': first_column
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
        row.sort_values = _.flatten(_.map(tableObject.groups, function(group) {
            return group.data[rowNo].sort_values;
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
            });
        });
    });
}

function numVal(value, defaultVal) {
    var num = Number(value);
    return num ? num : 0;
}

// If we're running under Node - required for testing
if(typeof exports !== 'undefined') {
    var _ = require('../vendor/underscore-min');
    var dataTools = require('./rd-data-tools');
    var uniqueDataInColumnMaintainOrder = dataTools.uniqueDataInColumnMaintainOrder;
    var seriesDecimalPlaces = dataTools.seriesDecimalPlaces;
    var seriesCouldBeYear = dataTools.seriesCouldBeYear;
    var formatNumberWithDecimalPlaces = dataTools.formatNumberWithDecimalPlaces;

    exports.buildTableObject = buildTableObject;
    exports.simpleTable = simpleTable;
    exports.groupedTable = groupedTable;
}