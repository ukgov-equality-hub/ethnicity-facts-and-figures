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
    if(tableObject.title && tableObject.title !== '') {
        table_html = table_html + "<div class='table-title'>" + tableObject.title + "</div>";
    }
    if(tableObject.subtitle && tableObject.subtitle !== '') {
        table_html = table_html + "<div class='table-subtitle'>" + tableObject.subtitle + "</div>";
    }

    table_html = table_html + "<table class='table table-sm'><thead>";
    table_html = table_html + "<tr><th></th>";
    _.forEach(tableObject.columns, function(column) {
        table_html = table_html + '<th>' + column + '</th>';
    });
    table_html = table_html + "</tr></thead>";

    table_html = table_html + "<tbody>";
    _.forEach(tableObject.data, function(item) {
        table_html = table_html + "<tr>";
        table_html = table_html + '<th>' + item.category + '</th>';
        _.forEach(item.values, function(value) {
            table_html = table_html + '<td>' + value + '</td>' ;
        });
        table_html = table_html + "</tr>";
    });
    table_html = table_html + "</tbody></table>";

    if(tableObject.footer && tableObject.footer !== '') {
        table_html = table_html + "<div class='table-footer'>" + tableObject.footer + "</div>";
    }

    $("#" + container_id).html(table_html);

    return true;
}

function groupedHtmlTable(container_id, tableObject) {

    var table_html = "";
    if(tableObject.header && tableObject.header !== '') {
        table_html = table_html + "<div class='table-title heading-small'>" + tableObject.header + "</div>";
    }
    if(tableObject.subtitle && tableObject.subtitle !== '') {
        table_html = table_html + "<div class='table-subtitle'>" + tableObject.subtitle + "</div>";
    }
    table_html = table_html + "<table class='table table-sm'>";

    var header_html = '<thead><tr><td></td>';
    _.forEach(tableObject.groups, function (group) {
        header_html = header_html + multicell(group.group, tableObject.columns.length);
    });
    header_html = header_html + '</tr>';

    header_html = header_html + '<tr><td>' + tableObject.category + '</td>';
    _.forEach(tableObject.groups, function (group) {
        _.forEach(tableObject.columns, function(column) {
            header_html = header_html + '<td>' + column + '</td>';
        });
    });
    header_html = header_html + '</tr>';
    header_html = header_html + '</thead>';

    table_html = table_html + header_html;
    table_html = table_html + '<tbody>';

    var items = _.sortBy(tableObject.groups[0].data, function(item) { return item.order; })
    var rows = _.map(items, function(item) { return item.category; });
    _.forEach(rows, function(row) {
        var row_html = '<tr><th>' + row + '</th>';
        _.forEach(tableObject.groups, function(group) {
            row_item = _.findWhere(group.data, {'category':row});
            _.forEach(row_item.values, function(cell) {
                row_html = row_html + '<td>' + cell + '</td>';
            })
        });
        row_html = row_html + '</tr>';
        table_html = table_html + row_html;
    });


    table_html = table_html + "</tbody></table>";

    if(tableObject.footer && tableObject.footer !== '') {
        table_html = table_html + "<div class='table-footer'>" + tableObject.footer + "</div>";
    }
    $("#" + container_id).html(table_html);

    return true;
}

function multicell(text, total_cells) {
    html = '<td>' + text + '</td>';
    for(i=1; i<total_cells; i++) {
        html = html + '<td></td>';
    }
    return html;
}