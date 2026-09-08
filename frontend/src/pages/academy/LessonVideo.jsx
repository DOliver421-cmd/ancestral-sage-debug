import { PlayCircle, ExternalLink } from "lucide-react";

/* LessonVideo — on-site embed for curated public educational videos.
   youtube-nocookie iframe: the student never navigates away; attribution is
   always visible so nothing is presented as MoreHelp-made content. */
export default function LessonVideo({ video, compact = false }) {
  if (!video || !video.video_id) return null;

  const watchUrl = `https://www.youtube.com/watch?v=${video.video_id}`;

  return (
    <figure
      className={`card-flat bg-white border border-ink/10 overflow-hidden ${compact ? "" : "shadow-sm"}`}
      data-testid={`enrichment-video-${video.video_id}`}
    >
      <div className="relative w-full" style={{ paddingTop: "56.25%" }}>
        <iframe
          className="absolute inset-0 w-full h-full"
          src={`https://www.youtube-nocookie.com/embed/${video.video_id}?rel=0`}
          title={video.title}
          loading="lazy"
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
          allowFullScreen
          referrerPolicy="strict-origin-when-cross-origin"
        />
      </div>
      <figcaption className="px-5 py-3.5 border-t border-ink/10 bg-bone">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <div className="min-w-0">
            <div className="flex items-center gap-2 text-sm font-bold text-ink">
              <PlayCircle className="w-4 h-4 text-copper shrink-0" />
              <span className="truncate">{video.title}</span>
            </div>
            <p className="text-xs text-ink/55 mt-1">
              Created by <span className="font-bold text-ink/70">{video.creator}</span> · a publicly accessible
              educational resource — not MoreHelp content. Plays right here on MoreHelp.
            </p>
          </div>
          <a
            href={watchUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-xs font-bold text-copper hover:text-ink transition-colors shrink-0"
          >
            Source <ExternalLink className="w-3 h-3" />
          </a>
        </div>
      </figcaption>
    </figure>
  );
}

/* Videos assigned to a specific unit — rendered above that unit's lessons. */
export function videosForPlacement(videos, placement) {
  return (videos || []).filter((v) => v && v.placement === placement);
}

export function unitVideos(videos, unitSlug) {
  return (videos || []).filter((v) => v && v.placement === `unit:${unitSlug}`);
}
