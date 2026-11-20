import { isRouteErrorResponse, Link, useRouteError } from "react-router-dom";
import { Helper } from "./art";

/** Shown in place of a page that failed to render. The header and footer stay, so the learner can carry on. */
export function RouteError() {
  const error = useRouteError();
  const notFound = isRouteErrorResponse(error) && error.status === 404;
  const detail = isRouteErrorResponse(error)
    ? `${error.status} ${error.statusText}`
    : error instanceof Error ? `${error.name}: ${error.message}` : String(error);
  if (!notFound) console.error(error); // keep the details for developers, out of the learner's way

  return (
    <div className="container page error-page" role="alert">
      <svg width="160" height="104" viewBox="-118 -70 236 154" aria-hidden="true"><Helper r={64} mood="wow" /></svg>
      <h1 className="page-title">{notFound ? "This page is not here" : "Something went wrong on this page"}</h1>
      <p className="lead">
        {notFound
          ? "The link may be old, or the lesson may have been deleted."
          : "Your lessons are safe: they are saved on this computer. Reloading usually fixes this."}
      </p>
      <div className="actions-row" style={{ justifyContent: "center" }}>
        {!notFound && <button type="button" className="btn btn-primary" onClick={() => window.location.reload()}>Reload the page</button>}
        <Link to="/" className="btn btn-secondary">Go home</Link>
        <Link to="/library" className="btn btn-secondary">Open the library</Link>
      </div>
      {!notFound && (
        <details className="error-detail">
          <summary>Details for reporting a problem</summary>
          <pre>{detail}</pre>
        </details>
      )}
    </div>
  );
}

export function NotFound() {
  return (
    <div className="container page error-page">
      <svg width="160" height="104" viewBox="-118 -70 236 154" aria-hidden="true"><Helper r={64} mood="wow" /></svg>
      <h1 className="page-title">This page is not here</h1>
      <p className="lead">The link may be old, or the lesson may have been deleted.</p>
      <div className="actions-row" style={{ justifyContent: "center" }}>
        <Link to="/" className="btn btn-primary">Go home</Link>
        <Link to="/library" className="btn btn-secondary">Open the library</Link>
      </div>
    </div>
  );
}
