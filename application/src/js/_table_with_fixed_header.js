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

        parentParentElement.appendChild(fixedTable)

        updatePositioning()

        /* Update again after 200ms. Solves a few weird issues. */
        setTimeout(updatePositioning, 200)

        window.addEventListener('resize', updatePositioning)
      }
    }
  }

  function updatePositioning() {
    var height = heightForElement(tableHeader);

    parentParentElement.style.paddingTop = height;
    tableElement.style.marginTop = '-' + height;

    fixedTable.style.width = widthForElement(tableElement);

    var mainTableHeaderCells = tableElement.querySelectorAll('thead th, thead td')
    var headerCells = fixedTable.querySelectorAll('thead th, thead td')

    for (var i = 0; i < mainTableHeaderCells.length; i++) {

      headerCells[i].style.width = widthForElement(mainTableHeaderCells[i])

    };


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