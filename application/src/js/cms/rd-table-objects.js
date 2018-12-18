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

function buildTableObject (data, title, subtitle, footer, rowColumn, parentColumn, groupColumn, orderColumn, dataColumns, columnCaptions, indexColumnCaption, groupOrderColumn) {
  var table = null
  if (!groupColumn || groupColumn === NONE_VALUE) {
    table = simpleTable(data, title, subtitle, footer, rowColumn, parentColumn, dataColumns, orderColumn, columnCaptions, indexColumnCaption)
  } else {
    table = groupedTable(data, title, subtitle, footer, rowColumn, parentColumn, groupColumn, dataColumns, orderColumn, columnCaptions, indexColumnCaption, groupOrderColumn)
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

function simpleTable (data, title, subtitle, footer, categoryColumn, parentColumn, dataColumns, orderColumn, columnCaptions, indexColumnCaption) {
  var dataRows = _.clone(data)
  var headerRow = dataRows.shift()
  var lowHeaders = _.map(headerRow, function (m) { return m.trim().toLowerCase() })

  var columnIndex = indexOfColumnNamed(lowHeaders, categoryColumn)
  var dataColumnIndices = _.map(dataColumns, function (dataColumn) { return indexOfColumnNamed(lowHeaders, dataColumn) })

  var parentIndex = columnIndex
  var hasParentChild = false
  if (parentColumn && parentColumn !== NONE_VALUE) {
    parentIndex = indexOfColumnNamed(lowHeaders, parentColumn)
    hasParentChild = true
  }

  if (orderColumn && orderColumn !== NONE_VALUE) {
    var sortIndex = indexOfColumnNamed(lowHeaders, orderColumn)
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

    var values = _.map(dataColumnIndices, function (i) { return item[i] })
    var sortValues = _.map(values, function (value) { return numVal(value) })

    if (sortIndex) {
      return {
        'category': item[columnIndex],
        'relationships': relationships,
        'order': item[sortIndex],
        'values': values,
        'sortValues': sortValues
      }
    } else {
      return {
        'category': item[columnIndex],
        'relationships': relationships,
        'order': index,
        'values': values,
        'sortValues': sortValues
      }
    }
  })

  tableData = _.sortBy(tableData, function (item) { return item['order'] })

  if (hasParentChild) {
    tableData = adjustSimpleTableDataForParents(tableData)
  }

  var indexColumn = indexColumnCaption || categoryColumn

  return {
    'type': 'simple',
    'parent_child': hasParentChild,
    'header': title,
    'subtitle': subtitle,
    'footer': footer,
    'category': categoryColumn,
    'columns': columnCaptions,
    'data': tableData,
    'category_caption': indexColumn
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

  var currentCategories = _.map(tableData, function (item) {
    return item['category']
  })
  var missingParents = _.filter(parents, function (parent) {
    return !_.contains(currentCategories, parent)
  })

  var newData = _.clone(tableData)
  var example = tableData[0]
  _.forEach(missingParents, function (missingParent) {
    // find order for the new parent by finding the minimum value for it's children and subtracting 1
    var parentItems = _.filter(tableData, function (item) { return item.relationships.parent === missingParent })
    var minOrder = _.min(_.map(parentItems, function (item) { return item.order })) - 1

    var newDataPoint = {
      'category': missingParent,
      'order': minOrder,
      'relationships': {'is_child': false, 'is_parent': true, 'parent': missingParent},
      'sortValues': _.map(example['sortValues'], function (value) {
        return 0
      }),
      'values': _.map(example.values, function (value) {
        return ''
      })
    }
    newData.push(newDataPoint)
  })

  return newData
}

function reorderSimpleTableDataForParentChild (tableData) {
  var itemDict = _.object(_.map(tableData, function (item) { return [item.category, item] }))
  var parents = _.uniq(_.map(tableData, function (item) { return item['relationships']['parent'] }))

  var orderedData = []
  _.forEach(parents, function (parent) {
    orderedData.push(itemDict[parent])
    var parentChildren = _.filter(tableData, function (item) { return item['category'] !== parent && item['relationships']['parent'] === parent })
    orderedData = orderedData.concat(parentChildren)
  })
  return orderedData
}

// ---------------------------------------------------------------------------
// GROUPED TABLE
// ---------------------------------------------------------------------------

function groupedTable (data, title, subtitle, footer, categoryColumn, parentColumn, groupColumn, dataColumns, orderColumn, columnCaptions, indexColumnCaption, groupOrderColumn) {
  var dataByRow = _.clone(data)
  var headerRow = dataByRow.shift()
  var lowHeaders = _.map(headerRow, function (m) { return m.trim().toLowerCase() })

  // ------------------- FIND INDICES FOR THE COLUMNS --------------------------

  var columnIndex = indexOfColumnNamed(lowHeaders, categoryColumn)
  var dataColumnIndices = _.map(dataColumns, function (dataColumn) { return indexOfColumnNamed(lowHeaders, dataColumn) })

  var groupColumnIndex = indexOfColumnNamed(lowHeaders, groupColumn)

  var sortIndex = null
  if (orderColumn === null) {
    sortIndex = columnIndex
  } else if (orderColumn !== NONE_VALUE) {
    sortIndex = indexOfColumnNamed(lowHeaders, orderColumn)
  } else {
    sortIndex = indexOfColumnNamed(lowHeaders, categoryColumn)
  }

  var parentIndex = columnIndex
  var hasParentChild = false
  if (parentColumn && parentColumn !== NONE_VALUE) {
    parentIndex = indexOfColumnNamed(lowHeaders, parentColumn)
    hasParentChild = true
  }

  // ----------------------- CONVERT TO DATA ITEM OBJECTS ----------------------
  var dataByGroup = getDataByGroup(dataByRow, groupColumnIndex, groupOrderColumn, headerRow)
  var dataItemsByGroup = buildDataObjectsByGroup(dataByGroup, dataByRow, groupColumnIndex, columnIndex, hasParentChild, parentIndex, sortIndex, dataColumnIndices)

  // ----------------------- ADJUSTMENTS FOR PARENT CHILD ----------------------
  dataItemsByGroup = adjustGroupedTableDataForParents(dataItemsByGroup)

  // --------------------- DATA VALUES (Values by row) -------------------------

  var partialTable = templateGroupTable(categoryColumn, title, columnCaptions, dataItemsByGroup)

  var groupColumns = [''].concat(_.map(partialTable.groups, function (group) { return group.group }))

  var rowCategories = _.map(partialTable.groups[0].data, function (item) { return item.category })
  var tableData = _.map(rowCategories, function (category) { return dataItemWithCategory(partialTable, category) })
  tableData = _.sortBy(tableData, function (item) { return item['order'] })

  dataItemsByGroup = _.map(dataItemsByGroup, function (group) {
    group.data = _.sortBy(group.data, function (item) { return item['order'] })
    return group
  })

  // --------------------- COMPLETE THE TABLE OBJECT --------------------------
  var indexColumn = indexColumnCaption || categoryColumn

  return {
    'groupColumns': groupColumns,
    'type': 'grouped',
    'category': categoryColumn,
    'groupColumn': groupColumn,
    'columns': columnCaptions,
    'data': tableData,
    'header': title,
    'subtitle': subtitle,
    'footer': footer,
    'groups': dataItemsByGroup,
    'parent_child': hasParentChild,
    'category_caption': indexColumn
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
    row.sortValues = _.flatten(_.map(tableObject.groups, function (group) {
      return group.data[rowNo].sortValues
    }))
    // add to the data
    tableObject.data.push(row)
  }

  var items = _.sortBy(tableObject.groups[0].data, function (item) { return item.order })
  var rows = _.map(items, function (item) { return item.category })
  _.forEach(rows, function (row) {
    var rowHTML = '<tr><th>' + row + '</th>'
    _.forEach(tableObject.groups, function (group) {
      var rowItem = _.findWhere(group.data, {'category': row})
      _.forEach(_.zip(rowItem.values, columnDps, couldBeYear), function (cellValues) {
        if (cellValues[2]) {
          rowHTML = rowHTML + '<td>' + cellValues[0] + '</td>'
        } else {
          rowHTML = rowHTML + '<td>' + formatNumberWithDecimalPlaces(cellValues[0], cellValues[1]) + '</td>'
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

function buildDataObjectsByGroup (groupValues, dataRows, groupColumnIndex, columnIndex, hasParentChild, parentIndex, sortIndex, dataColumnIndices) {
  return _.map(groupValues, function (group) {
    var groupData = _.filter(dataRows, function (item) {
      return item[groupColumnIndex] === group
    })
    var groupDataItems = _.map(groupData, function (item, index) {
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
      var sortVal = item[sortIndex]
      var values = _.map(dataColumnIndices, function (i) {
        return item[i]
      })
      var sortValues = _.map(values, function (value) {
        return numVal(value)
      })
      return {
        'category': item[columnIndex],
        'relationships': relationships,
        'order': sortVal,
        'values': values,
        'sortValues': sortValues
      }
    })
    return {'group': group, 'data': groupDataItems}
  })
}

function getDataByGroup (dataByRow, groupColumnIndex, groupOrderColumn, headerRow) {
  var groupValues = uniqueDataInColumnMaintainOrder(dataByRow, groupColumnIndex)
  if (groupOrderColumn && groupOrderColumn !== NONE_VALUE) {
    var groupOrderIndex = headerRow.indexOf(groupOrderColumn)
    var orderValues = _.map(groupValues, function (item) {
      var index = _.findIndex(dataByRow, function (row) {
        return row[groupColumnIndex] === item
      })
      return dataByRow[index][groupOrderIndex]
    })
    groupValues = _.map(_.sortBy(_.zip(groupValues, orderValues), function (pair) {
      return pair[1]
    }), function (pair) {
      return pair[0]
    })
  }
  return groupValues
}

function dataItemWithCategory (partialTableObject, category) {
  var values = []
  var sortValue = ''
  var parentValue = ''
  var relationships = {}

  _.forEach(partialTableObject.groups, function (group) {
    var categoryItem = _.findWhere(group.data, {'category': category})
    sortValue = categoryItem['order']
    parentValue = categoryItem['parent']
    relationships = categoryItem['relationships']
    _.forEach(categoryItem.values, function (cell) {
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
    'sortValues': sortValues
  }
}

function templateGroupTable (categoryColumn, title, columnCaptions, groupSeries) {
  return {
    'type': 'grouped',
    'category': categoryColumn,
    'title': {'text': 'Grouped Table'},
    'header': title,
    'columns': columnCaptions,
    'groups': groupSeries
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
  var currentCategories = _.uniq(
    _.flatten(
      _.map(tableData, function (column) {
        return _.map(column.data, function (cell) {
          return cell.category
        })
      }
      )
    ))

  // Find rows that need to be added
  var missingParents = _.filter(parents, function (parent) {
    return !_.contains(currentCategories, parent)
  })

  // Build the new data items
  var newData = _.clone(tableData)
  var example = tableData[0].data[0]
  _.forEach(missingParents, function (missingParent) {
    // find order for the new parent by finding the minimum value for it's children and subtracting 1
    var parentItems = _.filter(_.flatten(_.map(tableData, function (column) { return column.data })), function (item) { return item.relationships.parent === missingParent })
    var minOrder = _.min(_.map(parentItems, function (item) { return item.order })) - 1

    // build the new data points
    _.forEach(newData, function (group) {
      var newDataPoint = {
        'category': missingParent,
        'order': minOrder,
        'relationships': {'is_child': false, 'is_parent': true, 'parent': missingParent},
        'sortValues': _.map(example['sortValues'], function (value) {
          return 0
        }),
        'values': _.map(example.values, function (value) {
          return ''
        })
      }
      group.data.push(newDataPoint)
    })
  })

  return newData
}

function reorderGroupedTableDataForParentChild (tableData) {
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
    var itemDict = _.object(_.map(group.data, function (item) { return [item.category, item] }))
    var orderedData = []
    _.forEach(parents, function (parent) {
      orderedData.push(itemDict[parent])
      var parentChildren = _.filter(group.data, function (item) { return item['category'] !== parent && item['relationships']['parent'] === parent })
      orderedData = orderedData.concat(parentChildren)
    })
    group.data = orderedData
  })

  return tableData
}

// ---------------------------------------------------------------------------
// COMMON FUNCTIONS
// ---------------------------------------------------------------------------

function numVal (value, defaultVal) {
  var string = String(value).replace(/,/g, '')
  var num = Number(string)
  return num || value
}

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
  var indexOfColumnNamed = dataTools.indexOfColumnNamed

  exports.buildTableObject = buildTableObject
  exports.simpleTable = simpleTable
  exports.groupedTable = groupedTable
}
