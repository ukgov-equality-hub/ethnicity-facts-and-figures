;(function() {
    if ('addEventListener' in document) {
        document.addEventListener(
            'DOMContentLoaded',
            function () {
                /* The default form action is Google's custom search URL, which takes us off site.
                    We want to keep users on the site if possible, so we have own our search page for results. */
                $('header form.site-search').attr('action', '/search');
                $('header .site-search-label').text('Search facts and figures');

                /* We add a form field to direct users to our own custom search engine when javascript isn't
                    available. If it is, we keep them on our site, and so we don't want the custom search ID to
                    be injected into the form response. */
                $('header form.site-search input[name=cx]').remove();

                var $toggleTarget = $('.js-search-focus');

                function inputIsEmpty() {
                    return $toggleTarget.val() === '';
                }

                function addFocusClass() {
                    $toggleTarget.addClass('focus');
                }

                function removeFocusClassFromEmptyInput() {
                    if (inputIsEmpty()) {
                        $toggleTarget.removeClass('focus');
                    }
                }

                if (!inputIsEmpty()) {
                    addFocusClass();
                }

                $toggleTarget.on('focus', addFocusClass);
                $toggleTarget.on('blur', removeFocusClassFromEmptyInput);
            }
        );
    };
})();