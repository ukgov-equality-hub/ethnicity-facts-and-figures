var assert = require('assert');
var expect = require('chai').expect;
var dataTools = require('../application/static/javascripts/rd-data-tools');

describe('rd-data-tools', function() {
  describe('#decimalPlaces()', function() {
    it('should return 2 when the number value has 2dp', function() {
      assert.equal(dataTools.decimalPlaces(0.01), 2);
    });

    it('should return 0 when the number value is whole', function() {
      assert.equal(dataTools.decimalPlaces(100), 0);
    });

    it('should strip zeros when the value is numeric whole with zeros', function() {
      assert.equal(dataTools.decimalPlaces(1.00), 0);
    });

    it('should accept string values', function() {
      assert.equal(dataTools.decimalPlaces("100"), 0);
      assert.equal(dataTools.decimalPlaces("10.01"), 2);
    });

    it('should ignore a percent suffix', function() {
      assert.equal(dataTools.decimalPlaces("100%"), 0);
      assert.equal(dataTools.decimalPlaces("10.01%"), 2);
    });

    it('should return 0 for non-numeric', function() {
      assert.equal(dataTools.decimalPlaces("hello world"), 0);
      assert.equal(dataTools.decimalPlaces(""), 0);
    });
  });

  describe('#seriesDecimalPlaces', function() {

    it('should return 0 for empty series', function() {
      assert.equal(dataTools.seriesDecimalPlaces([]), 0);
    });

    it('should return 2 when number with greatest detail has 2dp', function() {
      assert.equal(dataTools.seriesDecimalPlaces(["0.01", "1", "1"]), 2);
    });
  });

  describe('#seriesCouldBeYear', function() {

    it('should return true for empty series', function() {
      assert.equal(dataTools.seriesCouldBeYear([]), true);
    });

    it('should return true if all whole values between 1950 and 2050', function() {
      assert.equal(dataTools.seriesCouldBeYear([1950, 2000, 2050]), true);
    });

    it('should accept string values', function() {
      assert.equal(dataTools.seriesCouldBeYear(["1950", "2000", "2050"]), true);
    });

    it('should return false if any values are fractions', function() {
      assert.equal(dataTools.seriesCouldBeYear([1950, 2000.1, 2050]), false);
      assert.equal(dataTools.seriesCouldBeYear(["1950", "2000.1", "2050"]), false);
    });

    it('should return false if any values above 2050', function() {
      assert.equal(dataTools.seriesCouldBeYear([1950, 2000, 2051]), false);
      assert.equal(dataTools.seriesCouldBeYear(["1950", "2000", "2051"]), false);
    });

    it('should return false if any values below 1950', function() {
      assert.equal(dataTools.seriesCouldBeYear([1949, 2000, 2050]), false);
      assert.equal(dataTools.seriesCouldBeYear(["1949", "2000", "2050"]), false);
    });
  });

  describe('#formatNumberWithDecimalPlaces()', function() {

    it('should add zeros for whole number with 2dp', function() {
      assert.equal(dataTools.formatNumberWithDecimalPlaces(1, 2), "1.00");
    });

    it('should crop extra dp for long fraction with 2dp', function() {
      assert.equal(dataTools.formatNumberWithDecimalPlaces(1.33333, 2), "1.33");
    });

    it('should accept string values', function() {
      assert.equal(dataTools.formatNumberWithDecimalPlaces("1", 2), "1.00");
      assert.equal(dataTools.formatNumberWithDecimalPlaces("1.33333", 2), "1.33");
    });

    it('should trim percentages', function() {
      assert.equal(dataTools.formatNumberWithDecimalPlaces("1%", 2), "1.00");
      assert.equal(dataTools.formatNumberWithDecimalPlaces("1.33333%", 2), "1.33");
    });

    it('should add commas to numbers greater than 1000', function() {
      assert.equal(dataTools.formatNumberWithDecimalPlaces(1000, 0), "1,000");
      assert.equal(dataTools.formatNumberWithDecimalPlaces(10000, 0), "10,000");
      assert.equal(dataTools.formatNumberWithDecimalPlaces(1000000, 0), "1,000,000");
    });

    it('should add commas to numbers greater than 1000 and keep decimal places', function() {
      assert.equal(dataTools.formatNumberWithDecimalPlaces(1000, 2), "1,000.00");
      assert.equal(dataTools.formatNumberWithDecimalPlaces(10000.23, 2), "10,000.23");
      assert.equal(dataTools.formatNumberWithDecimalPlaces(1000000.23456, 2), "1,000,000.23");
    });
  });

  describe('#uniqueDataInColumn', function() {

    it('should filter a column to unique values', function() {
      var rows = [
          ["a", 1, 2, 3],
          ["b", 1, 2, 3],
          ["c", 1, 2, 3],
          ["a", 1, 2, 3]];
      var values = dataTools.uniqueDataInColumn(rows, 0);
      assert.equal(values.length, 3);
      expect(values).to.have.same.members(["a", "b", "c"]);
    });

    it('should be able to find unique data in any column', function() {
      var rows = [
          ["a", "apple", 2, 3],
          ["b", "banana", 2, 3],
          ["c", "pear", 2, 3],
          ["a", "apple", 2, 3]];
      var values = dataTools.uniqueDataInColumn(rows, 1);
      assert.equal(values.length, 3);
      expect(values).to.have.same.members(["apple", "banana", "pear"]);
    });

    it('should sort results alphabetically', function() {
      var rows = [
          ["a", "pear", 2, 3],
          ["b", "apple", 2, 3],
          ["c", "banana", 2, 3],
          ["a", "pear", 2, 3]];
      var values = dataTools.uniqueDataInColumn(rows, 1);
      assert.equal(values.length, 3);
      expect(values).to.deep.equal(["apple", "banana", "pear"]);
    });
  });

  describe('#uniqueDataInColumnOrdered', function() {

    it('should filter a column to unique values', function() {
      var rows = [
          ["a", 1, 2, 3],
          ["b", 1, 2, 3],
          ["c", 1, 2, 3],
          ["a", 1, 2, 3]];
      var values = dataTools.uniqueDataInColumnOrdered(rows, 0, 0);
      assert.equal(values.length, 3);
      expect(values).to.have.same.members(["a", "b", "c"]);
    });

    it('should be able to find unique data in any column', function() {
      var rows = [
          ["a", "apple", 2, 3],
          ["b", "banana", 2, 3],
          ["c", "pear", 2, 3],
          ["a", "apple", 2, 3]];
      var values = dataTools.uniqueDataInColumnOrdered(rows, 1, 0);
      assert.equal(values.length, 3);
      expect(values).to.have.same.members(["apple", "banana", "pear"]);
    });

    it('should sort results by a third column', function() {
      var rows = [
          ["a", "pear", 2, 3],
          ["b", "apple", 1, 3],
          ["c", "banana", 4, 3],
          ["a", "pear", 3, 3]];
      var values = dataTools.uniqueDataInColumnOrdered(rows, 1, 2);
      assert.equal(values.length, 3);
      expect(values).to.deep.equal(["apple", "pear", "banana"]);
    });
  });

  describe('#uniqueDataInColumnMaintainOrder', function() {

    it('should filter a column to unique values', function() {
      var rows = [
          ["a", 1, 2, 3],
          ["b", 1, 2, 3],
          ["c", 1, 2, 3],
          ["a", 1, 2, 3]];
      var values = dataTools.uniqueDataInColumnMaintainOrder(rows, 0);
      assert.equal(values.length, 3);
      expect(values).to.have.same.members(["a", "b", "c"]);
    });

    it('should be able to find unique data in any column', function() {
      var rows = [
          ["a", "apple", 2, 3],
          ["b", "banana", 2, 3],
          ["c", "pear", 2, 3],
          ["a", "apple", 2, 3]];
      var values = dataTools.uniqueDataInColumnMaintainOrder(rows, 1);
      assert.equal(values.length, 3);
      expect(values).to.have.same.members(["apple", "banana", "pear"]);
    });

    it('should maintain original data order', function() {
      var rows = [
          ["a", "pear", 2, 3],
          ["b", "apple", 1, 3],
          ["c", "banana", 4, 3],
          ["a", "pear", 3, 3]];
      var values = dataTools.uniqueDataInColumnMaintainOrder(rows, 1);
      assert.equal(values.length, 3);
      expect(values).to.deep.equal(["pear", "apple", "banana"]);
    });
  });
});