/* globals _, $, preProcessTableObject */
/**
 * Created by Tom.Ridd on 05/05/2017.

rd-table renders tableObjects according to the requirements that were identified during the ethnicity facts & figures project

specifically...
- rendering methods for all chart types (bar, line, component, panel bar, panel line)
- render tables with parent-child relationships correctly
    -  in a parent-child table parent rows should be bold and childen light

rd-table is only used to preview tables in the table builder. tables in the static site are rendered using CSS/Html by the templates

 */

// ---------------------------------------------------------------------------
// PUBLIC
// ---------------------------------------------------------------------------

window.drawTable = function (containerId, tableObject) {
  preProcessTableObject(tableObject)

  if (tableObject.type === 'simple') {
    return simpleHtmlTable(containerId, tableObject)
  } else if (tableObject.type === 'grouped') {
    return groupedHtmlTable(containerId, tableObject)
  }
}

// ---------------------------------------------------------------------------
// SIMPLE
// ---------------------------------------------------------------------------

function simpleHtmlTable (containerId, tableObject) {
  var tableHtml = ''
  tableHtml = tableHtml + "<table class='table table-sm'>"
  tableHtml = appendSimpleTableHeader(tableHtml, tableObject)
  tableHtml = appendSimpleTableBody(tableHtml, tableObject)
  tableHtml = tableHtml + '</table>'

  $('#' + containerId).html(tableHtml)

  return true
}

function appendSimpleTableHeader (tableHtml, tableObject) {
  var headerHtml = ''
  if (tableObject['category_caption'] == null) {
    headerHtml = '<thead><tr><td></td>'
  } else {
    headerHtml = '<thead><tr><th>' + tableObject.category_caption + '</th>'
  }

  _.forEach(tableObject.columns, function (column) {
    headerHtml = headerHtml + '<th>' + column + '</th>'
  })
  headerHtml = headerHtml + '</tr></thead>'
  return tableHtml + headerHtml
}

function appendSimpleTableBody (tableHtml, tableObject) {
  var bodyHtml = '<tbody>'
  _.forEach(tableObject.data, function (item) {
    bodyHtml = bodyHtml + '<tr>'
    if (tableObject.parent_child) {
      if (item.relationships.is_parent) {
        bodyHtml = bodyHtml + '<th class="parent_row">'
      } else {
        bodyHtml = bodyHtml + '<th class="child_row">'
      }
    } else {
      bodyHtml = bodyHtml + '<th>'
    }
    bodyHtml = bodyHtml + item.category + '</th>'

    _.forEach(item.values, function (cellValue) {
      bodyHtml = bodyHtml + '<td>' + cellValue + '</td>'
    })
    bodyHtml = bodyHtml + '</tr>'
  })
  bodyHtml = bodyHtml + '</tbody>'
  return tableHtml + bodyHtml
}

// ---------------------------------------------------------------------------
// GROUPED
// ---------------------------------------------------------------------------

function groupedHtmlTable (containerId, tableObject) {
  var tableHtml = ''
  tableHtml = tableHtml + "<table class='table table-sm'>"
  tableHtml = appendGroupTableHeader(tableHtml, tableObject)
  tableHtml = appendGroupedTableBody(tableHtml, tableObject)
  tableHtml = tableHtml + '</table>'

  tableHtml = insertTableFooter(tableHtml, tableObject)

  $('#' + containerId).html(tableHtml)

  return true
}

function appendGroupedTableBody (tableHtml, tableObject) {
  var bodyHtml = '<tbody>'

  var items = _.sortBy(tableObject.groups[0].data, function (item) { return item.order })

  _.forEach(items, function (item) {
    var row = item.category
    var rowHtml = '<tr>'
    if (tableObject.parent_child) {
      if (item.relationships.is_parent) {
        rowHtml = rowHtml + '<th class="parent_row">'
      } else {
        rowHtml = rowHtml + '<th class="child_row">'
      }
    } else {
      rowHtml = rowHtml + '<th>'
    }
    rowHtml = rowHtml + row + '</th>'

    _.forEach(tableObject.groups, function (group) {
      var rowItem = _.findWhere(group.data, { 'category': row })
      _.forEach(rowItem.values, function (cellValue) {
        rowHtml = rowHtml + '<td>' + cellValue + '</td>'
      })
    })
    rowHtml = rowHtml + '</tr>'
    bodyHtml = bodyHtml + rowHtml
  })
  bodyHtml = bodyHtml + '</tbody>'
  return tableHtml + bodyHtml
}

function appendGroupTableHeader (tableHtml, tableObject) {
  // Check if we need two rows of headers (based on whether any column headings exist)
  var doSecondRow = false
  _.forEach(tableObject.columns, function (column) {
    if (column !== '') {
      doSecondRow = true
    }
  })

  var headerHtml = ''
  if (doSecondRow || tableObject['category_caption'] == null) {
    headerHtml = '<thead><tr><td></td>'
  } else {
    headerHtml = '<thead><tr><th>' + tableObject.category_caption + '</th>'
  }

  // Add a row with titles for each group
  _.forEach(tableObject.groups, function (group) {
    headerHtml = headerHtml + multicellTH(group.group, tableObject.columns.length)
  })
  headerHtml = headerHtml + '</tr>'

  // If a second row is required add it
  if (doSecondRow) {
    // category_caption should go in the second row if there is one
    if (tableObject['category_caption'] != null) {
      headerHtml = headerHtml + '<tr><th>' + tableObject.category_caption + '</th>'
    } else {
      headerHtml = headerHtml + '<tr><td></td>'
    }

    _.forEach(tableObject.groups, function (group) {
      _.forEach(tableObject.columns, function (column) {
        headerHtml = headerHtml + '<th>' + column + '</th>'
      })
    })
    headerHtml = headerHtml + '</tr>'
  }

  headerHtml = headerHtml + '</thead>'

  return tableHtml + headerHtml
}

// ---------------------------------------------------------------------------
// OTHER
// ---------------------------------------------------------------------------

window.appendTableTitle = function (tableHtml, tableObject) {
  if (tableObject.header && tableObject.header !== '') {
    return tableHtml + "<div class='table-title heading-small'>" + tableObject.header + '</div>'
  } else {
    return tableHtml
  }
}

window.appendTableSubtitle = function (tableHtml, tableObject) {
  if (tableObject.subtitle && tableObject.subtitle !== '') {
    return tableHtml + "<div class='table-subtitle'>" + tableObject.subtitle + '</div>'
  } else {
    return tableHtml
  }
}

function insertTableFooter (tableHtml, tableObject) {
  if (tableObject.footer && tableObject.footer !== '') {
    return tableHtml + "<div class='table-footer'>" + tableObject.footer + '</div>'
  } else {
    return tableHtml
  }
}

function multicellTH (text, totalCells) {
  return '<th colspan=' + totalCells + '>' + text + '</th>'
}
