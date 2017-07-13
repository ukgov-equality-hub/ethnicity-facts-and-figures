/**
 * Created by Tom.Ridd on 08/05/2017.
 */

function filterData(data, filter) {

    var indexFilter = textFilterToIndexFilter(data, filter);
    return applyFilter(data, indexFilter);
}

function numerateColumns(data, columns) {
    _.forEach(columns, function (column) {
        numerateColumn(data, column);
    });
}

function numerateColumn(data, column) {
    var index = data[0].indexOf(column);
    for(row = 1; row < data.length; row++) {
        row[index] = row[index].toFloat();
    }
}

function textFilterToIndexFilter(data, textFilter) {
    var indexFilter = {};
    var headers = data[0];

    for(var key in textFilter) {
        var i = headers.indexOf(key);
        indexFilter[i] = textFilter[key];
    }

    return indexFilter;
}

function applyFilter(data, indexFilter){
    var data2 = _.clone(data);

    var headerRow = data2.shift();
    var filteredRows = [];

    for(var d in data2) {
        var datum = data2[d];
        if(itemPassesFilter(datum, indexFilter)) {
            filteredRows.push(datum);
        }
    }

    filteredRows.unshift(headerRow);
    return filteredRows;
}

function itemPassesFilter(item, filter) {
    if(item[0] === '') { return false; }

    for(var index in filter) {
        if (item[index] !== filter[index]) {
            return false;
        }
    }
    return true;
}

function formatNumber(numStr) {
    var number = numStr.replaceAll("%","");
    var formatted = (number * 1).toLocaleString("en-uk");
    if(formatted === "NaN") {
        return number;
    } else {
        return formatted;
    }
}

function formatNumberWithDecimalPlaces(numStr, dp) {
    var number = numStr.replace("%","");
    var formatted = (number * 1).toLocaleString("en-uk", { minimumFractionDigits: dp, maximumFractionDigits: dp });
    if(formatted === "NaN") {
        return number;
    } else {
        return formatted;
    }
}