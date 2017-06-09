function Table(table) {

  var module = this;
  var $table = table ?  table : $("#table");
  var $headings = $table.find('thead td'), ordering, cachedIndex;

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

    $.each($headings, function (index) {
      var $button = $(this).find('button');
      $button.click(function () {
        module.ordering(index);
        $(this).unbind().attr('class', 'sorting_' + ordering);
        dataTable.order( [index,  ordering]).draw()
      }.bind(this))
    });

    $headings.attr('width', (960 / $headings.length));
    $headings.removeAttr('style');
    $table.removeAttr('style');
  }

  return module;

}

$(document).ready(function () {

  var $tables = $(".table");

  $.each($tables, function() {
    new Table($(this));
  });

});
