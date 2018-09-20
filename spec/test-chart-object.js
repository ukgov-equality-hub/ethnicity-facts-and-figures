var chai = require('chai');
var assert = chai.assert;
var expect = chai.expect;

var dataTools = require('../application/src/js/charts/rd-data-tools');
var charts = require('../application/src/js/charts/rd-graph');
var chartObjects = require('../application/src/js/cms/rd-chart-objects');
var _ = require('../application/src/js/charts/vendor/underscore-min');
var utils = require('./utils-for-testing');

describe('rd-chart-objects', function () {
    describe('#simpleBarchart()', function () {

        it('should pass data in original order for simple barchart', function () {
            var original = utils.getRandomArrayDataForChart([10]);
            var chartObject = chartObjects.barchartObject(original, 'Category_1', null, null, null, '', '', '', getNumberFormat('none'));
            var barChart = charts.barchartHighchartObject(chartObject);

            expect(simpleBarchartHighchartSeriesEqualsOriginalData(barChart, original)).to.equal(true);
        });

        it('should fail a non equal simple barchart', function () {
            var original = utils.getRandomArrayDataForChart([10]);
            var chartObject = chartObjects.barchartObject(original, 'Category_1', null, null, null, '', '', '', getNumberFormat('none'));
            var barChart = charts.barchartHighchartObject(chartObject);

            // when we compare to alternate data
            var alternate = utils.getRandomArrayDataForChart([10]);

            expect(simpleBarchartHighchartSeriesEqualsOriginalData(barChart, alternate)).to.equal(false);
        });

        it('should fail a grouped barchart', function () {
            var original = utils.getRandomArrayDataForChart([10, 5]);
            var chartObject = chartObjects.barchartObject(original, 'Category_1', 'Category_2', null, null, '', '', '', getNumberFormat('none'));
            var barChart = charts.barchartHighchartObject(chartObject);

            expect(simpleBarchartHighchartSeriesEqualsOriginalData(barChart, original)).to.equal(false);
        });
    });

    describe('#groupedBarchart()', function () {

        it('should pass a grouped barchart against original data', function () {
            var original = utils.getRandomArrayDataForChart([10, 5]);
            var chartObject = chartObjects.barchartObject(original, 'Category_1', 'Category_2', null, null, '', '', '', getNumberFormat('none'));
            var barChart = charts.barchartHighchartObject(chartObject);

            expect(groupedBarchartHighchartSeriesEqualsOriginalData(barChart, original, 'Category_1', 'Category_2')).to.equal(true);
        });

        it('should fail a grouped barchart against alternate data', function () {
            var original = utils.getRandomArrayDataForChart([10, 5]);
            var chartObject = chartObjects.barchartObject(original, 'Category_1', 'Category_2', null, null, '', '', '', getNumberFormat('none'));
            var barChart = charts.barchartHighchartObject(chartObject);

            var alternate = utils.getRandomArrayDataForChart([10, 5]);

            expect(groupedBarchartHighchartSeriesEqualsOriginalData(barChart, alternate, 'Category_1', 'Category_2')).to.equal(false);
        });
    });

    describe('#linechart()', function () {

        it('should pass a linechart against original data', function () {
            var original = utils.getRandomArrayDataForChart([10, 5]);
            var chartObject = chartObjects.linechartObject(original, 'Category_1', 'Category_2', null, '', '', getNumberFormat('none'));
            var lineChart = charts.linechartHighchartObject(chartObject);

            expect(linechartHighchartSeriesEqualsOriginalData(lineChart, original, 'Category_1', 'Category_2')).to.equal(true);
        });

        it('should fail a linechart against alternate data', function () {
            var original = utils.getRandomArrayDataForChart([10, 5]);
            var chartObject = chartObjects.linechartObject(original, 'Category_1', 'Category_2', null, '', '', getNumberFormat('none'));
            var lineChart = charts.linechartHighchartObject(chartObject);

            var alternate = utils.getRandomArrayDataForChart([10, 5]);

            expect(linechartHighchartSeriesEqualsOriginalData(lineChart, alternate, 'Category_1', 'Category_2')).to.equal(false);
        });

        it('should pass a linechart sorted by a column', function () {
            var original = utils.getRandomArrayDataForChart([3, 10]);
            var chartObject = chartObjects.linechartObject(original, 'Category_1', 'Category_2', null, '', '', getNumberFormat('none'), 'Sort_2');
            var lineChart = charts.linechartHighchartObject(chartObject);

            expect(linechartHighchartSeriesEqualsOriginalData(lineChart, original, 'Category_1', 'Category_2')).to.equal(true);
        });

        it('should expect linechart x-axis to stay same after sorting', function () {
            var original = utils.getRandomArrayDataForChart([8, 8]);

            var chartObject = chartObjects.linechartObject(original, 'Category_1', 'Category_2', null, '', '', getNumberFormat('none'));
            var lineChart = charts.linechartHighchartObject(chartObject);

            var chartObjectSorted = chartObjects.linechartObject(original, 'Category_1', 'Category_2', null, '', '', getNumberFormat('none'), 'Sort_2');
            var lineChartSorted = charts.linechartHighchartObject(chartObject);

            // expect series to be shuffled
            expect(_.pluck(lineChart.series, 'name')).to.not.equal(_.pluck(lineChartSorted.series, 'name'));

            // but x-axis categories to remain the same
            expect(lineChart.xAxis.categories).to.deep.equal(lineChartSorted.xAxis.categories);
        });
    });
});

function simpleBarchartHighchartSeriesEqualsOriginalData(highchart, original) {
    var fullMatch = true;
    var valueColumn = original[0].indexOf('Value');
    _.forEach(highchart.series, function (s) {
        var originalCategory = s.name;
        var originalColumn = original[0].indexOf(originalCategory);
        var originalCategoryValues = _.map(original, function (row) {
            return row[originalColumn];
        });
        var found = false;

        _.forEach(s.data, function (item, index) {
            var actual = item.y;
            var expectedRowIndex = originalCategoryValues.indexOf(item.category);
            if (expectedRowIndex >= 0) {
                var expected = original[expectedRowIndex][valueColumn];
                if (actual !== expected) {
                    fullMatch = false;
                }
            } else {
                fullMatch = false;
            }
        })
    });
    return fullMatch;
}

function groupedBarchartHighchartSeriesEqualsOriginalData(highchart, original, categoryColumn, groupedColumn) {
    var fullMatch = true;
    var valueIndex = original[0].indexOf('Value');
    var categoryIndex = original[0].indexOf(categoryColumn);
    var groupIndex = original[0].indexOf(groupedColumn);
    var originalCategoryGroupValues = _.map(original, function (row) {
        return row[categoryIndex] + '|' + row[groupIndex]
    });

    _.forEach(highchart.series, function (s) {
        var group = s.name;

        _.forEach(s.data, function (item, index) {
            var actual = item.y;
            var category = item.category;

            var expectedRowIndex = originalCategoryGroupValues.indexOf(category + '|' + group);
            if (expectedRowIndex >= 0) {
                var expected = original[expectedRowIndex][valueIndex];
                if (actual !== expected) {
                    fullMatch = false;
                }
            } else {
                fullMatch = false;
            }
        })
    });
    return fullMatch;
}

function linechartHighchartSeriesEqualsOriginalData(highchart, original, categoryColumn, seriesColumn) {
    var fullMatch = true;
    var valueIndex = original[0].indexOf('Value');
    var categoryIndex = original[0].indexOf(categoryColumn);
    var seriesIndex = original[0].indexOf(seriesColumn);
    var originalCategoryGroupValues = _.map(original, function (row) {
        return row[categoryIndex] + '|' + row[seriesIndex]
    });

    _.forEach(highchart.series, function (s) {
        var series = s.name;

        _.forEach(highchart.xAxis.categories, function (category, index) {
            var actual = s.data[index];

            var expectedRowIndex = originalCategoryGroupValues.indexOf(category + '|' + series);
            if (expectedRowIndex >= 0) {
                var expected = original[expectedRowIndex][valueIndex];
                if (actual !== expected) {
                    fullMatch = false;
                }
            } else {
                fullMatch = false;
            }
        })
    });
    return fullMatch;
}


function getNumberFormat(format, prefix, suffix, min, max) {
    if (format === 'none' || format === null) {
        return {'multiplier': 1.0, 'prefix': '', 'suffix': '', 'min': '', 'max': ''}
    } else if (format === 'percent') {
        return {'multiplier': 1.0, 'prefix': '', 'suffix': '%', 'min': 0.0, 'max': 100.0}
    } else if (format === 'percent100') {
        return {'multiplier': 100.0, 'prefix': '', 'suffix': '%', 'min': 0.0, 'max': 100.0}
    } else if (format === 'other') {
        return {'multiplier': 1.0, 'prefix': prefix, 'suffix': suffix, 'min': min, 'max': max}
    }
}