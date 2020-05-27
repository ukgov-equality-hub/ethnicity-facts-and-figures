
(function () {
  'use strict';

  // add cookie message
  if (window.GOVUK && GOVUK.addCookieMessage) {
    GOVUK.addCookieMessage();
  }

  var hideButton = document.getElementById('hide-cookie-banner');
  var cookieAcceptButton = document.getElementById('cookie-accept');
  var cookieDeclineButton = document.getElementById('cookie-decline');

  hideButton.onclick = function changeContent() {
    document.getElementById('global-cookie-message').style.display = 'none';
  }

  cookieAcceptButton.onclick = function acceptCookies() {
    GOVUK.cookie('cookies_preferences_set', true, { days: 356 });
    GOVUK.cookie('cookies_policy', JSON.stringify({"essential":true,"settings":true,"usage":true,"campaigns":true}), { days: 356 });
    document.getElementById('cookie-confirmation').style.display = 'block';
  }

  cookieDeclineButton.onclick = function declineCookies() {
    GOVUK.cookie('cookies_preferences_set', true, { days: 356 });
    GOVUK.cookie('cookies_policy', JSON.stringify({"essential":true,"settings":false,"usage":false,"campaigns":false}), { days: 356 });
    document.getElementById('global-cookie-message').style.display = 'none';
  }

  // cookie settings page
  var formElem = document.getElementById('cookie-settings-form');
  var cookieSettingsSubmit = document.getElementById('submit-settings');

  if (formElem) {
    if (GOVUK.cookie('cookies_policy')===null || JSON.parse(GOVUK.cookie('cookies_policy')).usage === true) {
      document.getElementById('radio-accept').checked = true;
    }else {
      document.getElementById('radio-decline').checked = true;
    }
  }

  cookieSettingsSubmit.onclick = function setCookiesSettings(e) {
    // on form submission, prevent default
    e.preventDefault();
    if(document.getElementById('radio-accept').checked) {
      GOVUK.cookie('cookies_preferences_set', true, { days: 356 });
      GOVUK.cookie('cookies_policy', JSON.stringify({"essential":true,"settings":true,"usage":true,"campaigns":true}), { days: 356 });
    } else {
      GOVUK.cookie('cookies_preferences_set', true, { days: 356 });
      GOVUK.cookie('cookies_policy', JSON.stringify({"essential":true,"settings":false,"usage":false,"campaigns":false}), { days: 356 });
    }

    var confirmation = document.getElementById('cookie-settings__confirmation');
    confirmation.style.display = 'block';
    confirmation.scrollIntoView();

  }
  // ./cookie settings page


}.call(this));
