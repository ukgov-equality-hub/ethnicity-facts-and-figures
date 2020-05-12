

function collapsibleTableBodies(table) {

  var headers = table.querySelectorAll('.header');

  for (var i = 0; i < headers.length; i++) {

    var header = headers[i];

    if (!header.classList.contains('empty')) {
      header.addEventListener('click', function(event) {
        var tbody = event.target.parentElement.parentElement
        tbody.classList.toggle('collapsed')
      })
    }
  }

}
