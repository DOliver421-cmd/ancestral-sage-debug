/* Render harness: executes Helper.jsx the way the browser does, so a
   render-time exception appears HERE instead of on the owner's screen.
   Server rendering runs no effects, which is what isolates a render crash
   from a data/effect problem. */
const path = require("path");
const esbuild = require("esbuild");

const HERE = __dirname;
const AUTH_STUB = path.join(HERE, "stub-auth.js");
const RRD_STUB = path.join(HERE, "stub-router.js");
const API_STUB = path.join(HERE, "stub-api.js");

async function main() {
  await esbuild.build({
    entryPoints: [path.join(HERE, process.env.HARNESS_PAGE || "src/pages/Helper.jsx")],
    bundle: true,
    format: "cjs",
    platform: "node",
    jsx: "automatic",
    loader: { ".js": "jsx", ".jsx": "jsx" },
    outfile: path.join(HERE, ".harness-bundle.js"),
    external: ["react", "react-dom", "react-dom/server"],
    plugins: [{
      name: "stub-local-deps",
      setup(build) {
        build.onResolve({ filter: /^\.\.\/lib\/auth$/ }, () => ({ path: AUTH_STUB }));
        build.onResolve({ filter: /^\.\.\/lib\/api$/ }, () => ({ path: API_STUB }));
        build.onResolve({ filter: /^react-router-dom$/ }, () => ({ path: RRD_STUB }));
      },
    }],
    logLevel: "error",
  });

  const React = require("react");
  const { renderToStaticMarkup } = require("react-dom/server");
  const Helper = require("./.harness-bundle.js").default;
  // SSR has no browser globals; components that touch them at render time get
  // inert stand-ins so a crash means a real defect, not a missing shim.
  const noop = () => {};
  global.window = global.window || {
    addEventListener: noop, removeEventListener: noop, matchMedia: () => ({ matches: false }),
    location: { href: "https://harness.local/", search: "" }, speechSynthesis: undefined,
    SpeechRecognition: undefined, webkitSpeechRecognition: undefined, open: () => null,
  };
  global.document = global.document || {
    getElementById: () => null, querySelector: () => null, querySelectorAll: () => [],
    addEventListener: noop, createElement: () => ({ style: {}, setAttribute: noop, appendChild: noop }),
    body: { appendChild: noop }, title: "",
  };
  global.navigator = global.navigator || { userAgent: "harness", mediaDevices: { getUserMedia: () => Promise.reject(new Error("no mic")) } };
  global.localStorage = global.localStorage || { getItem: () => null, setItem: noop, removeItem: noop };

  const user = {
    id: "u1", email: "t@example.com", full_name: "Test Parent",
    role: "student", feature_tier: "member", byok_enabled: false,
  };

  console.log("— rendering <Helper requireAuth /> …");
  try {
    const html = renderToStaticMarkup(React.createElement(Helper, { requireAuth: true }));
    console.log("RENDER OK — bytes:", html.length);
    console.log("  media tools present:", html.includes("Media & Accessibility"));
    console.log("  print tool present :", html.includes("Printable Summary Sheet"));
    console.log("  scanner present    :", html.includes("Scan or choose a document"));
  } catch (e) {
    console.log("RENDER CRASHED:", e.constructor.name + ":", e.message);
    console.log((e.stack || "").split("\n").slice(0, 10).join("\n"));
    process.exitCode = 2;
    return;
  }

  console.log("— rendering the public Helper …");
  try {
    const html = renderToStaticMarkup(React.createElement(Helper, { requireAuth: false }));
    console.log("PUBLIC RENDER OK — bytes:", html.length);
  } catch (e) {
    console.log("PUBLIC RENDER CRASHED:", e.constructor.name + ":", e.message);
    console.log((e.stack || "").split("\n").slice(0, 10).join("\n"));
    process.exitCode = 3;
  }
}

main().catch((e) => { console.error("HARNESS ERROR:", e); process.exit(9); });
