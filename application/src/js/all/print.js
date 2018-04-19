
document.addEventListener('DOMContentLoaded', function() {

  var printLinks = document.querySelectorAll('.js--print');

  for (var i = printLinks.length - 1; i >= 0; i--) {
    printLinks[i].addEventListener('click', function(event) {

      event.preventDefault();
      window.print();

    })
  }

})
