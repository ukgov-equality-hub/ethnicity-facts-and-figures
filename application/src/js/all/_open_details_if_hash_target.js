
function checkForDetailsHashTarget() {

  var element = document.getElementById(location.hash.substring(1))

  if (element && element.tagName === 'DETAILS' && 'open' in element) {
    element.open = true
  }

}

window.addEventListener('hashchange', checkForDetailsHashTarget)
document.addEventListener('DOMContentLoaded', checkForDetailsHashTarget)
