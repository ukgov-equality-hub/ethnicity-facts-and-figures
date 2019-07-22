

function BackToTop($module) {
  this.$module = $module;
  this.hasScrolled = false
  this.hasResized = false
  this.fixed = false
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

  window.addEventListener('scroll', this.onScroll.bind(this))
  window.addEventListener('resize', this.onResize.bind(this))
  setInterval(this.checkScrollOrResize.bind(this), 50)

}

BackToTop.prototype.onScroll = function() {
  this.hasScrolled = true
}

BackToTop.prototype.onResize = function() {
  this.hasResized = true
}

BackToTop.prototype.checkScrollOrResize = function() {

  if (this.hasScrolled || this.hasResized) {
    this.hasScrolled = false
    this.hasResized = false
    this.update()
  }
}

document.addEventListener('DOMContentLoaded', function() {

  var $backToTops = document.querySelectorAll('[data-module="app-back-to-top"]')

  for (var i = $backToTops.length - 1; i >= 0; i--) {
    new BackToTop($backToTops[i]).init()
  }

})
