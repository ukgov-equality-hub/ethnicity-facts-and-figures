function TableWithFixedHeader(tableElement) {
  var tableElement = tableElement
  var fixedTable, parentParentElement, tableHeader

  function setup() {

    if (tableElement) {
      var parentElement = tableElement.parentElement

      if (parentElement) {
        parentParentElement = parentElement.parentElement

        tableHeader = tableElement.querySelector('thead')

        var fixedTableHeader = tableHeader.cloneNode(true)
        fixedTableHeader.classList.add('fixed')

        fixedTable = document.createElement('table')
        fixedTable.setAttribute('class', tableElement.getAttribute('class') + ' fixed')
        fixedTable.classList.remove('fixed-headers')

        fixedTable.appendChild(fixedTableHeader)

        var fixedTableContainer = document.createElement('div')
        fixedTableContainer.classList.add('fixed-header-container')

        fixedTableContainer.appendChild(fixedTable)

        parentParentElement.appendChild(fixedTableContainer)

        // updatePositioning()

        /* Update again after 200ms. Solves a few weird issues. */
        setTimeout(updatePositioning, 200)

        window.addEventListener('resize', updatePositioning)
      }
    }
  }

  function updatePositioning() {

    var height = heightForElement(tableHeader);

    tableElement.style.marginTop = '-' + height;
    parentParentElement.style.paddingTop = height;

    var mainTableHeaderCells = tableElement.querySelectorAll('thead th, thead td')
    var headerCells = fixedTable.querySelectorAll('thead th, thead td')

    for (var i = 0; i < mainTableHeaderCells.length; i++) {
      headerCells[i].style.width = widthForElement(mainTableHeaderCells[i])
    };

    var innerContainerWidth = widthForElement(parentParentElement);
    var fixedTableHeaderWidth = widthForElement(fixedTable)

    if (parseFloat(innerContainerWidth) < parseFloat(fixedTableHeaderWidth)) {
      parentParentElement.style.width = widthForElement(fixedTable);
    }


  }

  function heightForElement(element) {

    if (typeof window.getComputedStyle === "function") {
      return getComputedStyle(element).height
    } else {
      return element.getBoundingClientRect().bottom - element.getBoundingClientRect().top;
    }


  }

  function widthForElement(element) {

    if (typeof window.getComputedStyle === "function") {
      return getComputedStyle(element).width
    } else {
      return element.getBoundingClientRect().right - element.getBoundingClientRect().left;
    }

  }

  // Check for required APIs
  if (
    document.querySelector &&
    document.body.classList
  ) {
    setup()
  }


}