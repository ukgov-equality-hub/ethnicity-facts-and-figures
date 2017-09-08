var chai = require('chai');
var assert = chai.assert;
var expect = chai.expect;

var dataTools = require('../application/static/javascripts/rd-data-tools');
var tableObjects = require('../application/static/javascripts/rd-table-objects');
var _ = require('../application/static/vendor/underscore-min');

// These are intense tests to see whether we can break table validity with randomly ordered data
// For tables we only need to test the table object

describe('test-table-ordering', function() {
  describe('#simpleTableDataEqualsArrayData()', function() {
      it('should pass a simple table if table data matches', function () {
          var original = getRandomArrayData([10],1);
          var table = tableObjects.buildTableObject(original,'','','','Category_1',null,null,null,['Values_1'],['Values_1'],'',null);

          assert.equal(simpleTableDataEqualsArrayData(table, original), true);
      });
      it('should fail a simple table if table data does not match', function () {
          var original = getRandomArrayData([10],1);
          var table = tableObjects.buildTableObject(original,'','','','Category_1',null,null,null,['Values_1'],['Values_1'],'',null);

          table.data[5].values[0] = '-10';

          assert.equal(simpleTableDataEqualsArrayData(table, original), false);
      });
      it('should pass a simple table if source columns are shuffled after building the table', function () {
          var original = getRandomArrayData([10],1);
          var table = tableObjects.buildTableObject(original,'','','','Category_1',null,null,null,['Values_1'],['Values_1'],'',null);

          var shuffled = columnShuffle(original);
          assert.equal(simpleTableDataEqualsArrayData(table, shuffled), true);
      });
      it('should pass a simple table if source rows are shuffled after building the table', function () {
          var original = getRandomArrayData([10],1);
          var table = tableObjects.buildTableObject(original,'','','','Category_1',null,null,null,['Values_1'],['Values_1'],'',null);

          var shuffled = rowShuffle(original);
          assert.equal(simpleTableDataEqualsArrayData(table, shuffled), true);
      });
      it('should pass a simple table if source rows and columns are shuffled after building the table', function () {
          var original = getRandomArrayData([10],1);
          var table = tableObjects.buildTableObject(original,'','','','Category_1',null,null,null,['Values_1'],['Values_1'],'',null);

          var shuffled = columnShuffle(rowShuffle(original));
          assert.equal(simpleTableDataEqualsArrayData(table, shuffled), true);
      });

      it('should pass a simple table if table is built with a sort column', function () {
          var original = getRandomArrayData([10],2);
          var table = tableObjects.buildTableObject(original,'','','','Category_1',null,null,'Sort_1',['Values_1','Values_2'],['Values_1'],'',null);

          assert.equal(simpleTableDataEqualsArrayData(table, original), true);
      });
  });

  describe('#groupedTableDataEqualsArrayData()', function() {
      it('should pass a grouped table if table data matches', function () {
          var original = getRandomArrayData([5, 3],1);
          var table = tableObjects.buildTableObject(original,'','','','Category_1',null,'Category_2',null,['Values_1'],['Values_1'],'',null);

          assert.equal(groupedTableDataEqualsArrayData(table, original), true);
      });
      it('should fail a grouped table if table data does not match', function () {
          var original = getRandomArrayData([5, 3],1);
          var table = tableObjects.buildTableObject(original,'','','','Category_1',null,'Category_2',null,['Values_1'],['Values_1'],'',null);

          table.groups[1].data[3].values[0] = -10;

          assert.equal(groupedTableDataEqualsArrayData(table, original), false);
      });
      it('should pass a grouped table if source columns are shuffled after building the table', function () {
          var original = getRandomArrayData([5, 3],1);
          var table = tableObjects.buildTableObject(original,'','','','Category_1',null,'Category_2',null,['Values_1'],['Values_1'],'',null);

          var shuffled = columnShuffle(original);
          assert.equal(groupedTableDataEqualsArrayData(table, shuffled), true);
      });
      it('should pass a grouped table if source rows are shuffled after building the table', function () {
          var original = getRandomArrayData([5, 3],1);
          var table = tableObjects.buildTableObject(original,'','','','Category_1',null,'Category_2',null,['Values_1'],['Values_1'],'',null);

          var shuffled = rowShuffle(original);
          assert.equal(groupedTableDataEqualsArrayData(table, shuffled), true);
      });
      it('should pass a grouped table if source rows and columns are shuffled after building the table', function () {
          var original = getRandomArrayData([5, 3],1);
          var table = tableObjects.buildTableObject(original,'','','','Category_1',null,'Category_2',null,['Values_1'],['Values_1'],'',null);

          var shuffled = columnShuffle(rowShuffle(original));
          assert.equal(groupedTableDataEqualsArrayData(table, shuffled), true);
      });

      it('should pass a grouped table if table is built with a row sort column', function () {
          var original = getRandomArrayData([10],2);
          var table = tableObjects.buildTableObject(original,'','','','Category_1',null,'Category_2','Sort_1',['Values_1','Values_2'],['Values_1'],'',null);

          assert.equal(groupedTableDataEqualsArrayData(table, original), true);
      });

      it('should pass a grouped table if table is built with a column sort column', function () {
          var original = getRandomArrayData([10],2);
          var table = tableObjects.buildTableObject(original,'','','','Category_1',null,'Category_2',null,['Values_1','Values_2'],['Values_1'],'','Sort_2');

          assert.equal(groupedTableDataEqualsArrayData(table, original), true);
      });

      it('should pass a grouped table if table is built with a row sort column and a column sort column', function () {
          var original = getRandomArrayData([10],2);
          var table = tableObjects.buildTableObject(original,'','','','Category_1',null,'Category_2','Sort_1',['Values_1','Values_2'],['Values_1'],'','Sort_2');

          assert.equal(groupedTableDataEqualsArrayData(table, original), true);
      });
  });
});



function columnShuffle(table) {
    var order = _.shuffle(_.range(0, table[0].length));
    return _.map(table, function(row) { return _.map(order, function(index) { return row[index]; })})
}

function rowShuffle(table) {
    var order = _.shuffle(_.range(1, table.length));
    var shuffled = [table[0]];
    _.forEach(order, function(index) { shuffled.push(table[index])});
    return shuffled;
}

function simpleTableDataEqualsArrayData(table, original) {
    var columns = table.columns;
    var originalCatIndex = original[0].indexOf(table.category);

    var fullMatch = true;
    // for each of the table's data columns
    _.forEach(columns, function(column, index) {
        // get the index of the original column
        var originalIndex = original[0].indexOf(column);

        // for each of the table's items in that column
        _.forEach(table.data, function(item){
            var expectedValue = item.values[index];

            // search through the original table for that item
            var found = false;
            _.forEach(original, function(originalRow) {

                // and if you get a match
                if(originalRow[originalCatIndex] === item.category) {
                    if(originalRow[originalIndex].toString() !== item.values[index].toString()) {
                        fullMatch = false;
                    } else {
                        found = true;
                    }
                }
            });
            // if you didn't even find that item return false
            if(!found) { fullMatch = false; }
        })
    });

    return fullMatch;
}

function groupedTableDataEqualsArrayData(table, original) {
    var columns = table.columns;
    var originalCatIndex = original[0].indexOf(table.category);
    var originalGroupIndex = original[0].indexOf(table.group_column);

    var fullMatch = true;
    // for each group
    _.forEach(table.groups, function(group) {
        var groupName = group.group;

        _.forEach(columns, function(column, index) {
            // get the index of the original column
            var originalIndex = original[0].indexOf(column);

            // for each of the table's items in that column
            _.forEach(group.data, function(item) {
                var expectedValue = item.values[index];

                var found = false;
                _.forEach(original, function(originalRow) {

                    // and if you get a match
                    if(originalRow[originalCatIndex] === item.category) {
                        if(originalRow[originalGroupIndex] === groupName) {
                            if (originalRow[originalIndex].toString() !== item.values[index].toString()) {
                                fullMatch = false;
                            } else {
                                found = true;
                            }
                        }
                    }
                });
                // if you didn't even find that item return false
                if(!found) { fullMatch = false; }
            });
        });
    });
    return fullMatch;
}

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
       for(var i = 0; i < valueColumnCount; i++) { newRow.push(Math.floor(Math.random() * 1000) + 1) };
       return newRow;
    });

    _.forEach(rows, function(row) { data.push(row); });
    return data;
}

// Random selection of categories in non-alphabetic order
function getRandomCategories(size, listIndex) {
    var categories = [['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k'],
    ['alpha', 'bravo', 'charlie', 'delta', 'echo', 'foxtrot', 'golf', 'hotel', 'india', 'juliet', 'kilo'],
    ['lima', 'mike', 'november', 'oscar', 'papa', 'quebec', 'romeo', 'sierra', 'tango', 'uniform']];
    return _.shuffle(categories[listIndex].slice(0, size));
}