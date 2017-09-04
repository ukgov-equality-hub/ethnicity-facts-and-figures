var chai = require('chai');
var assert = chai.assert;
var expect = chai.expect;

var dataTools = require('../application/static/javascripts/rd-data-tools');
var tableObjects = require('../application/static/javascripts/rd-table-objects');
var _ = require('../application/static/vendor/underscore-min');

describe('rd-table-objects', function() {
  describe('#buildTableObject()', function() {
    it('should return a simple table if no group column', function() {
      var tableWithNull = tableObjects.buildTableObject(getSimpleArrayData(),'title', '', '', 'Ethnicity', '', null, ['Value'], '', ['']);
      var tableWithEmpty = tableObjects.buildTableObject(getSimpleArrayData(),'title', '', '', 'Ethnicity', '', '', ['Value'], '', ['']);
      var tableWithNoneString = tableObjects.buildTableObject(getSimpleArrayData(),'title', '', '', 'Ethnicity', '', '[None]', ['Value'], '', ['']);
      assert.equal(tableWithNull.type, 'simple');
      assert.equal(tableWithEmpty.type, 'simple');
      assert.equal(tableWithNoneString.type, 'simple');
    });

    it('should return a grouped table if a group column is given', function() {
      var groupColumn = 'Socio-economic';
      var tableWithGroupColumn = tableObjects.buildTableObject(getGroupedArrayData(), 'title', '', '', 'Ethnicity', '', groupColumn, ['Value'], '', ['']);
      assert.equal(tableWithGroupColumn.type, 'grouped');
    });

    it('should accept null values for non-essential columns', function() {
      var table = tableObjects.buildTableObject(getSimpleArrayData(), null, null, null, 'Ethnicity', null, null, ['Value'], null, ['']);
      assert.isObject(table);
    });
  });

  describe('#simpleTable()', function() {
      describe('basics', function() {
        it('should return an object', function() {
          var table = tableObjects.simpleTable(getSimpleArrayData(),'title', '', '', 'Ethnicity', '', ['Value'], '', [''], null);
          assert.isObject(table);
        });

        it('should accept null values for non-essential columns', function() {
          var table = tableObjects.simpleTable(getSimpleArrayData(), null, null, null, 'Ethnicity', null, ['Value'], null, null);
          assert.isObject(table);
        });

        it('does set basic information', function() {
            var title_value = 'title_value';
            var subtitle_value = 'subtitle_value';
            var footer_value = 'footer_value';
            var table = tableObjects.simpleTable(getSimpleArrayData(), title_value, subtitle_value, footer_value, 'Ethnicity', null, ['Value'], null, null);

            assert.equal(table.header, title_value);
            assert.equal(table.subtitle, subtitle_value);
            assert.equal(table.footer, footer_value);
        });
      });

      describe('data', function() {
        it('should set category', function() {
            var CATEGORY = 'Ethnicity';

          var table = tableObjects.simpleTable(getSimpleArrayData(),'title', '', '', CATEGORY, '', ['Value'], '', [''], null);
          assert.equal(table.category_caption, CATEGORY);

          var expectedCategories = ['White', 'Black', 'Mixed', 'Asian', 'Other'];
          var categories = _.map(table['data'], function(item) { return item['category']});

          expect(categories).to.have.deep.members(expectedCategories);
        });

        it('should set right value columns', function() {
          var table = tableObjects.simpleTable(getSimpleArrayData(),'title', '', '', 'Ethnicity', '', ['Value', 'Denominator'], '', [''], null);
          // expect(table.columns).to.deep.equal(['Value', 'Denominator']);

          var expectedValues = ['10000','15000','5000','70000','9000'];
          var expectedDenominators = ['100020','100030','200020','200030', '300020'];

          var values = _.map(table['data'], function(item) { return item['values'][0]; });
          var denominators = _.map(table['data'], function(item) { return item['values'][1]; });

          expect(values).to.have.deep.members(expectedValues);
          expect(denominators).to.have.deep.members(expectedDenominators);
        });

        it('should accept null values for non-essential columns', function() {
          var table = tableObjects.simpleTable(getSimpleArrayData(), null, null, null, 'Ethnicity', null, ['Value'], null, null);
          assert.isObject(table);
        });

        it('does set basic information', function() {
            var title_value = 'title_value';
            var subtitle_value = 'subtitle_value';
            var footer_value = 'footer_value';
            var table = tableObjects.simpleTable(getSimpleArrayData(), title_value, subtitle_value, footer_value, 'Ethnicity', null, ['Value'], null, null);

            assert.equal(table.header, title_value);
            assert.equal(table.subtitle, subtitle_value);
            assert.equal(table.footer, footer_value);
        });
      });

  describe('order', function() {
    it('should maintain order if no sort column specified', function() {
        var ORDER = null;
        var table = tableObjects.simpleTable(getSimpleArrayData(), null, null, null, 'Ethnicity', null, ['Value'], ORDER, null);

        var originalOrder = ['White', 'Black', 'Mixed', 'Asian', 'Other'];
        var categories = _.map(table['data'], function(row) { return row['category']; });

        expect(categories).to.deep.equal(originalOrder);
    });

    it('should order by column if sort column specified', function() {
        var ORDER = 'Order column';
        var table = tableObjects.simpleTable(getSimpleArrayData(), null, null, null, 'Ethnicity', null, ['Value'], ORDER, null);

        var expectedSortOrder = ['Black', 'Asian', 'Mixed', 'White', 'Other'];
        var categories = _.map(table['data'], function(row) { return row['category']; });

        expect(categories).to.deep.equal(expectedSortOrder);
    });
  });

    describe('parents', function() {
        it('should have simple relationships if no parent column specified', function () {
            var PARENT = null;
            var table = tableObjects.simpleTable(getSimpleArrayData(), null, null, null, 'Ethnicity', PARENT, ['Value'], null, null);

            _.forEach(table['data'], function(item) {
                assert.equal(item['relationships']['is_parent'], false);
                assert.equal(item['relationships']['is_child'], false);
            });
        });

        it('should have parent of own category if no parent column specified', function () {
            var PARENT = null;
            var table = tableObjects.simpleTable(getSimpleArrayData(), null, null, null, 'Ethnicity', PARENT, ['Value'], null, null);

            var parents = _.map(table['data'], function(item) { return item['relationships']['parent']});
            var categories = _.map(table['data'], function(item) { return item['category']});

            expect(parents).to.deep.equal(categories);
        });

        it('should have parent if parent specified as column that does not link to categories', function () {
            var PARENT = 'Minority status';
            var table = tableObjects.simpleTable(getSimpleArrayData(), null, null, null, 'Ethnicity', PARENT, ['Value'], null, null);

            var minorityStatusParents = ['Majority', 'Minority', 'Minority', 'Minority', 'Minority'];
            var parents = _.map(table['data'], function(item) { return item['relationships']['parent']});

            expect(parents).to.deep.equal(minorityStatusParents);
        });

        it('should always be child if parent specified as column that does not link to categories', function () {
            var PARENT = 'Minority status';
            var table = tableObjects.simpleTable(getSimpleArrayData(), null, null, null, 'Ethnicity', PARENT, ['Value'], null, null);

            _.forEach(table['data'], function(row) {
                assert.equal(row['relationships']['is_parent'], false);
                assert.equal(row['relationships']['is_child'], true);
            });
        });

        it('should have parent if parent specified as column that does link to categories', function () {
            var PARENT = 'White or other';
            var table = tableObjects.simpleTable(getSimpleArrayData(), null, null, null, 'Ethnicity', PARENT, ['Value'], null, null);

            var whiteOtherParents = ['White', 'Other', 'Other', 'Other', 'Other'];
            var parents = _.map(table['data'], function(item) { return item['relationships']['parent']});

            expect(parents).to.deep.equal(whiteOtherParents);
        });

        it('should be a parent if parent specified as column that does link to categories and other rows declare it as their parent', function () {
            var PARENT = 'White or other';
            var table = tableObjects.simpleTable(getSimpleArrayData(), null, null, null, 'Ethnicity', PARENT, ['Value'], null, null);

            var expectedParentStatus = [true, false, false, false, true];
            var is_a_parent = _.map(table['data'], function(item) { return item['relationships']['is_parent']});

            expect(is_a_parent).to.deep.equal(expectedParentStatus);
        });

        it('should be a child if parent specified as column that does link to categories and it links to another row', function () {
            var PARENT = 'White or other';
            var table = tableObjects.simpleTable(getSimpleArrayData(), null, null, null, 'Ethnicity', PARENT, ['Value'], null, null);

            var expectedChildStatus = [false, true, true, true, false];
            var is_a_child = _.map(table['data'], function(item) { return item['relationships']['is_child']});

            expect(is_a_child).to.deep.equal(expectedChildStatus);
        });

        it('should be a child if parent specified as column that partially links to categories and it does not link to another row', function () {
            var PARENT = 'White or other or blue';
            var table = tableObjects.simpleTable(getSimpleArrayData(), null, null, null, 'Ethnicity', PARENT, ['Value'], null, null);

            assert.equal(table['data'][1]['relationships']['parent'], 'Blue');
            assert.equal(table['data'][1]['relationships']['is_parent'], false);
            assert.equal(table['data'][1]['relationships']['is_child'], true);
        });
    });
  });

  describe('#groupedTable()', function () {
    it('should return an object', function() {
      var table = tableObjects.groupedTable(getGroupedArrayData(),'title', '', '', 'Ethnicity', '', 'Socio-economic', ['Value'], '', ['']);
      assert.isObject(table);
    });

    it('should accept null values for non-essential columns', function() {
      var table = tableObjects.groupedTable(getGroupedArrayData(),null, null, null, 'Ethnicity', null, 'Socio-economic', ['Value'], null, null);
      assert.isObject(table);
    });

    it('should return rows sorted alphetically if null order specified', function() {
        var order_column = null;
        var table = tableObjects.groupedTable(getGroupedArrayData(),'title', '', '', 'Ethnicity', '', 'Socio-economic', ['Value'], order_column, ['']);

        assert.equal(table['data'][0]['category'], 'Any Other');
        assert.equal(table['data'][1]['category'], 'BAME');
        assert.equal(table['data'][2]['category'], 'White');
    });

    it('should return rows sorted by alternative column if specified', function() {
        var order_column = 'Alternate';
        var table = tableObjects.groupedTable(getGroupedArrayData(),'title', '', '', 'Ethnicity', '', 'Socio-economic', ['Value'], order_column, ['']);

        assert.equal(table['data'][0]['category'], 'White');
        assert.equal(table['data'][1]['category'], 'Any Other');
        assert.equal(table['data'][2]['category'], 'BAME');
    });

    it('should return rows in original order if [None] specified', function() {
        var order_column = '[None]';
        var table = tableObjects.groupedTable(getGroupedArrayData(),'title', '', '', 'Ethnicity', '', 'Socio-economic', ['Value'], order_column, ['']);

        assert.equal(table['data'][0]['category'], 'White');
        assert.equal(table['data'][1]['category'], 'BAME');
        assert.equal(table['data'][2]['category'], 'Any Other');
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
            ['Ethnicity',     'Alternate',  'Socio-economic', 'Value',   'Denominator'],
            ['White',         '0',          'Rich',           '10000',    '100020'    ],
            ['White',         '0',          'Poor',           '5000',     '200020'    ],
            ['BAME',          '2',          'Rich',           '9000',     '300020'    ],
            ['BAME',          '2',          'Poor',           '4000',     '400020'    ],
            ['Any Other',     '1',          'Rich',           '9000',     '300020'    ],
            ['Any Other',     '1',          'Poor',           '4000',     '400020'    ]
         ];
}