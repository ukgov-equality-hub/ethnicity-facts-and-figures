$(document).ready(function () {
  var $details = $('details');
  $('.js--print').click(function (e) {
    var states = [];
    e.preventDefault();
    $.each($details, function () {
      var flag = $(this).prop('open');
      states.push(flag ? true : false)
      $(this).prop('open', true);
    });
    window.print();

    // re-apply state to details widgets
    $(window).scroll(function () {
      $.each($details, function(i) {
        $(this).attr('open', states[i]);
      });
      $(window).unbind('scroll');
    });
  });
});