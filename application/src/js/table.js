
if ('addEventListener' in document &&
    document.querySelectorAll
  ) {

  document.addEventListener('DOMContentLoaded', function() {

    var fixedTableContainers = document.querySelectorAll('.table-container-outer.fixed-headers')

    for (var i = 0; i < fixedTableContainers.length; i++) {

      var table = fixedTableContainers[i].querySelector('table')
      new TableWithFixedHeader(table)

    };

  })

}

if ('addEventListener' in document &&
    document.querySelectorAll
  ) {

  document.addEventListener('DOMContentLoaded', function() {

    var tables = document.querySelectorAll('.table-container-outer')

    for (var i = tables.length - 1; i >= 0; i--) {

      var table = tables[i].querySelector('table')
      var header_table = tables[i].querySelector('table.fixed')

      new SortableTable(table, header_table, {})
    };

  })

}