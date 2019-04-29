function SortableTable(table, header_table, options) {

  // First do feature detection for required API methods
  if (
    document.querySelectorAll &&
    document.querySelector &&
    window.NodeList
    ) {

      this.table = table;
      this.header_table = header_table;
      this.setupOptions(options);
      this.createHeadingButtons();
      this.createStatusBox();

    }
};

SortableTable.prototype.setupOptions = function(options) {
    options = options || {};
    options.statusMessage = options.statusMessage || 'Sort by %heading% (%direction%)';
    options.ascendingText = options.ascendingText || 'ascending';
    options.descendingText = options.descendingText || 'descending';
    this.options = options;
};

SortableTable.prototype.createHeadingButtons = function() {

  var header_rows = this.table.querySelectorAll('thead tr')

  for (var j = 0; j < header_rows.length; j++) {

    var headings = header_rows[j].querySelectorAll('th')
    var heading;

    for(var i = 0; i < headings.length; i++) {
        heading = headings[i];
        if(heading.getAttribute('aria-sort')) {
            this.createHeadingButton(heading, i);
        }
    }

  };

  if (this.header_table) {

    var header_rows = this.header_table.querySelectorAll('thead tr')

    for (var j = 0; j < header_rows.length; j++) {


      var headings = header_rows[j].querySelectorAll('th')
      var heading;

      for(var i = 0; i < headings.length; i++) {
          heading = headings[i];
          if(heading.getAttribute('aria-sort')) {
              this.createHeadingButton(heading, i);
          }
      }


    };


  }
};

SortableTable.prototype.createHeadingButton = function(heading, i) {
    var text = heading.textContent;
    var button = document.createElement('button')
    button.setAttribute('type', 'button')
    button.setAttribute('data-index', i)
    button.setAttribute('class', 'govuk-button eff-button--link eff-button--sort')
    button.textContent = text
    button.addEventListener('click', this.sortButtonClicked.bind(this))
    heading.textContent = '';

    if ('ga' in window) {
      button.setAttribute('data-on', 'click')
      button.setAttribute('data-event-category', 'Table column sorted')
      button.setAttribute('data-event-action', 'Descending')
      button.setAttribute('data-event-label', text.trim())
    }


    heading.appendChild(button);
};

SortableTable.prototype.createStatusBox = function() {

    this.status = document.createElement('div')
    this.status.setAttribute('aria-live', 'polite')
    this.status.setAttribute('role', 'status')
    this.status.setAttribute('aria-atomic', 'true')
    this.status.setAttribute('class', 'sortableTable-status govuk-visually-hidden')

    // FIXME: This isn't associated with the table if the table isn't the only node in the parent (e.g. admin users view)
    this.table.parentElement.appendChild(this.status);
};

SortableTable.prototype.sortButtonClicked = function(event) {

  var columnNumber = event.target.getAttribute('data-index')
  var sortDirection = event.target.parentElement.getAttribute('aria-sort')
  var newSortDirection;
    if(sortDirection === 'none' || sortDirection === 'ascending') {
        newSortDirection = 'descending';
    } else {
        newSortDirection = 'ascending';
    }

  var tBodies = this.table.querySelectorAll('tbody')

  this.sortTBodies(tBodies,columnNumber,newSortDirection)

  for (var i = tBodies.length - 1; i >= 0; i--) {

    var rows = this.getTableRowsArray(tBodies[i])
    var sortedRows = this.sort(rows, columnNumber, newSortDirection);
    this.addRows(tBodies[i], sortedRows);

  };

  this.removeButtonStates();
  this.updateButtonState(event.target, newSortDirection);

}

SortableTable.prototype.sortTBodies = function(tBodies, columnNumber, sortDirection) {

  var tBodiesAsArray = []
  var _this = this

  for (var i = 0; i < tBodies.length; i++) {
    tBodiesAsArray.push(tBodies[i])
  };

  var newTbodies = tBodiesAsArray.sort(function(tBodyA, tBodyB) {

    var tBodyAHeaderRow = tBodyA.querySelector('th[scope="rowgroup"]')

    var tBodyBHeaderRow = tBodyB.querySelector('th[scope="rowgroup"]')


    if (tBodyAHeaderRow && tBodyBHeaderRow) {
      tBodyAHeaderRow = tBodyAHeaderRow.parentElement
      tBodyBHeaderRow = tBodyBHeaderRow.parentElement

      var tBodyACell = tBodyAHeaderRow.querySelectorAll('td, th')[columnNumber]
      var tBodyBCell = tBodyBHeaderRow.querySelectorAll('td, th')[columnNumber]

      var tBodyAValue = _this.getCellValue(tBodyACell)
      var tBodyBValue = _this.getCellValue(tBodyBCell)

      return _this.compareValues(tBodyAValue, tBodyBValue, sortDirection)

    } else {

      console.log('no way to compare tbodies')
      return 0
    }


  });

  for (var i = 0; i < newTbodies.length; i++) {
    this.table.appendChild(newTbodies[i])
  };

}

SortableTable.prototype.compareValues = function(valueA, valueB, sortDirection) {

  if(sortDirection === 'ascending') {
      if(valueA < valueB) {
          return -1;
      }
      if(valueA > valueB) {
          return 1;
      }
      return 0;
  } else {
      if(valueB < valueA) {
          return -1;
      }
      if(valueB > valueA) {
          return 1;
      }
      return 0;
  }

}

SortableTable.prototype.updateButtonState = function(button, direction) {
    button.parentElement.setAttribute('aria-sort', direction);

    button.classList.remove('eff-button--sort')
    button.classList.add('eff-button--sort-' + direction)

    if ('ga' in window) {
      var eventAction = (direction == 'ascending' ? 'Descending' : 'Ascending')
      button.setAttribute('data-event-action', eventAction)
    }

    var message = this.options.statusMessage;
    message = message.replace(/%heading%/, button.textContent);
    message = message.replace(/%direction%/, this.options[direction+'Text']);
    this.status.textContent = message;
};

SortableTable.prototype.removeButtonStates = function() {

    var tableHeaders = this.table.querySelectorAll('thead th')

    for (var i = tableHeaders.length - 1; i >= 0; i--) {
      tableHeaders[i].setAttribute('aria-sort', 'none')
    };


    var buttons = this.table.querySelectorAll('thead button')

    for (var i = buttons.length - 1; i >= 0; i--) {
      buttons[i].classList.remove('eff-button--sort-ascending')
      buttons[i].classList.remove('eff-button--sort-descending')
      buttons[i].classList.add('eff-button--sort')
    };

    if (this.header_table) {

      var tableHeaders = this.header_table.querySelectorAll('thead th')

      for (var i = tableHeaders.length - 1; i >= 0; i--) {
        tableHeaders[i].setAttribute('aria-sort', 'none')
      };

      var buttons = this.header_table.querySelectorAll('thead button')

      for (var i = buttons.length - 1; i >= 0; i--) {
        buttons[i].classList.remove('eff-button--sort-ascending')
        buttons[i].classList.remove('eff-button--sort-descending')
        buttons[i].classList.add('eff-button--sort')
      };


      if ('ga' in window) {

        // Reset event actions to default sort order ('Descending')
        var buttons = this.header_table.querySelectorAll('thead button')
        for (var i = buttons.length - 1; i >= 0; i--) {
          buttons[i].setAttribute('data-event-action', 'Descending')
        };
      }

    }

};

SortableTable.prototype.addRows = function(tbody, rows) {
    for(var i = 0; i < rows.length; i++) {
        tbody.appendChild(rows[i]);
    }
};

SortableTable.prototype.getTableRowsArray = function(tbody) {
    var rows = [];
    var trs = tbody.querySelectorAll('tr');
    for (var i = 0; i < trs.length; i++) {
        rows.push(trs[i]);
    }
    return rows;
};

SortableTable.prototype.sort = function(rows, columnNumber, sortDirection) {


    var _this = this

    var newRows = rows.sort(function(rowA, rowB) {

      var tdA = rowA.querySelectorAll('td, th')[columnNumber]
      var tdB = rowB.querySelectorAll('td, th')[columnNumber]

      var rowAIsHeader = rowA.querySelector('th[scope="rowgroup"]')
      var rowBIsHeader = rowB.querySelector('th[scope="rowgroup"]')

      var valueA = _this.getCellValue(tdA)
      var valueB = _this.getCellValue(tdB)

        if (rowAIsHeader) {
          return -1
        } else if (rowBIsHeader) {
          return 1
        } else {

          if(sortDirection === 'ascending') {
              if(valueA < valueB) {
                  return -1;
              }
              if(valueA > valueB) {
                  return 1;
              }
              return 0;
          } else {
              if(valueB < valueA) {
                  return -1;
              }
              if(valueB > valueA) {
                  return 1;
              }
              return 0;
          }

        }

    });
    return newRows

};

SortableTable.prototype.getCellValue = function(cell) {

  var cellValue

  if (cell) {

    if (cell.children.length == 1 && cell.children[0].tagName == "TIME") {

      var timeElement = cell.children[0]

      if (timeElement.getAttribute('datetime')) {
        cellValue = Date.parse(timeElement.getAttribute('datetime'))
      } else {
        cellValue = Date.parse(timeElement.textContent)
      }

    } else {

      cellValue = cell.getAttribute('data-sort-value') || cell.textContent

      /* Remove commas */
      cellValue = cellValue.replace(/[,]/gi, '')

      cellValue = parseFloat(cellValue) || cellValue

    }

  }

  return cellValue
}
