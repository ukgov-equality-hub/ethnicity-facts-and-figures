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

    var table_html = "<table class='table table-sm'>";
    table_html = table_html + "<thead><tr><th></th>";
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
    $("#" + container_id).html(table_html);

    return true;
}

function groupedHtmlTable(container_id, tableObject) {

    var table_html = "<table class='table table-sm'>";

    var header_html = '<thead>';
    header_html = header_html + '<tr><td></td>';
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
    var rows = _.map(tableObject.groups[0].data, function(item) { return item.category; });
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