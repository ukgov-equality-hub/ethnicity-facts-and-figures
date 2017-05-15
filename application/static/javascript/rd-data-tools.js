/**
 * Created by Tom.Ridd on 08/05/2017.
 */

function filterData(data, filter) {

    indexFilter = textFilterToIndexFilter(data, filter);
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
    indexFilter = {};
    headers = data[0];

    for(key in textFilter) {
        i = headers.indexOf(key);
        indexFilter[i] = textFilter[key];
    }

    return indexFilter;
}

function applyFilter(data, indexFilter){
    data2 = _.clone(data);

    headerRow = data2.shift();
    filteredRows = [];

    for(d in data2) {
        datum = data2[d];
        if(itemPassesFilter(datum, indexFilter)) {
            filteredRows.push(datum);
        }
    }

    filteredRows.unshift(headerRow);
    return filteredRows;
}

function itemPassesFilter(item, filter) {
    if(item[0] === '') { return false; }

    for(index in filter) {
        if (item[index] !== filter[index]) {
            return false;
        }
    }
    return true;
}