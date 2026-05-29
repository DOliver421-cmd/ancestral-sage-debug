import AppShell from "../components/AppShell";
import { Cable, LayoutGrid, Scissors, Sun, ShieldOff } from "lucide-react";

const LABS = [
  { key: "wiring", icon: Cable, title: "Wiring Circuits", desc: "Build series, parallel, 3-way, and 4-way circuits. Verify continuity and voltage drop on a virtual bench.", accent: "Coming soon" },
  { key: "panel", icon: LayoutGrid, title: "Panel Board Practice", desc: "Drag breakers, land feeders, size neutrals. Check your panel schedule against an NEC load calc.", accent: "Coming soon" },
  { key: "conduit", icon: Scissors, title: "Conduit Bending Simulator", desc: "Practice 90s, offsets, and 3-point saddles. Tolerance checker scores your bends.", accent: "Coming soon" },
  { key: "solar", icon: Sun, title: "Solar System Configuration", desc: "Size PV arrays, pick charge controllers, wire a 48V battery bank — all before the rooftop.", accent: "Coming soon" },
  { key: "loto", icon: ShieldOff, title: "Lockout/Tagout Scenario", desc: "Walk through six-step LOTO on a simulated plant. Miss a step and you go home.", accent: "Coming soon" },
];

export default function LabSimulations() {
  return (
    <AppShell>
      <div className="px-10 py-10 max-w-6xl">
        <div className="overline text-copper">Interactive Labs</div>
        <h1 className="font-heading text-4xl font-bold mt-2">Virtual Shop Floor</h1>
        <p className="text-ink/60 mt-2 max-w-2xl">Preview the interactive simulations that mirror our physical workshop. Practice the motions before you make them permanent.</p>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5 mt-10">
          {LABS.map((l) => (
            <div key={l.key} className="card-flat p-6" data-testid={`lab-${l.key}`}>
              <div className="w-12 h-12 bg-ink text-signal flex items-center justify-center mb-5">
                <l.icon className="w-6 h-6" strokeWidth={2.5} />
              </div>
              <div className="font-heading text-xl font-bold">{l.title}</div>
              <div className="text-sm text-ink/70 mt-3 leading-relaxed">{l.desc}</div>
              <div className="mt-5"><span className="badge-outline">{l.accent}</span></div>
            </div>
          ))}
        </div>

        <div className="mt-12 bg-ink text-white p-8">
          <div className="overline text-signal">On the Shop Floor</div>
          <div className="font-heading text-2xl font-bold mt-3">Every sim is matched to a physical station.</div>
          <div className="text-white/70 mt-3 max-w-2xl">Once you pass a simulation, your instructor unlocks the matching hands-on station — same tools, same diagram, same safety checklist.</div>
        </div>
      </div>
    </AppShell>
  );
}
