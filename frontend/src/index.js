import React from 'react';
import { createRoot } from 'react-dom/client';
import './index.css';

const supportCards = [
  { number: '01', title: 'Find your next step', text: 'Clear guides for housing, work, money, technology, and everyday stability.' },
  { number: '02', title: 'Learn without gatekeeping', text: 'Practical workshops and resources built for real life—not jargon or judgment.' },
  { number: '03', title: 'Build with community', text: 'Connect to people, programs, and shared knowledge that help you move forward.' },
];

function App() {
  return (
    <div className="site-shell">
      <header className="topbar">
        <a className="brand" href="#top" aria-label="M.O.R.E. Help Center home">
          <span className="brand-mark">M</span>
          <span><strong>M.O.R.E.</strong><small>HELP CENTER</small></span>
        </a>
        <nav className="nav-links" aria-label="Main navigation">
          <a href="#how-it-works">How it works</a>
          <a href="#resources">Resources</a>
          <a href="#about">About M.O.R.E.</a>
        </nav>
        <a className="nav-cta" href="#resources">Explore resources <span>↗</span></a>
      </header>

      <main id="top">
        <section className="hero grid-paper">
          <div className="hero-copy">
            <p className="overline"><span className="signal-dot" /> A community resource by the Michael Oliver Resource Exchange</p>
            <h1>Help that meets<br /><em>you</em> where you are.</h1>
            <p className="hero-lede">A practical, people-first help center for building skills, finding support, and creating more options—together.</p>
            <div className="hero-actions">
              <a className="btn-primary" href="#resources">Start here <span>→</span></a>
              <a className="text-link" href="#how-it-works">See how it works <span>↓</span></a>
            </div>
          </div>
          <div className="hero-art" aria-label="Illustration of connected community resources">
            <div className="art-sun" />
            <div className="art-ring ring-one" /><div className="art-ring ring-two" />
            <div className="art-card card-one"><span>RESOURCE</span><strong>Knowledge<br />is a bridge.</strong></div>
            <div className="art-card card-two"><span>COMMUNITY</span><strong>We move<br />together.</strong></div>
            <div className="art-line line-one" /><div className="art-line line-two" />
            <div className="art-label">MORE<br /><small>possibility</small></div>
          </div>
        </section>

        <section className="ticker" aria-label="What M.O.R.E. stands for">
          <span>Mutual aid</span><b>✦</b><span>Opportunity</span><b>✦</b><span>Resources</span><b>✦</b><span>Education</span><b>✦</b><span>Mutual aid</span>
        </section>

        <section className="intro" id="how-it-works">
          <div className="section-tag">WHY THIS EXISTS</div>
          <div><h2>Everyone deserves<br /><span>a place to start.</span></h2></div>
          <div className="intro-text"><p>The M.O.R.E. Help Center turns complicated systems into clear next steps. Whether you are looking for immediate support, learning a new skill, or helping someone you love, you are welcome here.</p><a className="arrow-link" href="#about">Learn about our approach <span>↗</span></a></div>
        </section>

        <section className="card-section" id="resources">
          <div className="section-heading"><div><div className="section-tag">YOUR STARTING POINT</div><h2>Make a little<br /><span>more possible.</span></h2></div><p>Choose what you need today. Come back when you need something new.</p></div>
          <div className="support-grid">{supportCards.map((card) => <a className="support-card" href="#about" key={card.number}><span className="card-number">{card.number}</span><h3>{card.title}</h3><p>{card.text}</p><span className="card-arrow">↗</span></a>)}</div>
        </section>

        <section className="quote-section" id="about">
          <div className="quote-mark">“</div>
          <blockquote>We are not here to tell you who to be.<br /><em>We are here to help you get there.</em></blockquote>
          <p>— The M.O.R.E. Help Center</p>
        </section>

        <section className="final-cta"><div><div className="section-tag">READY WHEN YOU ARE</div><h2>There is always<br /><em>more</em> to discover.</h2></div><a className="btn-copper" href="#resources">Explore the center <span>→</span></a></section>
      </main>
      <footer><span>© {new Date().getFullYear()} Michael Oliver Resource Exchange</span><span>Support • Learn • Connect</span></footer>
    </div>
  );
}

createRoot(document.getElementById('root')).render(<App />);
