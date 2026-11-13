"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { api, CourseSettings, Model, ModelProviderStatus } from "../../../../../lib/api";

export default function CourseSettingsPage({ params }: { params: Promise<{ courseId: string }> }) {
  const [id, setId] = useState("");
  const [data, setData] = useState<CourseSettings | null>(null);
  const [models, setModels] = useState<Model[]>([]);
  const [provider, setProvider] = useState<ModelProviderStatus | null>(null);
  const [objectives, setObjectives] = useState("");
  const [prerequisites, setPrerequisites] = useState("");
  const [guidance, setGuidance] = useState("");
  const [retentionDays, setRetentionDays] = useState("");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    void params.then(async ({ courseId }) => {
      setId(courseId);
      try {
        const [settings, availableModels, providerStatus] = await Promise.all([api<CourseSettings>(`/v1/courses/${courseId}/settings`), api<Model[]>("/v1/models"), api<ModelProviderStatus>("/v1/models/status")]);
        setData(settings); setModels(availableModels); setProvider(providerStatus);
        setObjectives(settings.learning_objectives.join("\n"));
        setPrerequisites((settings.tutoring_preferences.prerequisites ?? []).join("\n"));
        setGuidance(settings.tutoring_preferences.guidance ?? "");
        setRetentionDays(settings.tutoring_preferences.learning_evidence_retention_days?.toString() ?? "");
      } catch (cause) { setError(cause instanceof Error ? cause.message : "Could not load course settings."); }
    });
  }, [params]);

  async function submit(event: FormEvent) {
    event.preventDefault(); if (!data) return;
    const retention = retentionDays.trim() ? Number(retentionDays) : null;
    if (retention !== null && (!Number.isInteger(retention) || retention < 1 || retention > 3650)) { setError("Retention must be a whole number from 1 to 3650 days, or left blank."); return; }
    setSaving(true);
    try {
      const tutoring_preferences = {
        ...data.tutoring_preferences,
        guidance,
        prerequisites: prerequisites.split("\n").map(value => value.trim()).filter(Boolean),
        standard_tutor_model: data.tutoring_preferences.standard_tutor_model || undefined,
        learning_evidence_retention_days: retention,
      };
      const updated = await api<CourseSettings>(`/v1/courses/${id}/settings`, { method: "POST", body: JSON.stringify({ title: data.title, course_code: data.course_code || null, description: data.description, term: data.term || null, learning_objectives: objectives.split("\n").map(value => value.trim()).filter(Boolean), tutoring_preferences }) });
      setData(updated); setError("");
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Could not save course settings."); }
    finally { setSaving(false); }
  }
  async function refreshModels() {
    try { const [availableModels, providerStatus] = await Promise.all([api<Model[]>("/v1/models"), api<ModelProviderStatus>("/v1/models/status")]); setModels(availableModels); setProvider(providerStatus); setError(""); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "Could not refresh local models."); }
  }

  if (!data) return <main className="grid min-h-[70vh] place-items-center">{error || "Loading course settings…"}</main>;
  const availableModels = models.filter(model => model.approved);
  const unavailableModels = models.filter(model => !model.approved);
  const memoryDefault = data.tutoring_preferences.memory_enabled_default !== false;

  return <main className="mx-auto max-w-3xl px-5 pb-16 pt-10">
    <Link href={`/instructor/courses/${id}`} className="text-sm font-semibold">← Course tools</Link>
    <p className="mt-8 font-mono text-sm">INSTRUCTOR COURSE</p><h1 className="mt-2 text-4xl font-semibold">Course settings</h1>
    <form className="mt-8 space-y-5" onSubmit={submit}>
      <div><label className="label" htmlFor="title">Course title</label><input id="title" className="field" value={data.title} onChange={event => setData({ ...data, title: event.target.value })}/></div>
      <div className="grid gap-5 sm:grid-cols-2"><div><label className="label" htmlFor="code">Course code</label><input id="code" className="field" value={data.course_code ?? ""} onChange={event => setData({ ...data, course_code: event.target.value || null })}/></div><div><label className="label" htmlFor="term">Term</label><input id="term" className="field" value={data.term ?? ""} onChange={event => setData({ ...data, term: event.target.value || null })}/></div></div>
      <div><label className="label" htmlFor="description">Description</label><textarea id="description" className="field min-h-28" value={data.description} onChange={event => setData({ ...data, description: event.target.value })}/></div>
      <div><label className="label" htmlFor="objectives">Learning objectives</label><textarea id="objectives" className="field min-h-32" value={objectives} onChange={event => setObjectives(event.target.value)}/></div>
      <div><label className="label" htmlFor="prerequisites">Prerequisites</label><textarea id="prerequisites" className="field min-h-24" value={prerequisites} onChange={event => setPrerequisites(event.target.value)} placeholder="One prerequisite per line"/></div>
      <div><label className="label" htmlFor="guidance">Tutoring preference</label><textarea id="guidance" className="field min-h-28" value={guidance} onChange={event => setGuidance(event.target.value)}/></div>
      <section className="bordered p-4"><h2 className="font-semibold">New-session memory default</h2><p className="mt-1 text-sm text-[var(--muted)]">This only controls whether new replies use stored course memory. Eligible learning progress is still recorded.</p><button type="button" role="switch" aria-checked={memoryDefault} className={`mt-4 rounded-full border px-3 py-1 text-sm ${memoryDefault ? "bg-[var(--accent)] text-black" : ""}`} onClick={() => setData({ ...data, tutoring_preferences: { ...data.tutoring_preferences, memory_enabled_default: !memoryDefault } })}>Use stored memory by default: {memoryDefault ? "On" : "Off"}</button></section>
      <section className="bordered p-4"><h2 className="font-semibold">Learning-evidence retention</h2><p className="mt-1 text-sm text-[var(--muted)]">Optional. Keep derived learning observations and progress summaries for this many days. Chat history, source files, and practice submissions are not deleted by this setting.</p><label className="label mt-4" htmlFor="retention-days">Days to retain</label><input id="retention-days" className="field" type="number" min="1" max="3650" step="1" inputMode="numeric" value={retentionDays} onChange={event => setRetentionDays(event.target.value)} placeholder="Keep indefinitely"/><p className="mt-2 text-xs text-[var(--muted)]">Leave blank to retain learning evidence indefinitely. A change schedules a background cleanup.</p></section>
      <section className="bordered p-4"><div className="flex flex-wrap items-center justify-between gap-3"><h2 className="font-semibold">Standard tutor model</h2><button className="text-sm underline" type="button" onClick={refreshModels}>Refresh models</button></div><p className="mt-1 text-sm text-[var(--muted)]">{provider?.detail ?? "Checking local Ollama…"} {provider ? `${provider.approved_model_count} installed chat model${provider.approved_model_count === 1 ? "" : "s"}.` : ""}</p><label className="label mt-4" htmlFor="default-model">New sessions use</label><select id="default-model" className="field" value={data.tutoring_preferences.standard_tutor_model ?? "demo-tutor"} onChange={event => setData({ ...data, tutoring_preferences: { ...data.tutoring_preferences, standard_tutor_model: event.target.value } })}>{availableModels.length ? availableModels.map(model => <option value={model.name} key={model.name}>{model.name}{model.provider === "demo" ? " (demo)" : ""}</option>) : <option value="demo-tutor">demo-tutor (Ollama unavailable)</option>}</select><p className="mt-2 text-xs text-[var(--muted)]">Every installed chat-capable Ollama model is available. Changing this does not alter an existing student session.</p>{unavailableModels.length ? <div className="mt-4 border-t border-[var(--line)] pt-3 text-sm"><p className="font-semibold">Installed but unavailable for chat</p>{unavailableModels.map(model => <p className="mt-1 text-[var(--muted)]" key={model.name}>{model.name} — {model.reason}</p>)}<p className="mt-2 text-xs text-[var(--muted)]">Embedding-only models are shown here but cannot produce tutor replies.</p></div> : null}</section>
      {error ? <p role="alert">{error}</p> : null}<button className="primary" disabled={saving}>{saving ? "Saving…" : "Save settings"}</button>
    </form>
  </main>;
}
