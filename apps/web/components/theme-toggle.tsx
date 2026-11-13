"use client";

import { Moon, Sun } from "lucide-react";
import { useEffect, useState } from "react";

type Theme = "light" | "dark";

function systemTheme(): Theme {
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

export function ThemeToggle() {
  const [theme, setTheme] = useState<Theme | null>(null);

  useEffect(() => {
    const stored = window.localStorage.getItem("office-hours-theme");
    const initial = stored === "light" || stored === "dark" ? stored : systemTheme();
    document.documentElement.dataset.theme = initial;
    const update = window.setTimeout(() => setTheme(initial), 0);
    return () => window.clearTimeout(update);
  }, []);

  function toggle() {
    const next: Theme = theme === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    window.localStorage.setItem("office-hours-theme", next);
    setTheme(next);
  }

  if (!theme) return <span className="h-9 w-9" aria-hidden="true"/>;
  const switchingTo = theme === "dark" ? "light" : "dark";
  return <button className="secondary inline-flex h-9 w-9 items-center justify-center p-0" type="button" aria-label={`Switch to ${switchingTo} theme`} title={`Switch to ${switchingTo} theme`} onClick={toggle}>{theme === "dark" ? <Sun size={16}/> : <Moon size={16}/>}</button>;
}
