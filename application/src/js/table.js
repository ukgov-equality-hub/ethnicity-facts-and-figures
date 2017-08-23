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

    if(browser && !browser.msie) {
      $.each($headings, function (index) {
        var $button = $(this).find('button');
        $button.on('click', function () {
          module.ordering(index);
          $(this).unbind().attr('class', 'sorting_' + ordering);
          dataTable.order( [index,  ordering]).draw()
        }.bind(this))
      });
    }

    $headings.attr('width', (960 / $headings.length));
    $headings.removeAttr('style').attr('style', 'width:' + 100 / $headings.length + '%');
    $table.removeAttr('style');

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
  