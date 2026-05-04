import { useState } from "react";

function Input({ label, value, onChange, type = "number", testid, placeholder }) {
  return (
    <label className="block">
      <span className="overline text-ink/60">{label}</span>
      <input type={type} value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder}
        className="w-full mt-1 px-3 py-2 bg-white border border-ink/20 focus:border-ink focus:outline-none focus:ring-2 focus:ring-signal font-mono text-sm"
        data-testid={testid} />
    </label>
  );
}

function SubmitBtn({ onClick, children = "Submit for Grading" }) {
  return <button onClick={onClick} className="btn-primary mt-5" data-testid="btn-sim-submit">{children}</button>;
}

// 1. Basic Circuit
function BasicCircuit({ onSubmit }) {
  const [s, set] = useState({ voltage: 12, r1: 10, r2: 20, r3: 30, config: "series", total_r: "", total_i: "" });
  const up = (k) => (v) => set({ ...s, [k]: v });
  return (
    <div className="space-y-4">
      <div className="grid sm:grid-cols-2 gap-3">
        <Input label="Source Voltage (V)" value={s.voltage} onChange={up("voltage")} testid="bc-voltage" />
        <div>
          <span className="overline text-ink/60">Configuration</span>
          <div className="flex gap-2 mt-1">
            {["series", "parallel"].map((c) => (
              <button key={c} onClick={() => up("config")(c)}
                className={`px-4 py-2 text-xs font-bold uppercase border ${s.config === c ? "bg-ink text-white" : "bg-white text-ink border-ink/20"}`}
                data-testid={`bc-config-${c}`}>{c}</button>
            ))}
          </div>
        </div>
      </div>
      <div className="grid sm:grid-cols-3 gap-3">
        <Input label="R1 (Ω)" value={s.r1} onChange={up("r1")} testid="bc-r1" />
        <Input label="R2 (Ω)" value={s.r2} onChange={up("r2")} testid="bc-r2" />
        <Input label="R3 (Ω)" value={s.r3} onChange={up("r3")} testid="bc-r3" />
      </div>
      <div className="border-t border-ink/10 pt-4">
        <div className="overline text-copper mb-2">Your Answer</div>
        <div className="grid sm:grid-cols-2 gap-3">
          <Input label="Total Resistance (Ω)" value={s.total_r} onChange={up("total_r")} testid="bc-tr" />
          <Input label="Total Current (A)" value={s.total_i} onChange={up("total_i")} testid="bc-ti" />
        </div>
      </div>
      <SubmitBtn onClick={() => onSubmit(s)} />
    </div>
  );
}

// 2. Switch wiring
function SwitchWiring({ onSubmit }) {
  const [s, set] = useState({ hot_to: "", neutral_to: "", ground_to: "" });
  const opts = ["brass", "silver", "green"];
  return (
    <div className="space-y-4">
      <div className="text-sm text-ink/70 italic">Match each conductor to the correct terminal color on the duplex receptacle.</div>
      {[["hot_to", "Hot (black)"], ["neutral_to", "Neutral (white)"], ["ground_to", "Ground (bare)"]].map(([k, label]) => (
        <div key={k} className="flex items-center gap-4">
          <div className="w-40 font-mono text-sm">{label}</div>
          <div className="flex gap-2">
            {opts.map((o) => (
              <button key={o} onClick={() => set({ ...s, [k]: o })}
                className={`px-3 py-2 text-xs font-bold uppercase border ${s[k] === o ? "bg-ink text-white" : "bg-white text-ink border-ink/20"}`}
                data-testid={`sw-${k}-${o}`}>{o} screw</button>
            ))}
          </div>
        </div>
      ))}
      <SubmitBtn onClick={() => onSubmit(s)} />
    </div>
  );
}

// 3. Panel labeling
function PanelLabeling({ onSubmit }) {
  const SLOTS = ["slot_0", "slot_1", "slot_2", "slot_3", "slot_4", "slot_5"];
  const BREAKERS = ["15A", "20A", "20A GFCI", "15A", "30A 2P", "20A"];
  const CIRCUITS = ["kitchen", "bedroom", "bathroom_gfci", "living_room", "hvac", "laundry"];
  const [s, set] = useState({});
  return (
    <div className="space-y-3">
      <div className="text-sm text-ink/70 italic">Match each breaker to its branch circuit.</div>
      {SLOTS.map((k, i) => (
        <div key={k} className="flex items-center gap-3">
          <div className="w-10 font-mono font-bold">#{i + 1}</div>
          <div className="w-24 badge-ink text-center">{BREAKERS[i]}</div>
          <select value={s[k] || ""} onChange={(e) => set({ ...s, [k]: e.target.value })}
            className="flex-1 px-3 py-2 border border-ink/20 font-mono text-sm"
            data-testid={`pl-${k}`}>
            <option value="">— select circuit —</option>
            {CIRCUITS.map((c) => <option key={c} value={c}>{c.replace(/_/g, " ")}</option>)}
          </select>
        </div>
      ))}
      <SubmitBtn onClick={() => onSubmit(s)} />
    </div>
  );
}

// 4. Conduit calc
function ConduitCalc({ onSubmit }) {
  const [s, set] = useState({ rise: 6, angle: 30, distance: "", shrink: "" });
  const up = (k) => (v) => set({ ...s, [k]: v });
  return (
    <div className="space-y-4">
      <div className="grid sm:grid-cols-2 gap-3">
        <Input label="Rise / Offset Height (in)" value={s.rise} onChange={up("rise")} testid="cc-rise" />
        <label>
          <span className="overline text-ink/60">Bend Angle (°)</span>
          <select value={s.angle} onChange={(e) => up("angle")(e.target.value)}
            className="w-full mt-1 px-3 py-2 border border-ink/20 font-mono text-sm" data-testid="cc-angle">
            {[10, 22, 30, 45, 60].map((a) => <option key={a} value={a}>{a}°</option>)}
          </select>
        </label>
      </div>
      <div className="border-t border-ink/10 pt-4">
        <div className="overline text-copper mb-2">Your Answer</div>
        <div className="grid sm:grid-cols-2 gap-3">
          <Input label="Distance Between Marks (in)" value={s.distance} onChange={up("distance")} testid="cc-dist" />
          <Input label="Shrink (in)" value={s.shrink} onChange={up("shrink")} testid="cc-shrink" />
        </div>
      </div>
      <SubmitBtn onClick={() => onSubmit(s)} />
    </div>
  );
}

// 5. Voltage drop
function VDrop({ onSubmit }) {
  const [s, set] = useState({ length_ft: 100, current_a: 15, awg: 12, source_v: 120, vd_pct: "" });
  const up = (k) => (v) => set({ ...s, [k]: v });
  return (
    <div className="space-y-4">
      <div className="grid sm:grid-cols-2 gap-3">
        <Input label="One-way Length (ft)" value={s.length_ft} onChange={up("length_ft")} testid="vd-len" />
        <Input label="Current (A)" value={s.current_a} onChange={up("current_a")} testid="vd-i" />
        <label>
          <span className="overline text-ink/60">Conductor Size (AWG)</span>
          <select value={s.awg} onChange={(e) => up("awg")(e.target.value)}
            className="w-full mt-1 px-3 py-2 border border-ink/20 font-mono text-sm" data-testid="vd-awg">
            {[14, 12, 10, 8, 6, 4, 2].map((a) => <option key={a} value={a}>{a} AWG</option>)}
          </select>
        </label>
        <Input label="Source Voltage (V)" value={s.source_v} onChange={up("source_v")} testid="vd-sv" />
      </div>
      <div className="border-t border-ink/10 pt-4">
        <Input label="Your Answer: Voltage Drop (%)" value={s.vd_pct} onChange={up("vd_pct")} testid="vd-pct" />
      </div>
      <SubmitBtn onClick={() => onSubmit(s)} />
    </div>
  );
}

// 6. Solar config
function SolarConfig({ onSubmit }) {
  const [s, set] = useState({ daily_kwh: 5, sun_hours: 5, sys_v: 48, autonomy_days: 2, pv_watts: "", bank_ah: "" });
  const up = (k) => (v) => set({ ...s, [k]: v });
  return (
    <div className="space-y-4">
      <div className="grid sm:grid-cols-2 gap-3">
        <Input label="Daily Load (kWh)" value={s.daily_kwh} onChange={up("daily_kwh")} testid="sc-kwh" />
        <Input label="Peak Sun Hours" value={s.sun_hours} onChange={up("sun_hours")} testid="sc-sun" />
        <Input label="System Voltage (V)" value={s.sys_v} onChange={up("sys_v")} testid="sc-sv" />
        <Input label="Days of Autonomy" value={s.autonomy_days} onChange={up("autonomy_days")} testid="sc-auto" />
      </div>
      <div className="border-t border-ink/10 pt-4">
        <div className="overline text-copper mb-2">Your Answer</div>
        <div className="grid sm:grid-cols-2 gap-3">
          <Input label="PV Array (W)" value={s.pv_watts} onChange={up("pv_watts")} testid="sc-pv" />
          <Input label="Battery Bank (Ah)" value={s.bank_ah} onChange={up("bank_ah")} testid="sc-bank" />
        </div>
      </div>
      <SubmitBtn onClick={() => onSubmit(s)} />
    </div>
  );
}

// 7. LOTO sequence
function Loto({ onSubmit }) {
  const STEPS = ["notify", "shutdown", "lockout", "tagout", "verify_dead", "try_start"];
  const LABELS = {
    notify: "Notify affected workers",
    shutdown: "Shut down equipment at the control",
    lockout: "Lockout disconnect with personal padlock",
    tagout: "Apply tag with name & date",
    verify_dead: "Verify de-energized (test-verify-test)",
    try_start: "Attempt to restart — confirm dead",
  };
  const [seq, setSeq] = useState([]);
  const remaining = STEPS.filter((s) => !seq.includes(s));
  return (
    <div className="space-y-4">
      <div className="text-sm text-ink/70 italic">Click steps in the correct order.</div>
      <div className="card-flat p-4 bg-bone">
        <div className="overline text-copper mb-2">Your Sequence</div>
        <ol className="space-y-1 text-sm font-mono">
          {seq.length === 0 && <li className="text-ink/40">Empty — start with step 1</li>}
          {seq.map((k, i) => <li key={k}>{i + 1}. {LABELS[k]}</li>)}
        </ol>
      </div>
      <div className="flex flex-wrap gap-2">
        {remaining.map((k) => (
          <button key={k} onClick={() => setSeq([...seq, k])}
            className="px-3 py-2 text-xs font-bold uppercase border border-ink/20 hover:bg-ink hover:text-white transition-colors"
            data-testid={`loto-${k}`}>{LABELS[k]}</button>
        ))}
      </div>
      <div className="flex gap-2">
        <button onClick={() => setSeq([])} className="btn-ghost" data-testid="loto-reset">Reset</button>
        <SubmitBtn onClick={() => onSubmit({ sequence: seq })} />
      </div>
    </div>
  );
}

// 8. Troubleshooting
function Troubleshooting({ onSubmit }) {
  const CHOICES = [
    { k: "test_breaker", l: "Check the breaker at the panel" },
    { k: "test_receptacle_voltage", l: "Measure voltage at the dead receptacle" },
    { k: "test_neutral_continuity", l: "Check neutral continuity to panel" },
    { k: "find_open_neutral", l: "Locate open neutral at junction box" },
    { k: "replace_receptacle", l: "Replace the receptacle blindly" },
    { k: "check_load", l: "Unplug all appliances on the circuit" },
  ];
  const [path, setPath] = useState([]);
  return (
    <div className="space-y-4">
      <div className="text-sm text-ink/70 italic">A duplex receptacle on a 20A circuit reads 0V. Breaker is ON. Choose your diagnostic path.</div>
      <div className="card-flat p-4 bg-bone">
        <div className="overline text-copper mb-2">Your Diagnostic Path</div>
        <ol className="space-y-1 text-sm font-mono">
          {path.length === 0 && <li className="text-ink/40">Pick your first step →</li>}
          {path.map((k, i) => <li key={i}>{i + 1}. {CHOICES.find((c) => c.k === k)?.l}</li>)}
        </ol>
      </div>
      <div className="grid sm:grid-cols-2 gap-2">
        {CHOICES.map((c) => (
          <button key={c.k} onClick={() => setPath([...path, c.k])}
            className="text-left px-3 py-2 text-sm border border-ink/20 hover:bg-ink hover:text-white transition-colors"
            data-testid={`ts-${c.k}`}>{c.l}</button>
        ))}
      </div>
      <div className="flex gap-2">
        <button onClick={() => setPath([])} className="btn-ghost" data-testid="ts-reset">Reset</button>
        <SubmitBtn onClick={() => onSubmit({ path })} />
      </div>
    </div>
  );
}

// 9. Load Balance
function LoadBalance({ onSubmit }) {
  const LOADS = [
    { k: "c1", l: "Kitchen outlets", w: 1500 },
    { k: "c2", l: "Master bedroom", w: 800 },
    { k: "c3", l: "Living room", w: 1200 },
    { k: "c4", l: "Bathroom GFCI", w: 600 },
    { k: "c5", l: "Laundry", w: 1800 },
    { k: "c6", l: "Hallway lights", w: 400 },
  ];
  const [a, setA] = useState({});
  const phaseA = LOADS.filter((l) => a[l.k] === "A").reduce((s, l) => s + l.w, 0);
  const phaseB = LOADS.filter((l) => a[l.k] === "B").reduce((s, l) => s + l.w, 0);
  return (
    <div className="space-y-4">
      <div className="text-sm text-ink/70 italic">Assign each circuit to Phase A or Phase B. Balance to within 10%.</div>
      <div className="grid grid-cols-2 gap-4">
        <div className="p-3 bg-copper/10 border border-copper text-center"><div className="overline text-copper">Phase A</div><div className="font-heading text-2xl font-black">{phaseA}W</div></div>
        <div className="p-3 bg-ink/5 border border-ink text-center"><div className="overline text-ink">Phase B</div><div className="font-heading text-2xl font-black">{phaseB}W</div></div>
      </div>
      <div className="space-y-2">
        {LOADS.map((l) => (
          <div key={l.k} className="flex items-center gap-3 p-2 border border-ink/10">
            <div className="flex-1 text-sm"><span className="font-bold">{l.l}</span> <span className="text-ink/60 font-mono">· {l.w}W</span></div>
            {["A", "B"].map((p) => (
              <button key={p} onClick={() => setA({ ...a, [l.k]: p })}
                className={`w-10 py-1.5 text-xs font-bold ${a[l.k] === p ? (p === "A" ? "bg-copper text-white" : "bg-ink text-white") : "bg-white border border-ink/20"}`}
                data-testid={`lb-${l.k}-${p}`}>{p}</button>
            ))}
          </div>
        ))}
      </div>
      <SubmitBtn onClick={() => onSubmit({ assignments: a })} />
    </div>
  );
}

const Simulators = {
  basic_circuit: BasicCircuit,
  switch_wiring: SwitchWiring,
  panel_labeling: PanelLabeling,
  conduit_calc: ConduitCalc,
  vdrop: VDrop,
  solar_config: SolarConfig,
  loto: Loto,
  troubleshooting: Troubleshooting,
  load_balance: LoadBalance,
};

export default Simulators;
