(function() {
  "use strict";
  GOVUK.Tracker.load();
  var cookieDomain = (document.domain === 'www.digitalmarketplace.service.gov.uk') ? '.digitalmarketplace.service.gov.uk' : document.domain;
  var property = (document.domain === 'www.digitalmarketplace.service.gov.uk') ? 'UA-49258698-1' : 'UA-49258698-3';
  GOVUK.analytics = new GOVUK.Analytics({
    universalId: property,
    cookieDomain: cookieDomain
  });
  GOVUK.analytics.trackPageview();
})();
