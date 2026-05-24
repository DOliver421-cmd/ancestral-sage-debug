import { Link } from "react-router-dom";
import PublicNav from "../components/PublicNav";
import BackButton from "../components/BackButton";
import { HandHelping, Users, Sparkles } from "lucide-react";

// Public community page — explains the "members are partners" mutual-aid model
// and funnels into the M.O.R.E. exchange + free registration.
export default function Community() {
  return (
    <div className="min-h-screen bg-bone">
      <PublicNav />
      <div className="max-w-5xl mx-auto px-6 py-10">
        <BackButton to="/" />
        <div className="mt-6 text-center">
          <div className="overline" style={{ color: "var(--wai-purple)" }}>Community</div>
          <h1 className="font-heading text-4xl font-bold text-ink mt-2">Members are partners, not customers.</h1>
          <p className="text-ink/60 mt-3 max-w-2xl mx-auto">
            A festival of mutual aid, learning, and creation. Post a need, offer a skill, earn your way up — together.
          </p>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-8">
          <div className="card-flat p-6">
            <HandHelping className="w-7 h-7" style={{ color: "var(--wai-purple)" }} />
            <div className="font-heading font-bold mt-3">Mutual Aid</div>
            <div className="text-sm text-ink/60 mt-1">Needs and skills exchanged — no money, just people helping people.</div>
          </div>
          <div className="card-flat p-6">
            <Users className="w-7 h-7 text-copper" />
            <div className="font-heading font-bold mt-3">Earn Your Way</div>
            <div className="text-sm text-ink/60 mt-1">Take part, raise your partnership tier, unlock free membership.</div>
          </div>
          <div className="card-flat p-6">
            <Sparkles className="w-7 h-7" style={{ color: "var(--wai-gold)" }} />
            <div className="font-heading font-bold mt-3">Creators & Elders</div>
            <div className="text-sm text-ink/60 mt-1">Artists, mentors, and elders holding the culture together.</div>
          </div>
        </div>
        <div className="text-center mt-8 flex gap-3 justify-center flex-wrap">
          <Link to="/app/more" className="btn-primary text-sm">Enter the Exchange</Link>
          <Link to="/register" className="btn-copper text-sm">Join Free</Link>
        </div>
      </div>
    </div>
  );
}
