import type { ButtonHTMLAttributes, ReactNode } from "react";
import { Link } from "react-router-dom";
import type { Level } from "../api";

type Variant = "primary" | "secondary" | "blue" | "danger" | "ghost";

export function Button({ variant = "primary", wide, small, className = "", ...rest }:
  ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant; wide?: boolean; small?: boolean }) {
  const classes = ["btn", `btn-${variant}`, wide && "btn-wide", small && "btn-small", className].filter(Boolean).join(" ");
  return <button type="button" className={classes} {...rest} />;
}

export function LinkButton({ to, variant = "primary", wide, small, children }:
  { to: string; variant?: Variant; wide?: boolean; small?: boolean; children: ReactNode }) {
  const classes = ["btn", `btn-${variant}`, wide && "btn-wide", small && "btn-small"].filter(Boolean).join(" ");
  return <Link to={to} className={classes}>{children}</Link>;
}

export function LevelTag({ level }: { level: Level | string }) {
  return <span className={`tag tag-${level}`}>{level}</span>;
}

export function Tag({ children, mono }: { children: ReactNode; mono?: boolean }) {
  return <span className={`tag${mono ? " tag-complexity" : ""}`}>{children}</span>;
}

export function Spinner({ label }: { label?: string }) {
  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: 10 }}>
      <span className="spinner" aria-hidden="true" />
      {label && <span>{label}</span>}
    </span>
  );
}

export function Notice({ tone = "grey", children }: { tone?: "grey" | "blue" | "red" | "green"; children: ReactNode }) {
  return <div className={`notice${tone === "grey" ? "" : ` notice-${tone}`}`} role={tone === "red" ? "alert" : undefined}>{children}</div>;
}

export function Segmented<T extends string>({ options, value, onChange, label, labels }:
  { options: readonly T[]; value: T; onChange: (v: T) => void; label: string; labels?: Partial<Record<T, string>> }) {
  return (
    <div className="segmented" role="group" aria-label={label}>
      {options.map((o) => (
        <button key={o} type="button" aria-pressed={o === value} onClick={() => onChange(o)}>{labels?.[o] ?? o}</button>
      ))}
    </div>
  );
}

export function Tabs<T extends string>({ tabs, value, onChange }: { tabs: { id: T; label: string }[]; value: T; onChange: (t: T) => void }) {
  return (
    <div className="tabs" role="tablist">
      {tabs.map((t) => (
        <button key={t.id} role="tab" aria-selected={t.id === value} onClick={() => onChange(t.id)}>{t.label}</button>
      ))}
    </div>
  );
}

export function ErrorNotice({ error }: { error: unknown }) {
  if (!error) return null;
  const text = error instanceof Error ? error.message : String(error);
  return <Notice tone="red"><span>{text}</span></Notice>;
}

export function Loading({ what = "Loading" }: { what?: string }) {
  return <div className="empty"><Spinner label={`${what}…`} /></div>;
}
