import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { api } from "../lib/api";
import { WAI_LOGO, BRAND } from "../lib/brand";
import PortfolioBody from "../components/PortfolioBody";

export default function PublicPortfolio() {
  const { slug } = useParams();
  const [data, setData] = useState(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    api.get(`/portfolio/public/${slug}`)
      .then((r) => setData(r.data))
      .catch(() => setError(true));
  }, [slug]);

  if (error) return (
    <div className="min-h-screen bg-bone flex items-center justify-center">
      <div className="card-flat p-12 text-center">
        <div className="font-heading text-2xl font-bold">Portfolio not found</div>
        <div className="text-ink/60 mt-2">This portfolio is private or the link is invalid.</div>
        <Link to="/" className="btn-primary mt-6 inline-block">Back to W.A.I.</Link>
      </div>
    </div>
  );
  if (!data) return <div className="min-h-screen bg-bone flex items-center justify-center">Loading…</div>;

  return (
    <div className="min-h-screen bg-bone">
      <header className="bg-ink text-white">
        <div className="max-w-5xl mx-auto px-6 py-6 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-3" data-testid="public-brand">
            <img src={WAI_LOGO} alt="W.A.I." className="w-12 h-12 object-contain bg-white p-1" />
            <div>
              <div className="overline text-signal">{BRAND.short}</div>
              <div className="font-heading font-bold">{BRAND.name}</div>
            </div>
          </Link>
          <span className="overline text-signal">Public Apprentice Portfolio</span>
        </div>
      </header>

      <div className="max-w-5xl mx-auto px-6 py-10">
        <div className="overline text-copper">Apprentice</div>
        <h1 className="font-heading text-5xl font-bold mt-2">{data.user.full_name}</h1>
        {data.user.associate && <div className="overline text-ink/60 mt-2">{data.user.associate}</div>}
        {data.bio && <p className="text-lg text-ink/70 mt-6 max-w-3xl">{data.bio}</p>}
        <div className="mt-8">
          <PortfolioBody data={data} publicView />
        </div>
      </div>

      <footer className="bg-ink text-white/70 mt-16">
        <div className="max-w-5xl mx-auto px-6 py-8 flex justify-between items-center text-sm">
          <div>Credentials verifiable via OpenBadges v2.</div>
          <Link to="/" className="overline text-signal">wai.org →</Link>
        </div>
      </footer>
    </div>
  );
}
