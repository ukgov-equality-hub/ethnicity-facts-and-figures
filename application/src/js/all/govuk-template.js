(function () {
  'use strict';

  // add cookie message
  if (window.GOVUK && GOVUK.addCookieMessage) {
    GOVUK.addCookieMessage();
  }

  var hideButton = document.getElementById('hide-cookie-banner');
  var cookieAcceptButton = document.getElementById('cookie-accept');
  var cookieDeclineButton = document.getElementById('cookie-decline');

  function setCookiesSettings(value) {
    GOVUK.cookie('cookies_preferences_set', true, { days: 365 });
    GOVUK.cookie(
      'cookies_policy',
      JSON.stringify({
        essential: value,
        settings: value,
        usage: value,
        campaigns: value,
      }),
      { days: 365 }
    );
  }

  hideButton.onclick = function changeContent() {
    document.getElementById('global-cookie-message').style.display = 'none';
  };

  cookieAcceptButton.onclick = function acceptCookies() {
    setCookiesSettings(true);
    document.getElementById('cookie-actions').style.display = 'none';
    document.getElementById('cookie-confirmation').style.display = 'block';
  };

  cookieDeclineButton.onclick = function declineCookies() {
    setCookiesSettings(false);
    document.getElementById('global-cookie-message').style.display = 'none';
  };

  // cookie settings page
  var formElem = document.getElementById('cookie-settings-form');
  var cookieSettingsSubmit = document.getElementById('submit-settings');

  if (formElem) {
    if (
      GOVUK.cookie('cookies_policy') === null ||
      JSON.parse(GOVUK.cookie('cookies_policy')).usage === true
    ) {
      document.getElementById('radio-accept').checked = true;
    } else {
      document.getElementById('radio-decline').checked = true;
    }
  }

  if (cookieSettingsSubmit) {
    cookieSettingsSubmit.addEventListener('click', function (event) {
      // on form submission, prevent default
      event.preventDefault();
      if (document.getElementById('radio-accept').checked) {
        setCookiesSettings(true);
      } else {
        setCookiesSettings(false);
      }

      var confirmation = document.getElementById(
        'cookie-settings__confirmation'
      );
      confirmation.style.display = 'block';
      confirmation.scrollIntoView();
    });
  }
  // ./cookie settings page
}.call(this));
