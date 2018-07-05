var assert = require('assert');
var expect = require('chai').expect;
var dataTools = require('../application/src/js/charts/rd-data-tools');
var _ = require('../application/src/js/charts/vendor/underscore-min');

describe('rd-data-tools', function () {

    describe('#formatNumberWithDecimalPlaces()', function () {

        it('should round 1.26 up when formatting to one decimal place', function () {
            assert.equal(dataTools.formatNumberWithDecimalPlaces(1.26, 1), '1.3');
        })

        it('should round 1.344 down when formatting to one decimal place', function () {
            assert.equal(dataTools.formatNumberWithDecimalPlaces(1.344, 2), '1.34');
        })

        it('should round 1.55 up when formatting to one decimal place', function () {
            assert.equal(dataTools.formatNumberWithDecimalPlaces(1.55, 1), '1.6');
        })

        it('should add a trailing zero to 1.5 when formatting with 2 decimal places', function () {
            assert.equal(dataTools.formatNumberWithDecimalPlaces(1.5, 2), '1.50');
        })

        it('should round 1.6 up when formatting to zero decimal places', function () {
            assert.equal(dataTools.formatNumberWithDecimalPlaces(1.6, 0), '2');
        })

        it('should add a trailing zero to 2 when formatting to 1 decimal place', function () {
            assert.equal(dataTools.formatNumberWithDecimalPlaces(2, 1), '2.0');
        })

        it('should add two trailing zeros to 2 when formatting to two decimal places', function () {
            assert.equal(dataTools.formatNumberWithDecimalPlaces(2, 2), '2.00');
        })

        it('should add a comma to separate thousands for 12345678', function () {
            assert.equal(dataTools.formatNumberWithDecimalPlaces(12345678, 1), '12,345,678.0');
        })

        it('should remove the % sign from 10.2%', function () {
            assert.equal(dataTools.formatNumberWithDecimalPlaces('10.2%', 1), '10.2');
        })

        it('should not change a N/A string', function () {
            assert.equal(dataTools.formatNumberWithDecimalPlaces('N/A', 2), 'N/A');
        })

        it('should not change a * string', function () {
            assert.equal(dataTools.formatNumberWithDecimalPlaces('*', 2), '*');
        })

        it('should not change a blank string', function () {
            assert.equal(dataTools.formatNumberWithDecimalPlaces('', 2), '');
        })

    });

    describe('#decimalPlaces()', function () {
        it('should return 2 when the number value has 2dp', function () {
            assert.equal(dataTools.decimalPlaces(0.01), 2);
        });

        it('should return 0 when the number value is whole', function () {
            assert.equal(dataTools.decimalPlaces(100), 0);
        });

        it('should strip zeros when the value is numeric whole with zeros', function () {
            assert.equal(dataTools.decimalPlaces(1.00), 0);
        });

        it('should accept string values', function () {
            assert.equal(dataTools.decimalPlaces("100"), 0);
            assert.equal(dataTools.decimalPlaces("10.01"), 2);
        });

        it('should ignore a percent suffix', function () {
            assert.equal(dataTools.decimalPlaces("100%"), 0);
            assert.equal(dataTools.decimalPlaces("10.01%"), 2);
        });

        it('should ignore a space suffix', function () {
            assert.equal(dataTools.decimalPlaces("100 "), 0);
            assert.equal(dataTools.decimalPlaces("10.01 "), 2);
        });

        it('should return 0 for non-numeric', function () {
            assert.equal(dataTools.decimalPlaces("hello world"), 0);
            assert.equal(dataTools.decimalPlaces(""), 0);
        });
    });

    describe('#seriesDecimalPlaces', function () {

        it('should return 0 for empty series', function () {
            assert.equal(dataTools.seriesDecimalPlaces([]), 0);
        });

        it('should return 2 when number with greatest detail has 2dp', function () {
            assert.equal(dataTools.seriesDecimalPlaces(["0.01", "1", "1"]), 2);
        });
    });

    describe('#seriesCouldBeYear', function () {

        it('should return true for empty series', function () {
            assert.equal(dataTools.seriesCouldBeYear([]), true);
        });

        it('should return true if all whole values between 1950 and 2050', function () {
            assert.equal(dataTools.seriesCouldBeYear([1950, 2000, 2050]), true);
        });

        it('should accept string values', function () {
            assert.equal(dataTools.seriesCouldBeYear(["1950", "2000", "2050"]), true);
        });

        it('should return false if any values are fractions', function () {
            assert.equal(dataTools.seriesCouldBeYear([1950, 2000.1, 2050]), false);
            assert.equal(dataTools.seriesCouldBeYear(["1950", "2000.1", "2050"]), false);
        });

        it('should return false if any values above 2050', function () {
            assert.equal(dataTools.seriesCouldBeYear([1950, 2000, 2051]), false);
            assert.equal(dataTools.seriesCouldBeYear(["1950", "2000", "2051"]), false);
        });

        it('should return false if any values below 1950', function () {
            assert.equal(dataTools.seriesCouldBeYear([1949, 2000, 2050]), false);
            assert.equal(dataTools.seriesCouldBeYear(["1949", "2000", "2050"]), false);
        });
    });

    describe('#formatNumberWithDecimalPlaces()', function () {

        it('should add zeros for whole number with 2dp', function () {
            assert.equal(dataTools.formatNumberWithDecimalPlaces(1, 2), "1.00");
        });

        it('should crop extra dp for long fraction with 2dp', function () {
            assert.equal(dataTools.formatNumberWithDecimalPlaces(1.33333, 2), "1.33");
        });

        it('should accept string values', function () {
            assert.equal(dataTools.formatNumberWithDecimalPlaces("1", 2), "1.00");
            assert.equal(dataTools.formatNumberWithDecimalPlaces("1.33333", 2), "1.33");
        });

        it('should trim percentages', function () {
            assert.equal(dataTools.formatNumberWithDecimalPlaces("1%", 2), "1.00");
            assert.equal(dataTools.formatNumberWithDecimalPlaces("1.33333%", 2), "1.33");
        });

        it('should add commas to numbers greater than 1000', function () {
            assert.equal(dataTools.formatNumberWithDecimalPlaces(1000, 0), "1,000");
            assert.equal(dataTools.formatNumberWithDecimalPlaces(10000, 0), "10,000");
            assert.equal(dataTools.formatNumberWithDecimalPlaces(1000000, 0), "1,000,000");
        });

        it('should add commas to numbers greater than 1000 and keep decimal places', function () {
            assert.equal(dataTools.formatNumberWithDecimalPlaces(1000, 2), "1,000.00");
            assert.equal(dataTools.formatNumberWithDecimalPlaces(10000.23, 2), "10,000.23");
            assert.equal(dataTools.formatNumberWithDecimalPlaces(1000000.23456, 2), "1,000,000.23");
        });
    });

    describe('#uniqueDataInColumn', function () {

        it('should filter a column to unique values', function () {
            var rows = [
                ["a", 1, 2, 3],
                ["b", 1, 2, 3],
                ["c", 1, 2, 3],
                ["a", 1, 2, 3]];
            var values = dataTools.uniqueDataInColumn(rows, 0);
            assert.equal(values.length, 3);
            expect(values).to.have.same.members(["a", "b", "c"]);
        });

        it('should be able to find unique data in any column', function () {
            var rows = [
                ["a", "apple", 2, 3],
                ["b", "banana", 2, 3],
                ["c", "pear", 2, 3],
                ["a", "apple", 2, 3]];
            var values = dataTools.uniqueDataInColumn(rows, 1);
            assert.equal(values.length, 3);
            expect(values).to.have.same.members(["apple", "banana", "pear"]);
        });

        it('should sort results alphabetically', function () {
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

    describe('#uniqueDataInColumnOrdered', function () {

        it('should filter a column to unique values', function () {
            var rows = [
                ["a", 1, 2, 3],
                ["b", 1, 2, 3],
                ["c", 1, 2, 3],
                ["a", 1, 2, 3]];
            var values = dataTools.uniqueDataInColumnOrdered(rows, 0, 0);
            assert.equal(values.length, 3);
            expect(values).to.have.same.members(["a", "b", "c"]);
        });

        it('should be able to find unique data in any column', function () {
            var rows = [
                ["a", "apple", 2, 3],
                ["b", "banana", 2, 3],
                ["c", "pear", 2, 3],
                ["a", "apple", 2, 3]];
            var values = dataTools.uniqueDataInColumnOrdered(rows, 1, 0);
            assert.equal(values.length, 3);
            expect(values).to.have.same.members(["apple", "banana", "pear"]);
        });

        it('should sort results by a third column', function () {
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

    describe('#uniqueDataInColumnMaintainOrder', function () {

        it('should filter a column to unique values', function () {
            var rows = [
                ["a", 1, 2, 3],
                ["b", 1, 2, 3],
                ["c", 1, 2, 3],
                ["a", 1, 2, 3]];
            var values = dataTools.uniqueDataInColumnMaintainOrder(rows, 0);
            assert.equal(values.length, 3);
            expect(values).to.have.same.members(["a", "b", "c"]);
        });

        it('should be able to find unique data in any column', function () {
            var rows = [
                ["a", "apple", 2, 3],
                ["b", "banana", 2, 3],
                ["c", "pear", 2, 3],
                ["a", "apple", 2, 3]];
            var values = dataTools.uniqueDataInColumnMaintainOrder(rows, 1);
            assert.equal(values.length, 3);
            expect(values).to.have.same.members(["apple", "banana", "pear"]);
        });

        it('should maintain original data order', function () {
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

    describe('#textToData', function () {

        it('should split a string with tabs by tabs for columns and carriage returns for rows', function () {
            var text = "a\tb\tc\n" + "d\te\tf";
            var values = dataTools.textToData(text);

            assert.equal(values.length, 2);
            expect(values[0]).to.deep.equal(["a", "b", "c"]);
            expect(values[1]).to.deep.equal(["d", "e", "f"]);
        });

        it('should split a string without tabs by pipe for columns and carriage returns for rows', function () {
            var text = "a|b|c\n" + "d|e|f";
            var values = dataTools.textToData(text);

            assert.equal(values.length, 2);
            expect(values[0]).to.deep.equal(["a", "b", "c"]);
            expect(values[1]).to.deep.equal(["d", "e", "f"]);
        });

        it('should split a string with tabs and pipes by tabs for columns and carriage returns for rows', function () {
            var text = "a\tb|anomaly\tc\n" + "d|anomaly\te\tf";
            var values = dataTools.textToData(text);

            assert.equal(values.length, 2);
            expect(values[0]).to.deep.equal(["a", "b|anomaly", "c"]);
            expect(values[1]).to.deep.equal(["d|anomaly", "e", "f"]);
        });
    });

    describe('#hasHeader', function () {

        it('should return true when there is a specific value in the header', function () {
            var data = [['alpha', 'beta'], ['gamma', 'delta']];
            var found = dataTools.hasHeader('alpha', data);
            assert.equal(found, true);
        });

        it('should return false when there is not a specific value in the header', function () {
            var data = [['alpha', 'beta'], ['gamma', 'delta']];
            var found = dataTools.hasHeader('lemon', data);
            assert.equal(found, false);
        });
    });

    describe('#validateChart', function () {

        it('return an ethnicity error if there is no ethnicity column', function () {
            var data = [['a', 'b'], ['c', 'd']];
            var errors = dataTools.validateChart(data);
            var found = false;

            _.forEach(errors, function (error) {
                if (error.errorType === dataTools.ETHNICITY_ERROR) {
                    found = true;
                }
            });

            assert.equal(found, true);
        });

        it('should not return an ethnicity error if there is an ethnicity column', function () {
            var data = [['Ethnicity', 'b'], ['c', 'd']];
            var errors = dataTools.validateChart(data);
            var found = false;

            _.forEach(errors, function (error) {
                if (error.errorType === dataTools.ETHNICITY_ERROR) {
                    found = true;
                }
            });

            assert.equal(found, false);
        });

        it('return a value error if there is no value column', function () {
            var data = [['a', 'b'], ['c', 'd']];
            var errors = dataTools.validateChart(data);
            var found = false;

            _.forEach(errors, function (error) {
                if (error.errorType === dataTools.VALUE_ERROR) {
                    found = true;
                }
            });

            assert.equal(found, true);
        });

        it('should not return an value error if there is an value column', function () {
            var data = [['Ethnicity', 'Value'], ['White', '7'], ['BAME', '4']];
            var errors = dataTools.validateChart(data);
            var found = false;

            _.forEach(errors, function (error) {
                if (error === dataTools.VALUE_ERROR) {
                    found = true;
                }
            });

            assert.equal(found, false);
        });
    });

    describe('#nonNumericData', function () {

        it('should not return header data', function () {
            var data = [['Ethnicity', 'Value'], ['White', '7'], ['BAME', '4']];
            var columns = [0];
            var nonNumericValues = dataTools.nonNumericData(data, columns);

            assert.notEqual(nonNumericValues[0], 'Ethnicity');
            assert.equal(nonNumericValues.length, 2);
        });

        it('should not return integer data', function () {
            var data = [['Ethnicity', 'Value'], ['White', '7'], ['BAME', '4']];
            var columns = [1];
            var nonNumericValues = dataTools.nonNumericData(data, columns);

            assert.equal(nonNumericValues.length, 0)
        });

        it('should not return floating point data', function () {
            var data = [['Ethnicity', 'Value'], ['White', '7.5'], ['BAME', '4.2']];
            var columns = [1];
            var nonNumericValues = dataTools.nonNumericData(data, columns);

            assert.equal(nonNumericValues.length, 0)
        });

        it('should return non numeric data', function () {
            var data = [['Ethnicity', 'Value'], ['White', '7'], ['BAME', '4']];
            var columns = [0];
            var nonNumericValues = dataTools.nonNumericData(data, columns);

            assert.deepEqual(nonNumericValues, ['White', 'BAME'])
        });

        it('should return non numeric from multiple columns', function () {
            var data = [['Ethnicity', 'Age', 'Value'],
                ['White', '47', '12'],
                ['Black', '34', 'minimal'],
                ['Other', 'unclassified', '22']];
            var columns = [1, 2];
            var nonNumericValues = dataTools.nonNumericData(data, columns);

            assert.deepEqual(nonNumericValues, ['minimal', 'unclassified'])
        });
    });
});