var chai = require('chai');
var assert = chai.assert;
var expect = chai.expect;

var dataTools = require('../application/src/js/charts/rd-data-tools');
var tableObjects = require('../application/src/js/cms/rd-table-objects');
var utils = require('./utils-for-testing');

var _ = require('../application/src/js/charts/vendor/underscore-min');

// These are intense tests to see whether we can break table validity with randomly ordered data
// For tables we only need to test the table object

describe('test-table-ordering', function() {
  describe('#simpleTableDataEqualsArrayData()', function() {
      it('should pass a simple table if table data matches', function () {
          var original = utils.getRandomArrayData([10],1);
          var table = tableObjects.buildTableObject(original,'','','','Category_1',null,null,null,['Values_1'],['Values_1'],'',null);

          assert.equal(simpleTableDataEqualsArrayData(table, original), true);
      });
      it('should fail a simple table if table data does not match', function () {
          var original = utils.getRandomArrayData([10],1);
          var table = tableObjects.buildTableObject(original,'','','','Category_1',null,null,null,['Values_1'],['Values_1'],'',null);

          table.data[5].values[0] = '-10';

          assert.equal(simpleTableDataEqualsArrayData(table, original), false);
      });
      it('should pass a simple table if source columns are shuffled after building the table', function () {
          var original = utils.getRandomArrayData([10],1);
          var table = tableObjects.buildTableObject(original,'','','','Category_1',null,null,null,['Values_1'],['Values_1'],'',null);

          var shuffled = columnShuffle(original);
          assert.equal(simpleTableDataEqualsArrayData(table, shuffled), true);
      });
      it('should pass a simple table if source rows are shuffled after building the table', function () {
          var original = utils.getRandomArrayData([10],1);
          var table = tableObjects.buildTableObject(original,'','','','Category_1',null,null,null,['Values_1'],['Values_1'],'',null);

          var shuffled = rowShuffle(original);
          assert.equal(simpleTableDataEqualsArrayData(table, shuffled), true);
      });
      it('should pass a simple table if source rows and columns are shuffled after building the table', function () {
          var original = utils.getRandomArrayData([10],1);
          var table = tableObjects.buildTableObject(original,'','','','Category_1',null,null,null,['Values_1'],['Values_1'],'',null);

          var shuffled = columnShuffle(rowShuffle(original));
          assert.equal(simpleTableDataEqualsArrayData(table, shuffled), true);
      });

      it('should pass a simple table if table is built with a sort column', function () {
          var original = utils.getRandomArrayData([10],2);
          var table = tableObjects.buildTableObject(original,'','','','Category_1',null,null,'Sort_1',['Values_1','Values_2'],['Values_1'],'',null);

          assert.equal(simpleTableDataEqualsArrayData(table, original), true);
      });
  });

  describe('#groupedTableDataEqualsArrayData()', function() {
      it('should pass a grouped table if table data matches', function () {
          var original = utils.getRandomArrayData([5, 3],1);
          var table = tableObjects.buildTableObject(original,'','','','Category_1',null,'Category_2',null,['Values_1'],['Values_1'],'',null);

          assert.equal(groupedTableDataEqualsArrayData(table, original), true);
      });
      it('should fail a grouped table if table data does not match', function () {
          var original = utils.getRandomArrayData([5, 3],1);
          var table = tableObjects.buildTableObject(original,'','','','Category_1',null,'Category_2',null,['Values_1'],['Values_1'],'',null);

          table.groups[1].data[3].values[0] = -10;

          assert.equal(groupedTableDataEqualsArrayData(table, original), false);
      });
      it('should pass a grouped table if source columns are shuffled after building the table', function () {
          var original = utils.getRandomArrayData([5, 3],1);
          var table = tableObjects.buildTableObject(original,'','','','Category_1',null,'Category_2',null,['Values_1'],['Values_1'],'',null);

          var shuffled = columnShuffle(original);
          assert.equal(groupedTableDataEqualsArrayData(table, shuffled), true);
      });
      it('should pass a grouped table if source rows are shuffled after building the table', function () {
          var original = utils.getRandomArrayData([5, 3],1);
          var table = tableObjects.buildTableObject(original,'','','','Category_1',null,'Category_2',null,['Values_1'],['Values_1'],'',null);

          var shuffled = rowShuffle(original);
          assert.equal(groupedTableDataEqualsArrayData(table, shuffled), true);
      });
      it('should pass a grouped table if source rows and columns are shuffled after building the table', function () {
          var original = utils.getRandomArrayData([5, 3],1);
          var table = tableObjects.buildTableObject(original,'','','','Category_1',null,'Category_2',null,['Values_1'],['Values_1'],'',null);

          var shuffled = columnShuffle(rowShuffle(original));
          assert.equal(groupedTableDataEqualsArrayData(table, shuffled), true);
      });

      it('should pass a grouped table if table is built with a row sort column', function () {
          var original = utils.getRandomArrayData([10],2);
          var table = tableObjects.buildTableObject(original,'','','','Category_1',null,'Category_2','Sort_1',['Values_1','Values_2'],['Values_1'],'',null);

          assert.equal(groupedTableDataEqualsArrayData(table, original), true);
      });

      it('should pass a grouped table if table is built with a column sort column', function () {
          var original = utils.getRandomArrayData([10],2);
          var table = tableObjects.buildTableObject(original,'','','','Category_1',null,'Category_2',null,['Values_1','Values_2'],['Values_1'],'','Sort_2');

          assert.equal(groupedTableDataEqualsArrayData(table, original), true);
      });

      it('should pass a grouped table if table is built with a row sort column and a column sort column', function () {
          var original = utils.getRandomArrayData([10],2);
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
