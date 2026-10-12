import React from "react";
import ReactDOM from "react-dom/client";
import "./index.css";
import App from "./App";

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);

if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    // The version query is a deliberate cache key: a CDN edge can hold a
    // stale /sw.js long after a deploy (observed: 86 minutes), and a stale
    // worker keeps its old caches. A distinct URL forces a fresh fetch of the
    // file the browser actually runs. Bump it whenever sw.js changes.
    navigator.serviceWorker.register("/sw.js?v=6").catch(() => {});
  });
}
