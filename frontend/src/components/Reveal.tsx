import { type ElementType, type ReactNode, useEffect, useRef, useState } from "react";

/** Fades and lifts its content into place the first time it scrolls into view. */
export function Reveal({ as: Tag = "div", className = "", children, ...rest }:
  { as?: ElementType; className?: string; children: ReactNode; id?: string }) {
  const ref = useRef<HTMLElement>(null);
  const [shown, setShown] = useState(false);
  useEffect(() => {
    const element = ref.current;
    if (!element || typeof IntersectionObserver === "undefined") {
      setShown(true);
      return;
    }
    const observer = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting) {
        setShown(true);
        observer.disconnect();
      }
    }, { threshold: 0.18 });
    observer.observe(element);
    return () => observer.disconnect();
  }, []);
  return <Tag ref={ref} className={`reveal${shown ? " shown" : ""} ${className}`.trim()} {...rest}>{children}</Tag>;
}
