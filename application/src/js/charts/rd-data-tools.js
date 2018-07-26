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



function formatNumberWithDecimalPlaces(value, dp) {

    var number = ""+value;

    // Only do formatting if the string contains some digits
    if (number.match(/\d/)) {
      try {
          number = number.replace("%","");
      } finally {
          var formatted = (number * 1).toLocaleString("en-uk", {minimumFractionDigits: dp, maximumFractionDigits: dp});
          if (formatted !== "NaN") {
              return formatted;
          }
      }
    }
    return number;
}

function seriesDecimalPlaces(series) {
    var maxDp = 0;
    for(var s in series) {
        var dp = decimalPlaces(series[s]);
        if (dp > maxDp) {
            maxDp = dp;
        }
    }
    return maxDp;
}

function seriesCouldBeYear(series) {
    for(var s in series) {
        var val = series[s];
        if(decimalPlaces(val) > 0 || val < 1950 || val > 2050) {
            return false;
        }
    }
    return true;
}

function decimalPlaces(valueStr) {

    // We only want to match digits following the first
    // full stop, ignoring any trailing zeros.
    var decimalPlacesRegex = /\.(\d*[1-9])/;

    var numStr = valueStr ? String(valueStr) : "";

    var decimalFigureMatch = numStr.match(decimalPlacesRegex);

    if (decimalFigureMatch) {
      return decimalFigureMatch[1].length
    } else {
      return 0
    }
}

function uniqueDataInColumn(data, index) {
    var values = _.map(data.slice(start = 0), function(item) {
        return item[index]; });
    return _.uniq(values).sort();
}

function uniqueDataInColumnOrdered(data, index, order_column) {
    // Sort by the specified column
    var sorted = _.sortBy(data, function (item) {
        return item[order_column];
    });
    // Pull out unique items
    var values = _.map(sorted, function(item) { return item[index];});
    return _.uniq(values);
}

function uniqueDataInColumnMaintainOrder(data, index) {
    var values = [];
    var used = {};
    _.forEach(data, function (item) {
        if(!(item[index] in used)) {
            values.push(item[index]);
            used[item[index]] = 1;
        }
    });
    return values;
}


function textToData(textData) {
    var cleanData = textData.trim();
    if(cleanData.search('\t') >= 0) {
       return  _.map(cleanData.split('\n'), function (line) { return line.split('\t') });
    } else {
       return  _.map(cleanData.split('\n'), function (line) { return line.split('|') });
    }
}

var ETHNICITY_ERROR = 'Ethnicity column error';
var VALUE_ERROR = 'Value column error';
var RECTANGLE_ERROR = 'Data table error';

function validateChart(data) {
    var errors = [];
    if(hasHeader('ethnic', data) === false) { errors.push({'errorType':ETHNICITY_ERROR}); }
    if(hasHeader('value', data) === false) { errors.push({'errorType':VALUE_ERROR});}
    if(isRectangular(data) === false) { errors.push({'errorType':RECTANGLE_ERROR});}

    return errors;
}

function hasHeader(header, data) {
    var headers = data[0];
    var found = false;
    _.forEach(headers, function (str) {
        var lower = str.toLowerCase();
        if(lower.search(header) >= 0) { found = true; }
    });
    return found;
}

function isRectangular(data) {
    var size = data[0].length;
    for(var i=1; i<data.length; i++) {
        if(data[i].length !== size) { return false; }
    }
    return true;
}

function nonNumericData(data, columns) {
    var nonNumeric = [];
    var values = data.slice(1);

    _.forEach(values, function (row) {
        _.forEach(columns, function (column) {
            var item = row[column];
            if(isNaN(item)) {
                nonNumeric.push(item);
            }
        });
    });
    return nonNumeric;
}

function index_of_column_named(headers, column) {
    if(!column || column === '') {
        return null
    } else {
        var index = headers.indexOf(column.trim().toLowerCase());
        if(index === -1) {
            return null;
        } else {
            return index;
        }
    }
}

// If we're running under Node - required for testing
if(typeof exports !== 'undefined') {
    var _ = require('./vendor/underscore-min');

    exports.hasHeader = hasHeader;
    exports.decimalPlaces = decimalPlaces;
    exports.seriesDecimalPlaces = seriesDecimalPlaces;
    exports.seriesCouldBeYear = seriesCouldBeYear;
    exports.formatNumberWithDecimalPlaces = formatNumberWithDecimalPlaces;

    exports.uniqueDataInColumn = uniqueDataInColumn;
    exports.uniqueDataInColumnOrdered = uniqueDataInColumnOrdered;
    exports.uniqueDataInColumnMaintainOrder = uniqueDataInColumnMaintainOrder;

    exports.validateChart = validateChart;
    exports.textToData = textToData;

    exports.nonNumericData = nonNumericData;

    exports.index_of_column_named = index_of_column_named;

    exports.ETHNICITY_ERROR = ETHNICITY_ERROR;
    exports.VALUE_ERROR = VALUE_ERROR;
}
