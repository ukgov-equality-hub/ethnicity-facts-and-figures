

function BackToTop($module) {
  this.$module = $module;
  this.hasScrolled = false
  this.hasResized = false
  this.fixed = false
}


BackToTop.prototype.update = function() {

  var distanceFromEnd = document.body.scrollHeight - (window.scrollY + window.innerHeight)

  if (!this.fixed) {
    var linkNotInView = (distanceFromEnd > this.linkDistanceFromBottom)
  } else {
    var linkNotInView = ((distanceFromEnd + this.$moduleHeight) > this.linkDistanceFromBottom)
  }

  var linkTargetNotInView = window.scrollY > this.linkTargetDistanceFromTop

  if (linkTargetNotInView && linkNotInView) {
    this.$module.classList.add('app-back-to-top--fixed')
    this.fixed = true
  } else {
    this.$module.classList.remove('app-back-to-top--fixed')
    this.fixed = false
  }

}

BackToTop.prototype.init = function () {

  // Check for module
  if (!this.$module) {
    return
  }

  var link = this.$module.querySelector('.app-back-to-top__link')

  if (!link) {
    return
  }

  this.$linkTarget = document.getElementById(link.getAttribute('href').substr(1))

  if (!this.$linkTarget) {
    return
  }

  this.$moduleHeight = this.$module.getBoundingClientRect().height

  var windowScrollY = window.scrollY
  var documentHeight = document.body.getBoundingClientRect().height

  var moduleClientRect = this.$module.getBoundingClientRect()

  this.linkDistanceFromBottom = documentHeight - (moduleClientRect.y + windowScrollY)

  var linkTargetBoundingClientRect = this.$linkTarget.getBoundingClientRect()
  var linkTargetHeight = linkTargetBoundingClientRect.height
  var linkTargetY = linkTargetBoundingClientRect.y

  this.linkTargetDistanceFromTop = linkTargetHeight + linkTargetY + windowScrollY


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
