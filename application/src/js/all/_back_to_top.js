

function BackToTop($module) {
  this.$module = $module;
}


BackToTop.prototype.update = function() {

  var distanceFromEnd = document.body.scrollHeight - (window.scrollY + window.innerHeight)

  if (window.scrollY > 600 && distanceFromEnd > 800) {
    this.$module.classList.add('app-back-to-top--fixed')
  } else {
    this.$module.classList.remove('app-back-to-top--fixed')
  }

}

BackToTop.prototype.init = function () {

  // Check for module
  if (!this.$module) {
    return
  }

  this.$footer = document.querySelector('footer')

  setInterval(this.update.bind(this), 500)

}

document.addEventListener('DOMContentLoaded', function() {

  var $backToTops = document.querySelectorAll('[data-module="app-back-to-top"]')

  for (var i = $backToTops.length - 1; i >= 0; i--) {
    new BackToTop($backToTops[i]).init()
  }

})
