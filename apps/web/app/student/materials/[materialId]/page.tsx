"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "../../../../lib/api";

type Source = { material_id: string; title: string; module: string | null; location: string; content: string; previous_location: string | null; previous_content: string | null; next_location: string | null; next_content: string | null };

export default function SourceExcerpt({ params }: { params: Promise<{ materialId: string }> }) {
  const search = useSearchParams(); const [source, setSource] = useState<Source | null>(null); const [error, setError] = useState("");
  useEffect(() => { params.then(({ materialId }) => api<Source>(`/v1/materials/${materialId}/source?location=${encodeURIComponent(search.get("location") ?? "")}`).then(setSource).catch(cause => setError(cause instanceof Error ? cause.message : "Could not load course source."))); }, [params, search]);
  if (!source) return <main className="grid min-h-[70vh] place-items-center">{error || "Loading cited source…"}</main>;
  return <main className="mx-auto max-w-3xl px-5 pb-16 pt-10"><Link href="/workspace" className="text-sm font-semibold">← Courses</Link><p className="mt-8 font-mono text-sm">CITED COURSE SOURCE</p><h1 className="mt-2 text-3xl font-semibold">{source.title}</h1><p className="mt-2 text-sm text-[var(--muted)]">{source.module ? `${source.module} · ` : ""}{source.location}</p><p className="mt-4 text-sm text-[var(--muted)]">The highlighted passage is the exact extracted course chunk used for this citation. Adjacent chunks are context only.</p><div className="mt-8 space-y-4">{source.previous_content ? <article className="bordered whitespace-pre-wrap p-5 leading-7 text-[var(--muted)]"><p className="mb-3 font-mono text-xs">CONTEXT BEFORE · {source.previous_location}</p>{source.previous_content}</article> : null}<article className="rounded-lg border-2 border-[var(--accent)] bg-[var(--surface)] whitespace-pre-wrap p-5 leading-7"><p className="mb-3 font-mono text-xs font-semibold">CITED PASSAGE · {source.location}</p>{source.content}</article>{source.next_content ? <article className="bordered whitespace-pre-wrap p-5 leading-7 text-[var(--muted)]"><p className="mb-3 font-mono text-xs">CONTEXT AFTER · {source.next_location}</p>{source.next_content}</article> : null}</div></main>;
}
