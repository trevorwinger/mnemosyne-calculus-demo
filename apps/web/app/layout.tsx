import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";
import "katex/dist/katex.min.css";
import { ThemeToggle } from "../components/theme-toggle";

export const metadata: Metadata = { title: "Mnemosyne Calculus III", description: "A course-scoped Calculus III tutoring prototype" };
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body><header className="mx-auto flex max-w-6xl items-center justify-between px-5 py-5"><Link className="font-mono text-lg font-bold tracking-tight" href="/">MNEMOSYNE · CALCULUS III</Link><ThemeToggle/></header>{children}</body></html>;
}
