// Code to support the cookie preferences page

(function (root) {
  'use strict'
  window.GOVUK.GDM = window.GOVUK.GDM || {}
  function CookieSettings () { }

  CookieSettings.prototype.init = function () {
    this.$module = document.querySelector('#cookie-settings')
    this.$module.submitSettingsForm = this.submitSettingsForm.bind(this)

    document.querySelector('#cookie-settings').addEventListener('submit', this.$module.submitSettingsForm)

    this.setInitialFormValues()
  }

  CookieSettings.prototype.setInitialFormValues = function () {
    if (!window.GOVUK.GDM.CookieHelper.cookie('cookie_policy')) {
      window.GOVUK.GDM.CookieHelper.setDefaultConsentCookie()
    }

    var currentConsentCookie = window.GOVUK.GDM.CookieHelper.cookie('cookie_policy')
    var currentConsentCookieJSON = JSON.parse(currentConsentCookie)
    var preferencesSet = window.GOVUK.GDM.CookieHelper.getCookie('cookie_preferences_set')

    // We don't need the essential value as this cannot be changed by the user
    delete currentConsentCookieJSON.essential

    // If user has selected options previously re-select them, otherwise they must be left blank
    if (preferencesSet) {
      this.hideWarningMessage()
      for (var cookieType in currentConsentCookieJSON) {
        var radioButton
        if (currentConsentCookieJSON[cookieType]) {
          radioButton = document.querySelector('input[name=cookies-' + cookieType + '][value=On]')
        } else {
          radioButton = document.querySelector('input[name=cookies-' + cookieType + '][value=Off]')
        }
        radioButton.checked = true
      }
    }
  }

  CookieSettings.prototype.submitSettingsForm = function (event) {
    event.preventDefault()

    var formInputs = event.target.getElementsByTagName('input')
    var options = {}
    var checkedItems = 0
    for (var i = 0; i < formInputs.length; i++) {
      var input = formInputs[i]
      if (input.checked) {
        var name = input.name.replace('cookies-', '')
        var value = input.value === 'On' ? true : false
        checkedItems++

        options[name] = value
      }

    }
    // both cookie options must be set when form is submitted
    if (checkedItems < 2) {
      this.showErrorMessage()
      return false
    }

    window.GOVUK.GDM.CookieHelper.setConsentCookie(options)
    window.GOVUK.GDM.CookieHelper.setCookie('cookie_preferences_set', true, { days: 365 })

    this.fireAnalyticsEvent(options)

    if (!window.GOVUK.GDM.CookieHelper.cookie('seen_cookie_message')) {
      window.GOVUK.GDM.CookieHelper.setCookie('seen_cookie_message', true, { days: 365 })
    }
    this.hideWarningMessage()

    var errorMessage = document.querySelector('div#cookie-settings-error')
    if (errorMessage !== null && errorMessage.style.display === 'block') {
      this.hideErrorMessage()
    }
    this.showConfirmationMessage()

    return false
  }

  CookieSettings.prototype.fireAnalyticsEvent = function (consent) {
    var eventLabel = ''

    for (var option in consent) {
      var optionValue = consent[option] ? 'yes' : 'no'
      eventLabel += option + '-' + optionValue + ' '
    }

    if (GOVUK.GDM.analytics && GOVUK.GDM.analytics.events) {
      GOVUK.GDM.analytics.events.sendEvent('cookieSettings', 'Save changes', { label: eventLabel })
    }
  }

  CookieSettings.prototype.showConfirmationMessage = function () {
    var confirmationMessage = document.querySelector('div#cookie-settings-confirmation')
    var previousPageLink = document.querySelector('.cookie-settings__prev-page')
    var referrer = CookieSettings.prototype.getReferrerLink()

    document.body.scrollTop = document.documentElement.scrollTop = 0

    if (referrer && referrer !== document.location.pathname) {
      previousPageLink.href = referrer
      previousPageLink.style.display = 'block'
    } else {
      previousPageLink.style.display = 'none'
    }

    confirmationMessage.style.display = 'block'
  }

  CookieSettings.prototype.showErrorMessage = function () {
    var errorMessage = document.querySelector('div#cookie-settings-error')
    if (errorMessage !== null) {
      errorMessage.style.display = 'block'
      document.body.scrollTop = document.documentElement.scrollTop = 0
    }
  }

  CookieSettings.prototype.hideErrorMessage = function () {
    var errorMessage = document.querySelector('div#cookie-settings-error')
    if (errorMessage !== null) {
      errorMessage.style.display = 'none'
    }
  }

  CookieSettings.prototype.hideWarningMessage = function () {
    var warningMessage = document.querySelector('div#cookie-settings-warning')
    if (warningMessage !== null) {
      warningMessage.style.display = 'none'
    }
  }

  CookieSettings.prototype.getReferrerLink = function () {
    return document.referrer ? new URL(document.referrer).pathname : false
  }

  window.GOVUK.GDM.CookieSettings = CookieSettings
})(window);

(function (window) {
  // Initialise the code above if we're on the cookie settings page
  window.GOVUK.GDM = window.GOVUK.GDM || {}
  var _cookieSettingsForm = new window.GOVUK.GDM.CookieSettings();
  if (window.location.pathname === '/cookie-settings') {
    _cookieSettingsForm.init()
  }
})(window);