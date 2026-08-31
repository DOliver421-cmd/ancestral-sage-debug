/**
 * CreatorContextBar
 *
 * Sticky breadcrumb + feature-switcher shown at the top of every creator
 * feature page. Keeps "← My Profile" always one click away and surfaces
 * sister features so users never have to hunt through the sidebar.
 *
 * Usage:
 *   <AppShell>
 *     <CreatorContextBar current="blast" />
 *     … page content …
 *   </AppShell>
 */

import { Link } from "react-router-dom";
import { useAuth } from "../lib/auth";
import {
  ArrowLeft, Share2, Music, BookOpen, DollarSign, Receipt,
  Mic, Palette, Radio, Gamepad2, Video, UserCircle,
} from "lucide-react";

const FEATURES = [
  { id: "blast",    label: "Social Blast",   to: "/social/publish",     icon: Share2    },
  { id: "studio",   label: "Studio",         to: "/studio",             icon: Music     },
  { id: "ghost",    label: "Ghost Producer", to: "/ghost-producer",     icon: Palette   },
  { id: "courses",  label: "My Courses",     to: "/creator/courses",    icon: Video     },
  { id: "earnings", label: "Earnings",       to: "/creator/earnings",   icon: DollarSign},
  { id: "payouts",  label: "Payouts",        to: "/creator/payouts",    icon: Receipt   },
  { id: "lounge",   label: "Creator Lounge", to: "/creator-lounge",     icon: Mic       },
  { id: "band",     label: "Band Page",      to: "/band",               icon: Radio     },
  { id: "playlist", label: "Playlists",      to: "/playlist/dashboard", icon: Gamepad2  },
];

export default function CreatorContextBar({ current }) {
  const { user } = useAuth();

  const others = FEATURES.filter(f => f.id !== current);

  return (
    <div className="sticky top-0 z-30 bg-white border-b border-ink/8 shadow-sm">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 flex items-center gap-3 h-10 overflow-x-auto">

        {/* Back to profile */}
        <Link
          to="/profile"
          className="flex items-center gap-1.5 text-xs font-black text-copper hover:text-copper/70 transition-colors whitespace-nowrap shrink-0"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          {user?.full_name ? `${user.full_name.split(" ")[0]}'s Profile` : "My Profile"}
        </Link>

        <div className="w-px h-4 bg-ink/10 shrink-0" />

        {/* Feature pills */}
        {others.map(f => (
          <Link
            key={f.id}
            to={f.to}
            className="flex items-center gap-1 text-xs font-bold text-ink/40 hover:text-ink/80 hover:bg-ink/5 whitespace-nowrap transition-colors px-2.5 py-1 rounded-full shrink-0"
          >
            <f.icon className="w-3 h-3 shrink-0" />
            {f.label}
          </Link>
        ))}

        {/* Profile edit shortcut */}
        <Link
          to="/profile"
          className="ml-auto flex items-center gap-1 text-xs font-bold text-ink/30 hover:text-copper whitespace-nowrap transition-colors shrink-0"
        >
          <UserCircle className="w-3.5 h-3.5" />
          Edit Profile
        </Link>
      </div>
    </div>
  );
}
