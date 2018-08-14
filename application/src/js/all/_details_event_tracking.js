document.addEventListener('DOMContentLoaded', function () {
  var detailsElements = document.getElementsByTagName('DETAILS')

  for (var i = detailsElements.length - 1; i >= 0; i--) {
    detailsElements[i].addEventListener('toggle', updateEventAction)
  }

  function updateEventAction (event) {
    var target = event.target

    if (target.open === true || target.open === false) {
      var eventAction = target.open === true ? 'Closed' : 'Opened'
      target.setAttribute('data-event-action', eventAction)
    }
  }
})
