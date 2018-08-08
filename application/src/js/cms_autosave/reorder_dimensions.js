// Functions from original CMS form page for moving dimensions up and down

    function moveDimensionUp(event) {
        event.preventDefault();
        var row = $(event.currentTarget).parents('tr:first');
        if (row.prev().length > 0) {
            row.insertBefore(row.prev());
            syncDimensionOrder();
        }
    }

    function moveDimensionDown(event) {
        event.preventDefault();
        var row = $(event.currentTarget).parents('tr:last');
        if (row.next().length > 0) {
            row.insertAfter(row.next());
            syncDimensionOrder();
        }
    }

    function syncDimensionOrder() {
        var rows = $('tr.movable'),
            dimensions = [],
            guid;

        $(rows).each(function (index, row) {
            guid = $(row).data('dimension-guid');
            dimensions.push({"index": index, "guid": guid});
        });
        $.ajax({
            type: 'POST',
            url: set_dimension_order_post_url,
            dataType: 'json',
            contentType: 'application/json',
            data: JSON.stringify({"dimensions": dimensions})
        });
    }

    $(document).ready(function () {
        $('.move-up').click(moveDimensionUp);
        $('.move-down').click(moveDimensionDown);
    })
