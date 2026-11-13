"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { api, Concept } from "../../../../../lib/api";

export default function Concepts({ params }: { params: Promise<{ courseId: string }> }) {
  const [courseId, setCourseId] = useState(""); const [concepts, setConcepts] = useState<Concept[]>([]); const [name, setName] = useState(""); const [error, setError] = useState(""); const [saving, setSaving] = useState(false);
  useEffect(() => { params.then(async ({ courseId: id }) => { setCourseId(id); try { setConcepts(await api<Concept[]>(`/v1/courses/${id}/concepts`)); } catch (cause) { setError(cause instanceof Error ? cause.message : "Could not load concepts."); } }); }, [params]);
  async function submit(event: FormEvent) { event.preventDefault(); if (!name.trim()) return; setSaving(true); try { const concept = await api<Concept>(`/v1/courses/${courseId}/concepts`, { method: "POST", body: JSON.stringify({ name }) }); setConcepts(items => [...items, concept].sort((a, b) => a.name.localeCompare(b.name))); setName(""); } catch (cause) { setError(cause instanceof Error ? cause.message : "Could not add a concept."); } finally { setSaving(false); } }
  return <main className="mx-auto max-w-3xl px-5 pb-16 pt-10"><Link href={`/instructor/courses/${courseId}`} className="text-sm font-semibold">← Course tools</Link><p className="mt-8 font-mono text-sm">INSTRUCTOR COURSE</p><h1 className="mt-2 text-4xl font-semibold">Learning concepts</h1><p className="mt-3 text-[var(--muted)]">Concepts organize course evidence and instructor aggregates. They do not assign a mastery score.</p><form className="bordered mt-8 flex flex-wrap gap-3 p-4" onSubmit={submit}><label className="sr-only" htmlFor="concept-name">Concept name</label><input id="concept-name" className="field min-w-56 flex-1" value={name} onChange={event => setName(event.target.value)} placeholder="e.g., Array boundaries"/><button className="primary" disabled={saving}>{saving ? "Adding…" : "Add concept"}</button></form>{error ? <p role="alert" className="mt-4">{error}</p> : null}<div className="mt-8 grid gap-3 sm:grid-cols-2">{concepts.map(concept => <article className="bordered p-4" key={concept.id}><p className="font-semibold">{concept.name}</p><p className="mt-1 font-mono text-xs text-[var(--muted)]">{concept.slug}</p></article>)}</div></main>;
}
