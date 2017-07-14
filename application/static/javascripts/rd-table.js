/**
 * Created by Tom.Ridd on 05/05/2017.
 */

function drawTable(container_id, tableObject) {
    console.log(tableObject);

    if(tableObject.type === 'simple') {
        return simpleHtmlTable(container_id, tableObject);
    } else if (tableObject.type === 'grouped') {
        return groupedHtmlTable(container_id, tableObject);
    }
}

function simpleHtmlTable(container_id, tableObject) {

    var table_html = "";
    table_html = appendTableTitle(table_html, tableObject);
    table_html = appendTableSubtitle(table_html, tableObject);

    table_html = table_html + "<table class='table table-sm'>";
    table_html = appendSimpleTableHeader(table_html, tableObject);
    table_html = appendSimpleTableBody(table_html, tableObject);
    table_html = table_html + "</table>";

    $("#" + container_id).html(table_html);

    return true;
}

function groupedHtmlTable(container_id, tableObject) {

    var table_html = "";
    table_html = appendTableTitle(table_html, tableObject);
    table_html = appendTableSubtitle(table_html, tableObject);

    table_html = table_html + "<table class='table table-sm'>";
    table_html = appendGroupTableHeader(table_html, tableObject);
    table_html = appendGroupedTableBody(table_html, tableObject)
    table_html = table_html + "</table>";

    table_html = insertTableFooter(table_html, tableObject);

    $("#" + container_id).html(table_html);

    return true;
}

function appendSimpleTableBody(table_html, tableObject) {
    var columnDps = columnDecimalPlaces(tableObject);
    var couldBeYear = columnCouldBeAYear(tableObject);

    var body_html = "<tbody>";
    _.forEach(tableObject.data, function(item) {
        body_html = body_html + "<tr>";
        body_html = body_html + '<th>' + item.category + '</th>';
        _.forEach(_.zip(item.values, columnDps, couldBeYear), function(cellValues) {
            if(cellValues[2]) {
                body_html = body_html + '<td>' + cellValues[0] + '</td>';
            } else {
                body_html = body_html + '<td>' + formatNumberWithDecimalPlaces(cellValues[0], cellValues[1]) + '</td>';
            }
        });
        body_html = body_html + "</tr>";
    });
    body_html = body_html + "</tbody>";
    return table_html + body_html;
}

function appendGroupedTableBody(table_html, tableObject) {
    var columnDps = groupedTableDecimalPlaces(tableObject);
    var couldBeYear = groupedTableCouldBeAYear(tableObject);
    var body_html = '<tbody>';

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
        row_html = row_html + '</tr>';
        body_html = body_html + row_html;
    });
    body_html = body_html + "</tbody>";
    return table_html + body_html;
}

function appendTableTitle(table_html, tableObject) {
    if(tableObject.header && tableObject.header !== '') {
        return table_html + "<div class='table-title heading-small'>" + tableObject.header + "</div>";
    } else {
        return table_html;
    }
}

function insertTableFooter(table_html, tableObject) {
    if(tableObject.footer && tableObject.footer !== '') {
        return table_html + "<div class='table-footer'>" + tableObject.footer + "</div>";
    } else {
        return table_html;
    }
}

function appendTableSubtitle(table_html, tableObject) {
    if(tableObject.subtitle && tableObject.subtitle !== '') {
        return table_html + "<div class='table-subtitle'>" + tableObject.subtitle + "</div>";
    } else {
        return table_html;
    }
}

function appendSimpleTableHeader(table_html, tableObject) {
    var header_html = "<thead><tr><th></th>";
    _.forEach(tableObject.columns, function(column) {
        header_html = header_html + '<th>' + column + '</th>';
    });
    header_html = header_html + "</tr></thead>"
    return table_html + header_html;
}

function appendGroupTableHeader(table_html, tableObject) {
    var header_html = '<thead><tr><td></td>';

    // Add a row with titles for each group
    _.forEach(tableObject.groups, function (group) {
        header_html = header_html + multicell(group.group, tableObject.columns.length);
    });
    header_html = header_html + '</tr>';

    // Check if we need to add a second row (based if any column headings exist)
    var doSecondRow = false;
    _.forEach(tableObject.columns, function(column) {
        if(column !== '') {
            doSecondRow = true;
        }
    });

    // If a second row is required add it
    if(doSecondRow) {
        header_html = header_html + '<tr><td>' + tableObject.category + '</td>';
        _.forEach(tableObject.groups, function (group) {
            _.forEach(tableObject.columns, function(column) {
                header_html = header_html + '<td>' + column + '</td>';
            });
        });
        header_html = header_html + '</tr>';
    }

    header_html = header_html + '</thead>';

    return table_html + header_html;
}

function columnDecimalPlaces(tableObject) {
    var dps = [];
    // iterate through columns
    for(var i in tableObject.data[0].values) {

        // iterate through items
        var max_dps = 0;
        for(var d in tableObject.data) {
            var item = tableObject.data[d];
            var dp = decimalPlaces(item.values[i]);
            if(dp > max_dps) {
                max_dps = dp;
            }
        }
        dps.push(max_dps);
    }
    return dps;
}

function columnCouldBeAYear(tableObject) {
    var years = [];
    // iterate through columns
    for(var i in tableObject.data[0].values) {

        // iterate through items
        var couldBeAYear = true;
        for(var d in tableObject.data) {
            var item = tableObject.data[d];
            var dp = decimalPlaces(item.values[i]);
            if(dp > 0 || item.values[i] < 1950 || item.values[i] > 2050) {
                couldBeAYear = false;
            }
        }
        years.push(couldBeAYear);
    }
    return years;
}

function groupedTableDecimalPlaces(tableObject) {
    var dps = [];
    // iterate through columns
    for(var c in tableObject.groups[0].data[0].values) {

        var max_dps = 0;
        // iterate through groups
        for(var g in tableObject.groups) {
            var group = tableObject.groups[g];

            // iterate through data
            for(var d in group.data) {
                var item = group.data[d];
                var dp = decimalPlaces(item.values[c]);
                if (dp > max_dps) {
                    max_dps = dp;
                }
            }
        }
        dps.push(max_dps);
    }
    return dps;
}

function groupedTableCouldBeAYear(tableObject) {

    var years = [];
    // iterate through columns
    for(var c in tableObject.groups[0].data[0].values) {

        var couldBeAYear = true;
        // iterate through groups
        for(var g in tableObject.groups) {
            var group = tableObject.groups[g];

            // iterate through data
            for(var d in group.data) {
                var item = group.data[d];
                var dp = decimalPlaces(item.values[c]);
                if(dp > 0 || item.values[c] < 1950 || item.values[c] > 2050) {
                    couldBeAYear = false;
                    break;
                }
            }
        }
        years.push(couldBeAYear);
    }
    return years;
}

function decimalPlaces(valueStr) {
    if(valueStr) {
        var numStr = valueStr.replace("%","");
        var pieces = numStr.split(".");
        if (pieces.length < 2) {
            return 0;
        } else {
            return pieces[1].length;
        }
    } else {
        return 0;
    }
}

function multicell(text, total_cells) {
    return '<td colspan=' + total_cells + '>' + text + '</td>';
}