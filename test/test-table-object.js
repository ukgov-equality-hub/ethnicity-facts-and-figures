var chai = require('chai');
var assert = chai.assert;
var expect = chai.expect;

var dataTools = require('../application/src/js/charts/rd-data-tools');
var tableObjects = require('../application/src/js/cms/rd-table-objects');
var _ = require('../application/src/js/charts/vendor/underscore-min');

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

        describe('does include all parents even if not in data when a parent column is specified', function() {
            var title_value = 'title_value';
            var subtitle_value = 'subtitle_value';
            var footer_value = 'footer_value';
            var parent_column = '';
            var table = tableObjects.simpleTable(getSimpleArrayData(), title_value, subtitle_value, footer_value, 'Ethnicity', null, ['Value'], null, null);

        })
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

            // needs to be rewritten now extra parent rows are added
        });

        it('should always be child if parent specified as column that does not link to categories', function () {
            var PARENT = 'Minority status';
            var table = tableObjects.simpleTable(getSimpleArrayData(), null, null, null, 'Ethnicity', PARENT, ['Value'], null, null);

            // needs to be rewritten now extra parent rows are added
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

            var expectedRows = ['White', 'Other', 'Black', 'Mixed', 'Asian'];
            var expectedParentStatus = [true, true, false, false, false];

            var row_categories = _.map(table['data'], function(item) { return item['category']});
            var is_a_parent = _.map(table['data'], function(item) { return item['relationships']['is_parent']});

            expect(row_categories).to.deep.equal(expectedRows);
            expect(is_a_parent).to.deep.equal(expectedParentStatus);
        });

        it('should be a child if parent specified as column that does link to categories and it links to another row', function () {
            var PARENT = 'White or other';
            var table = tableObjects.simpleTable(getSimpleArrayData(), null, null, null, 'Ethnicity', PARENT, ['Value'], null, null);

            var expectedRows = ['White', 'Other', 'Black', 'Mixed', 'Asian'];
            var expectedChildStatus = [false, false, true, true, true];

            var row_categories = _.map(table['data'], function(item) { return item['category']});
            var is_a_child = _.map(table['data'], function(item) { return item['relationships']['is_child']});

            expect(row_categories).to.deep.equal(expectedRows);
            expect(is_a_child).to.deep.equal(expectedChildStatus);
        });

        it('should be a child if parent specified as column that partially links to categories and it does not link to another row', function () {
            var PARENT = 'Blue or other';
            var table = tableObjects.simpleTable(getSimpleArrayData(), null, null, null, 'Ethnicity', PARENT, ['Value'], null, null);

            assert.equal(table['data'][1]['relationships']['parent'], 'Blue');
            assert.equal(table['data'][1]['relationships']['is_parent'], false);
            assert.equal(table['data'][1]['relationships']['is_child'], true);
        });

        it('should have added parent row if parent row is not included in original data', function () {
            var PARENT_COLUMN = 'Blue or other';
            var table = tableObjects.simpleTable(getSimpleArrayData(), null, null, null, 'Ethnicity', PARENT_COLUMN, ['Value'], null, null);
            var categories = _.map(table.data, function(item) { return item.category; });

            expect(categories).to.include('Blue');
        });
    });
  });

  describe('#groupedTable()', function () {
      describe('basics', function() {
          it('should return an object', function () {
              var table = tableObjects.groupedTable(getGroupedArrayData(), 'title', '', '', 'Ethnicity', '', 'Socio-economic', ['Value'], '', ['']);
              assert.isObject(table);
          });

          it('should accept null values for non-essential columns', function () {
              var table = tableObjects.groupedTable(getGroupedArrayData(), null, null, null, 'Ethnicity', null, 'Socio-economic', ['Value'], null, null);
              assert.isObject(table);
          });

          it('should set basic information', function () {
              var EXAMPLE_HEADER = 'title';
              var EXAMPLE_SUBTITLE = 'subtitle';
              var EXAMPLE_FOOTER = 'footer';

              var table = tableObjects.groupedTable(getGroupedArrayData(), EXAMPLE_HEADER, EXAMPLE_SUBTITLE, EXAMPLE_FOOTER, 'Ethnicity', null, 'Socio-economic', ['Value'], null, null);
              assert.equal(table.header, EXAMPLE_HEADER);
              assert.equal(table.subtitle, EXAMPLE_SUBTITLE);
              assert.equal(table.footer, EXAMPLE_FOOTER);
          });
      });
      describe('data', function() {
          it('should set category information on main table object', function () {
              var CATEGORY = 'Ethnicity';
              var table = tableObjects.groupedTable(getGroupedArrayData(), null, null, null, CATEGORY, null, 'Socio-economic', ['Value'], null, null);

              assert.equal(table.category_caption, CATEGORY);
              var expectedCategories = ['White', 'BAME', 'Any Other'];
              var categories = _.map(table.data, function (item) {
                  return item.category;
              });
              expect(categories).to.have.deep.members(expectedCategories);
          });

          it('should set category information in group objects', function () {
              var CATEGORY = 'Ethnicity';
              var table = tableObjects.groupedTable(getGroupedArrayData(), null, null, null, CATEGORY, null, 'Socio-economic', ['Value'], null, null);

              var expectedCategories = ['White', 'BAME', 'Any Other'];
              _.forEach(table.groups, function (group) {
                  var categories = _.map(group.data, function (item) {
                      return item.category;
                  });
                  expect(categories).to.have.deep.members(expectedCategories);
              });
          });
      });

      describe('validate', function() {
          it('should identify if group data is incomplete', function () {
              var CATEGORY = 0;
              var GROUP = 2;
              var data_with_missing_bame_poor_point = [
                    ['White',         '0',          'Rich',           '10000',    '100020',     'Majority',        'White',          'Pink'],
                    ['White',         '0',          'Poor',           '5000',     '200020',     'Majority',        'White',          'Pink'],
                    ['BAME',          '2',          'Rich',           '4000',     '400020',     'Minority',        'Any Other',      'Any Other'],
                    ['Any Other',     '1',          'Rich',           '9000',     '300020',     'Minority',        'Any Other',      'Any Other'],
                    ['Any Other',     '1',          'Poor',           '4000',     '400020',     'Minority',        'Any Other',      'Any Other']
                ];

              var errors = tableObjects.validateGroupedData(data_with_missing_bame_poor_point, CATEGORY, GROUP);

              expect(errors).to.deep.equal([{'error':'missing data', 'category':'BAME', 'group': 'Poor'}]);

          });

          it('should identify if group data has duplicates', function () {
              var CATEGORY = 0;
              var GROUP = 2;
              var data_with_double_bame_rich_point = [
                    ['White',         '0',          'Rich',           '10000',    '100020',     'Majority',        'White',          'Pink'],
                    ['White',         '0',          'Poor',           '5000',     '200020',     'Majority',        'White',          'Pink'],
                    ['BAME',          '2',          'Rich',           '4000',     '400020',     'Minority',        'Any Other',      'Any Other'],
                    ['BAME',          '2',          'Poor',           '4000',     '400020',     'Minority',        'Any Other',      'Any Other'],
                    ['BAME',          '2',          'Rich',           '4000',     '400020',     'Minority',        'Any Other',      'Any Other'],
                    ['Any Other',     '1',          'Rich',           '9000',     '300020',     'Minority',        'Any Other',      'Any Other'],
                    ['Any Other',     '1',          'Poor',           '4000',     '400020',     'Minority',        'Any Other',      'Any Other']
                ];

              var errors = tableObjects.validateGroupedData(data_with_double_bame_rich_point, 0, 2);

              expect(errors).to.deep.equal([{'error':'duplicate data', 'category':'BAME', 'group': 'Rich'}]);
          });

          it('should identify all errors in data', function () {
              var CATEGORY = 0;
              var GROUP = 2;
              var data_with_double_bame_rich_point_no_white_poor_point = [
                    ['White',         '0',          'Rich',           '10000',    '100020',     'Majority',        'White',          'Pink'],
                    ['BAME',          '2',          'Rich',           '4000',     '400020',     'Minority',        'Any Other',      'Any Other'],
                    ['BAME',          '2',          'Poor',           '4000',     '400020',     'Minority',        'Any Other',      'Any Other'],
                    ['BAME',          '2',          'Rich',           '4000',     '400020',     'Minority',        'Any Other',      'Any Other'],
                    ['Any Other',     '1',          'Rich',           '9000',     '300020',     'Minority',        'Any Other',      'Any Other'],
                    ['Any Other',     '1',          'Poor',           '4000',     '400020',     'Minority',        'Any Other',      'Any Other']
                ];

              var errors = tableObjects.validateGroupedData(data_with_double_bame_rich_point_no_white_poor_point, 0, 2);

              expect(errors).to.deep.equal([{'error':'missing data', 'category':'White', 'group': 'Poor'},
                  {'error':'duplicate data', 'category':'BAME', 'group': 'Rich'}]);
          });
      });

      describe('row order', function() {
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

      describe('parents', function() {
          it('should have simple relationships if no parent column specified', function () {
            var PARENT = null;
            var table = tableObjects.groupedTable(getGroupedArrayData(),'title', '', '', 'Ethnicity', PARENT, 'Socio-economic', ['Value'], null, ['']);

            _.forEach(table['data'], function(row) {
                assert.equal(row['relationships']['is_parent'], false);
                assert.equal(row['relationships']['is_child'], false);
            });

            _.forEach(table['groups'], function(group) {
                _.forEach(group.data, function(cell) {
                    assert.equal(cell['relationships']['is_parent'], false);
                    assert.equal(cell['relationships']['is_child'], false);
                })
            })
        });

        it('should have parent of own category if no parent column specified', function () {
            var PARENT = null;
            var table = tableObjects.groupedTable(getGroupedArrayData(),'title', '', '', 'Ethnicity', PARENT, 'Socio-economic', ['Value'], null, ['']);

            var categories = _.map(table['data'], function(item) { return item['category']});
            var parents = _.map(table['data'], function(item) { return item['relationships']['parent']});
            expect(parents).to.deep.equal(categories);

            _.forEach(table['groups'], function(group) {
                parents = _.map(group['data'], function(item) { return item.category; });
                expect(parents).to.deep.equal(categories);
            })
        });

        it('should have parent if parent specified as column that does link to categories', function () {
            var PARENT = 'White or other';
            var table = tableObjects.groupedTable(getGroupedArrayData(),'title', '', '', 'Ethnicity', PARENT, 'Socio-economic', ['Value'], '[None]', ['']);

            var whiteOtherParents = ['White', 'Any Other', 'Any Other'];
            var parents = _.map(table['data'], function(item) { return item['relationships']['parent']});
            expect(parents).to.deep.equal(whiteOtherParents);

            _.forEach(table['groups'], function(group) {
                parents = _.map(group.data, function(item) { return item['relationships']['parent']});
                expect(parents).to.deep.equal(whiteOtherParents);
            });
        });

        it('should be a parent if parent specified as column that does link to categories and other rows declare it as their parent', function () {
            var PARENT = 'White or other';
            var table = tableObjects.groupedTable(getGroupedArrayData(),'title', '', '', 'Ethnicity', PARENT, 'Socio-economic', ['Value'], '[None]', ['']);

            var expectedParentStatus = [true, false, true];
            var is_a_parent = _.map(table['data'], function(item) { return item['relationships']['is_parent']});
            expect(is_a_parent).to.deep.equal(expectedParentStatus);

            _.forEach(table['groups'], function(group) {
                is_a_parent = _.map(group.data, function(item) { return item['relationships']['is_parent']});
                expect(is_a_parent).to.deep.equal(expectedParentStatus);
            });
        });

        it('should be a child if parent specified as column that does link to categories and it links to another row', function () {
            var PARENT = 'White or other';
            var table = tableObjects.groupedTable(getGroupedArrayData(),'title', '', '', 'Ethnicity', PARENT, 'Socio-economic', ['Value'], '[None]', ['']);

            var expectedChildStatus = [false, true, false];
            var is_a_child = _.map(table['data'], function(item) { return item['relationships']['is_child']});
            expect(is_a_child).to.deep.equal(expectedChildStatus);

            _.forEach(table['groups'], function(group) {
                is_a_child = _.map(group.data, function(item) { return item['relationships']['is_child']});
                expect(is_a_child).to.deep.equal(expectedChildStatus);
            });
        });
      });
  });
});



function getSimpleArrayData() {
  // These are all entirely fictitious numbers
  return  [
              ['Ethnicity',     'Value',   'Denominator', 'Order column', 'Minority status', 'White or other', 'Blue or other'],
              ['White',         '10000',    '100020',     '400',          'Majority',        'White'         , 'Blue'],
              ['Black',         '15000',    '100030',     '100',          'Minority',        'Other'         , 'Other'],
              ['Mixed',         '5000',     '200020',     '300',          'Minority',        'Other'         , 'Blue'],
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