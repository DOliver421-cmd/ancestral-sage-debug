import { useState } from "react";
import { Plus, Trash2, Calculator, List, Copy } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { constructionApi } from "@/lib/construction-pm";
import { toast } from "sonner";

const DEFAULT_MULTIPLIERS = [1.0];

export default function EstimatorGrid({ projectId, estimate, onEstimateChange }) {
  const [items, setItems] = useState(
    estimate?.line_items?.map((li) => ({
      item_id: li.item_id,
      csi_code: li.csi_code,
      description: li.description,
      uom: li.uom,
      quantity: li.quantity,
      applied_multipliers: li.applied_multipliers || [1.0],
      base_material_cost: li.base_material_cost,
      base_labor_hours: li.base_labor_hours,
      extended_material: li.extended_material,
      extended_labor: li.extended_labor,
    })) || []
  );
  const [calculating, setCalculating] = useState(false);

  const addRow = () => {
    setItems([...items, { item_id: "", csi_code: "", description: "", uom: "ea", quantity: 0, applied_multipliers: [1.0], base_material_cost: 0, base_labor_hours: 0, extended_material: 0, extended_labor: 0 }]);
  };

  const removeRow = (idx) => setItems(items.filter((_, i) => i !== idx));

  const updateCell = (idx, field, value) => {
    const next = items.map((it, i) => (i === idx ? { ...it, [field]: value } : it));
    setItems(next);
  };

  const calculate = async () => {
    setCalculating(true);
    try {
      const payload = {
        crew: { foreman_ratio: 0.2, journeyman_ratio: 0.6, apprentice_ratio: 0.2, blended_hourly_rate: 85, fringe_burden: 12 },
        target_margin: 0.2,
        notes: "Calculated from Estimator Grid",
        items: items.map((it) => ({
          item_id: it.item_id,
          quantity: it.quantity,
          applied_multipliers: it.applied_multipliers.filter(Boolean).length ? it.applied_multipliers : [1.0],
          extended_material: it.extended_material,
          extended_labor: it.extended_labor,
        })),
      };
      const r = await constructionApi.calculateEstimate(projectId, payload);
      const data = r.data;
      onEstimateChange?.(data);
      toast.success(`Estimate calculated — sell price $${data.sell_price.toLocaleString()}`);
    } catch (e) {
      toast.error("Estimate calculation failed");
    } finally {
      setCalculating(false);
    }
  };

  const totals = items.reduce(
    (acc, it) => ({
      material: acc.material + (it.extended_material || 0),
      labor: acc.labor + (it.extended_labor || 0),
      cost: acc.cost + ((it.extended_material || 0) + (it.extended_labor || 0)),
    }),
    { material: 0, labor: 0, cost: 0 }
  );

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Calculator className="w-5 h-5 text-copper" />
          <h3 className="font-bold text-lg text-ink">Master Line-Item Worksheet</h3>
        </div>
        <Button onClick={calculate} disabled={calculating} className="flex items-center gap-2">
          {calculating ? "Calculating…" : "Calculate Estimate"}
          <Calculator className="w-4 h-4" />
        </Button>
      </div>

      <div className="overflow-x-auto border border-ink/10 rounded-xl">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-ink/5 border-b border-ink/10">
              <th className="px-4 py-3 text-xs font-bold text-ink/60">CSI / Description</th>
              <th className="px-4 py-3 text-xs font-bold text-ink/60">UOM</th>
              <th className="px-4 py-3 text-xs font-bold text-ink/60">Qty</th>
              <th className="px-4 py-3 text-xs font-bold text-ink/60">Mat. Cost / unit</th>
              <th className="px-4 py-3 text-xs font-bold text-ink/60">Labor hrs / unit</th>
              <th className="px-4 py-3 text-xs font-bold text-ink/60">Multipliers</th>
              <th className="px-4 py-3 text-xs font-bold text-ink/60">Ext. Material</th>
              <th className="px-4 py-3 text-xs font-bold text-ink/60">Ext. Labor</th>
              <th className="px-4 py-3 text-xs font-bold text-ink/60 text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {items.map((it, idx) => (
              <tr key={idx} className="border-b border-ink/5 hover:bg-ink/2 transition-colors group">
                <td className="px-4 py-3">
                  <Input
                    value={it.csi_code}
                    onChange={(e) => updateCell(idx, "csi_code", e.target.value)}
                    className="text-xs w-16 font-mono text-ink bg-transparent border-none focus:ring-0"
                    placeholder="26 05 33"
                  />
                  <Input
                    value={it.description}
                    onChange={(e) => updateCell(idx, "description", e.target.value)}
                    className="text-xs w-full text-ink bg-transparent border-none focus:ring-0 ml-2"
                    placeholder="Description"
                  />
                </td>
                <td className="px-4 py-3">
                  <Input value={it.uom} onChange={(e) => updateCell(idx, "uom", e.target.value)} className="text-xs w-full text-ink bg-transparent border-none focus:ring-0" />
                </td>
                <td className="px-4 py-3">
                  <Input type="number" value={it.quantity} onChange={(e) => updateCell(idx, "quantity", Number(e.target.value) || 0)} className="text-xs w-full text-right text-ink bg-transparent border-none focus:ring-0" />
                </td>
                <td className="px-4 py-3">
                  <Input type="number" value={it.base_material_cost} onChange={(e) => updateCell(idx, "base_material_cost", Number(e.target.value) || 0)} className="text-xs w-full text-right text-ink bg-transparent border-none focus:ring-0" />
                </td>
                <td className="px-4 py-3">
                  <Input type="number" value={it.base_labor_hours} onChange={(e) => updateCell(idx, "base_labor_hours", Number(e.target.value) || 0)} className="text-xs w-full text-right text-ink bg-transparent border-none focus:ring-0" />
                </td>
                <td className="px-4 py-3">
                  <div className="flex gap-1">
                    {it.applied_multipliers.map((m, mi) => (
                      <Input key={mi} type="number" value={m} onChange={(e) => {
                        const next = [...it.applied_multipliers];
                        next[mi] = Number(e.target.value) || 1;
                        updateCell(idx, "applied_multipliers", next);
                      }} className="text-xs w-14 text-right text-ink bg-transparent border-none focus:ring-0" />
                    ))}
                    <button onClick={() => { const next=[...it.applied_multipliers,1]; updateCell(idx,"applied_multipliers",next); }} className="text-xs text-copper hover:underline px-1">+</button>
                  </div>
                </td>
                <td className="px-4 py-3 text-right">
                  <span className="text-xs font-mono text-ink">${((it.extended_material || 0)).toFixed(2)}</span>
                </td>
                <td className="px-4 py-3 text-right">
                  <span className="text-xs font-mono text-ink">${((it.extended_labor || 0)).toFixed(2)}</span>
                </td>
                <td className="px-4 py-3 text-right">
                  <Button variant="ghost" size="sm" onClick={() => removeRow(idx)} className="h-7 w-7 p-0 text-ink/40 hover:text-red-600">
                    <Trash2 className="w-3 h-3" />
                  </Button>
                </td>
              </tr>
            ))}
            <tr>
              <td className="px-4 py-3 font-bold text-ink border-t border-ink/10" colSpan="6">Totals</td>
              <td className="px-4 py-3 font-bold text-ink border-t border-ink/10 text-right">${totals.material.toFixed(2)}</td>
              <td className="px-4 py-3 font-bold text-ink border-t border-ink/10 text-right">${totals.labor.toFixed(2)}</td>
              <td className="px-4 py-3 text-right border-t border-ink/10">
                <Button variant="ghost" size="sm" onClick={addRow} className="h-7 p-0 text-copper">
                  <Plus className="w-3 h-3" />
                </Button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div className="grid grid-cols-3 gap-4 text-xs text-ink/60">
        <div className="bg-ink/5 rounded-lg p-3">
          <div className="font-bold text-ink">Extended Material</div>
          <div>${totals.material.toFixed(2)}</div>
        </div>
        <div className="bg-ink/5 rounded-lg p-3">
          <div className="font-bold text-ink">Extended Labor</div>
          <div>${totals.labor.toFixed(2)}</div>
        </div>
        <div className="bg-ink/5 rounded-lg p-3">
          <div className="font-bold text-ink">Direct Cost</div>
          <div>${totals.cost.toFixed(2)}</div>
        </div>
      </div>
    </div>
  );
}
