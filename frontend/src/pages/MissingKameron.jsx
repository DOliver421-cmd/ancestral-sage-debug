import { Link } from "react-router-dom";

export default function MissingKameron() {
  return (
    <div className="min-h-screen bg-bone flex items-center justify-center p-8">
      <div className="max-w-lg w-full text-center space-y-6">
        <div style={{ fontSize: 64 }}>🎉</div>
        <h1 className="font-heading text-4xl font-bold text-ink">
          Kameron Has Been Found!
        </h1>
        <p className="text-ink/60 text-lg leading-relaxed">
          Thank you to everyone who shared and helped. Kameron McMullen has been
          safely recovered and is doing great.
        </p>
        <div className="bg-green-50 border border-green-200 rounded-2xl p-6">
          <p className="text-green-800 font-bold text-lg">
            ✓ Safe and home
          </p>
          <p className="text-green-600 text-sm mt-1">
            This page is no longer active as a missing person case.
          </p>
        </div>
        <Link
          to="/"
          className="inline-block btn-primary text-sm mt-4"
        >
          Return Home
        </Link>
      </div>
    </div>
  );
}
