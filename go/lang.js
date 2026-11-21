/* Shared language redirect for /go/ pages.
 *
 * KNOWN: browser languages we understand (extend here).
 * READY: language prefixes that already have published pages.
 *        Languages in KNOWN but not READY (currently none) are
 *        checked with a same-origin fetch; if the page is missing
 *        the visitor is sent to the English path.
 * English ("en") is matched so a visitor who prefers English over
 * another listed language is not sent to that other language.
 */
(function (global) {
  "use strict";

  var ROOT = "/travel-south-gallery/";
  var KNOWN = ["fi", "sv", "de", "fr", "es", "it", "ru", "uk", "ja", "ar"];
  var READY = ["fi", "sv", "de", "fr", "es", "it", "ru", "uk", "ja", "ar"];

  function browserLangs() {
    var list = navigator.languages;
    if (!list || !list.length) {
      list = [navigator.language || navigator.userLanguage || "en"];
    }
    return list;
  }

  function primaryTag(tag) {
    return String(tag || "")
      .toLowerCase()
      .replace(/_/g, "-")
      .split("-")[0];
  }

  function preferredLang() {
    var langs = browserLangs();
    var i, primary;
    for (i = 0; i < langs.length; i++) {
      primary = primaryTag(langs[i]);
      if (primary === "en") return "en";
      if (KNOWN.indexOf(primary) !== -1) return primary;
    }
    return "en";
  }

  function go(path) {
    location.replace(ROOT + path + location.search + location.hash);
  }

  function langPath(lang, page) {
    return lang === "en" ? page : lang + "/" + page;
  }

  function redirectTo(page) {
    var lang = preferredLang();
    if (lang === "en" || READY.indexOf(lang) !== -1) {
      go(langPath(lang, page));
      return;
    }
    var target = ROOT + langPath(lang, page);
    fetch(target, { method: "GET", redirect: "follow", cache: "no-store" })
      .then(function (res) {
        go(res.ok ? langPath(lang, page) : page);
      })
      .catch(function () {
        go(page);
      });
  }

  global.TSGo = {
    redirectTo: redirectTo,
    known: KNOWN,
    ready: READY
  };
})(window);
