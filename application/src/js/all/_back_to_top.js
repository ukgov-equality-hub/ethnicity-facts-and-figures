

function BackToTop($module) {
  this.$module = $module;
  this._has_scrolled = false
  this._has_resized = false
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
  this._has_scrolled = true
}

BackToTop.prototype.onResize = function() {
  this._has_resized = true
}

BackToTop.prototype.checkScrollOrResize = function() {

  if (this._has_scrolled || this._has_resized) {
    this._has_scrolled = false
    this._has_resized = false
    this.update()
  }
}

document.addEventListener('DOMContentLoaded', function() {

  var $backToTops = document.querySelectorAll('[data-module="app-back-to-top"]')

  for (var i = $backToTops.length - 1; i >= 0; i--) {
    new BackToTop($backToTops[i]).init()
  }

})
