$(document).ready(function () {

  // demo highcharts configuaration for bar charts

  if($(".chart").length) {
    Highcharts.chart('chart', {
      colors: ['red'],
      chart: {
        type: 'bar',
        marginBottom: true,
        marginLeft: 160
      },
      title: {
        text: ''
      },
      xAxis: {
        categories: ['Indian', 'Pakistani', 'Other Asian', 'Black', 'Chinese', 'Mixed', 'White', 'Other'],
        title: {
          text: null
        }
      },
      yAxis: {
        min: 0,
        max: 15,
        title: {
          text: 'unemployment rate (%)',
          align: 'high'
        },
        labels: {
          overflow: 'justify'
        }
      },
      labels: {
        style: {
          fontFamily: "nta"
        }
      },
      plotOptions: {
        bar: {
          pointWidth: 40, 
          dataLabels: {
            enabled: true,
            color: '#000',
            align: 'left',
            style: {
              textOutline: false,
              fontSize: "16px",
              fontFamily: "nta",
              fontWeight: "400"
            },
            formatter: function() {return this.y + '%'},
            inside: true,
            rotation: 0
          }
        }
      },
      credits: {
        enabled: false
      },
      series: [{
        name: 'unemployment rate',
        data: [10, 10, 5, 10, 10, 10, 5, 9]
      }]
    });
  }

});
// = require_tree ./govuk

(function(){
  // stop everything being called twice if loaded with turbolinks and page load.
  var initialised = false;

  function accordions(){
    var accordionsAllOpen = false;

    $(".accordion__header").click(function(e){
        var body = $(e.currentTarget).parent().find(".accordion__body")
        $(e.currentTarget).find(".plus-minus-icon").toggleClass("open")
        $(body).toggle()
    })


    $(".accordion__body").hide()

    $("#accordion-all-control").click(function(){
    a= $(".plus-minus-icon").filter(function(_,icon) {
        return icon.classList.contains("open")
      })

      if(a.size() == 0){
        console.log("called")
        $(".plus-minus-icon").addClass("open")
        $("#accordion-all-control").text("Close all")
        $(".accordion__body").show()
      } else {
        $(".plus-minus-icon").removeClass("open")
        $("#accordion-all-control").text("Open all")
        $(".accordion__body").hide()
      }
    })
  }
  $(document).ready(accordions)
}())

$(document).ready(function () {
  var $details = $('details');
  $details.each(function () {
    $(this).after('<div class="print-node"><h3 class="heading-small">' + $(this).find('span').html() + '</h3><div>' + $(this).find('.panel').html() + '</div></div>')
  });

  $('.js--print').click(function (e) {
    e.preventDefault();
    window.print();
  });
});
// Stageprompt 2.0.1
//
// See: https://github.com/alphagov/stageprompt
//
// Stageprompt allows user journeys to be described and instrumented
// using data attributes.
//
// Setup (run this on document ready):
//
//   GOVUK.performance.stageprompt.setupForGoogleAnalytics();
//
// Usage:
//
//   Sending events on page load:
//
//     <div id="wrapper" class="service" data-journey="pay-register-birth-abroad:start">
//         [...]
//     </div>
//
//   Sending events on click:
//
//     <a class="help-button" href="#" data-journey-click="stage:help:info">See more info...</a>

;(function (global) {
  'use strict'

  var $ = global.jQuery
  var GOVUK = global.GOVUK || {}

  GOVUK.performance = GOVUK.performance || {}

  GOVUK.performance.stageprompt = (function () {
    var setup, setupForGoogleAnalytics, splitAction

    splitAction = function (action) {
      var parts = action.split(':')
      if (parts.length <= 3) return parts
      return [parts.shift(), parts.shift(), parts.join(':')]
    }

    setup = function (analyticsCallback) {
      var journeyStage = $('[data-journey]').attr('data-journey')
      var journeyHelpers = $('[data-journey-click]')

      if (journeyStage) {
        analyticsCallback.apply(null, splitAction(journeyStage))
      }

      journeyHelpers.on('click', function (event) {
        analyticsCallback.apply(null, splitAction($(this).data('journey-click')))
      })
    }

    setupForGoogleAnalytics = function () {
      setup(GOVUK.performance.sendGoogleAnalyticsEvent)
    }

    return {
      setup: setup,
      setupForGoogleAnalytics: setupForGoogleAnalytics
    }
  }())

  GOVUK.performance.sendGoogleAnalyticsEvent = function (category, event, label) {
    global._gaq.push(['_trackEvent', category, event, label, undefined, true])
  }

  global.GOVUK = GOVUK
})(window)

$(document).ready(function () {
  var $stickies = $(".sticky-js");
  $.each($stickies, function () {
    var stickyPosition = parseInt($(this).position().top);
    $(window).scroll(function () {
      var scrollTop = $(window).scrollTop();
      if (scrollTop >= stickyPosition) {
        $(this).addClass('sticky-js-fixed');
      } else {
        $(this).removeClass('sticky-js-fixed');
      }
    }.bind(this));
  });
});
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
    $headings.removeAttr('style').attr('style', 'width:' + 100 / $headings.length + '%');
    $table.removeAttr('style');

    if($table.hasClass('grouped')) {
      createGroupedTables();
    }

    $table.find('tbody')
      .on('touchstart', function(e) {
        yPos = e.originalEvent.layerY;
        console.info(yPos);
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

  var $tables = $(".table");

  $.each($tables, function() {
    new Table($(this));
  });

});

$(document).ready(function () {
  var expanded, $headers = $('.accordion__header');
  $('.accordion-link--expand-all').each(function () {
    $(this).click(function (e) {
      e.preventDefault();
      $(this).text(expanded ? 'Open all' : 'Close all');
      expanded = expanded ? false : true;
      $.each($headers, function(index, header){
        if(expanded) {
          if (!$(header).find('.plus-minus-icon').hasClass('open')) {
            $(header).click();
          }
        } else {
          if ($(header).find('.plus-minus-icon').hasClass('open')) {
            $(header).click();
          }
        }
      });
    })
  })

});