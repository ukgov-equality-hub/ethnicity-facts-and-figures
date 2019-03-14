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

function drawTable(container_id, tableObject) {

    preProcessTableObject(tableObject);

    if (tableObject.type === 'simple') {
        return simpleHtmlTable(container_id, tableObject);
    } else if (tableObject.type === 'grouped') {
        return groupedHtmlTable(container_id, tableObject);
    }
}




// ---------------------------------------------------------------------------
// SIMPLE
// ---------------------------------------------------------------------------

function simpleHtmlTable(container_id, tableObject) {

    var table_html = "";
    table_html = table_html + "<table class='govuk-table eff-table--dense'>";
    table_html = appendSimpleTableHeader(table_html, tableObject);
    table_html = appendSimpleTableBody(table_html, tableObject);
    table_html = table_html + "</table>";

    document.getElementById(container_id).innerHTML = table_html

    return true;
}

function appendSimpleTableHeader(table_html, tableObject) {
    var header_html = "";
    if (tableObject['category_caption'] == null) {
        header_html = "<thead class='govuk-table__head'><tr class='govuk-table__row'><td></td>";
    } else {
        header_html = "<thead class='govuk-table__head'><tr class='govuk-table__row'><th class='govuk-table__header' scope='col'>" + tableObject.category_caption + "</th>";
    }

    _.forEach(tableObject.columns, function (column) {
        header_html = header_html + '<th class="govuk-table__header" scope="col">' + column + '</th>';
    });
    header_html = header_html + '</tr></thead>';
    return table_html + header_html;
}

function appendSimpleTableBody(table_html, tableObject) {
    var body_html = "<tbody class='govuk-table__body'>";
    _.forEach(tableObject.data, function (item) {
        body_html = body_html + "<tr class='govuk-table__row'>";
        if (tableObject.parent_child) {
            if (item.relationships.is_parent) {
                body_html = body_html + '<th class="govuk-table__header parent_row" scope="row">'
            } else {
                body_html = body_html + '<th class="govuk-table__header child_row" scope="row">'
            }
        } else {
            body_html = body_html + '<th class="govuk-table__header" scope="row">'
        }
        body_html = body_html + item.category + '</th>';

        _.forEach(item.values, function (cellValue) {
            body_html = body_html + '<td class="govuk-table__cell">' + cellValue + '</td>';
        });
        body_html = body_html + "</tr>";
    });
    body_html = body_html + "</tbody>";
    return table_html + body_html;
}





// ---------------------------------------------------------------------------
// GROUPED
// ---------------------------------------------------------------------------

function groupedHtmlTable(container_id, tableObject) {

    var table_html = "";
    table_html = table_html + "<table class='govuk-table eff-table--dense'>";
    table_html = appendGroupTableHeader(table_html, tableObject);
    table_html = appendGroupedTableBody(table_html, tableObject)
    table_html = table_html + "</table>";

    table_html = insertTableFooter(table_html, tableObject);

    document.getElementById(container_id).innerHTML = table_html

    return true;
}


function appendGroupedTableBody(table_html, tableObject) {
    var body_html = '<tbody class="govuk-table__body">';

    var items = _.sortBy(tableObject.groups[0].data, function (item) { return item.order; });

    _.forEach(items, function (item) {
        var row = item.category;
        var row_html = '<tr class="govuk-table__row">';
        if (tableObject.parent_child) {
            if (item.relationships.is_parent) {
                row_html = row_html + '<th class="govuk-table__header parent_row" scope="row">'
            } else {
                row_html = row_html + '<th class="govuk-table__header child_row" scope="row">'
            }
        } else {
            row_html = row_html + '<th class="govuk-table__header" scope="row">'
        }
        row_html = row_html + row + '</th>';

        _.forEach(tableObject.groups, function (group) {
            var row_item = _.findWhere(group.data, { 'category': row });
            _.forEach(row_item.values, function (cellValue) {
                row_html = row_html + '<td class="govuk-table__cell">' + cellValue + '</td>';
            });
        });
        row_html = row_html + '</tr>';
        body_html = body_html + row_html;
    });
    body_html = body_html + "</tbody>";
    return table_html + body_html;
}


function appendGroupTableHeader(table_html, tableObject) {
    // Check if we need two rows of headers (based on whether any column headings exist)
    var doSecondRow = false;
    _.forEach(tableObject.columns, function (column) {
        if (column !== '') {
            doSecondRow = true;
        }
    });

    var header_html = '';
    if (doSecondRow || tableObject['category_caption'] == null) {
        header_html = "<thead class='govuk-table__head'><tr class='govuk-table__row'><td></td>";
    } else {
        header_html = "<thead class='govuk-table__head'><tr class='govuk-table__row'><th class='govuk-table__header' scope='col'>" + tableObject.category_caption + "</th>";
    }

    // Add a row with titles for each group
    _.forEach(tableObject.groups, function (group) {
        header_html = header_html + multicell_th(group.group, tableObject.columns.length);
    });
    header_html = header_html + '</tr>';

    // If a second row is required add it
    if (doSecondRow) {
        // category_caption should go in the second row if there is one
        if (tableObject['category_caption'] != null) {
            header_html = header_html + "<tr class='govuk-table__row'><th class='govuk-table__header'>" + tableObject.category_caption + "</th>";
        } else {
            header_html = header_html + '<tr class="govuk-table__row"><td></td>';
        }

        _.forEach(tableObject.groups, function (group) {
            _.forEach(tableObject.columns, function (column) {
                header_html = header_html + '<th class="govuk-table__header">' + column + '</th>';
            });
        });
        header_html = header_html + '</tr>';
    }

    header_html = header_html + '</thead>';

    return table_html + header_html;
}



// ---------------------------------------------------------------------------
// OTHER
// ---------------------------------------------------------------------------

function appendTableTitle(table_html, tableObject) {
    if (tableObject.header && tableObject.header !== '') {
        return table_html + "<div class='table-title heading-small'>" + tableObject.header + "</div>";
    } else {
        return table_html;
    }
}

function appendTableSubtitle(table_html, tableObject) {
    if (tableObject.subtitle && tableObject.subtitle !== '') {
        return table_html + "<div class='table-subtitle'>" + tableObject.subtitle + "</div>";
    } else {
        return table_html;
    }
}

function insertTableFooter(table_html, tableObject) {
    if (tableObject.footer && tableObject.footer !== '') {
        return table_html + "<div class='table-footer'>" + tableObject.footer + "</div>";
    } else {
        return table_html;
    }
}

function multicell_th(text, total_cells) {
    return '<th class="govuk-table__header" scope="col" colspan=' + total_cells + '>' + text + '</th>';
}
