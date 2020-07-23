;(function() {

    if(window.location.href === "https://www.ethnicity-facts-figures.service.gov.uk/") {
        // hide header search bar
        var headerSearchBar = document.getElementById('header_search_bar');
        headerSearchBar.parentNode.removeChild(headerSearchBar);
    }

    if ('addEventListener' in document) {
        document.addEventListener(
            'DOMContentLoaded',
            function () {
                /* The default form action is Google's custom search URL, which takes us off site.
                    We want to keep users on the site if possible, so we have own our search page for results. */
                document.getElementById('search-form').action = '/search';
                // document.getElementById('site-search-label').innerHTML = 'Search facts and figures';

                /* We add a form field to direct users to our own custom search engine when javascript isn't
                    available. If it is, we keep them on our site, and so we don't want the custom search ID to
                    be injected into the form response. */
                var cx_input = document.getElementById('search-form-cx');
                cx_input.parentNode.removeChild(cx_input);

                var toggleTargets = document.getElementsByClassName('js-search-focus');

                function inputIsEmpty(el) {
                    return el.value === '';
                }

                function addFocusClass() {
                    this.classList.add('focus');
                }

                function removeFocusClassFromEmptyInput() {
                    if (inputIsEmpty(this)) {
                        this.classList.remove('focus');
                    }
                }

                Array.prototype.forEach.call(toggleTargets, function (el) {
                    if (!inputIsEmpty(el)) {
                        addFocusClass.bind(el)();
                    }
                    el.addEventListener('focus', addFocusClass);
                    el.addEventListener('blur', removeFocusClassFromEmptyInput);
                });
            }
        );
    };
})();
