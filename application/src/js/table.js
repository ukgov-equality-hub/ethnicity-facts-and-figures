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
      "info":     false
    }),
    offset = 0, yPos, scrolling;

    function createGroupedTables() {
      var $categories = $table.find('thead tr').first().children();
      var $labels = $table.find('thead tr').last().children();

      $.each($table.find('tbody tr'), function () {
        var $cells = $(this).find('td');
        var $columns = parseInt($table.attr('columns'));
        var x = $categories.length - 1;
        var lineIndexes = [];

        // create array containing indexes of tables cell requiring a dividing line
        for (var i = 1; i <= x; i++) {
          lineIndexes.push((i * $columns) - 1);
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

    if(browser && !browser.msie) {
      $.each($headings, function (index) {
        var $button = $(this).find('button');
        $button.on('click', function () {
          module.ordering(index);
          $(this).unbind().attr('class', 'sorting_' + ordering);
          dataTable.order( [index,  ordering]).draw()
          createGroupedTables();
        }.bind(this))
      });
    }

    $headings.attr('width', (960 / $headings.length));
    $headings.removeAttr('style').attr('style', 'width:' + 100 / $headings.length + '%');
    $table.removeAttr('style');

    if($table.hasClass('grouped')) {
      createGroupedTables();
    }

    $table.find('tbody')
      .on('touchstart', function(e) {
        yPos = e.originalEvent.layerY;
        if(e.touches.length > 1) {
          $(this).removeClass('scrolling--disabled');
          $('body')
            .bind('touchmove', function(e){e.preventDefault()})
        }
        else {
          $(this).addClass('scrolling--disabled');
        }
      })
      .on('touchend', function(e) {
        $(this).removeClass('scrolling--disabled');
        $('body').unbind('touchmove');
      })
      .on('touchmove', function(e) {
        if(e.touches.length > 1) {
          yPos > e.originalEvent.layerY ? offset++ : offset--;
          if(scrolling == null) {
            scrolling = setTimeout(function() {
              scrolling = null;
              $(this).scrollTop(offset);
            }.bind(this), 30);
          }
        }
      })
  }

  return module;

}

$(document).ready(function () {

  var browser = typeof bowser !== 'undefined' ? bowser : null;
  
  if(browser) {
    var osversion = parseFloat(browser.osversion);

    if(browser.mac && osversion >= 10.6 && osversion <= 10.8 || browser.msie) {
      $("table").each(function () {
        if($(this).hasClass('cropped')) {
          $(this).addClass("table-fix");
        }
      });
    }
  }

  var $tables = $(".table");

  $.each($tables, function() {
    if (!$(this).hasClass('no-sort')) {
      new Table($(this));
    }
  });

});
  