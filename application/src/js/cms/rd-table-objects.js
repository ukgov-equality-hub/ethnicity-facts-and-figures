/**
 * Created by Tom.Ridd on 25/05/2017.

rd-table-objects builds a tableObject with input and settings provided in the Table Builder interface

- build tableObjects for all supported table types (simple, grouped)
- support tables with multiple value columns
- support parent-child relationships in the tables

building the table objects it also does data transforms required by stories from user research

specifically...
- support sorting both, one of, or neither of rows and columns
- inserting parent data rows where none exist

 */

var NONE_VALUE = '[None]'

// ---------------------------------------------------------------------------
// PUBLIC
// ---------------------------------------------------------------------------

function buildTableObject (data, title, subtitle, footer, row_column, parent_column, group_column, order_column, data_columns, column_captions, index_column_caption, group_order_column) {
  var table = null
  if (!group_column || group_column === NONE_VALUE) {
    table = simpleTable(data, title, subtitle, footer, row_column, parent_column, data_columns, order_column, column_captions, index_column_caption)
  } else {
    table = groupedTable(data, title, subtitle, footer, row_column, parent_column, group_column, data_columns, order_column, column_captions, index_column_caption, group_order_column)
  }
  return preProcessTableObject(table)
}

// ---------------------------------------------------------------------------
// PREPROCESSING
// ---------------------------------------------------------------------------

function preProcessTableObject (tableObject) {
  if (tableObject.type === 'simple') {
    preProcessSimpleTableObject(tableObject)
  } else if (tableObject.type === 'grouped') {
    preProcessGroupedTableObject(tableObject)
  }
  return tableObject
}

// ---------------------------------------------------------------------------
// SIMPLE TABLE
// ---------------------------------------------------------------------------

function simpleTable (data, title, subtitle, footer, category_column, parent_column, data_columns, order_column, column_captions, index_column_caption) {
  var dataRows = _.clone(data)
  var headerRow = dataRows.shift()
  var lowHeaders = _.map(headerRow, function (m) { return m.trim().toLowerCase() })

  var columnIndex = index_of_column_named(lowHeaders, category_column)
  var data_column_indices = _.map(data_columns, function (data_column) { return index_of_column_named(lowHeaders, data_column) })

  var parentIndex = columnIndex
  var hasParentChild = false
  if (parent_column && parent_column !== NONE_VALUE) {
    parentIndex = index_of_column_named(lowHeaders, parent_column)
    hasParentChild = true
  }

  if (order_column && order_column !== NONE_VALUE) {
    var sortIndex = index_of_column_named(lowHeaders, order_column)
  }

  var tableData = _.map(dataRows, function (item, index) {
    var relationships = {
      'is_parent': false,
      'is_child': false,
      'parent': item[columnIndex]
    }
    if (hasParentChild) {
      var parent = item[parentIndex]
      var child = item[columnIndex]
      relationships = {
        'is_parent': parent === child,
        'is_child': parent !== child,
        'parent': parent
      }
    }

    var values = _.map(data_column_indices, function (i) { return item[i] })
    var sortValues = _.map(values, function (value) { return numVal(value) })

    if (sortIndex) {
      return {
        'category': item[columnIndex],
        'relationships': relationships,
        'order': item[sortIndex],
        'values': values,
        'sort_values': sortValues
      }
    } else {
      return {
        'category': item[columnIndex],
        'relationships': relationships,
        'order': index,
        'values': values,
        'sort_values': sortValues
      }
    }
  })

  tableData = _.sortBy(tableData, function (item) { return item['order'] })

  if (hasParentChild) {
    tableData = adjustSimpleTableDataForParents(tableData)
  }

  var index_column = index_column_caption == null ? category_column : index_column_caption

  return {
    'type': 'simple',
    'parent_child': hasParentChild,
    'header': title,
    'subtitle': subtitle,
    'footer': footer,
    'category': category_column,
    'columns': column_captions,
    'data': tableData,
    'category_caption': index_column
  }
}

// ---------------------------------
// PREPROCESSING
// ---------------------------------

function preProcessSimpleTableObject (tableObject) {
  var columnDps = columnDecimalPlaces(tableObject)
  var couldBeYear = columnCouldBeAYear(tableObject)

  tableObject.data = _.map(tableObject.data, function (item) {
    item.values = _.map(_.zip(item.values, columnDps, couldBeYear), function (cellTuple) {
      if (cellTuple[2] === false) {
        return formatNumberWithDecimalPlaces(cellTuple[0], cellTuple[1])
      } else {
        return cellTuple[0]
      }
    })
    return item
  })
}

function columnDecimalPlaces (tableObject) {
  var dps = []
  // iterate through columns
  for (var i in tableObject.data[0].values) {
    // gather all the data for that column
    var series = _.map(tableObject.data, function (item) {
      return item.values[i]
    })
    dps.push(seriesDecimalPlaces(series))
  }
  return dps
}

function columnCouldBeAYear (tableObject) {
  var years = []

  // iterate through columns
  for (var i in tableObject.data[0].values) {
    // gather all the data for that column
    var series = _.map(tableObject.data, function (item) { return item.values[i] })
    years.push(seriesCouldBeYear(series))
  }
  return years
}

// ---------------------------------
// PARENTS
// ---------------------------------

function adjustSimpleTableDataForParents (tableData) {
  var fullData = addMissingSimpleTableParentItems(tableData)
  return reorderSimpleTableDataForParentChild(fullData)
}

function addMissingSimpleTableParentItems (tableData) {
  var parents = _.uniq(_.map(tableData, function (item) {
    return item['relationships']['parent']
  }))

  var current_categories = _.map(tableData, function (item) {
    return item['category']
  })
  var missing_parents = _.filter(parents, function (parent) {
    return !_.contains(current_categories, parent)
  })

  var newData = _.clone(tableData)
  var example = tableData[0]
  _.forEach(missing_parents, function (missing_parent) {
    // find order for the new parent by finding the minimum value for it's children and subtracting 1
    var parent_items = _.filter(tableData, function (item) { return item.relationships.parent === missing_parent })
    var min_order = _.min(_.map(parent_items, function (item) { return item.order })) - 1

    var new_data_point = {
      'category': missing_parent,
      'order': min_order,
      'relationships': {'is_child': false, 'is_parent': true, 'parent': missing_parent},
      'sort_values': _.map(example['sort_values'], function (value) {
        return 0
      }),
      'values': _.map(example.values, function (value) {
        return ''
      })
    }
    newData.push(new_data_point)
  })

  return newData
}

function reorderSimpleTableDataForParentChild (tableData) {
  var item_dict = _.object(_.map(tableData, function (item) { return [item.category, item] }))
  var parents = _.uniq(_.map(tableData, function (item) { return item['relationships']['parent'] }))

  var ordered_data = []
  _.forEach(parents, function (parent) {
    ordered_data.push(item_dict[parent])
    var parent_children = _.filter(tableData, function (item) { return item['category'] !== parent && item['relationships']['parent'] === parent })
    ordered_data = ordered_data.concat(parent_children)
  })
  return ordered_data
}

// ---------------------------------------------------------------------------
// GROUPED TABLE
// ---------------------------------------------------------------------------

function groupedTable (data, title, subtitle, footer, category_column, parent_column, group_column, data_columns, order_column, column_captions, index_column_caption, group_order_column) {
  var DEFAULT_SORT = -2
  var data_by_row = _.clone(data)
  var headerRow = data_by_row.shift()
  var lowHeaders = _.map(headerRow, function (m) { return m.trim().toLowerCase() })

  // ------------------- FIND INDICES FOR THE COLUMNS --------------------------

  var columnIndex = index_of_column_named(lowHeaders, category_column)
  var data_column_indices = _.map(data_columns, function (data_column) { return index_of_column_named(lowHeaders, data_column) })

  var group_column_index = index_of_column_named(lowHeaders, group_column)

  var sortIndex = DEFAULT_SORT
  if (order_column === null) {
    sortIndex = columnIndex
  } else if (order_column !== NONE_VALUE) {
    sortIndex = index_of_column_named(lowHeaders, order_column)
  }

  var parentIndex = columnIndex
  var hasParentChild = false
  if (parent_column && parent_column !== NONE_VALUE) {
    parentIndex = index_of_column_named(lowHeaders, parent_column)
    hasParentChild = true
  }

  // ----------------------- CONVERT TO DATA ITEM OBJECTS ----------------------
  var data_by_group = getDataByGroup(data_by_row, group_column_index, group_order_column, headerRow)
  var data_items_by_group = buildDataObjectsByGroup(data_by_group, data_by_row, group_column_index, columnIndex, hasParentChild, parentIndex, sortIndex, DEFAULT_SORT, data_column_indices)

  // ----------------------- ADJUSTMENTS FOR PARENT CHILD ----------------------
  data_items_by_group = adjustGroupedTableDataForParents(data_items_by_group)

  // --------------------- DATA VALUES (Values by row) -------------------------

  var partial_table = templateGroupTable(category_column, title, column_captions, data_items_by_group)

  var group_columns = [''].concat(_.map(partial_table.groups, function (group) { return group.group }))

  var row_categories = _.map(partial_table.groups[0].data, function (item) { return item.category })
  var table_data = _.map(row_categories, function (category) { return dataItemWithCategory(partial_table, category) })
  table_data = _.sortBy(table_data, function (item) { return item['order'] })

  data_items_by_group = _.map(data_items_by_group, function (group) {
    group.data = _.sortBy(group.data, function (item) { return item['order'] })
    return group
  })

  // --------------------- COMPLETE THE TABLE OBJECT --------------------------
  var index_column = index_column_caption == null ? category_column : index_column_caption

  return {
    'group_columns': group_columns,
    'type': 'grouped',
    'category': category_column,
    'group_column': group_column,
    'columns': column_captions,
    'data': table_data,
    'header': title,
    'subtitle': subtitle,
    'footer': footer,
    'groups': data_items_by_group,
    'parent_child': hasParentChild,
    'category_caption': index_column
  }
}

// ---------------------------------
// PREPROCESSING
// ---------------------------------

function preProcessGroupedTableObject (tableObject) {
  var columnDps = groupedTableDecimalPlaces(tableObject)
  var couldBeYear = groupedTableCouldBeAYear(tableObject)

  tableObject.groups = _.map(tableObject.groups, function (group) {
    group.data = _.map(group.data, function (item) {
      item.values = _.map(_.zip(item.values, columnDps, couldBeYear), function (cellTuple) {
        if (cellTuple[2] === false) {
          return formatNumberWithDecimalPlaces(cellTuple[0], cellTuple[1])
        } else {
          return cellTuple[0]
        }
      })
      return item
    })
    return group
  })

  // update tableObject data
  tableObject.data = []
  // for each row
  for (var rowNo in tableObject.groups[0].data) {
    // grab a prototype cell
    var row = _.clone(tableObject.groups[0].data[rowNo])
    // fill it with all contents across the groups
    row.values = _.flatten(_.map(tableObject.groups, function (group) {
      return group.data[rowNo].values
    }))
    row.sort_values = _.flatten(_.map(tableObject.groups, function (group) {
      return group.data[rowNo].sort_values
    }))
    // add to the data
    tableObject.data.push(row)
  }

  var items = _.sortBy(tableObject.groups[0].data, function (item) { return item.order })
  var rows = _.map(items, function (item) { return item.category })
  _.forEach(rows, function (row) {
    var row_html = '<tr><th>' + row + '</th>'
    _.forEach(tableObject.groups, function (group) {
      var row_item = _.findWhere(group.data, {'category': row})
      _.forEach(_.zip(row_item.values, columnDps, couldBeYear), function (cellValues) {
        if (cellValues[2]) {
          row_html = row_html + '<td>' + cellValues[0] + '</td>'
        } else {
          row_html = row_html + '<td>' + formatNumberWithDecimalPlaces(cellValues[0], cellValues[1]) + '</td>'
        }
      })
    })
  })
}

function groupedTableDecimalPlaces (tableObject) {
  var dps = []
  // iterate through columns
  for (var c in tableObject.groups[0].data[0].values) {
    // gather all data for a column
    var series = _.flatten(
      _.map(tableObject.groups, function (group) {
        return _.map(group.data, function (item) {
          return item.values[c]
        })
      }))
    dps.push(seriesDecimalPlaces(series))
  }
  return dps
}

function groupedTableCouldBeAYear (tableObject) {
  var years = []
  // iterate through columns
  for (var c in tableObject.groups[0].data[0].values) {
    // gather all data for a column
    var series = _.flatten(
      _.map(tableObject.groups, function (group) {
        return _.map(group.data, function (item) {
          return item.values[c]
        })
      }))
    years.push(seriesCouldBeYear(series))
  }
  return years
}

// ---------------------------------
// DATA BUILDING
// ---------------------------------

function buildDataObjectsByGroup (group_values, dataRows, group_column_index, columnIndex, hasParentChild, parentIndex, sortIndex, DEFAULT_SORT, data_column_indices) {
  return _.map(group_values, function (group) {
    var group_data = _.filter(dataRows, function (item) {
      return item[group_column_index] === group
    })
    var group_data_items = _.map(group_data, function (item, index) {
      var relationships = {
        'is_parent': false,
        'is_child': false,
        'parent': item[columnIndex]
      }
      if (hasParentChild) {
        var parent = item[parentIndex]
        var child = item[columnIndex]
        relationships = {
          'is_parent': parent === child,
          'is_child': parent !== child,
          'parent': parent
        }
      }
      var sort_val = sortIndex === DEFAULT_SORT ? index : item[sortIndex]
      var values = _.map(data_column_indices, function (i) {
        return item[i]
      })
      var sortValues = _.map(values, function (value) {
        return numVal(value)
      })
      return {
        'category': item[columnIndex],
        'relationships': relationships,
        'order': sort_val,
        'values': values,
        'sort_values': sortValues
      }
    })
    return {'group': group, 'data': group_data_items}
  })
}

function getDataByGroup (data_by_row, group_column_index, group_order_column, headerRow) {
  var group_values = uniqueDataInColumnMaintainOrder(data_by_row, group_column_index)
  if (group_order_column && group_order_column !== NONE_VALUE) {
    var group_order_index = headerRow.indexOf(group_order_column)
    var order_values = _.map(group_values, function (item) {
      var index = _.findIndex(data_by_row, function (row) {
        return row[group_column_index] === item
      })
      return data_by_row[index][group_order_index]
    })
    group_values = _.map(_.sortBy(_.zip(group_values, order_values), function (pair) {
      return pair[1]
    }), function (pair) {
      return pair[0]
    })
  }
  return group_values
}

function dataItemWithCategory (partial_table_object, category) {
  var values = []
  var sortValue = ''
  var parentValue = ''
  var relationships = {}

  _.forEach(partial_table_object.groups, function (group) {
    var category_item = _.findWhere(group.data, {'category': category})
    sortValue = category_item['order']
    parentValue = category_item['parent']
    relationships = category_item['relationships']
    _.forEach(category_item.values, function (cell) {
      values.push(cell)
    })
  })

  var sortValues = _.map(values, function (val) { return numVal(val) })

  return {
    'category': category,
    'relationships': relationships,
    'parent': parentValue,
    'order': sortValue,
    'values': values,
    'sort_values': sortValues
  }
}

function templateGroupTable (category_column, title, column_captions, group_series) {
  return {
    'type': 'grouped',
    'category': category_column,
    'title': {'text': 'Grouped Table'},
    'header': title,
    'columns': column_captions,
    'groups': group_series
  }
}

// ---------------------------------
// PARENT-CHILD
// ---------------------------------

function adjustGroupedTableDataForParents (tableData) {
  var fullData = addMissingGroupedTableParentItems(tableData)
  return reorderGroupedTableDataForParentChild(fullData)
}

function addMissingGroupedTableParentItems (tableData) {
  // Find all existing parents
  var parents = _.uniq(
    _.flatten(
      _.map(tableData, function (column) {
        return _.map(column.data, function (cell) {
          return cell.relationships.parent
        })
      }
      )
    ))

  // Find all existing rows
  var current_categories = _.uniq(
    _.flatten(
      _.map(tableData, function (column) {
        return _.map(column.data, function (cell) {
          return cell.category
        })
      }
      )
    ))

  // Find rows that need to be added
  var missing_parents = _.filter(parents, function (parent) {
    return !_.contains(current_categories, parent)
  })

  // Build the new data items
  var newData = _.clone(tableData)
  var example = tableData[0].data[0]
  _.forEach(missing_parents, function (missing_parent) {
    // find order for the new parent by finding the minimum value for it's children and subtracting 1
    var parent_items = _.filter(_.flatten(_.map(tableData, function (column) { return column.data })), function (item) { return item.relationships.parent === missing_parent })
    var min_order = _.min(_.map(parent_items, function (item) { return item.order })) - 1

    // build the new data points
    _.forEach(newData, function (group) {
      var new_data_point = {
        'category': missing_parent,
        'order': min_order,
        'relationships': {'is_child': false, 'is_parent': true, 'parent': missing_parent},
        'sort_values': _.map(example['sort_values'], function (value) {
          return 0
        }),
        'values': _.map(example.values, function (value) {
          return ''
        })
      }
      group.data.push(new_data_point)
    })
  })

  return newData
}

function reorderGroupedTableDataForParentChild (tableData) {
  var item_dict = _.object(_.map(tableData, function (item) { return [item.category, item] }))
  var parents = _.uniq(
    _.flatten(
      _.map(tableData, function (column) {
        return _.map(column.data, function (cell) {
          return cell.relationships.parent
        })
      }
      )
    ))

  _.forEach(tableData, function (group) {
    var item_dict = _.object(_.map(group.data, function (item) { return [item.category, item] }))
    var ordered_data = []
    _.forEach(parents, function (parent) {
      ordered_data.push(item_dict[parent])
      var parent_children = _.filter(group.data, function (item) { return item['category'] !== parent && item['relationships']['parent'] === parent })
      ordered_data = ordered_data.concat(parent_children)
    })
    group.data = ordered_data
  })

  return tableData
}

// ---------------------------------------------------------------------------
// COMMON FUNCTIONS
// ---------------------------------------------------------------------------

function preProcessGroupedTableObject (tableObject) {
  var columnDps = groupedTableDecimalPlaces(tableObject)
  var couldBeYear = groupedTableCouldBeAYear(tableObject)

  tableObject.groups = _.map(tableObject.groups, function (group) {
    group.data = _.map(group.data, function (item) {
      item.values = _.map(_.zip(item.values, columnDps, couldBeYear), function (cellTuple) {
        if (cellTuple[2] === false) {
          return formatNumberWithDecimalPlaces(cellTuple[0], cellTuple[1])
        } else {
          return cellTuple[0]
        }
      })
      return item
    })
    return group
  })

  // update tableObject data
  tableObject.data = []
  // for each row
  for (var rowNo in tableObject.groups[0].data) {
    // grab a prototype cell
    var row = _.clone(tableObject.groups[0].data[rowNo])
    // fill it with all contents across the groups
    row.values = _.flatten(_.map(tableObject.groups, function (group) {
      return group.data[rowNo].values
    }))
    row.sort_values = _.flatten(_.map(tableObject.groups, function (group) {
      return group.data[rowNo].sort_values
    }))
    // add to the data
    tableObject.data.push(row)
  }

  var items = _.sortBy(tableObject.groups[0].data, function (item) { return item.order })
  var rows = _.map(items, function (item) { return item.category })
  _.forEach(rows, function (row) {
    var row_html = '<tr><th>' + row + '</th>'
    _.forEach(tableObject.groups, function (group) {
      var row_item = _.findWhere(group.data, {'category': row})
      _.forEach(_.zip(row_item.values, columnDps, couldBeYear), function (cellValues) {
        if (cellValues[2]) {
          row_html = row_html + '<td>' + cellValues[0] + '</td>'
        } else {
          row_html = row_html + '<td>' + formatNumberWithDecimalPlaces(cellValues[0], cellValues[1]) + '</td>'
        }
      })
    })
  })
}

function numVal (value, defaultVal) {
  var string = String(value).replace(/\,/g, '')
  var num = Number(string)
  return num || value
}

// function validateAndAdjust(data, rowIndex, columnIndex, sortIndex, parentIndex, valueIndex) {
//     var missingData = [];
//     var doubleData = [];

//     var rowItems = _.uniq(_.map(data, function(item) { return item[rowIndex]; }));
//     var columnItems = _.uniq(_.map(data, function(item) { return item[columnIndex]; }));

//     var mapOfPairs = _.object(_.map(rowItems, function(item) {
//        return [item, _.map(_.filter(data, function(row) { return row[rowIndex] === item}), function (row) {
//             return row[columnIndex]
//        })];
//     }));

//     _.forEach(rowItems, function (row) {
//         _.forEach(columnItems, function (col) {
//             if(!_.contains(mapOfPairs[row], col)) {
//                 missingData.push({'category': row, 'group': col})
//             }
//         })
//     });

//     if(missingData.length > 0) {
//         _.forEach(missingData, function (item) {
//             var newRow = _.map(_.range(data[0].length), function(i) { return '' });
//             newRow[rowIndex] = item['category'];
//             newRow[columnIndex] = item['group'];
//             data.push(newRow)
//         });
//         return data;
//     }
//     return null
// }

// If we're running under Node - required for testing
if (typeof exports !== 'undefined') {
  var _ = require('../charts/vendor/underscore-min')
  var dataTools = require('../charts/rd-data-tools')
  var builderTools = require('../cms/rd-builder')
  var uniqueDataInColumnMaintainOrder = dataTools.uniqueDataInColumnMaintainOrder
  var seriesDecimalPlaces = dataTools.seriesDecimalPlaces
  var seriesCouldBeYear = dataTools.seriesCouldBeYear
  var formatNumberWithDecimalPlaces = dataTools.formatNumberWithDecimalPlaces
  var getColumnIndex = builderTools.getColumnIndex
  var index_of_column_named = dataTools.index_of_column_named

  exports.buildTableObject = buildTableObject
  exports.simpleTable = simpleTable
  exports.groupedTable = groupedTable
}
