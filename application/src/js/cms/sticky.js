/* globals $ */
$(document).ready(function () {
  var $stickies = $('.sticky-js')
  $.each($stickies, function () {
    var stickyPosition = parseInt($(this).position().top)
    $(window).scroll(function () {
      var scrollTop = $(window).scrollTop()
      if (scrollTop >= stickyPosition) {
        $(this).addClass('sticky-js-fixed')
      } else {
        $(this).removeClass('sticky-js-fixed')
      }
    }.bind(this))
  })
})
