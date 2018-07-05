/**
 * Created by Tom.Ridd on 25/02/2018.

 rd-builder provides common functions that are required by both the chartbuilder and tablebuilder screens

 specifically
 - validate that data does not have multiple rows that correspond to a single data point
 - validate that data has coverage of every data point
 - provide useful error messages when data is invalid

 */

// Forms of data error
var DATA_ERROR_DUPLICATION = "duplication";
var DATA_ERROR_MISSING_DATA = "missing data";
var DATA_ERROR_SETTINGS_ERROR = "settings";
var DATA_ERROR_COMPLEX_DATA = "complex data";


// ---------------------------------------------------------------------------
// PUBLIC
// ---------------------------------------------------------------------------


function validateData(data, categoryColumn, groupColumn) {
    var errors = [];
    var dataRows = _.clone(data);
    var headerRow = dataRows.shift();
    var lowerHeaderRow = _.map(headerRow, function (m) {
        return m.trim().toLowerCase()
    })

    var categoryIndex = index_of_column_named(lowerHeaderRow, categoryColumn);
    if (categoryIndex === null) {
        return [{
            'error': 'could not find data column',
            'column': categoryColumn,
            'errorType': DATA_ERROR_SETTINGS_ERROR
        }]
    }
    if (groupColumn !== null) {
        var groupIndex = index_of_column_named(lowerHeaderRow, groupColumn);
        if (groupIndex === null) {
            return [{
                'error': 'could not find data column',
                'column': groupColumn,
                'errorType': DATA_ERROR_SETTINGS_ERROR
            }]
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
    var lowerHeaderRow = _.map(headerRow, function (m) {
        return m.trim().toLowerCase();
    });
    var categoryIndex = index_of_column_named(lowerHeaderRow, categoryColumn);

    if (categoryIndex === null) {
        return [{'error': 'could not find data column', 'column': categoryColumn}]
    }
    if (groupColumn !== null) {
        var groupIndex = index_of_column_named(lowerHeaderRow, groupColumn);

        if (groupIndex === null) {
            return [{'error': 'could not find data column', 'column': groupColumn}]
        } else {
            return validateGroupedDataDuplicates(dataRows, categoryIndex, groupIndex)
        }
    } else {
        return validateSimpleData(dataRows, categoryIndex)
    }
}


// ---------------------------------------------------------------------------
// SIMPLE DATA (not cross tab, multiseries, panel, etc...)
// ---------------------------------------------------------------------------

function validateSimpleData(data, categoryIndex, categoryColumn) {
    var duplicateErrors = [];

    var uniqueCategories = _.uniq(_.map(data, function (row) {
        return row[categoryIndex];
    }));

    if (uniqueCategories.length === data.length) {
        return [];
    } else if (data.length % uniqueCategories.length === 0) {
        return [{'errorType': DATA_ERROR_COMPLEX_DATA}]
    } else {
        var dict = {};
        _.forEach(data, function (row) {
            var value = row[categoryIndex];
            if (value in dict) {
                // wrap in if to make sure we don't add multiple error messages
                if (dict[value] !== 'added to errors') {
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

}


// ---------------------------------------------------------------------------
// GROUPED DATA VALIDATION (cross tab, multiseries, panel, etc...)
// ---------------------------------------------------------------------------

function validateGroupedData(data, categoryIndex, groupIndex, categoryColumn, groupColumn) {
    var completeErrors = validateGroupedDataCompleteness(data, categoryIndex, groupIndex, categoryColumn, groupColumn);
    var duplicateErrors = validateGroupedDataDuplicates(data, categoryIndex, groupIndex, categoryColumn, groupColumn);

    return completeErrors.concat(duplicateErrors);
}

function validateGroupedDataCompleteness(data, categoryIndex, groupIndex, categoryColumn, groupColumn) {
    var rowItems = _.uniq(_.map(data, function (item) {
        return item[categoryIndex];
    }));
    var columnItems = _.uniq(_.map(data, function (item) {
        return item[groupIndex];
    }));
    var errors = [];

    var mapOfPairs = _.object(_.map(rowItems, function (item) {
        return [item, _.map(_.filter(data, function (row) {
            return row[categoryIndex] === item
        }), function (row) {
            return row[groupIndex];
        })];
    }));

    _.forEach(rowItems, function (row) {
        _.forEach(columnItems, function (col) {
            if (!_.contains(mapOfPairs[row], col)) {
                errors.push({
                    'error': 'missing data',
                    'category': row,
                    'group': col,
                    'categoryColumn': categoryColumn,
                    'groupColumn': groupColumn,
                    'errorType': DATA_ERROR_MISSING_DATA
                })
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
        if (categoryValue in groupValuesUsedByCategory) {
            if (groupValue in groupValuesUsedByCategory[categoryValue]) {
                errors.push({
                    'error': 'duplicate data',
                    'category': row[categoryIndex],
                    'group': row[groupIndex],
                    'categoryColumn': categoryColumn,
                    'groupColumn': groupColumn,
                    'errorType': DATA_ERROR_DUPLICATION
                })
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


// ---------------------------------------------------------------------------
// ERROR REPORTING
// ---------------------------------------------------------------------------

function errorDescription(error) {
    switch (error.errorType) {
        case DATA_ERROR_SETTINGS_ERROR:
            return "Column '" + error.column + "' not found";

        case DATA_ERROR_MISSING_DATA:
            return "The data is missing a row for " + error.categoryColumn + " = '" + error.category + "' and " + error.groupColumn + " = '" + error.group + "'"

        case DATA_ERROR_DUPLICATION:
            if ('group' in error) {
                return "The data has duplicate entries for the rows with " + error.categoryColumn + " = '" + error.category + "' and " + error.groupColumn + " = '" + error.group + "'"
            } else {
                return "The data has duplicate entries for " + error.categoryColumn + " = '" + error.category + "'"
            }
    }
}

function errorResolutionHint(error) {
    switch (error.errorType) {
        case DATA_ERROR_SETTINGS_ERROR:
            return "Make sure the column values selected for this table are valid";

        case DATA_ERROR_MISSING_DATA:
            return "Add rows to your source spreadsheet and try again";

        case DATA_ERROR_DUPLICATION:
            return "Remove data rows in your source spreadsheet and try again"

    }
}


// If we're running under Node - required for testing
if (typeof exports !== 'undefined') {
    var _ = require('../charts/vendor/underscore-min');
    var dataTools = require('../charts/rd-data-tools');
    var index_of_column_named = dataTools.index_of_column_named;

    exports.validateSimpleData = validateSimpleData;
    exports.validateGroupedData = validateGroupedData;
    exports.validateData = validateData;
    exports.DATA_ERROR_DUPLICATION = DATA_ERROR_DUPLICATION;
    exports.DATA_ERROR_MISSING_DATA = DATA_ERROR_MISSING_DATA;
    exports.DATA_ERROR_COMPLEX_DATA = DATA_ERROR_COMPLEX_DATA;
    exports.DATA_ERROR_SETTINGS_ERROR = DATA_ERROR_SETTINGS_ERROR;
}
