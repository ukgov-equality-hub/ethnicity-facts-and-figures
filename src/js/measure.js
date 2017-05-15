(function(){
  // stop everything being called twice if loaded with turbolinks and page load.
  var initialised = false;

  function accordions(){
    var accordionsAllOpen = false;

    $(".accordion__header").click(function(e){
        var body = $(e.currentTarget).parent().find(".accordion__body")
        $(e.currentTarget).find(".plus-minus-icon").toggleClass("open")
        $(body).toggle()
    })


    $(".accordion__body").hide()

    $("#accordion-all-control").click(function(){
    a= $(".plus-minus-icon").filter(function(_,icon) {
        return icon.classList.contains("open")
      })

      if(a.size() == 0){
        console.log("called")
        $(".plus-minus-icon").addClass("open")
        $("#accordion-all-control").text("Close all")
        $(".accordion__body").show()
      } else {
        $(".plus-minus-icon").removeClass("open")
        $("#accordion-all-control").text("Open all")
        $(".accordion__body").hide()
      }
    })
  }
  $(document).ready(accordions)
}())
