

/*
DATA VALIDATION
 */
var DATA_ERROR_DUPLICATION = "duplication";
var DATA_ERROR_MISSING_DATA = "missing data";
var DATA_ERROR_SETTINGS_ERROR = "settings";

function validateData(data, categoryColumn, groupColumn) {
    var errors = [];
    var dataRows = _.clone(data);
    var headerRow = dataRows.shift();

    var categoryIndex = getColumnIndex(headerRow, categoryColumn);
    if(categoryIndex === null) {
        return [{'error': 'could not find data column', 'column': categoryColumn, 'errorType': DATA_ERROR_SETTINGS_ERROR}]
    }
    if(groupColumn !== null) {
        var groupIndex = getColumnIndex(headerRow, groupColumn);
        if(groupIndex === null) {
            return [{'error': 'could not find data column', 'column': groupColumn, 'errorType': DATA_ERROR_SETTINGS_ERROR}]
        } else {
            return validateGroupedData(dataRows, categoryIndex, groupIndex, categoryColumn, groupColumn)
        }
    } else {
        return validateSimpleData(dataRows, categoryIndex, categoryColumn)
    }
}

function validateDataDuplicatesOnly(data, categoryColumn, groupColumn) {
    var errors = [];
    var dataRows = _.clone(data);
    var headerRow = dataRows.shift();
    var categoryIndex = getColumnIndex(headerRow, categoryColumn);
    if(categoryIndex === null) {
        return [{'error': 'could not find data column', 'column': categoryColumn}]
    }
    if(groupColumn !== null) {
        var groupIndex = getColumnIndex(headerRow, groupColumn);

        if(groupIndex === null) {
            return [{'error': 'could not find data column', 'column': groupColumn}]
        } else {
            return validateGroupedDataDuplicates(dataRows, categoryIndex, groupIndex)
        }
    } else {
        return validateSimpleData(dataRows, categoryIndex)
    }
}

function validateSimpleData(data, categoryIndex, categoryColumn) {
    var duplicateErrors = [];

    var dict = {};
    _.forEach(data, function (row) {
       var value = row[categoryIndex];
        if(value in dict){
            // wrap in if to make sure we don't add multiple error messages
           if(dict[value] !== 'added to errors') {
               duplicateErrors.push({
                   'error': 'duplicate data',
                   'category': value,
                   'categoryColumn': categoryColumn,
                   'errorType': DATA_ERROR_DUPLICATION
               });
               dict[value] = 'added to errors'
           }
        } else {
           dict[value] = 'value in dict'
        }
    });

    return duplicateErrors;
}

function validateGroupedData(data, categoryIndex, groupIndex, categoryColumn, groupColumn) {
    var completeErrors = validateGroupedDataCompleteness(data, categoryIndex, groupIndex, categoryColumn, groupColumn);
    var duplicateErrors = validateGroupedDataDuplicates(data, categoryIndex, groupIndex, categoryColumn, groupColumn);

    return completeErrors.concat(duplicateErrors);
}

function validateGroupedDataCompleteness(data, categoryIndex, groupIndex, categoryColumn, groupColumn) {
    var rowItems = _.uniq(_.map(data, function(item) { return item[categoryIndex]; }));
    var columnItems = _.uniq(_.map(data, function(item) { return item[groupIndex]; }));
    var errors = [];

    var mapOfPairs = _.object(_.map(rowItems, function(item) {
       return [item, _.map(_.filter(data, function(row) { return row[categoryIndex] === item}), function (row) {
            return row[groupIndex];
       })];
    }));

    _.forEach(rowItems, function (row) {
        _.forEach(columnItems, function (col) {
            if(!_.contains(mapOfPairs[row], col)) {
                errors.push({'error':'missing data', 'category': row, 'group': col, 'categoryColumn': categoryColumn, 'groupColumn': groupColumn, 'errorType': DATA_ERROR_MISSING_DATA})
            }
        })
    });

    return errors
}

function validateGroupedDataDuplicates(data, categoryIndex, groupIndex, categoryColumn, groupColumn) {
    var errors = [];

    var groupValuesUsedByCategory = {};
    _.forEach(data, function (row) {
        var categoryValue = row[categoryIndex];
        var groupValue = row[groupIndex];
        if(categoryValue in groupValuesUsedByCategory) {
            if(groupValue in groupValuesUsedByCategory[categoryValue]) {
                errors.push({'error':'duplicate data', 'category': row[categoryIndex], 'group':row[groupIndex], 'categoryColumn': categoryColumn, 'groupColumn': groupColumn, 'errorType': DATA_ERROR_DUPLICATION})
            } else {
                groupValuesUsedByCategory[categoryValue][groupValue] = 1;
            }
        } else {
            groupValuesUsedByCategory[categoryValue] = {};
            groupValuesUsedByCategory[categoryValue][groupValue] = 1;
        }
    });

    return errors;
}

/*
ERROR REPORTING
 */


function errorDescription(error) {
    if(error.error === "could not find data column") {
        return "Column '" + error.column + "' not found"
    } else if(error.error === "missing data") {
        return "The data is missing a row for " + error.categoryColumn + " = '" + error.category + "' and " + error.groupColumn + " = '" + error.group + "'"
    } else if(error.error === "duplicate data") {
        if('group' in error) {
            return "The data has duplicate entries for the rows with " + error.categoryColumn + " = '" + error.category + "' and " + error.groupColumn + " = '" + error.group + "'"
        } else {
            return "The data has duplicate entries for " + error.categoryColumn + " = '" + error.category + "'"
        }
    }
}

function errorResolutionHint(error) {
    if(error.error === "could not find data column") {
        return "Make sure the column values selected for this table are valid"
    } else if(error.error === "missing data") {
        return "Add rows to your source spreadsheet and try again"
    } else if(error.error === "duplicate data") {
        if('group' in error) {
            return "Remove data rows in your source spreadsheet and try again"
        } else {
            return "Remove data rows in your source spreadsheet and try again"
        }
    }
}

function getColumnIndex(headerRow, column_name) {
    var index = headerRow.indexOf(column_name);
    if(index >= 0) {
        return index;
    } else {
        return null;
    }
}

// If we're running under Node - required for testing
if(typeof exports !== 'undefined') {
    var _ = require('../charts/vendor/underscore-min');
    var dataTools = require('../charts/rd-data-tools');

    exports.validateSimpleData = validateSimpleData;
    exports.validateGroupedData = validateGroupedData;
    exports.validateData = validateData;
    exports.getColumnIndex = getColumnIndex;
    exports.DATA_ERROR_DUPLICATION = DATA_ERROR_DUPLICATION;
    exports.DATA_ERROR_MISSING_DATA = DATA_ERROR_MISSING_DATA;
    exports.DATA_ERROR_SETTINGS_ERROR = DATA_ERROR_SETTINGS_ERROR;
}