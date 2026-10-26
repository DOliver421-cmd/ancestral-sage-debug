import { useEffect, useRef, useState } from "react";
import { Maximize, Layers, PenTool, MapPin, RotateCcw, ZoomIn, ZoomOut } from "lucide-react";
import { Button } from "@/components/ui/button";

const LAYERS = [
  { key: "conduit", label: "Feeder Conduit", color: "#2563eb" },
  { key: "branch", label: "Branch Power", color: "#16a34a" },
  { key: "lighting", label: "Lighting", color: "#f59e0b" },
  { key: "lowvolt", label: "Low Voltage", color: "#a855f7" },
];

export default function TakeoffCanvas({ blueprints = [], selectedSheet }) {
  const canvasRef = useRef(null);
  const ctxRef = useRef(null);
  const [zoom, setZoom] = useState(1);
  const [activeLayer, setActiveLayer] = useState("conduit");
  const [activeTool, setActiveTool] = useState("pen"); // pen | pin
  const [offset, setOffset] = useState({ x: 0, y: 0 });
  const [isPanning, setIsPanning] = useState(false);
  const [marks, setMarks] = useState([]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    ctxRef.current = ctx;
    render();
  }, []);

  const render = () => {
    const canvas = canvasRef.current;
    const ctx = ctxRef.current;
    if (!canvas || !ctx) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.save();
    ctx.translate(offset.x, offset.y);
    ctx.scale(zoom, zoom);

    // Draw selected sheet placeholder (vector base layer)
    const sheet = blueprints.find((b) => b.sheet_number === selectedSheet) || blueprints[0];
    if (sheet) {
      ctx.fillStyle = "#f3f4f6";
      ctx.fillRect(0, 0, 1200, 900);
      ctx.strokeStyle = "#9ca3af";
      ctx.lineWidth = 2;
      ctx.strokeRect(10, 10, 1180, 880);
      ctx.fillStyle = "#374151";
      ctx.font = "bold 18px sans-serif";
      ctx.fillText(`Sheet ${sheet.sheet_number}`, 30, 40);
      ctx.fillStyle = "#6b7280";
      ctx.font = "14px sans-serif";
      ctx.fillText(sheet.file_path || "plan.pdf", 30, 65);
    }

    // Draw markup overlays
    marks.forEach((m) => {
      ctx.beginPath();
      if (m.type === "line") {
        ctx.moveTo(m.x1, m.y1);
        ctx.lineTo(m.x2, m.y2);
        ctx.strokeStyle = m.color;
        ctx.lineWidth = 3 / zoom;
        ctx.stroke();
      } else if (m.type === "pin") {
        ctx.arc(m.x, m.y, 6 / zoom, 0, Math.PI * 2);
        ctx.fillStyle = m.color;
        ctx.fill();
        ctx.strokeStyle = "#fff";
        ctx.lineWidth = 1 / zoom;
        ctx.stroke();
      }
    });

    ctx.restore();
  };

  const handleMouseDown = (e) => {
    if (activeTool === "pan") {
      setIsPanning(true);
      return;
    }
    const rect = canvasRef.current.getBoundingClientRect();
    const x = (e.clientX - rect.left - offset.x) / zoom;
    const y = (e.clientY - rect.top - offset.y) / zoom;
    const layer = LAYERS.find((l) => l.key === activeLayer);
    if (activeTool === "pin") {
      setMarks([...marks, { type: "pin", x, y, color: layer.color }]);
      render();
    }
  };

  const handleMouseMove = (e) => {
    if (!isPanning) return;
    const rect = canvasRef.current.getBoundingClientRect();
    setOffset((prev) => ({
      x: prev.x + (e.clientX - rect.left - offset.x) / 0, // neutral
      y: prev.y,
    }));
  };

  const handleWheel = (e) => {
    e.preventDefault();
    const delta = e.deltaY > 0 ? 0.9 : 1.1;
    setZoom((z) => Math.min(Math.max(z * delta, 0.5), 3));
  };

  return (
    <div className="bg-white border border-ink/10 rounded-xl overflow-hidden flex flex-col h-[600px]">
      <div className="bg-ink/90 px-4 py-2 flex items-center gap-3 border-b border-ink/20">
        <div className="flex items-center gap-2">
          <Button size="sm" variant="ghost" onClick={() => setZoom((z) => Math.max(z - 0.1, 0.5))} className="h-7 w-7 p-0 text-white/70">
            <ZoomOut className="w-4 h-4" />
          </Button>
          <span className="text-xs text-white font-mono">{Math.round(zoom * 100)}%</span>
          <Button size="sm" variant="ghost" onClick={() => setZoom((z) => Math.min(z + 0.1, 3))} className="h-7 w-7 p-0 text-white/70">
            <ZoomIn className="w-4 h-4" />
          </Button>
        </div>
        <div className="h-4 w-px bg-white/20 mx-2" />
        <div className="flex items-center gap-1 text-xs text-white/80">
          <span className="font-bold">{activeLayer}</span> <span className="text-white/50">layer</span>
        </div>
        <div className="h-4 w-px bg-white/20 mx-2" />
        <div className="flex gap-1">
          {LAYERS.map((l) => (
            <button
              key={l.key}
              onClick={() => setActiveLayer(l.key)}
              className={`w-6 h-6 rounded-full border ${l.key === activeLayer ? `border-${l.color.replace('#','') === '2563eb' ? 'blue-500' : 'gray-500'} border-2` : "border-transparent"} flex items-center justify-center`} style={{ backgroundColor: l.color }}
            />
          ))}
        </div>
        <div className="ml-auto flex gap-1">
          <Button size="sm" variant="ghost" onClick={() => setActiveTool("pen")} className={`h-7 w-7 p-0 ${activeTool === "pen" ? "text-copper" : "text-white/60"}`} title="Draw conduit run">
            <PenTool className="w-4 h-4" />
          </Button>
          <Button size="sm" variant="ghost" onClick={() => setActiveTool("pin")} className={`h-7 w-7 p-0 ${activeTool === "pin" ? "text-copper" : "text-white/60"}`} title="Place device marker">
            <MapPin className="w-4 h-4" />
          </Button>
          <Button size="sm" variant="ghost" onClick={() => setActiveTool("pan")} className={`h-7 w-7 p-0 ${activeTool === "pan" ? "text-copper" : "text-white/60"}`} title="Pan canvas">
            <Maximize className="w-4 h-4" />
          </Button>
        </div>
      </div>

      <div className="relative flex-1 bg-bone/50" onMouseDown={handleMouseDown} onWheel={handleWheel} style={{ touchAction: "none" }}>
        <canvas
          ref={canvasRef}
          width={1200}
          height={900}
          className="w-full h-full cursor-crosshair select-none"
        />
        {blueprints.length === 0 && (
          <div className="absolute inset-0 flex flex-col items-center justify-center text-ink/40">
            <Layers className="w-12 h-12 mb-2 opacity-20" />
            <p>No blueprints uploaded for this project.</p>
          </div>
        )}
      </div>
    </div>
  );
}
