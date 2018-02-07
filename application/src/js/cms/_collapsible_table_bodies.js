

function collapsibleTableBodies(table) {

  for (header of table.querySelectorAll('.header')) {

    if (!header.classList.contains('empty')) {
      header.addEventListener('click', function(event) {
        var tbody = event.target.parentElement.parentElement
        tbody.classList.toggle('collapsed')
      })
    }
  }

}

