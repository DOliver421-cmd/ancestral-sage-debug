// error-suppress.js — silence a known benign browser error. Some Chrome
// versions fire a DataCloneError DOMException tied to PerformanceServerTiming
// entries on pages that use performance APIs; it is harmless but spams the
// console and trips error-reporting hooks.
window.addEventListener(
  "error",
  function (e) {
    if (
      e.error instanceof DOMException &&
      e.error.name === "DataCloneError" &&
      e.message &&
      e.message.indexOf("PerformanceServerTiming") !== -1
    ) {
      e.stopImmediatePropagation();
      e.preventDefault();
    }
  },
  true
);
