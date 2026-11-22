import { useEffect, useState } from "react";
import { Link, NavLink, Outlet, useLocation } from "react-router-dom";
import { useHealth } from "../api";
import { Helper } from "./art";

function Wordmark() {
  return (
    <Link to="/" className="wordmark" aria-label="DSA Explainer home">
      <svg width="34" height="34" viewBox="-64 -64 128 136" aria-hidden="true"><Helper r={58} arms={false} /></svg>
      dsa explainer
    </Link>
  );
}

function ProviderPill() {
  const { data } = useHealth();
  if (!data) return null;
  const llm = data.llm;
  const text = llm.configured ? `${llm.provider_name ?? llm.provider} · ${llm.model}` : "No key: saved lessons only";
  return (
    <Link to="/settings#language-model" className={`provider-pill${llm.configured ? " ok" : ""}`} title="Language model in use">
      <span className="dot" aria-hidden="true" />
      <span>{text}</span>
    </Link>
  );
}

function Header() {
  const [open, setOpen] = useState(false);
  const location = useLocation();
  useEffect(() => { setOpen(false); }, [location.pathname]);
  return (
    <header className="site-header">
      <div className="container">
        <Wordmark />
        <nav className={`nav${open ? " open" : ""}`} aria-label="Main">
          <NavLink to="/studio">Studio</NavLink>
          <NavLink to="/library">Library</NavLink>
          <NavLink to="/lessons">My lessons</NavLink>
          <NavLink to="/settings">Settings</NavLink>
        </nav>
        <div className="header-tools">
          <ProviderPill />
          <Link to="/studio" className="btn btn-primary btn-small">New lesson</Link>
          <button type="button" className="icon-btn menu-toggle" aria-label="Menu" aria-expanded={open} onClick={() => setOpen(!open)}
            style={{ background: "none", border: 0, cursor: "pointer" }}>
            <svg width="24" height="24" viewBox="0 0 24 24" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h16" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" /></svg>
          </button>
        </div>
      </div>
    </header>
  );
}

export function GreenFooter() {
  return (
    <footer className="site-footer">
      <div className="container columns">
        <div><h4>Make</h4><ul><li><Link to="/studio">Studio</Link></li><li><Link to="/library">Library</Link></li><li><Link to="/lessons">My lessons</Link></li></ul></div>
        <div><h4>Learn</h4><ul><li><Link to="/library?category=sorting">Sorting</Link></li><li><Link to="/library?category=graphs">Graphs</Link></li><li><Link to="/library?category=trees">Trees and heaps</Link></li><li><Link to="/library?category=dp">Dynamic programming</Link></li></ul></div>
        <div><h4>How it works</h4><ul><li><a href="/#how-it-works">The pipeline</a></li><li><a href="/#checked">Verification</a></li><li><a href="/#faq">Questions</a></li></ul></div>
        <div><h4>Set up</h4><ul><li><Link to="/settings#language-model">Language model</Link></li><li><Link to="/settings#voice">Voice</Link></li><li><Link to="/settings#video">Video</Link></li></ul></div>
        <div><h4>Project</h4><ul><li><a href="https://github.com/Ammad-Ashraf/dsa-explainer" target="_blank" rel="noreferrer">Source code</a></li><li><a href="/api/docs" target="_blank" rel="noreferrer">API reference</a></li></ul></div>
      </div>
      <div className="container legal">
        <span>DSA Explainer: open source, runs on your computer.</span>
        <span>Made by{" "}
          <a href="https://github.com/Ahmed-Javaid" target="_blank" rel="noreferrer">Ahmed Javaid</a> and{" "}
          <a href="https://ammad-ashraf.dev/" target="_blank" rel="noreferrer">Ammad Ashraf</a>
        </span>
      </div>
    </footer>
  );
}

export function CompactFooter() {
  return (
    <footer className="compact-footer">
      <Link to="/">Home</Link><Link to="/studio">Studio</Link><Link to="/library">Library</Link>
      <Link to="/lessons">My lessons</Link><Link to="/settings">Settings</Link>
      <a href="https://github.com/Ammad-Ashraf/dsa-explainer" target="_blank" rel="noreferrer">Source</a>
    </footer>
  );
}

export function Layout() {
  const { pathname } = useLocation();
  // a block body: an effect must return nothing or a cleanup function
  useEffect(() => { window.scrollTo(0, 0); }, [pathname]);
  return (
    <>
      <a href="#main" className="visually-hidden">Skip to content</a>
      <Header />
      <main id="main"><Outlet /></main>
      {pathname === "/" ? <GreenFooter /> : <CompactFooter />}
    </>
  );
}
