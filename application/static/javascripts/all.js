
/*
  Accordion

  This allows a collection of sections to be collapsed by default,
  showing only their headers. Sections can be exanded or collapsed
  individually by clicking their headers. An "Open all" button is
  also added to the top of the accordion, which switches to "Close all"
  when all the sections are expanded.

  The state of each section is saved to the DOM via the `aria-expanded`
  attribute, which also provides accessibility.

*/


function Accordion(element) {
  this.element = element
  this.sections = []
  this.setup()
}

function AccordionSection(element, accordion) {
  this.element = element
  this.accordion = accordion
  this.setup()
}

Accordion.prototype.setup = function() {

  var accordion_sections = this.element.querySelectorAll('.accordion-section')

  for (accordion_section of accordion_sections) {
    this.sections.push(new AccordionSection(accordion_section, this))
  }

  var accordion_controls = document.createElement('div')
  accordion_controls.setAttribute('class', 'accordion-controls')

  var open_or_close_all_button = document.createElement('button')
  open_or_close_all_button.textContent = 'Open all'
  open_or_close_all_button.setAttribute('class', 'accordion-expand-all')
  open_or_close_all_button.setAttribute('aria-expanded', 'false')

  open_or_close_all_button.addEventListener('click', this.openOrCloseAll.bind(this))

  accordion_controls.appendChild(open_or_close_all_button)

  this.element.insertBefore(accordion_controls, this.element.firstChild)
  this.element.classList.add('with-js')
}

Accordion.prototype.openOrCloseAll = function(event) {

  var open_or_close_all_button = event.target
  var now_expanded = !(open_or_close_all_button.getAttribute('aria-expanded') == 'true')

  for (section of this.sections) {
    section.setExpanded(now_expanded)
  }

  this.setOpenCloseButtonExpanded(now_expanded)

}


Accordion.prototype.setOpenCloseButtonExpanded = function(expanded) {

  var open_or_close_all_button = this.element.querySelector('.accordion-expand-all')

  var new_button_text = expanded ? "Close all" : "Open all"
  open_or_close_all_button.setAttribute('aria-expanded', expanded)
  open_or_close_all_button.textContent = new_button_text

}

Accordion.prototype.updateOpenAll = function() {

  var sectionsCount = this.sections.length

  var openSectionsCount = this.sections.filter(function(section) { return section.expanded() }).length

  if (sectionsCount == openSectionsCount) {
    this.setOpenCloseButtonExpanded(true)
  } else {
    this.setOpenCloseButtonExpanded(false)
  }

}

AccordionSection.prototype.setup = function() {
  this.element.setAttribute('aria-expanded', 'false')

  var header = this.element.querySelector('.accordion-section-header')
  header.addEventListener('click', this.toggleExpanded.bind(this))

  var icon = document.createElement('span')
  icon.setAttribute('class', 'icon')

  header.appendChild(icon)
}

AccordionSection.prototype.toggleExpanded = function(){
  var expanded = (this.element.getAttribute('aria-expanded') == 'true')

  this.setExpanded(!expanded)
  this.accordion.updateOpenAll()
}

AccordionSection.prototype.expanded = function() {
  return (this.element.getAttribute('aria-expanded') == 'true')
}

AccordionSection.prototype.setExpanded = function(expanded) {
  this.element.setAttribute('aria-expanded', expanded)
}


document.addEventListener('DOMContentLoaded', function() {

  var accordions = document.querySelectorAll('.accordion')

  for (accordion of accordions) {
    new Accordion(accordion)
  }

})
// = require_tree ./govuk


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
  