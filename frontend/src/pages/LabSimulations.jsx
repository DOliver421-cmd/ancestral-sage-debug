import { useState } from "react";
import AppShell from "../components/AppShell";
import { Cable, LayoutGrid, Scissors, Sun, ShieldOff, CheckCircle, XCircle, RotateCcw, ChevronRight } from "lucide-react";

// ─── Wiring Circuits Simulator ─────────────────────────────────────────────

function WiringCircuit() {
  const [config, setConfig] = useState("series");
  const [bulbs, setBulbs] = useState([true, true, true]);
  const [checked, setChecked] = useState(false);
  const [result, setResult] = useState(null);

  const toggle = (i) => {
    const next = [...bulbs];
    next[i] = !next[i];
    setBulbs(next);
    setChecked(false);
    setResult(null);
  };

  const check = () => {
    setChecked(true);
    const allOn = bulbs.every(Boolean);
    const anyOn = bulbs.some(Boolean);
    if (config === "series") {
      setResult(allOn
        ? { pass: true, msg: "Correct! In a series circuit all bulbs must be on for current to flow." }
        : { pass: false, msg: "In series: if one bulb is off, the circuit breaks — all go dark." }
      );
    } else {
      setResult(anyOn
        ? { pass: true, msg: "Correct! In a parallel circuit each bulb has its own path — others stay lit." }
        : { pass: false, msg: "All branches are open. At least one must be closed for current to flow." }
      );
    }
  };

  const reset = () => { setBulbs([true, true, true]); setChecked(false); setResult(null); };

  const circuitOn = config === "series" ? bulbs.every(Boolean) : bulbs.some(Boolean);

  return (
    <div>
      <div className="flex gap-4 mb-6">
        {["series", "parallel"].map(c => (
          <button key={c} onClick={() => { setConfig(c); reset(); }}
            className={`px-4 py-2 rounded font-bold text-sm border-2 transition-all ${config === c ? "border-copper bg-copper text-white" : "border-ink/20 text-ink/70 hover:border-copper"}`}>
            {c === "series" ? "Series Circuit" : "Parallel Circuit"}
          </button>
        ))}
      </div>

      <div className="bg-ink/5 rounded-lg p-6 mb-6">
        <p className="text-sm text-ink/60 mb-4 font-bold uppercase">
          {config === "series" ? "All bulbs in one loop — one break stops everything" : "Each bulb on its own branch — one break doesn't stop others"}
        </p>
        <div className="flex items-center gap-4 justify-center flex-wrap">
          {/* Power source */}
          <div className="flex flex-col items-center">
            <div className={`w-10 h-16 rounded border-4 flex items-center justify-center font-bold text-xs ${circuitOn ? "border-green-500 bg-green-100 text-green-700" : "border-red-400 bg-red-50 text-red-600"}`}>
              PWR
            </div>
            <span className="text-xs text-ink/60 mt-1">Source</span>
          </div>

          {config === "series" && <div className={`h-1 w-6 ${circuitOn ? "bg-green-500" : "bg-red-400"}`} />}

          {bulbs.map((on, i) => (
            <div key={i} className="flex items-center gap-2">
              {config === "parallel" && i > 0 && <div className="w-1 h-8 bg-ink/30 mx-1" />}
              <div className="flex flex-col items-center">
                <button
                  onClick={() => toggle(i)}
                  className={`w-14 h-14 rounded-full border-4 flex items-center justify-center text-2xl transition-all ${
                    on ? "border-yellow-400 bg-yellow-100 shadow-lg shadow-yellow-200" : "border-ink/30 bg-white text-ink/30"
                  }`}
                  title="Click to toggle"
                >
                  {on ? "💡" : "🔦"}
                </button>
                <span className="text-xs text-ink/60 mt-1">Bulb {i + 1}</span>
                <span className={`text-xs font-bold ${on ? "text-green-600" : "text-red-500"}`}>{on ? "ON" : "OFF"}</span>
              </div>
              {config === "series" && i < bulbs.length - 1 && (
                <div className={`h-1 w-6 ${on && bulbs[i + 1] ? "bg-green-500" : "bg-red-400"}`} />
              )}
            </div>
          ))}

          {config === "series" && <div className={`h-1 w-6 ${circuitOn ? "bg-green-500" : "bg-red-400"}`} />}

          <div className="flex flex-col items-center">
            <div className={`w-10 h-10 rounded-full border-4 flex items-center justify-center text-sm font-bold ${circuitOn ? "border-green-500 bg-green-100 text-green-700" : "border-red-400 bg-red-50 text-red-600"}`}>
              {circuitOn ? "✓" : "✗"}
            </div>
            <span className="text-xs text-ink/60 mt-1">Load</span>
          </div>
        </div>
        <p className="text-center mt-4 text-sm font-bold text-ink/70">Click bulbs to toggle ON/OFF</p>
      </div>

      <div className="flex gap-3">
        <button onClick={check} className="px-6 py-2 bg-copper text-white rounded font-bold hover:bg-copper/80 transition-colors">
          Check My Circuit
        </button>
        <button onClick={reset} className="px-4 py-2 border border-ink/20 rounded font-bold hover:border-copper transition-colors flex items-center gap-2">
          <RotateCcw className="w-4 h-4" /> Reset
        </button>
      </div>

      {checked && result && (
        <div className={`mt-4 p-4 rounded-lg border flex items-start gap-3 ${result.pass ? "bg-green-50 border-green-300" : "bg-red-50 border-red-300"}`}>
          {result.pass ? <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" /> : <XCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />}
          <p className={`font-bold text-sm ${result.pass ? "text-green-800" : "text-red-800"}`}>{result.msg}</p>
        </div>
      )}
    </div>
  );
}

// ─── Panel Board Simulator ──────────────────────────────────────────────────

const BREAKER_SIZES = [15, 20, 30, 50];
const CIRCUITS = [
  { label: "Kitchen Outlets", amps: 20, double: false },
  { label: "Bedroom Lights", amps: 15, double: false },
  { label: "Dryer", amps: 30, double: true },
  { label: "HVAC", amps: 50, double: true },
  { label: "Bathroom GFCI", amps: 20, double: false },
  { label: "Garage", amps: 20, double: false },
];

function PanelBoard() {
  const [assignments, setAssignments] = useState({});
  const [checked, setChecked] = useState(false);
  const [errors, setErrors] = useState([]);

  const assign = (circuitIdx, size) => {
    setAssignments(prev => ({ ...prev, [circuitIdx]: size }));
    setChecked(false);
    setErrors([]);
  };

  const check = () => {
    const errs = [];
    CIRCUITS.forEach((c, i) => {
      const selected = assignments[i];
      if (!selected) { errs.push(`${c.label}: No breaker assigned.`); return; }
      if (selected < c.amps) errs.push(`${c.label}: Undersized — needs ${c.amps}A, got ${selected}A.`);
      if (selected > c.amps * 1.5) errs.push(`${c.label}: Oversized — ${selected}A breaker is too large for ${c.amps}A circuit.`);
    });
    setErrors(errs);
    setChecked(true);
  };

  const reset = () => { setAssignments({}); setChecked(false); setErrors([]); };
  const allAssigned = CIRCUITS.every((_, i) => assignments[i]);

  return (
    <div>
      <p className="text-sm text-ink/60 mb-6">Assign the correct breaker size to each circuit. Match amps to the load requirement.</p>
      <div className="grid md:grid-cols-2 gap-4 mb-6">
        {CIRCUITS.map((c, i) => (
          <div key={i} className={`border-2 rounded-lg p-4 transition-all ${
            checked
              ? errors.some(e => e.startsWith(c.label))
                ? "border-red-400 bg-red-50"
                : assignments[i] ? "border-green-400 bg-green-50" : "border-ink/20"
              : "border-ink/10 bg-white"
          }`}>
            <div className="flex items-start justify-between mb-3">
              <div>
                <p className="font-bold text-ink">{c.label}</p>
                <p className="text-xs text-ink/60">{c.double ? "240V Double-pole" : "120V Single-pole"} · {c.amps}A load</p>
              </div>
              {checked && assignments[i] && !errors.some(e => e.startsWith(c.label)) && (
                <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0" />
              )}
              {checked && errors.some(e => e.startsWith(c.label)) && (
                <XCircle className="w-5 h-5 text-red-500 flex-shrink-0" />
              )}
            </div>
            <div className="flex gap-2 flex-wrap">
              {BREAKER_SIZES.map(sz => (
                <button key={sz}
                  onClick={() => assign(i, sz)}
                  className={`px-3 py-1 rounded text-sm font-bold border-2 transition-all ${
                    assignments[i] === sz
                      ? "border-copper bg-copper text-white"
                      : "border-ink/20 text-ink/70 hover:border-copper"
                  }`}
                >
                  {sz}A
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>

      <div className="flex gap-3">
        <button onClick={check} disabled={!allAssigned}
          className="px-6 py-2 bg-copper text-white rounded font-bold hover:bg-copper/80 transition-colors disabled:opacity-40">
          Check Panel Schedule
        </button>
        <button onClick={reset} className="px-4 py-2 border border-ink/20 rounded font-bold hover:border-copper transition-colors flex items-center gap-2">
          <RotateCcw className="w-4 h-4" /> Reset
        </button>
      </div>

      {checked && (
        <div className={`mt-4 p-4 rounded-lg border ${errors.length === 0 ? "bg-green-50 border-green-300" : "bg-red-50 border-red-300"}`}>
          {errors.length === 0 ? (
            <p className="font-bold text-green-800 flex items-center gap-2"><CheckCircle className="w-5 h-5" /> Panel schedule correct! All breakers properly sized.</p>
          ) : (
            <div>
              <p className="font-bold text-red-800 mb-2">Fix these errors ({errors.length}):</p>
              <ul className="space-y-1">
                {errors.map((e, i) => <li key={i} className="text-sm text-red-700">• {e}</li>)}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ─── Conduit Bending Simulator ──────────────────────────────────────────────

const BEND_TYPES = [
  { key: "90", label: "90° Stub-up", stub: 12, multiplier: 6, deduction: 6 },
  { key: "offset", label: "Offset Bend", stub: 8, multiplier: 2.5, deduction: 0 },
  { key: "saddle", label: "3-Point Saddle", stub: 6, multiplier: 2.5, deduction: 0 },
];

function ConduitBending() {
  const [bendType, setBendType] = useState("90");
  const [stubLength, setStubLength] = useState(12);
  const [userMark, setUserMark] = useState("");
  const [checked, setChecked] = useState(false);
  const [result, setResult] = useState(null);

  const bt = BEND_TYPES.find(b => b.key === bendType);
  const correctMark = bt.key === "90"
    ? (stubLength - bt.deduction).toFixed(1)
    : (stubLength * bt.multiplier).toFixed(1);

  const check = () => {
    const user = parseFloat(userMark);
    const correct = parseFloat(correctMark);
    const tolerance = 0.25;
    setChecked(true);
    if (isNaN(user)) {
      setResult({ pass: false, msg: "Enter a measurement to check." });
    } else if (Math.abs(user - correct) <= tolerance) {
      setResult({ pass: true, msg: `Correct! Mark at ${correctMark}" is within tolerance. Good bend!` });
    } else {
      setResult({ pass: false, msg: `Off by ${Math.abs(user - correct).toFixed(2)}". Correct mark is ${correctMark}". ${bt.key === "90" ? `Formula: Stub (${stubLength}") − Deduction (${bt.deduction}") = ${correctMark}"` : `Formula: Rise × ${bt.multiplier} = ${correctMark}"`}` });
    }
  };

  const reset = () => { setUserMark(""); setChecked(false); setResult(null); };

  return (
    <div>
      <div className="flex gap-3 mb-6 flex-wrap">
        {BEND_TYPES.map(b => (
          <button key={b.key} onClick={() => { setBendType(b.key); reset(); }}
            className={`px-4 py-2 rounded font-bold text-sm border-2 transition-all ${bendType === b.key ? "border-copper bg-copper text-white" : "border-ink/20 text-ink/70 hover:border-copper"}`}>
            {b.label}
          </button>
        ))}
      </div>

      <div className="bg-ink text-white rounded-lg p-6 mb-6">
        <p className="text-signal font-bold uppercase text-xs mb-3">Scenario</p>
        {bendType === "90" && (
          <>
            <p className="text-lg font-bold mb-2">Bend a 90° stub-up to reach a box {stubLength}" from the floor.</p>
            <p className="text-white/70 text-sm">Using a ½" EMT bender (deduction = {bt.deduction}"). Formula: Stub height − Deduction = Mark distance from end.</p>
          </>
        )}
        {bendType === "offset" && (
          <>
            <p className="text-lg font-bold mb-2">Clear an {stubLength}" obstacle using an offset.</p>
            <p className="text-white/70 text-sm">30°/30° offset. Formula: Rise × {bt.multiplier} = distance between bends.</p>
          </>
        )}
        {bendType === "saddle" && (
          <>
            <p className="text-lg font-bold mb-2">Saddle over a {stubLength}" wide obstruction.</p>
            <p className="text-white/70 text-sm">3-point saddle. Formula: Width × {bt.multiplier} = spread between marks.</p>
          </>
        )}

        {bendType === "90" && (
          <div className="mt-4 flex gap-3 items-center">
            <label className="text-sm text-white/70">Stub height (in):</label>
            <input type="number" value={stubLength} min={6} max={36}
              onChange={e => { setStubLength(Number(e.target.value)); reset(); }}
              className="w-20 bg-white/10 border border-white/30 rounded px-2 py-1 text-white text-center"
            />
          </div>
        )}
      </div>

      <div className="mb-6">
        <label className="block font-bold text-ink mb-2">Where do you mark the conduit? (inches from end)</label>
        <div className="flex gap-3 items-center">
          <input
            type="number"
            step="0.25"
            value={userMark}
            onChange={e => { setUserMark(e.target.value); setChecked(false); setResult(null); }}
            placeholder="e.g. 6.00"
            className="w-32 border-2 border-ink/20 rounded px-3 py-2 text-ink focus:outline-none focus:border-copper text-lg font-bold"
          />
          <span className="text-ink/60 font-bold">inches</span>
        </div>
      </div>

      <div className="flex gap-3">
        <button onClick={check} className="px-6 py-2 bg-copper text-white rounded font-bold hover:bg-copper/80 transition-colors">
          Check Measurement
        </button>
        <button onClick={reset} className="px-4 py-2 border border-ink/20 rounded font-bold hover:border-copper transition-colors flex items-center gap-2">
          <RotateCcw className="w-4 h-4" /> Reset
        </button>
      </div>

      {checked && result && (
        <div className={`mt-4 p-4 rounded-lg border flex items-start gap-3 ${result.pass ? "bg-green-50 border-green-300" : "bg-red-50 border-red-300"}`}>
          {result.pass ? <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" /> : <XCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />}
          <p className={`font-bold text-sm ${result.pass ? "text-green-800" : "text-red-800"}`}>{result.msg}</p>
        </div>
      )}
    </div>
  );
}

// ─── Solar System Configurator ──────────────────────────────────────────────

const PANELS = [
  { watts: 100, volts: 12, label: "100W 12V" },
  { watts: 200, volts: 24, label: "200W 24V" },
  { watts: 400, volts: 48, label: "400W 48V" },
];
const CONTROLLERS = [
  { type: "PWM", efficiency: 0.75, maxAmps: 30, label: "PWM 30A" },
  { type: "MPPT", efficiency: 0.95, maxAmps: 40, label: "MPPT 40A" },
];
const BATTERIES = [
  { ah: 100, volts: 12, label: "100Ah 12V" },
  { ah: 200, volts: 24, label: "200Ah 24V" },
  { ah: 200, volts: 48, label: "200Ah 48V" },
];

function SolarConfig() {
  const [panelIdx, setPanelIdx] = useState(1);
  const [panelCount, setPanelCount] = useState(2);
  const [ctrlIdx, setCtrlIdx] = useState(1);
  const [battIdx, setBattIdx] = useState(1);
  const [checked, setChecked] = useState(false);
  const [issues, setIssues] = useState([]);

  const panel = PANELS[panelIdx];
  const ctrl = CONTROLLERS[ctrlIdx];
  const batt = BATTERIES[battIdx];

  const totalWatts = panel.watts * panelCount;
  const arrayAmps = (totalWatts / panel.volts).toFixed(1);
  const usableAh = (batt.ah * 0.8).toFixed(0);
  const dailyKwh = (totalWatts * 5 * ctrl.efficiency / 1000).toFixed(2);

  const check = () => {
    const errs = [];
    if (panel.volts !== batt.volts) errs.push(`Voltage mismatch: panels are ${panel.volts}V but battery bank is ${batt.volts}V.`);
    if (parseFloat(arrayAmps) > ctrl.maxAmps) errs.push(`Array output (${arrayAmps}A) exceeds controller rating (${ctrl.maxAmps}A). Add another controller or reduce panels.`);
    if (ctrl.type === "PWM" && panel.volts > batt.volts) errs.push("PWM controllers require panel voltage to match battery voltage.");
    setIssues(errs);
    setChecked(true);
  };

  const reset = () => { setChecked(false); setIssues([]); };

  return (
    <div>
      <div className="grid md:grid-cols-3 gap-4 mb-6">
        <div className="bg-white border border-ink/10 rounded-lg p-4">
          <p className="font-bold text-sm text-ink/60 mb-3 uppercase">Solar Panels</p>
          <div className="space-y-2">
            {PANELS.map((p, i) => (
              <button key={i} onClick={() => { setPanelIdx(i); reset(); }}
                className={`w-full text-left px-3 py-2 rounded border-2 text-sm font-bold transition-all ${panelIdx === i ? "border-copper bg-copper/10 text-copper" : "border-ink/10 text-ink/70 hover:border-copper/50"}`}>
                {p.label}
              </button>
            ))}
          </div>
          <div className="mt-3">
            <label className="text-xs text-ink/60 font-bold">Quantity:</label>
            <input type="number" min={1} max={8} value={panelCount}
              onChange={e => { setPanelCount(Number(e.target.value)); reset(); }}
              className="ml-2 w-16 border border-ink/20 rounded px-2 py-1 text-sm text-center" />
          </div>
        </div>

        <div className="bg-white border border-ink/10 rounded-lg p-4">
          <p className="font-bold text-sm text-ink/60 mb-3 uppercase">Charge Controller</p>
          <div className="space-y-2">
            {CONTROLLERS.map((c, i) => (
              <button key={i} onClick={() => { setCtrlIdx(i); reset(); }}
                className={`w-full text-left px-3 py-2 rounded border-2 text-sm font-bold transition-all ${ctrlIdx === i ? "border-copper bg-copper/10 text-copper" : "border-ink/10 text-ink/70 hover:border-copper/50"}`}>
                {c.label} <span className="font-normal text-xs">({(c.efficiency * 100).toFixed(0)}% eff.)</span>
              </button>
            ))}
          </div>
        </div>

        <div className="bg-white border border-ink/10 rounded-lg p-4">
          <p className="font-bold text-sm text-ink/60 mb-3 uppercase">Battery Bank</p>
          <div className="space-y-2">
            {BATTERIES.map((b, i) => (
              <button key={i} onClick={() => { setBattIdx(i); reset(); }}
                className={`w-full text-left px-3 py-2 rounded border-2 text-sm font-bold transition-all ${battIdx === i ? "border-copper bg-copper/10 text-copper" : "border-ink/10 text-ink/70 hover:border-copper/50"}`}>
                {b.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="bg-ink/5 rounded-lg p-5 mb-6">
        <p className="font-bold text-sm text-ink/60 mb-3 uppercase">System Summary</p>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
          <div><p className="text-2xl font-heading font-bold text-ink">{totalWatts}W</p><p className="text-xs text-ink/60">Array Size</p></div>
          <div><p className="text-2xl font-heading font-bold text-ink">{arrayAmps}A</p><p className="text-xs text-ink/60">Array Output</p></div>
          <div><p className="text-2xl font-heading font-bold text-ink">{usableAh}Ah</p><p className="text-xs text-ink/60">Usable Storage</p></div>
          <div><p className="text-2xl font-heading font-bold text-ink">{dailyKwh}kWh</p><p className="text-xs text-ink/60">Daily Est.</p></div>
        </div>
      </div>

      <div className="flex gap-3">
        <button onClick={check} className="px-6 py-2 bg-copper text-white rounded font-bold hover:bg-copper/80 transition-colors">
          Validate System
        </button>
        <button onClick={reset} className="px-4 py-2 border border-ink/20 rounded font-bold hover:border-copper transition-colors flex items-center gap-2">
          <RotateCcw className="w-4 h-4" /> Reset
        </button>
      </div>

      {checked && (
        <div className={`mt-4 p-4 rounded-lg border ${issues.length === 0 ? "bg-green-50 border-green-300" : "bg-red-50 border-red-300"}`}>
          {issues.length === 0 ? (
            <p className="font-bold text-green-800 flex items-center gap-2"><CheckCircle className="w-5 h-5" /> System validated! Voltages match, controller is correctly sized.</p>
          ) : (
            <div>
              <p className="font-bold text-red-800 mb-2">Design issues found:</p>
              <ul className="space-y-1">{issues.map((e, i) => <li key={i} className="text-sm text-red-700">• {e}</li>)}</ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ─── Lockout / Tagout Simulator ─────────────────────────────────────────────

const LOTO_STEPS = [
  { id: 1, label: "Notify Affected Employees", desc: "Inform all workers in the area that maintenance will begin and energy isolation is required.", required: true },
  { id: 2, label: "Identify All Energy Sources", desc: "Locate electrical, pneumatic, hydraulic, and stored energy sources for this equipment.", required: true },
  { id: 3, label: "Shut Down Equipment", desc: "Use the normal stopping procedure to bring the machine to a complete stop.", required: true },
  { id: 4, label: "Isolate Energy Sources", desc: "Open disconnect switches, close valves, and block all energy isolating devices.", required: true },
  { id: 5, label: "Apply Lockout/Tagout Devices", desc: "Apply your personal lock and tag to each energy isolating device. One lock per worker.", required: true },
  { id: 6, label: "Release or Restrain Stored Energy", desc: "Bleed hydraulic lines, release capacitor charge, block gravity hazards, relieve spring tension.", required: true },
  { id: 7, label: "Verify Energy Isolation", desc: "Attempt to start equipment to confirm it cannot energize. Test with a meter before touching.", required: true },
];

function LOTOSim() {
  const [completed, setCompleted] = useState([]);
  const [submitted, setSubmitted] = useState(false);
  const [skipped, setSkipped] = useState([]);
  const [result, setResult] = useState(null);

  const toggle = (id) => {
    if (submitted) return;
    setCompleted(prev =>
      prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]
    );
  };

  const submit = () => {
    const missing = LOTO_STEPS.filter(s => s.required && !completed.includes(s.id));
    setSkipped(missing.map(s => s.id));
    setSubmitted(true);
    if (missing.length === 0) {
      setResult({ pass: true, msg: "All 7 steps completed correctly. Equipment is safely isolated. You may begin maintenance." });
    } else {
      setResult({ pass: false, msg: `${missing.length} required step${missing.length > 1 ? "s" : ""} skipped. In a real plant, this is a serious safety violation.` });
    }
  };

  const reset = () => { setCompleted([]); setSubmitted(false); setSkipped([]); setResult(null); };

  return (
    <div>
      <div className="bg-red-50 border-l-4 border-red-500 p-4 mb-6 rounded-r-lg">
        <p className="font-bold text-red-800 text-sm">SIMULATION — A motor control center requires maintenance. Complete all LOTO steps before proceeding.</p>
      </div>

      <div className="space-y-3 mb-6">
        {LOTO_STEPS.map(step => {
          const done = completed.includes(step.id);
          const isSkipped = skipped.includes(step.id);
          return (
            <button
              key={step.id}
              onClick={() => toggle(step.id)}
              disabled={submitted}
              className={`w-full text-left p-4 rounded-lg border-2 transition-all ${
                isSkipped ? "border-red-400 bg-red-50" :
                done ? "border-green-400 bg-green-50" :
                "border-ink/10 bg-white hover:border-copper/50"
              }`}
            >
              <div className="flex items-start gap-4">
                <div className={`w-8 h-8 rounded-full border-2 flex items-center justify-center font-bold text-sm flex-shrink-0 ${
                  isSkipped ? "border-red-500 bg-red-500 text-white" :
                  done ? "border-green-500 bg-green-500 text-white" :
                  "border-ink/30 text-ink/40"
                }`}>
                  {isSkipped ? "✗" : done ? "✓" : step.id}
                </div>
                <div>
                  <p className={`font-bold text-sm ${isSkipped ? "text-red-700" : done ? "text-green-800" : "text-ink"}`}>{step.label}</p>
                  <p className={`text-xs mt-1 ${done || isSkipped ? "text-ink/60" : "text-ink/50"}`}>{step.desc}</p>
                </div>
              </div>
            </button>
          );
        })}
      </div>

      <div className="flex gap-3">
        {!submitted ? (
          <button onClick={submit}
            className="px-6 py-2 bg-copper text-white rounded font-bold hover:bg-copper/80 transition-colors">
            Submit LOTO Procedure
          </button>
        ) : (
          <button onClick={reset} className="px-4 py-2 border border-ink/20 rounded font-bold hover:border-copper transition-colors flex items-center gap-2">
            <RotateCcw className="w-4 h-4" /> Try Again
          </button>
        )}
      </div>

      {submitted && result && (
        <div className={`mt-4 p-4 rounded-lg border flex items-start gap-3 ${result.pass ? "bg-green-50 border-green-300" : "bg-red-50 border-red-300"}`}>
          {result.pass ? <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" /> : <XCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />}
          <div>
            <p className={`font-bold text-sm ${result.pass ? "text-green-800" : "text-red-800"}`}>{result.msg}</p>
            {!result.pass && (
              <p className="text-xs text-red-700 mt-1">Skipped: {LOTO_STEPS.filter(s => skipped.includes(s.id)).map(s => s.label).join(", ")}</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Main Page ──────────────────────────────────────────────────────────────

const LABS = [
  { key: "wiring", icon: Cable, title: "Wiring Circuits", desc: "Build and test series and parallel circuits. Toggle bulbs to see how current flows.", Component: WiringCircuit },
  { key: "panel", icon: LayoutGrid, title: "Panel Board Practice", desc: "Assign breaker sizes to circuits. Check your panel schedule against NEC requirements.", Component: PanelBoard },
  { key: "conduit", icon: Scissors, title: "Conduit Bending", desc: "Calculate measurement marks for 90° stubs, offsets, and 3-point saddles.", Component: ConduitBending },
  { key: "solar", icon: Sun, title: "Solar System Config", desc: "Size PV arrays, pick charge controllers, configure a 48V battery bank.", Component: SolarConfig },
  { key: "loto", icon: ShieldOff, title: "Lockout/Tagout", desc: "Walk through the six-step LOTO procedure. Miss a step and find out why it matters.", Component: LOTOSim },
];

export default function LabSimulations() {
  const [active, setActive] = useState(null);
  const ActiveLab = active ? LABS.find(l => l.key === active)?.Component : null;
  const activeLab = active ? LABS.find(l => l.key === active) : null;

  return (
    <AppShell>
      <div className="px-6 md:px-10 py-10 max-w-6xl">
        <div className="overline text-copper">Interactive Labs</div>
        <h1 className="font-heading text-4xl font-bold mt-2">Virtual Shop Floor</h1>
        <p className="text-ink/60 mt-2 max-w-2xl">Practice the motions before you make them permanent. Each simulation mirrors a physical station in our workshop.</p>

        {!active ? (
          <>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5 mt-10">
              {LABS.map((l) => (
                <button
                  key={l.key}
                  onClick={() => setActive(l.key)}
                  data-testid={`lab-${l.key}`}
                  className="card-flat p-6 text-left hover:border-copper hover:shadow-lg transition-all group"
                >
                  <div className="w-12 h-12 bg-ink text-signal flex items-center justify-center mb-5 group-hover:bg-copper transition-colors">
                    <l.icon className="w-6 h-6" strokeWidth={2.5} />
                  </div>
                  <div className="font-heading text-xl font-bold">{l.title}</div>
                  <div className="text-sm text-ink/70 mt-3 leading-relaxed">{l.desc}</div>
                  <div className="mt-5 flex items-center gap-2 text-copper font-bold text-sm">
                    Open Simulation <ChevronRight className="w-4 h-4" />
                  </div>
                </button>
              ))}
            </div>

            <div className="mt-12 bg-ink text-white p-8">
              <div className="overline text-signal">On the Shop Floor</div>
              <div className="font-heading text-2xl font-bold mt-3">Every sim is matched to a physical station.</div>
              <div className="text-white/70 mt-3 max-w-2xl">Once you pass a simulation, your instructor unlocks the matching hands-on station — same tools, same diagram, same safety checklist.</div>
            </div>
          </>
        ) : (
          <div className="mt-8">
            <button
              onClick={() => setActive(null)}
              className="flex items-center gap-2 text-sm font-bold text-ink/60 hover:text-copper transition-colors mb-6"
            >
              ← Back to All Labs
            </button>

            <div className="flex items-center gap-4 mb-8">
              <div className="w-12 h-12 bg-ink text-signal flex items-center justify-center flex-shrink-0">
                {activeLab && <activeLab.icon className="w-6 h-6" strokeWidth={2.5} />}
              </div>
              <div>
                <h2 className="font-heading text-2xl font-bold text-ink">{activeLab?.title}</h2>
                <p className="text-ink/60 text-sm">{activeLab?.desc}</p>
              </div>
            </div>

            <div className="bg-white border border-ink/10 rounded-lg p-6">
              {ActiveLab && <ActiveLab />}
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}
