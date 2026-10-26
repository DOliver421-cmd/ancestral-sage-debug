import { useState } from "react";
import {
  FileText,
  Play,
  ShieldCheck,
  Link,
  Copy,
  Check,
  CheckCircle2,
  Maximize2,
  ExternalLink,
  ChevronRight,
  Film,
} from "lucide-react";

const EXTERNAL_LINK_STYLE =
  "text-copper font-bold text-sm hover:underline transition-colors flex items-center gap-1";

const FREE_BADGE_STYLE =
  "inline-flex items-center gap-1.5 rounded-full border border-green-200 bg-green-50 px-3 py-1 text-xs font-bold text-green-700";

const CARD_STYLE = "bg-white border border-ink/10 rounded-xl p-6";

const PROMPT_TEXT =
  "Act as a narrative director. Here are the lyrics/poetry for my audio track: [Paste Lyrics]. Break this track down into 8 distinct visual scene prompts that tell a sequential story. Keep character details, style, and lighting consistent across all 8 shots.";

// ── Producer on a $0 Budget Tab ───────────────────────────────────────────────
// Zero-cost, multi-workflow production guide. Free for all registered users —
// no tier gates, credits, or subscription checks. Every third-party tool is
// linked outward (target="_blank" rel="noopener noreferrer"); nothing is iframed.

export default function ProducerOnZeroBudgetTab() {
  const [checked, setChecked] = useState({ quick: new Set(), high: new Set() });
  const [copied, setCopied] = useState(false);

  const toggle = (section, stepId) => {
    setChecked((prev) => {
      const next = { ...prev, [section]: new Set(prev[section]) };
      if (next[section].has(stepId)) next[section].delete(stepId);
      else next[section].add(stepId);
      return next;
    });
  };

  const isChecked = (section, stepId) => checked[section]?.has(stepId) || false;

  const copyPrompt = async () => {
    await navigator.clipboard?.writeText(PROMPT_TEXT);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-10">
      {/* ── Header ── */}
      <div className={CARD_STYLE}>
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <Film className="w-5 h-5 text-copper" />
              <span className={FREE_BADGE_STYLE}>
                <CheckCircle2 className="w-3 h-3" /> FREE FOR MEMBERS
              </span>
            </div>
            <h2 className="font-heading font-bold text-2xl text-ink mb-2">Producer on a $0 Budget</h2>
            <p className="text-ink/60 text-sm leading-relaxed max-w-2xl">
              A zero-cost workflow designed specifically to convert your Suno music and spoken-word poetry
              into narrative videos using standard, safe external links and free-tier tools.
            </p>
          </div>
        </div>
      </div>

      {/* ── Path Selector ── */}
      <div className="grid md:grid-cols-2 gap-6">
        <div className={CARD_STYLE}>
          <div className="flex items-center gap-2 mb-3">
            <Play className="w-5 h-5 text-copper" />
            <h3 className="font-bold text-lg text-ink">Path A: Quick Automated Workflow</h3>
          </div>
          <div className="space-y-3 text-sm">
            <div className="flex items-center gap-2 text-ink/60">
              <Maximize2 className="w-3.5 h-3.5 text-copper" />
              <span>~5–10 Minutes</span>
            </div>
            <div className="flex items-center gap-2 text-ink/60">
              <ShieldCheck className="w-3.5 h-3.5 text-copper" />
              <span>Skill Level: Beginner</span>
            </div>
            <div className="flex items-center gap-2 text-ink/60">
              <Link className="w-3.5 h-3.5 text-amber-600" />
              <span>Watermark: Possible (tool dependent)</span>
            </div>
            <div className="mt-2 p-3 rounded-lg border border-ink/10 bg-ink/5 text-ink text-sm leading-relaxed">
              <strong className="text-ink">Deliverable:</strong> Fast MP4 video auto-synced to your Suno
              link or lyrics.
            </div>
          </div>
        </div>

        <div className={CARD_STYLE}>
          <div className="flex items-center gap-2 mb-3">
            <FileText className="w-5 h-5 text-copper" />
            <h3 className="font-bold text-lg text-ink">Path B: High-Control Storyboard Workflow</h3>
          </div>
          <div className="space-y-3 text-sm">
            <div className="flex items-center gap-2 text-ink/60">
              <Maximize2 className="w-3.5 h-3.5 text-copper" />
              <span>~30–45 Minutes</span>
            </div>
            <div className="flex items-center gap-2 text-ink/60">
              <ShieldCheck className="w-3.5 h-3.5 text-copper" />
              <span>Skill Level: Intermediate</span>
            </div>
            <div className="flex items-center gap-2 text-ink/60">
              <ShieldCheck className="w-3.5 h-3.5 text-green-600" />
              <span>Watermark: 100% Watermark-Free</span>
            </div>
            <div className="mt-2 p-3 rounded-lg border border-ink/10 bg-ink/5 text-ink text-sm leading-relaxed">
              <strong className="text-ink">Deliverable:</strong> High-resolution custom visual story with
              kinetic auto-captions.
            </div>
          </div>
        </div>
      </div>

      {/* ═══ Section 1: Quick Automated Workflow ═══ */}
      <section>
        <div className={CARD_STYLE}>
          <div className="flex items-center gap-3 mb-5">
            <div className="w-8 h-8 rounded-full bg-copper/10 flex items-center justify-center text-copper font-bold">
              1
            </div>
            <div>
              <h3 className="font-bold text-lg text-ink">Quick Automated Workflow</h3>
              <p className="text-ink/60 text-sm">Direct link &amp; render</p>
            </div>
          </div>

          <p className="text-ink text-sm leading-relaxed mb-6">
            This approach takes your public Suno URL and automatically breaks down your lyrics or spoken-word
            audio into a beat-synced visual story.
          </p>

          <div className="space-y-5">
            {/* Step 1 */}
            <div className="flex gap-3">
              <input
                type="checkbox"
                checked={isChecked("quick", "suno-link")}
                onChange={() => toggle("quick", "suno-link")}
                className="w-4 h-4 rounded border-ink/30 text-copper accent-copper mt-0.5 focus:ring-copper shrink-0"
              />
              <div className="flex-1">
                <p className="font-bold text-ink text-sm">1. Copy Your Track Link</p>
                <p className="text-ink/60 text-sm leading-relaxed mb-2">
                  Go to your <ExternalLink className={EXTERNAL_LINK_STYLE} href="https://suno.com" rel="noopener noreferrer" target="_blank">Suno Library</ExternalLink>, click the share icon on your track, and select <strong>Copy Link</strong>.
                </p>
              </div>
            </div>

            {/* Step 2 */}
            <div className="flex gap-3">
              <input
                type="checkbox"
                checked={isChecked("quick", "generate-video")}
                onChange={() => toggle("quick", "generate-video")}
                className="w-4 h-4 rounded border-ink/30 text-copper accent-copper mt-0.5 focus:ring-copper shrink-0"
              />
              <div className="flex-1">
                <p className="font-bold text-ink text-sm">2. Generate the Automated Video (Choose One Tool)</p>

                <div className="mt-3 space-y-3">
                  <div className="flex gap-3">
                    <input
                      type="checkbox"
                      checked={isChecked("quick", "freebeat")}
                      onChange={() => toggle("quick", "freebeat")}
                      className="w-4 h-4 rounded border-ink/30 text-copper accent-copper mt-0.5 focus:ring-copper shrink-0"
                    />
                    <div className="flex-1">
                      <p className="font-bold text-ink text-sm">Freebeat.ai</p>
                      <a
                        href="https://freebeat.ai"
                        className={EXTERNAL_LINK_STYLE}
                        rel="noopener noreferrer"
                        target="_blank"
                      >
                        https://freebeat.ai
                      </a>
                      <p className="text-ink/60 text-sm leading-relaxed mt-1">
                        Paste your Suno track link directly into the generator. Select <strong>Storytelling</strong> mode. The system extracts your lyrics, builds a locked "Character Bible" for scene consistency, and renders a complete beat-synced video.
                      </p>
                      <p className="text-xs text-ink/50 mt-1 font-bold">
                        Free-Tier Limits: Free accounts generate full-length videos with a small watermark.
                      </p>
                    </div>
                  </div>

                  <div className="flex gap-3">
                    <input
                      type="checkbox"
                      checked={isChecked("quick", "sunomv")}
                      onChange={() => toggle("quick", "sunomv")}
                      className="w-4 h-4 rounded border-ink/30 text-copper accent-copper mt-0.5 focus:ring-copper shrink-0"
                    />
                    <div className="flex-1">
                      <p className="font-bold text-ink text-sm">SunoMV</p>
                      <a
                        href="https://suno.bi"
                        className={EXTERNAL_LINK_STYLE}
                        rel="noopener noreferrer"
                        target="_blank"
                      >
                        https://suno.bi
                      </a>
                      <p className="text-ink/60 text-sm leading-relaxed mt-1">
                        Paste your Suno track link or upload your audio file. Pick one of the 7 style presets (e.g., <em>Realistic Photo</em>, <em>Cyberpunk</em>, <em>Cinematic Anime</em>) and choose a subtitle style. Click <strong>Generate</strong> to watch the finished storyboard video render in your browser.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ═══ Section 2: High-Control Storyboard Workflow ═══ */}
      <section>
        <div className={CARD_STYLE}>
          <div className="flex items-center gap-3 mb-5">
            <div className="w-8 h-8 rounded-full bg-copper/10 flex items-center justify-center text-copper font-bold">
              2
            </div>
            <div>
              <h3 className="font-bold text-lg text-ink">High-Control Storyboard Workflow</h3>
              <p className="text-ink/60 text-sm">Custom visuals &amp; zero watermarks</p>
            </div>
          </div>

          <p className="text-ink text-sm leading-relaxed mb-6">
            If you want absolute artistic direction over how every scene of your poetry is illustrated—without
            any platform watermarks—use this free modular workflow.
          </p>

          <div className="space-y-5">
            {/* Step 1 */}
            <div className="flex gap-3">
              <input
                type="checkbox"
                checked={isChecked("high", "extract-audio")}
                onChange={() => toggle("high", "extract-audio")}
                className="w-4 h-4 rounded border-ink/30 text-copper accent-copper mt-0.5 focus:ring-copper shrink-0"
              />
              <div className="flex-1">
                <p className="font-bold text-ink text-sm">1. Extract Audio &amp; Lyrics from Suno</p>
                <p className="text-ink/60 text-sm leading-relaxed mb-2">
                  Go to <ExternalLink className={EXTERNAL_LINK_STYLE} href="https://suno.com" rel="noopener noreferrer" target="_blank">Suno</ExternalLink>, open your track, click the options menu (`...`), download the Audio MP3, and copy the lyric text.
                </p>
              </div>
            </div>

            {/* Step 2 + Copy Prompt */}
            <div className="flex gap-3">
              <input
                type="checkbox"
                checked={isChecked("high", "scene-prompts")}
                onChange={() => toggle("high", "scene-prompts")}
                className="w-4 h-4 rounded border-ink/30 text-copper accent-copper mt-0.5 focus:ring-copper shrink-0"
              />
              <div className="flex-1">
                <p className="font-bold text-ink text-sm">2. Generate a Scene-by-Scene Prompt List</p>
                <p className="text-ink/60 text-sm leading-relaxed mb-3">
                  Open <ExternalLink className={EXTERNAL_LINK_STYLE} href="https://chatgpt.com" rel="noopener noreferrer" target="_blank">ChatGPT</ExternalLink> or <ExternalLink className={EXTERNAL_LINK_STYLE} href="https://claude.ai" rel="noopener noreferrer" target="_blank">Claude</ExternalLink> and execute this exact prompt:
                </p>

                {/* Copyable Prompt Box */}
                <div className="rounded-lg border border-ink/20 bg-ink/5 overflow-hidden">
                  <div className="flex items-center justify-between px-4 py-2 border-b border-ink/10 bg-ink/10">
                    <span className="text-xs font-bold text-ink/50 mono">Copy Prompt</span>
                    <button
                      onClick={copyPrompt}
                      disabled={copied}
                      className="flex items-center gap-1.5 px-2.5 py-1 rounded border border-ink/20 text-xs font-bold text-ink hover:bg-ink/5 transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
                    >
                      <Copy className="w-3 h-3" />
                      {copied ? "Copied!" : "Copy Prompt"}
                    </button>
                  </div>
                  <pre className="p-4 text-sm text-ink font-mono overflow-x-auto whitespace-pre-wrap border-t border-ink/10">{PROMPT_TEXT}</pre>
                </div>
                <p className="text-xs text-ink/50 mt-2">Replace <em>[Paste Lyrics]</em> with your track's lyric text before sending.</p>
              </div>
            </div>

            {/* Step 3 */}
            <div className="flex gap-3">
              <input
                type="checkbox"
                checked={isChecked("high", "generate-scenes")}
                onChange={() => toggle("high", "generate-scenes")}
                className="w-4 h-4 rounded border-ink/30 text-copper accent-copper mt-0.5 focus:ring-copper shrink-0"
              />
              <div className="flex-1">
                <p className="font-bold text-ink text-sm">3. Generate Visual Scenes (100% Free)</p>
                <p className="text-ink/60 text-sm leading-relaxed mb-2">
                  Use <ExternalLink className={EXTERNAL_LINK_STYLE} href="https://www.recraft.ai" rel="noopener noreferrer" target="_blank">Recraft.ai</ExternalLink> or <ExternalLink className={EXTERNAL_LINK_STYLE} href="https://leonardo.ai" rel="noopener noreferrer" target="_blank">Leonardo.ai</ExternalLink>. Paste each scene prompt generated in Step 2. Select your aspect ratio (e.g., <code className="text-ink">16:9</code> for landscape/YouTube or <code className="text-ink">9:16</code> for TikTok/Reels) and export the high-resolution images.
                </p>
              </div>
            </div>

            {/* Step 4 */}
            <div className="flex gap-3">
              <input
                type="checkbox"
                checked={isChecked("high", "motion-clips")}
                onChange={() => toggle("high", "motion-clips")}
                className="w-4 h-4 rounded border-ink/30 text-copper accent-copper mt-0.5 focus:ring-copper shrink-0"
              />
              <div className="flex-1">
                <p className="font-bold text-ink text-sm">4. (Optional) Turn Static Images into Motion Clips</p>
                <p className="text-ink/60 text-sm leading-relaxed mb-2">
                  To convert static scenes into video motion, upload your key images to <ExternalLink className={EXTERNAL_LINK_STYLE} href="https://lumalabs.ai/dream-machine" rel="noopener noreferrer" target="_blank">Luma Dream Machine</ExternalLink> or <ExternalLink className={EXTERNAL_LINK_STYLE} href="https://runwayml.com" rel="noopener noreferrer" target="_blank">RunwayML</ExternalLink> to render 4-second camera-panning clips.
                </p>
              </div>
            </div>

            {/* Step 5 */}
            <div className="flex gap-3">
              <input
                type="checkbox"
                checked={isChecked("high", "assemble-capcut")}
                onChange={() => toggle("high", "assemble-capcut")}
                className="w-4 h-4 rounded border-ink/30 text-copper accent-copper mt-0.5 focus:ring-copper shrink-0"
              />
              <div className="flex-1">
                <p className="font-bold text-ink text-sm">5. Assemble &amp; Auto-Sync Captions in CapCut</p>
                <p className="text-ink/60 text-sm leading-relaxed mb-2">
                  Open <ExternalLink className={EXTERNAL_LINK_STYLE} href="https://www.capcut.com" rel="noopener noreferrer" target="_blank">CapCut Online</ExternalLink> or launch the free CapCut desktop app.
                </p>
                <ul className="list-disc list-inside text-ink/60 text-sm space-y-1 mt-2">
                  <li>Drag and drop your Suno MP3 audio file and your generated image/video clips onto the timeline.</li>
                  <li>Select <strong>Captions → Auto Captions</strong>. The AI will transcribe your spoken poetry/lyrics and display animated typography perfectly synced to the audio beats.</li>
                  <li>Export your finished, watermark-free MP4 video.</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer note */}
      <div className="p-4 rounded-lg border border-ink/10 bg-ink/5 text-xs text-ink/50">
        All external links open in a new tab. This tab is free for every registered user — no subscription,
        credits, or tier required. Third-party tools are not embedded; you are directed to their official sites.
      </div>
    </div>
  );
}
