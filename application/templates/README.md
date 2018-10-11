## Templates

Our site templates are all derived from a single base template, `base.html`, at the root of the templates directory.
The base template declares the interface for all sub-templates and exposes a number of blocks that can be overriden,
as needed, to customise content and structure. The exposed interface consists of the following blocks (closely
derived from the GOV.UK Design System: https://design-system.service.gov.uk/styles/page-template):

* pageTitle
    * The name of the page as it appears next to the favicon (i.e. in the window/tab).
* headIcons
    * Override the default icons used for the page.
* socialMetadata
    * Wraps around a set of blocks that define attributes for Open Graph and other social-sharing protocols.
    * Helps links to our site render nicely and with useful metadata when shared socially via other sites.
    * Sub-blocks:
        * socialType
            * Sets the type of page being shared (for us, our pages are generally of the `article` type)
        * socialTitle
            * The title of the page as it should appear when shared
        * socialDescription
            * A short description of the page to provide a summary or some context when shared
        * socialImage
            * An image to be displayed for the page when shared
        * twitterMetadata
            * Additional metadata that extends the Open Graph protocol specifically for Twitter.
    * See also http://ogp.me, https://developer.twitter.com/en/docs/tweets/optimize-with-cards/guides/getting-started
* httpEquiv
    * Declares and defines any `http-equiv` meta attributes for the page, currently used for the inline Content Security Policy.
* googleAnalytics
    * A hook into the inline JavaScript that configures our Google Analytics for each page.
* headEnd
    * A hook into the end of the `<head>` element.
* bodyClasses
    * Can be used to set the `class` attribute on the `<body>` element.
* bodyStart
    * A hook into the start of the `<body>` element.
* skipLink
    * Can be used to override the default `skipLink` container used to allow keyboard users to skip past the navbar.
* cookieMessage
    * Contains the global GOV.UK cookie messages
* header
    * Contains the default page header for the site, including the CMS header (if appropriate)
* main
    * Wrapper around the declaration of the `<main>` element.
    * Sub-blocks:
        * mainElementDefinition
            * Wraps around the opening tag of the default `<main>` element, allowing to override it and assign additional/alternative properties.
        * beforeContent
            * A hook into the `main` element, before any of the core content of the specific page is rendered. By default, contains the page breadcrumbs.
            * Sub-blocks:
                * breadcrumbs
                    * Renders the breadcrumbs for the page, using the `breadcrumbs` variable defined in each sub-template.
                * flashMessages
                    * Renders flash messages for the page, retrieving them from `get_flashed_messages` exposed by Flask.
        * content
            * Where sub-templates should declare the content for the specific page, including its `<h1>`.
* footer
    * Wraps the default footer of the page, should it need to be overriden.
* bodyEnd
    * A section just before the closing tag of the `<body>` element to include - most likely - scripts on the page. By default, this includes the main scripts for the site - such as `all.js` for the static site, and `cms.js`/`charts.js` for the CMS.