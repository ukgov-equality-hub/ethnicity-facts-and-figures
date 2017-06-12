function Table(table) {

  var module = this;
  var $table = table ?  table : $("#table");
  var groupLength = $table.find('thead tr').first().find('td').length - 1;
  var cellLength = $table.find('thead tr td').length;
  var $headings = $table.find('thead tr').last().find('td'), ordering, cachedIndex;

  this.ordering = function(index) {
    var firstClick = cachedIndex !== index;
    if(firstClick) {
      ordering = 'desc';
    } else {
      ordering = ordering !== 'asc' ? 'asc' : 'desc';
    }
    cachedIndex = index;
  }

  if($headings.length) {
    var dataTable = $table.DataTable({
      "paging":   false,
      "searching": false,
      "info":     false,
    });

    function createGroupedTables() {
      var $categories = $table.find('thead tr').first().children();
      var $labels = $table.find('thead tr').last().children();
      $.each($table.find('tbody tr'), function () {
        var $cells = $(this).find('td');
        var x = $cells.length / ($categories.length - 1);
        var lineIndexes = [];
        
        // create array containing indexes of tables cell requiring a dividing line
        for (var i = 1; i <= x; i++) {
          lineIndexes.push((x * i) - 1);
        }

        // pop last array item so that a line isn't added to right edge of table
        if (lineIndexes.length > 1) {
          lineIndexes.pop();
        }

        // add class to table cells numbers from lineIndex array
        for (var i = 0; i < lineIndexes.length; i++) {
          $($cells[lineIndexes[i]]).addClass('line');
          $($labels[lineIndexes[i] + 1]).addClass('line');
        }
      });
    }

    $.each($headings, function (index) {
      var $button = $(this).find('button');
      $button.click(function () {
        module.ordering(index);
        $(this).unbind().attr('class', 'sorting_' + ordering);
        dataTable.order( [index,  ordering]).draw()
        createGroupedTables();
      }.bind(this))
    });

    $headings.attr('width', (960 / $headings.length));
    $headings.removeAttr('style');
    $table.removeAttr('style');

    if($table.hasClass('grouped')) {
      createGroupedTables();
    }
  }

  return module;

}

$(document).ready(function () {

  var $tables = $(".table");

  $.each($tables, function() {
    new Table($(this));
  });

});
