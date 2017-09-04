var chai = require('chai');
var assert = chai.assert;
var expect = chai.expect;

var dataTools = require('../application/static/javascripts/rd-data-tools');
var tableObjects = require('../application/static/javascripts/rd-chart-objects');
var _ = require('../application/static/vendor/underscore-min');

describe('rd-chart-objects', function() {
  describe('#buildTableObject()', function() {
    it('should return a simple table if no group column', function() {

    });

    it('should return a grouped table if a group column is given', function() {

    });

    it('should accept null values for non-essential columns', function() {

    });
  });
});

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