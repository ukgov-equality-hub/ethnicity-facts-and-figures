$(document).ready(function () {
  var expanded, $headers = $('.accordion__header');
  $('.accordion-link--expand-all').each(function () {
    $(this).click(function (e) {
      e.preventDefault();
      $(this).text(expanded ? 'Open all' : 'Close all');
      expanded = expanded ? false : true;
      $.each($headers, function(index, header){
        if(expanded) {
          if (!$(header).find('.plus-minus-icon').hasClass('open')) {
            $(header).click();
          }
        } else {
          if ($(header).find('.plus-minus-icon').hasClass('open')) {
            $(header).click();
          }
        }
      });
    })
  })

});