var _ = require('../application/src/js/charts/vendor/underscore-min');

function getRandomArrayData(categoryColumnSizes, valueColumnCount) {
    var categories = _.map(categoryColumnSizes, function(columnCount, index) { return getRandomCategories(columnCount, index)});
    var sorts = _.map(categories, function(category) {
        return _.map(category, function(item) { return Math.floor(Math.random() * 1000) + 1; });
    });
    var pairLists = _.map(categories, function(category, index) { return _.zip(category, sorts[index])});

    var headers = [];
    _.forEach(pairLists, function(pairList, index) {
        headers.push('Category_' + (index + 1));
        headers.push('Sort_' + (index + 1));
    });
    for(var i = 1; i <= valueColumnCount; i++) { headers.push('Values_' + i);}

    var data = [headers];
    var rows = [];
    _.forEach(pairLists, function(pairList) {
        if (rows.length === 0) {
            rows = _.map(pairList, function (pair) {
                return [pair[0], pair[1]];
            });
        } else {
            var newRows = [];
            _.forEach(pairList, function (pair) {
                return _.forEach(rows, function (row) {
                    var newRow = _.clone(row);
                    newRow.push(pair[0]);
                    newRow.push(pair[1]);
                    newRows.push(newRow);
                })
            });
            rows = newRows;
        }
    });

    rows = _.map(rows, function(row) {
       var newRow = _.clone(row);
       for(var i = 0; i < valueColumnCount; i++) { newRow.push(Math.floor((Math.random() * 998) + 1)) };
       return newRow;
    });

    _.forEach(rows, function(row) { data.push(row); });
    return data;
}

// Differs in that it only has one value column which must be called Value
function getRandomArrayDataForChart(categoryColumnSizes) {
    var array = getRandomArrayData(categoryColumnSizes, 1);
    array[0] = _.map(array[0], function(item) { return item === 'Values_1' ? 'Value' : item });
    return array;
}

// Random selection of categories in non-alphabetic order
function getRandomCategories(size, listIndex) {
    var categories = [['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k'],
    ['alpha', 'bravo', 'charlie', 'delta', 'echo', 'foxtrot', 'golf', 'hotel', 'india', 'juliet', 'kilo'],
    ['lima', 'mike', 'november', 'oscar', 'papa', 'quebec', 'romeo', 'sierra', 'tango', 'uniform']];
    return _.shuffle(categories[listIndex].slice(0, size));
}

function getSimpleArrayData() {
  // These are all entirely fictitious numbers
  return  [
              ['Ethnicity',     'Value',   'Denominator', 'Order column', 'Minority status', 'White or other', 'White or other or blue'],
              ['White',         '10000',    '100020',     '400',          'Majority',        'White'         , 'White'],
              ['Black',         '15000',    '100030',     '100',          'Minority',        'Other'         , 'Blue'],
              ['Mixed',         '5000',     '200020',     '300',          'Minority',        'Other'         , 'Other'],
              ['Asian',         '70000',    '200030',     '200',          'Minority',        'Other'         , 'Other'],
              ['Other',         '9000',     '300020',     '500',          'Minority',        'Other'         , 'Other']
          ];
}

function getGroupedArrayData() {
  // These are all entirely fictitious numbers
  return [
            ['Ethnicity',     'Alternate',  'Socio-economic', 'Value',   'Denominator', 'Minority status', 'White or other', 'Pink or other'],
            ['White',         '0',          'Rich',           '10000',    '100020',     'Majority',        'White',          'Pink'],
            ['White',         '0',          'Poor',           '5000',     '200020',     'Majority',        'White',          'Pink'],
            ['BAME',          '2',          'Rich',           '9000',     '300020',     'Minority',        'Any Other',      'Any Other'],
            ['BAME',          '2',          'Poor',           '4000',     '400020',     'Minority',        'Any Other',      'Any Other'],
            ['Any Other',     '1',          'Rich',           '9000',     '300020',     'Minority',        'Any Other',      'Any Other'],
            ['Any Other',     '1',          'Poor',           '4000',     '400020',     'Minority',        'Any Other',      'Any Other']
         ];
}

if(typeof exports !== 'undefined') {
    exports.getRandomArrayData = getRandomArrayData;
    exports.getRandomArrayDataForChart = getRandomArrayDataForChart;
    exports.getSimpleArrayData = getSimpleArrayData;
    exports.getGroupedArrayData = getGroupedArrayData;
}
