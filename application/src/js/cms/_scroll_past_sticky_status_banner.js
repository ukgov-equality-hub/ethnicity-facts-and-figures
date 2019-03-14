/*
   ErrorSummaryWithStickyBanner

   Used to make the browser scroll past any present sticky header when clicking anchor links in validation boxes
   at the top of the page, so that the full question label is always visible.
 */

function ErrorSummaryWithStickyBanner($module, $banner) {
    this.$module = $module;
    this.$banner = $banner;
}

ErrorSummaryWithStickyBanner.prototype.init = function () {
    if (!this.$module || !this.$banner) {
        return
    }

    var hrefAnchorRegex = /\#(.+)$/;
    var errorLinks = this.$module.querySelectorAll('a');
    var $banner = this.$banner;

    var scrollForStickyHeader = function (event) {
        /* We use a timeout here so that this code runs after the default click event, which adds an anchor
         * to the URL and scrolls to the right place. */
        window.setTimeout(function () {
            var anchorRegexResult = hrefAnchorRegex.exec(this.getAttribute('href'));
            if (anchorRegexResult.length === 2) {
                var targetElement = document.getElementById(anchorRegexResult[1]);

                targetElement.scrollIntoView();

                var statusBannerHeight = $banner.clientHeight;
                window.scrollBy(0, -statusBannerHeight);
            }
        }.bind(this), 0)
    };

    for (var i = 0; i < errorLinks.length; i++) {
        errorLinks[i].addEventListener('click', scrollForStickyHeader);
    }
}

var $validationErrorBox = document.querySelector('.govuk-error-summary');
var $stickyStatusBanner = document.querySelector('.status-banner.sticky-js');
if ($validationErrorBox != null && $stickyStatusBanner != null) {
    new ErrorSummaryWithStickyBanner($validationErrorBox, $stickyStatusBanner).init();
}
