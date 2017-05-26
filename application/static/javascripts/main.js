$( document ).ready(function() {
  $(document).foundation();
  $(function () {
    $('#jstree').jstree({
        'core': {
            'themes': {
                'name': 'proton',
                'responsive': true
            }
        }
    });
        $("#jstree li").on("click", "a",
        function() {
            document.location.href = this;
        }
    );
  });
});