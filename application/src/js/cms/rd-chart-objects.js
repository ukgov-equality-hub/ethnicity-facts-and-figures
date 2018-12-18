/* globals uniqueDataInColumnOrdered, uniqueDataInColumn */
/**
 * Created by Tom.Ridd on 05/05/2017.

rd-chart-objects builds a chartObject with input and settings provided in the Chart Builder interface

- build chartObjects for all supported chart types (bar, line, component, panel bar, panel line)
- store sufficient data rd-graph.js can render a chart

building the chart objects it also does data transforms required by stories in

specifically...
- sorting data points by a specified order
- sorting series by a specified order

THERE IS INAPPROPRIATE SEPARATION OF POWERS BETWEEN HERE AND rd-graph.js

THE PARENT COLOUR SECTION IS TO DO WITH DISPLAY, NOT DATA CONTENT

 */

var defaultParentColor = '#2B8CC4'
var defaultChildColor = '#B3CBD9'
var VERSION = '1.1' // panel charts include sort option
var BAR_CHART = 'bar'
var LINE_CHART = 'line'
var COMPONENT_CHART = 'component'
var PANEL_BAR_CHART = 'panel_bar'
var PANEL_LINE_CHART = 'panel_line'

// ---------------------------------------------------------------------------
// CHART OBJECT GENERATORS
// build chart settings into a ChartObject for storage and rendering using rd-graph.js
// ---------------------------------------------------------------------------

window.buildChartObject = function (data, chartType, valueColumn,
  categoryColumn, secondaryColumn, parentColumn, categoryOrderColumn, secondaryOrderColumn,
  chartTitle, xAxisLabel, yAxisLabel, numberFormat,
  nullValue) {
  // data: an array of data including headers
  // chartType: a chart type constant (see above)
  //
  // following arguments should be the string headers of the columns with data
  //
  // valueColumn: chart values (current defaults to 'value')
  // categoryColumn: the primary chart column (bars, series, component groups)
  // secondaryColumn (optional): the secondary chart column (sub-bars, time, panels, component items)
  // parentColumn (optional): the column item parent values may be kept in
  // categoryOrderColumn (optional): to sort categories
  // secondaryOrderColumn (optional): to sort items such as panels or component items
  //
  // other values should be self explanatory

  // case statement to build chart based on type

  var nullColumnValue = nullValue || '[None]'
  switch (chartType.toLowerCase()) {
    case BAR_CHART:
      var dataRows = _.clone(data)
      var headerRow = dataRows.shift()
      if (secondaryColumn === nullColumnValue || secondaryColumn === null) {
        return barchartSingleObject(headerRow, dataRows, categoryColumn, parentColumn, categoryOrderColumn, chartTitle, xAxisLabel, yAxisLabel, numberFormat)
      } else {
        return barchartDoubleObject(headerRow, dataRows, categoryColumn, secondaryColumn, parentColumn, categoryOrderColumn, chartTitle, xAxisLabel, yAxisLabel, numberFormat)
      }

    case LINE_CHART:
      return linechartObject(data, categoryColumn, secondaryColumn, chartTitle, xAxisLabel, yAxisLabel, numberFormat, categoryOrderColumn)

    case COMPONENT_CHART:
      return componentChartObject(data, categoryColumn, secondaryColumn, chartTitle, xAxisLabel, yAxisLabel, numberFormat, null, secondaryOrderColumn)
    case PANEL_BAR_CHART:
      return panelBarchartObject(data, categoryColumn, secondaryColumn, chartTitle, xAxisLabel, yAxisLabel, numberFormat, categoryOrderColumn, secondaryOrderColumn)

    case PANEL_LINE_CHART:
      return panelLinechartObject(data, secondaryColumn, categoryColumn, chartTitle, xAxisLabel, yAxisLabel, numberFormat, secondaryOrderColumn)
    default:
      return null
  }
}

// -----------------------------------------------------------------------------------------

// ---------------------------------------------------------------------------
// CHARTOBJECT GENERATORS
// build chart settings into a ChartObject for storage and rendering using rd-graph.js
// ---------------------------------------------------------------------------

// ----------------------------------
// BARCHART
// ----------------------------------

function barchartObject (data, primaryColumn, secondaryColumn, parentColumn, orderColumn,
  chartTitle, xAxisLabel, yAxisLabel, numberFormat) {
  var dataRows = _.clone(data)
  var headerRow = dataRows.shift()
  if (isSimpleBarchart(secondaryColumn)) {
    return barchartSingleObject(headerRow, dataRows, primaryColumn, parentColumn, orderColumn, chartTitle, xAxisLabel, yAxisLabel, numberFormat)
  } else {
    return barchartDoubleObject(headerRow, dataRows, primaryColumn, secondaryColumn, parentColumn, orderColumn, chartTitle, xAxisLabel, yAxisLabel, numberFormat)
  }
}

function isSimpleBarchart (columnName) {
  return columnName === '[None]' || columnName === null
}

function barchartSingleObject (headerRow, dataRows, categoryColumn, parentColumn, orderColumn, chartTitle, xAxisLabel, yAxisLabel, numberFormat) {
  var indices = getIndices(headerRow, categoryColumn, null, parentColumn, orderColumn)

  var categories = uniqueCategories(dataRows, indices['category'], indices['order'])
  var values = _.map(categories, function (category) {
    return valueForCategory(dataRows, indices['category'], indices['value'], indices['parent'], category)
  })

  var parents = []
  if (indices['parent'] !== null) {
    parents = _.unique(_.map(dataRows, function (row) { return row[indices['parent']] }))
  }

  return {
    'type': 'bar',
    'title': {'text': chartTitle},
    'parent_child': indices['parent'] !== null,
    'xAxis': {'title': {'text': xAxisLabel}, 'categories': categories},
    'yAxis': {'title': {'text': yAxisLabel}},
    'series': [{'name': categoryColumn, 'data': values}],
    'numberFormat': numberFormat,
    'parents': parents,
    'version': VERSION
  }
}

function barchartDoubleObject (headerRow, dataRows, category1, category2, parentColumn, orderColumn, chartTitle, xAxisLabel, yAxisLabel, numberFormat) {
  var indices = getIndices(headerRow, category1, category2, parentColumn, orderColumn)

  var categories = uniqueCategories(dataRows, indices['category'], indices['order'])

  var series = uniqueDataInColumnMaintainOrder(dataRows, indices['secondary'])

  var seriesData = []
  series.forEach(function (s) {
    var seriesRows = _.filter(dataRows, function (row) { return row[indices['secondary']] === s })
    var values = []
    _.forEach(categories, function (category) {
      values.push(valueForCategory(seriesRows, indices['category'], indices['value'], indices['parent'], category))
    })
    seriesData.push({'name': s, 'data': values})
  })

  return {
    'type': 'bar',
    'title': {'text': chartTitle},
    'xAxis': {'title': {'text': xAxisLabel}, 'categories': categories},
    'yAxis': {'title': {'text': yAxisLabel}},
    'series': sortChartSeries(seriesData),
    'numberFormat': numberFormat,
    'version': VERSION
  }
}

// ----------------------------------
// LINE CHART
// ----------------------------------

function linechartObject (data, categoriesColumn, seriesColumn, chartTitle, xAxisLabel, yAxisLabel, numberFormat, seriesOrderColumn) {
  var dataRows = _.clone(data)
  var headerRow = dataRows.shift()
  var seriesOrderColumnName = seriesOrderColumn === '[None]' ? null : seriesOrderColumn

  var indices = getIndices(headerRow, categoriesColumn, seriesColumn, null, null, seriesOrderColumnName)
  var categories = uniqueDataInColumnMaintainOrder(dataRows, indices['category'])
  var seriesNames = uniqueDataInColumnMaintainOrder(dataRows, indices['secondary'])

  /*
    This is going to require some major refactoring down line
    For now we are going to compromise with a degree of code ugliness, build tests, and then get to beautification
     */
  var seriesIndex = indices['secondary']
  var seriesOrderIndex = indices['custom']
  if (seriesOrderIndex) {
    var orderValues = _.map(seriesNames, function (series) {
      var index = _.findIndex(dataRows, function (row) {
        return row[seriesIndex] === series
      })
      return dataRows[index][seriesOrderIndex]
    })
    seriesNames = _.map(_.sortBy(_.zip(seriesNames, orderValues), function (pair) { return pair[1] }), function (pair) { return pair[0] })
  }

  var chartSeries = []
  _.forEach(seriesNames, function (seriesName) {
    var values = []
    _.forEach(categories, function (category) {
      values.push(valueForCategoryAndSeries(dataRows, indices['category'], category, indices['secondary'], seriesName, indices['value']))
    })
    chartSeries.push({'name': seriesName, 'data': values})
  })

  return {
    'type': 'line',
    'title': {'text': chartTitle},
    'xAxis': {'title': {'text': xAxisLabel}, 'categories': categories},
    'yAxis': {'title': {'text': yAxisLabel}},
    'series': sortChartSeries(chartSeries),
    'numberFormat': numberFormat,
    'version': VERSION}
}

// ----------------------------------
// COMPONENT CHART
// ----------------------------------

function componentChartObject (data, groupingColumn, seriesColumn, chartTitle, xAxisLabel, yAxisLabel, numberFormat, rowOrderColumn, seriesOrderColumn) {
  var dataRows = _.clone(data)
  var headerRow = dataRows.shift()
  var indices = getIndices(headerRow, groupingColumn, seriesColumn, null, rowOrderColumn, seriesOrderColumn)

  var groups = null
  if (isUndefinedOrNull(rowOrderColumn) || rowOrderColumn === '[None]') {
    groups = uniqueDataInColumnMaintainOrder(dataRows, indices['category'])
  } else {
    groups = uniqueDataInColumnOrdered(dataRows, indices['category'], indices['order'])
  }

  var seriesNames = null
  if (isUndefinedOrNull(seriesOrderColumn) || seriesOrderColumn === '[None]') {
    seriesNames = uniqueDataInColumnMaintainOrder(dataRows, indices['secondary']).reverse()
  } else {
    seriesNames = uniqueDataInColumnOrdered(dataRows, indices['secondary'], indices['custom']).reverse()
  }

  var chartSeries = seriesNames.map(function (seriesName) {
    var values = groups.map(function (group) {
      return valueForCategoryAndSeries(dataRows, indices['category'], group, indices['secondary'], seriesName, indices['value'])
    })
    return {'name': seriesName, 'data': values}
  })

  return {
    'type': 'component',
    'title': {'text': chartTitle},
    'xAxis': {'title': {'text': xAxisLabel}, 'categories': groups},
    'yAxis': {'title': {'text': yAxisLabel}},
    'series': chartSeries,
    'numberFormat': numberFormat,
    'version': VERSION
  }
}

// ----------------------------------
// PANEL BAR CHART
// ----------------------------------

function panelBarchartObject (data, categoryColumn, panelColumn, chartTitle, xAxisLabel, yAxisLabel, numberFormat, categoryOrderColumn, panelOrderColumn) {
  var dataRows = _.clone(data)
  var headerRow = dataRows.shift()

  var indices = getIndices(headerRow, categoryColumn, panelColumn, null, categoryOrderColumn, panelOrderColumn)
  var categories = uniqueCategories(dataRows, indices['category'], indices['order'])

  var panelValues = null
  if (isUndefinedOrNull(panelOrderColumn) || panelOrderColumn === '[None]') {
    panelValues = uniqueDataInColumnMaintainOrder(dataRows, indices['secondary'])
  } else {
    panelValues = uniqueDataInColumnOrdered(dataRows, indices['secondary'], indices['custom'])
  }

  var panels = panelValues.map(function (panelValue) {
    var panelRows = _.filter(dataRows, function (row) { return row[indices['secondary']] === panelValue })

    var values = categories.map(function (category) {
      return valueForCategory(panelRows, indices['category'], indices['value'], indices['parent'], category)
    })

    return {
      'type': 'small_bar',
      'title': {'text': panelValue},
      'xAxis': {'title': {'text': xAxisLabel}, 'categories': categories},
      'yAxis': {'title': {'text': yAxisLabel}},
      'series': [{'name': categoryColumn, 'data': values}],
      'numberFormat': numberFormat
    }
  })

  return {
    'type': 'panel_bar_chart',
    'title': {'text': chartTitle},
    'xAxis': {'title': {'text': xAxisLabel}, 'categories': categories},
    'yAxis': {'title': {'text': yAxisLabel}},
    'panels': panels,
    'version': VERSION
  }
}

// ----------------------------------
// PANEL LINE CHART
// ----------------------------------

function panelLinechartObject (data, xAxisColumn, panelColumn, chartTitle, xAxisLabel, yAxisLabel, numberFormat, panelOrderColumn) {
  var dataRows = _.clone(data)
  var headerRow = dataRows.shift()
  var indices = getIndices(headerRow, panelColumn, xAxisColumn, null, null, panelOrderColumn)

  var panelNames = null
  if (isUndefinedOrNull(panelOrderColumn) || panelOrderColumn === '[None]') {
    panelNames = uniqueDataInColumnMaintainOrder(dataRows, indices['category'])
  } else {
    panelNames = uniqueDataInColumnOrdered(dataRows, indices['category'], indices['custom'])
  }
  var xAxisNames = uniqueDataInColumn(dataRows, indices['secondary'])

  var panelCharts = _.map(panelNames, function (panelName) {
    var values = _.map(xAxisNames, function (category) {
      return valueForCategoryAndSeries(dataRows, indices['secondary'], category, indices['category'], panelName, indices['value'])
    })

    return {'type': 'line',
      'title': {'text': panelName},
      'xAxis': {'title': {'text': xAxisLabel}, 'categories': xAxisNames},
      'yAxis': {'title': {'text': yAxisLabel}},
      'series': [{'name': panelName, 'data': values}],
      'numberFormat': numberFormat
    }
  })

  return {
    'type': 'panel_line_chart',
    'title': {'text': chartTitle},
    'panels': panelCharts,
    'numberFormat': numberFormat,
    'version': VERSION
  }
}

// ---------------------------------------------------------------------------
// PROCESSING
// ---------------------------------------------------------------------------

function getIndices (headerRow, categoryColumn, secondaryColumn, parentColumn, orderColumn, customColumn) {
  var headersLower = _.map(headerRow, function (item) { return item.trim().toLowerCase() })

  var category = isUndefinedOrNull(categoryColumn) ? null : indexOfColumnNamed(headersLower, categoryColumn)
  var order = isUndefinedOrNull(orderColumn) ? category : indexOfColumnNamed(headersLower, orderColumn)
  var parent = isUndefinedOrNull(parentColumn) ? null : indexOfColumnNamed(headersLower, parentColumn)
  var secondary = isUndefinedOrNull(secondaryColumn) ? null : indexOfColumnNamed(headersLower, secondaryColumn)
  var custom = isUndefinedOrNull(customColumn) ? null : indexOfColumnNamed(headersLower, customColumn)

  return {
    'category': category >= 0 ? category : null,
    'order': order >= 0 ? order : null,
    'secondary': secondary >= 0 ? secondary : null,
    'value': indexOfColumnNamed(headersLower, 'value'),
    'parent': parent >= 0 ? parent : null,
    'custom': custom >= 0 ? custom : null
  }
}

function uniqueCategories (dataRows, categoryIndex, orderIndex) {
  if (orderIndex) {
    return uniqueDataInColumnOrdered(dataRows, categoryIndex, orderIndex)
  } else {
    return uniqueDataInColumnMaintainOrder(dataRows, categoryIndex)
  }
}

function valueForCategory (dataRows, categoryIndex, valueIndex, parentIndex, categoryValue) {
  var rows = dataRows.filter(function (row) { return row[categoryIndex] === categoryValue })
  if (rows.length === 0) {
    return {y: 0, category: categoryValue}
  } else {
    var row = rows[0]
    if (row[categoryIndex] === categoryValue) {
      var valueIsNumeric = isNumber(row[valueIndex])
      if (parentIndex) {
        var parentValue = row[parentIndex]
        var relationships = {is_parent: parentValue === categoryValue,
          is_child: parentValue !== categoryValue,
          parent: parentValue}
        if (relationships['is_parent']) {
          return {
            y: valueIsNumeric ? parseFloat(row[valueIndex]) : 0,
            relationships: relationships,
            category: row[categoryIndex],
            color: defaultParentColor,
            text: valueIsNumeric ? 'number' : row[valueIndex]
          }
        } else {
          return {
            y: valueIsNumeric ? parseFloat(row[valueIndex]) : 0,
            relationships: relationships,
            category: row[categoryIndex],
            color: defaultChildColor,
            text: valueIsNumeric ? 'number' : row[valueIndex]
          }
        }
      } else {
        return {y: valueIsNumeric ? parseFloat(row[valueIndex]) : 0,
          category: row[categoryIndex],
          text: valueIsNumeric ? 'number' : row[valueIndex]}
      }
    }
  }
}

function valueForCategoryAndSeries (dataRows, categoryIndex, categoryValue, seriesIndex, seriesValue, valueIndex) {
  var rows = _.filter(dataRows, function (row) { return row[categoryIndex] === categoryValue && row[seriesIndex] === seriesValue })
  return rows.length > 0 ? parseFloat(rows[0][valueIndex]) : 0
}

function isNumber (value) {
  return !isNaN(parseFloat(value))
}

function isUndefinedOrNull (value) {
  return value === undefined || value === null
}

// ---------------------------------------------------------------------------
// SORTING
// ---------------------------------------------------------------------------

function sortChartSeries (serieses) {
  // check if these series are numerically sortable
  var invalidSerieses = serieses.filter(function (series) {
    return isNaN(toNumberSortValue(series.name))
  })
  if (invalidSerieses.length > 0) { return serieses }

  // if series sortable assign a sort value
  serieses.forEach(function (series) {
    series.name_value = toNumberSortValue(series.name)
  })

  // return the sorted series
  return _.sortBy(serieses, function (series) {
    return series.name_value
  })
}

function toNumberSortValue (value) {
  var floatVal = parseFloat(value)
  if (isNaN(floatVal)) {
    return parseFloat(value.substring(1))
  } else {
    return floatVal
  }
}

// If we're running under Node - required for testing
if (typeof exports !== 'undefined') {
  var _ = require('../charts/vendor/underscore-min')
  var dataTools = require('../charts/rd-data-tools')
  var builderTools = require('../cms/rd-builder')

  var indexOfColumnNamed = dataTools.indexOfColumnNamed
  var uniqueDataInColumnMaintainOrder = dataTools.uniqueDataInColumnMaintainOrder
  var getColumnIndex = builderTools.getColumnIndex

  exports.barchartObject = barchartObject
  exports.linechartObject = linechartObject
  exports.componentChartObject = componentChartObject
  exports.panelLinechartObject = panelLinechartObject
  exports.panelBarchartObject = panelBarchartObject
}
