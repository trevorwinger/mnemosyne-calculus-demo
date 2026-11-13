"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, MemoryObservation, ProgressItem } from "../../../../../lib/api";

export default function StudentInsights({ params }: { params: Promise<{ courseId: string }> }) {
  const [courseId, setCourseId] = useState("");
  const [progress, setProgress] = useState<ProgressItem[]>([]);
  const [memory, setMemory] = useState<MemoryObservation[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function load(id = courseId) {
    if (!id) return;
    try {
      const [nextProgress, nextMemory] = await Promise.all([api<ProgressItem[]>(`/v1/courses/${id}/progress`), api<MemoryObservation[]>(`/v1/courses/${id}/memory`)]);
      setProgress(nextProgress); setMemory(nextMemory); setError("");
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Could not load your learning data."); }
  }
  // The route parameter is the only initialization input; later reloads use the current course id.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { void params.then(({ courseId: id }) => { setCourseId(id); return load(id); }); }, [params]);
  async function forget(id: string) { setBusy(true); try { await api<void>(`/v1/memory/${id}/forget`, { method: "POST" }); await load(); } catch (cause) { setError(cause instanceof Error ? cause.message : "Could not forget this observation."); } finally { setBusy(false); } }
  async function correct(id: string, result: string) { setBusy(true); try { await api<MemoryObservation>(`/v1/memory/${id}/correct`, { method: "POST", body: JSON.stringify({ result }) }); await load(); } catch (cause) { setError(cause instanceof Error ? cause.message : "Could not correct this observation."); } finally { setBusy(false); } }
  async function clear() { if (!window.confirm("Clear all stored learning observations for this course? This cannot be undone.")) return; setBusy(true); try { await api<void>(`/v1/courses/${courseId}/memory/clear`, { method: "POST" }); await load(); } catch (cause) { setError(cause instanceof Error ? cause.message : "Could not clear learning data."); } finally { setBusy(false); } }
  async function download() { setBusy(true); try { const data = await api<Record<string, unknown>>(`/v1/courses/${courseId}/export`); const link = document.createElement("a"); link.href = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: "application/json" })); link.download = "mnemosyne-learning-data.json"; link.click(); URL.revokeObjectURL(link.href); } catch (cause) { setError(cause instanceof Error ? cause.message : "Could not export learning data."); } finally { setBusy(false); } }

  return <main className="mx-auto max-w-4xl px-5 pb-16 pt-10">
    <Link href="/workspace" className="text-sm font-semibold">← Courses</Link>
    <p className="mt-8 font-mono text-sm">LEARNING RECORD</p><h1 className="mt-2 text-4xl font-semibold">Progress & stored memory</h1>
    <p className="mt-3 max-w-2xl text-[var(--muted)]">This is course-specific evidence Mnemosyne uses to continue your learning. It is separate from chat history.</p>
    {error ? <p role="alert" className="bordered mt-6 p-4">{error}</p> : null}
    <section className="mt-10"><h2 className="text-xl font-semibold">Progress by concept</h2>{progress.length ? <div className="mt-4 grid gap-3 sm:grid-cols-2">{progress.map(item => <article className="bordered p-4" key={item.concept}><p className="font-semibold">{item.concept}</p><p className="mt-2 text-sm text-[var(--muted)]">{item.status} · {item.recent_evidence_count} observation{item.recent_evidence_count === 1 ? "" : "s"}</p></article>)}</div> : <p className="bordered mt-4 p-4 text-[var(--muted)]">No progress observations yet. They appear after eligible course attempts.</p>}</section>
    <section className="mt-10"><div className="flex flex-wrap items-end justify-between gap-3"><div><h2 className="text-xl font-semibold">Stored observations</h2><p className="mt-1 text-sm text-[var(--muted)]">Correct a result, view supporting chat evidence, forget one observation, or clear this course’s memory.</p></div><div className="flex gap-2"><button className="secondary text-sm" disabled={busy} onClick={download}>Export JSON</button><button className="secondary text-sm" disabled={busy || !memory.length} onClick={clear}>Clear all</button></div></div>{memory.length ? <div className="mt-4 space-y-3">{memory.map(item => <article className="bordered flex flex-wrap items-start justify-between gap-4 p-4" key={item.id}><div><p className="font-semibold">{item.concept}</p><p className="mt-1 text-sm text-[var(--muted)]">{item.observed_behavior}</p><p className="mt-2 font-mono text-xs text-[var(--muted)]">{item.evidence_type.replaceAll("_", " ")} · {item.independence.replaceAll("_", " ")}</p>{item.source_session_id ? <Link className="mt-2 inline-block text-sm underline" href={`/student/chat/${item.source_session_id}`}>View chat evidence</Link> : null}</div><div className="flex items-center gap-2"><label className="text-sm">Result <select className="field ml-1 w-auto py-1" value={item.result} disabled={busy} onChange={event => correct(item.id, event.target.value)}><option value="needs_practice">Needs practice</option><option value="success">Success</option></select></label><button className="secondary text-sm" disabled={busy} onClick={() => forget(item.id)}>Forget</button></div></article>)}</div> : <p className="bordered mt-4 p-4 text-[var(--muted)]">No stored observations for this course.</p>}</section>
  </main>;
}
