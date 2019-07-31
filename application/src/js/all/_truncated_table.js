var TruncatedTable = function(tableElement) {
  this.tableElement = tableElement;
  this.showAllRowsButton;
}

TruncatedTable.prototype.showAllRows = function() {
  this.tableElement.classList.remove('eff-table--truncated')
  this.showAllRowsButton.parentElement.removeChild(this.showAllRowsButton)
};

TruncatedTable.prototype.init = function() {
  this.tableElement.classList.add('eff-table--truncated')

  var rowCount = this.tableElement.querySelectorAll('tbody tr').length

  if (rowCount > 25) {

    this.showAllRowsButton = document.createElement('button')
    this.showAllRowsButton.textContent = 'Show ' + (rowCount - 20) + ' more rows'
    this.showAllRowsButton.classList.add('eff-button-link')
    this.showAllRowsButton.classList.add('govuk-!-margin-top-3')

    this.showAllRowsButton.addEventListener('click', this.showAllRows.bind(this))

    this.tableElement.parentElement.insertBefore(this.showAllRowsButton, this.tableElement.nextSibling)

  }

};

document.addEventListener('DOMContentLoaded', function() {

  var $truncatedTables = document.querySelectorAll('[data-module*="eff-truncated-table"]')

  for (var i = $truncatedTables.length - 1; i >= 0; i--) {
    new TruncatedTable($truncatedTables[i]).init()
  }

})
