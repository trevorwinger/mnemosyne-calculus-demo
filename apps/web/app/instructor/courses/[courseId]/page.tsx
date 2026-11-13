"use client";

import { ChangeEvent, DragEvent, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { Copy, Link2, Upload, Users } from "lucide-react";
import { api, apiBlob, apiUpload, Course, IngestionCapabilities, InstructorConceptProgress, InstructorStudentEvidence, QueueStatus } from "../../../../lib/api";

type Material = {
  id: string; title: string; material_type: string; module: string | null;
  student_visible: boolean; processing_status: string; release_at: string | null;
  extraction_error: string | null; extracted_text: string; original_filename: string | null; version: number; active: boolean; replaces_material_id: string | null;
};
type Enrollment = { id: string; expires_at: string | null; revoked_at: string | null; created_at: string };
type StudentMaterialPreview = { id: string; title: string; material_type: string; module: string | null; preview: string };
type UploadUpdate = { id: string; status: string };

export default function InstructorCourse({ params }: { params: Promise<{ courseId: string }> }) {
  const [id, setId] = useState("");
  const [materials, setMaterials] = useState<Material[]>([]);
  const [progress, setProgress] = useState<InstructorConceptProgress[]>([]);
  const [evidence, setEvidence] = useState<InstructorStudentEvidence[]>([]);
  const [queue, setQueue] = useState<QueueStatus[]>([]);
  const [studentPreview, setStudentPreview] = useState<StudentMaterialPreview[] | null>(null);
  const [enrollments, setEnrollments] = useState<Enrollment[]>([]);
  const [code, setCode] = useState("");
  const [enrollmentExpiresAt, setEnrollmentExpiresAt] = useState("");
  const [error, setError] = useState("");
  const [uploading, setUploading] = useState(false);
  const uploadControllers = useRef<AbortController[]>([]);
  const [uploadUpdates, setUploadUpdates] = useState<UploadUpdate[]>([]);
  const [ingestionCapabilities, setIngestionCapabilities] = useState<IngestionCapabilities | null>(null);
  const [published, setPublished] = useState(false);
  const [materialType, setMaterialType] = useState("lecture");
  const [module, setModule] = useState("");
  const [releaseAt, setReleaseAt] = useState("");
  const [editing, setEditing] = useState<Material | null>(null);
  const [editTitle, setEditTitle] = useState("");
  const [editType, setEditType] = useState("lecture");
  const [editModule, setEditModule] = useState("");
  const [editText, setEditText] = useState("");
  const [editReleaseAt, setEditReleaseAt] = useState("");
  const [savingMaterial, setSavingMaterial] = useState(false);
  const [replaceTarget, setReplaceTarget] = useState<Material | null>(null);
  const [since, setSince] = useState("");

  async function load(courseId = id) {
    if (!courseId) return;
    try {
      const [nextMaterials, nextProgress, nextEvidence, nextEnrollments, courses, nextQueue, capabilities] = await Promise.all([
        api<Material[]>(`/v1/courses/${courseId}/materials`),
        api<InstructorConceptProgress[]>(`/v1/courses/${courseId}/instructor-progress`),
        api<InstructorStudentEvidence[]>(`/v1/courses/${courseId}/instructor-evidence`),
        api<Enrollment[]>(`/v1/courses/${courseId}/enrollments`),
        api<Course[]>("/v1/courses"),
        api<QueueStatus[]>(`/v1/courses/${courseId}/work-queue`),
        api<IngestionCapabilities>("/v1/ingestion-capabilities"),
      ]);
      setMaterials(nextMaterials); setProgress(nextProgress); setEvidence(nextEvidence); setEnrollments(nextEnrollments); setQueue(nextQueue); setIngestionCapabilities(capabilities);
      setPublished(courses.find(course => course.id === courseId)?.status === "published"); setError("");
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Could not load course tools."); }
  }

  // The route parameter is the sole initialization input; later reloads use the current course id.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { params.then(({ courseId }) => { setId(courseId); void load(courseId); }); }, [params]);
  useEffect(() => {
    if (!id || !materials.some(material => ["received", "extracting"].includes(material.processing_status))) return;
    const refresh = window.setInterval(() => { void load(); }, 5000);
    return () => window.clearInterval(refresh);
    // `load` intentionally uses the current course id; re-creating it is not needed for polling.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id, materials]);

  async function enrollment() {
    try { const expires_at = enrollmentExpiresAt ? new Date(enrollmentExpiresAt).toISOString() : null; const result = await api<{ code: string }>(`/v1/courses/${id}/enrollments`, { method: "POST", body: JSON.stringify({ expires_at }) }); setCode(result.code); await load(); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "Could not create enrollment link."); }
  }
  async function rotateEnrollment() {
    if (!window.confirm("Rotate enrollment? Current active codes will stop working.")) return;
    try { const result = await api<{ code: string }>(`/v1/courses/${id}/enrollments/rotate`, { method: "POST" }); setCode(result.code); await load(); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "Could not rotate enrollment codes."); }
  }
  async function uploadFiles(files: File[]) {
    if (!files.length) return;
    if (replaceTarget && files.length !== 1) { setError("Choose one replacement file at a time so the version history stays clear."); return; }
    setUploading(true); setError("");
    setUploadUpdates(files.map((file, index) => ({ id: `${file.name}-${index}`, status: `Uploading ${file.name}: 0%` })));
    try {
      const results = await Promise.all(files.map(async (file, index) => {
        const controller = new AbortController(); uploadControllers.current.push(controller);
        try {
          const form = new FormData(); form.append("file", file); form.append("material_type", materialType);
          if (module.trim()) form.append("module", module.trim());
          if (releaseAt) form.append("release_at", new Date(releaseAt).toISOString());
          if (replaceTarget) form.append("replaces_material_id", replaceTarget.id);
          const material = await apiUpload<Material>(`/v1/courses/${id}/materials/upload`, form, {
            signal: controller.signal,
            onProgress: ({ loaded, total }) => setUploadUpdates(updates => updates.map((update, updateIndex) => updateIndex === index ? { ...update, status: `Uploading ${file.name}: ${Math.round((loaded / total) * 100)}%` } : update)),
          });
          return { material, update: `${file.name}: uploaded and queued for extraction.` };
        } catch (cause) { return { material: null, update: `${file.name}: ${cause instanceof Error && cause.name === "AbortError" ? "upload canceled" : cause instanceof Error ? cause.message : "upload failed"}` }; }
        finally { uploadControllers.current = uploadControllers.current.filter(item => item !== controller); }
      }));
      const completed = results.flatMap(result => result.material ? [result.material] : []);
      if (completed.length) setMaterials(items => [...items, ...completed]);
      if (completed.length && replaceTarget) setReplaceTarget(null);
      setUploadUpdates(results.map((result, index) => ({ id: `${files[index].name}-${index}`, status: result.update })));
      if (!completed.length && results.some(result => result.update.includes("failed"))) setError("No files in this batch were uploaded.");
    } finally { setUploading(false); }
  }
  async function upload(event: ChangeEvent<HTMLInputElement>) { const input = event.target; await uploadFiles(Array.from(input.files ?? [])); input.value = ""; }
  function dropFiles(event: DragEvent<HTMLDivElement>) { event.preventDefault(); void uploadFiles(Array.from(event.dataTransfer.files)); }
  function cancelUploads() { uploadControllers.current.forEach(controller => controller.abort()); }
  async function toggle(material: Material) {
    try { const updated = await api<Material>(`/v1/materials/${material.id}/review`, { method: "POST", body: JSON.stringify({ student_visible: !material.student_visible }) }); setMaterials(items => items.map(item => item.id === updated.id ? updated : item)); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "Could not update material."); }
  }
  async function reprocess(material: Material) {
    try { const updated = await api<Material>(`/v1/materials/${material.id}/reprocess`, { method: "POST" }); setMaterials(items => items.map(item => item.id === updated.id ? updated : item)); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "Could not retry material processing."); }
  }
  async function previewOriginal(material: Material) {
    try { const file = await apiBlob(`/v1/materials/${material.id}/original`); const url = URL.createObjectURL(file); window.open(url, "_blank", "noopener,noreferrer"); window.setTimeout(() => URL.revokeObjectURL(url), 60_000); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "Could not preview the private original."); }
  }
  function startEdit(material: Material) {
    setEditing(material); setEditTitle(material.title); setEditType(material.material_type); setEditModule(material.module ?? ""); setEditText(material.extracted_text); setEditReleaseAt(material.release_at ? new Date(material.release_at).toISOString().slice(0, 16) : "");
  }
  async function saveMaterial() {
    if (!editing || !editTitle.trim() || !editText.trim()) return;
    setSavingMaterial(true);
    try { const updated = await api<Material>(`/v1/materials/${editing.id}/review`, { method: "POST", body: JSON.stringify({ title: editTitle.trim(), material_type: editType, module: editModule.trim() || null, extracted_text: editText.trim(), release_at: editReleaseAt ? new Date(editReleaseAt).toISOString() : null }) }); setMaterials(items => items.map(item => item.id === updated.id ? updated : item)); setEditing(null); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "Could not save material changes."); }
    finally { setSavingMaterial(false); }
  }
  async function remove(material: Material) {
    if (!window.confirm(`Delete “${material.title}”? This removes its private original and it can no longer be cited.`)) return;
    try { await api<void>(`/v1/materials/${material.id}`, { method: "DELETE" }); setMaterials(items => items.filter(item => item.id !== material.id)); if (editing?.id === material.id) setEditing(null); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "Could not delete this material."); }
  }
  async function revoke(enrollmentId: string) {
    try { await api<void>(`/v1/enrollments/${enrollmentId}/revoke`, { method: "POST" }); await load(); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "Could not revoke code."); }
  }
  async function publish() {
    try {
      const needsAcknowledgement = !materials.some(item => item.student_visible && item.processing_status === "ready");
      if (needsAcknowledgement && !window.confirm("No released course source is ready. Publish enrollment with this limitation?")) return;
      const course = await api<{ status: string }>(`/v1/courses/${id}/publish`, { method: "POST", body: JSON.stringify({ acknowledge_without_sources: needsAcknowledgement }) });
      setPublished(course.status === "published");
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Could not publish enrollment access."); }
  }
  async function archive() {
    if (!window.confirm("Archive this course? Students will no longer be able to access it.")) return;
    try { await api<Course>(`/v1/courses/${id}/archive`, { method: "POST" }); setPublished(false); setError("Course archived. It is no longer available to students."); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "Could not archive course."); }
  }
  async function refreshSignals() {
    try { const query = since ? `?since=${encodeURIComponent(`${since}T00:00:00Z`)}` : ""; const [nextProgress, nextEvidence] = await Promise.all([api<InstructorConceptProgress[]>(`/v1/courses/${id}/instructor-progress${query}`), api<InstructorStudentEvidence[]>(`/v1/courses/${id}/instructor-evidence${query}`)]); setProgress(nextProgress); setEvidence(nextEvidence); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "Could not filter learning signals."); }
  }
  async function previewAsStudent() {
    try { setStudentPreview(await api<StudentMaterialPreview[]>(`/v1/courses/${id}/preview-as-student/materials`)); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "Could not load the student material preview."); }
  }

  const readyReleased = materials.filter(material => material.active && material.student_visible && material.processing_status === "ready").length;
  const failedMaterials = materials.filter(material => material.active && material.processing_status === "failed").length;
  const processingMaterials = materials.filter(material => material.active && ["received", "extracting"].includes(material.processing_status)).length;
  const replacementByMaterialId = new Map(materials.filter(material => material.replaces_material_id).map(material => [material.replaces_material_id!, material]));

  return <main className="mx-auto max-w-5xl px-5 pb-16 pt-10">
    <nav className="flex flex-wrap gap-4 text-sm" aria-label="Instructor course navigation">
      <Link href="/workspace" className="font-semibold">← Workspaces</Link>
      <Link href={`/instructor/courses/${id}/settings`} className="underline">Settings</Link>
      <Link href={`/instructor/courses/${id}/concepts`} className="underline">Concepts</Link>
      <Link href={`/instructor/courses/${id}/exercises`} className="underline">Practice</Link>
      <Link href={`/instructor/courses/${id}/roster`} className="underline">Roster</Link>
    </nav>
    <p className="mt-8 font-mono text-sm">INSTRUCTOR COURSE</p><h1 className="mt-2 text-4xl font-semibold">Course tools & learning signals</h1>
    <section className="bordered mt-6 grid gap-3 p-4 text-sm sm:grid-cols-3"><div><p className="font-semibold">{readyReleased} released source{readyReleased === 1 ? "" : "s"}</p><p className="mt-1 text-[var(--muted)]">Ready for student retrieval</p></div><div><p className="font-semibold">{processingMaterials} processing</p><p className="mt-1 text-[var(--muted)]">Review again after extraction</p></div><div><p className="font-semibold">{failedMaterials} failed</p><p className="mt-1 text-[var(--muted)]">Retry or correct before release</p></div>{!readyReleased ? <p className="sm:col-span-3 text-[var(--muted)]">Publishing without a ready released source requires the explicit no-source acknowledgment.</p> : null}</section>
    <section className="bordered mt-4 p-4 text-sm"><h2 className="font-semibold">Course work queue</h2>{queue.length ? <div className="mt-2 flex flex-wrap gap-2">{queue.map(item => <span className="rounded border border-[var(--line)] px-2 py-1" key={`${item.kind}-${item.status}`}>{item.count} {item.kind.replaceAll("_", " ")} · {item.status}</span>)}</div> : <p className="mt-1 text-[var(--muted)]">No pending, retrying, processing, or failed work for this course.</p>}<p className="mt-2 text-xs text-[var(--muted)]">Failed material extraction can be retried from its source card.</p></section>
    <div className="mt-9 grid gap-5 md:grid-cols-[1fr_300px]">
      <section className="bordered p-6" onDragOver={event => event.preventDefault()} onDrop={dropFiles}>
        <div className="flex flex-wrap items-center justify-between gap-3"><div><h2 className="text-xl font-semibold">Materials</h2><p className="mt-1 text-sm text-[var(--muted)]">Drop files here or browse · {ingestionCapabilities ? ingestionCapabilities.extensions.map(extension => `.${extension}`).join(", ") : "supported course files"} · {ingestionCapabilities ? `${ingestionCapabilities.max_upload_mb} MB max per file` : "loading size limit…"}</p></div><div className="flex gap-2"><label className="primary inline-flex cursor-pointer items-center gap-2"><Upload size={16}/>{uploading ? "Uploading…" : "Upload files"}<input className="sr-only" type="file" multiple accept=".pdf,.docx,.doc,.pptx,.ppt,.xlsx,.xls,.txt,.md,.csv,.html,.htm,.rtf,.odt,.odp,.png,.jpg,.jpeg" onChange={upload} disabled={uploading}/></label>{uploading ? <button className="secondary text-sm" type="button" onClick={cancelUploads}>Cancel uploads</button> : null}</div></div>
        {uploadUpdates.length ? <div aria-live="polite" className="mt-4 space-y-1 text-sm text-[var(--muted)]">{uploadUpdates.map(update => <p key={update.id}>{update.status}</p>)}</div> : null}
        <div className="mt-4 grid gap-3 sm:grid-cols-3"><select aria-label="Material type" className="field" value={materialType} onChange={event => setMaterialType(event.target.value)}><option value="lecture">Lecture</option><option value="reading">Reading</option><option value="assignment">Assignment</option><option value="syllabus">Syllabus</option><option value="answer_key">Answer key</option></select><input className="field" value={module} onChange={event => setModule(event.target.value)} placeholder="Module or week" aria-label="Module or week"/><input className="field" type="datetime-local" value={releaseAt} onChange={event => setReleaseAt(event.target.value)} aria-label="Optional release time"/></div>
        {materials.length ? <div className="mt-5 space-y-3">{materials.map(material => { const replacement = replacementByMaterialId.get(material.id); return <article className="bordered p-4" key={material.id}><div className="flex justify-between gap-4"><div><p className="font-mono text-xs text-[var(--muted)]">VERSION {material.version} · {material.active ? material.processing_status.toUpperCase() : "SUPERSEDED"} · {material.material_type.toUpperCase()}{material.module ? ` · ${material.module}` : ""}{material.release_at ? ` · releases ${new Date(material.release_at).toLocaleString()}` : ""}</p><h3 className="mt-1 font-semibold">{material.title}</h3></div><button className={material.student_visible ? "primary text-xs" : "secondary text-xs"} onClick={() => toggle(material)} disabled={!material.active || material.processing_status !== "ready"}>{!material.active ? "Historical version" : material.student_visible ? "Student visible" : material.processing_status === "ready" ? "Draft — release" : "Processing"}</button></div>{replacement ? <p className="mt-3 text-sm text-[var(--muted)]">Superseded by version {replacement.version} ({replacement.title}). This preserved version is excluded from new retrieval and remains accessible only from a student’s own earlier citation.</p> : null}{material.extraction_error ? <p className="mt-3 text-sm">Processing failed: {material.extraction_error} {material.active ? <button className="underline" onClick={() => reprocess(material)}>Retry</button> : null}</p> : <p className="mt-3 line-clamp-4 text-sm leading-6 text-[var(--muted)]">{material.extracted_text || "Extraction is queued. Refresh in a moment."}</p>}<div className="mt-3 flex gap-4 text-sm">{material.original_filename ? <button className="underline" onClick={() => previewOriginal(material)}>Preview original</button> : null}{material.active ? <button className="underline" onClick={() => startEdit(material)}>Review & edit</button> : <span className="text-[var(--muted)]">Preserved for citation history</span>}<button className="underline" onClick={() => remove(material)}>Delete</button></div></article>; })}</div> : <p className="mt-5 text-[var(--muted)]">No course materials yet. Upload a source to review its extracted text.</p>}
        <section className="bordered mt-5 p-4"><div className="flex flex-wrap items-center justify-between gap-3"><div><h3 className="font-semibold">Preview as student</h3><p className="mt-1 text-sm text-[var(--muted)]">Shows the exact active, released, ready sources eligible for student retrieval right now.</p></div><button className="secondary text-sm" type="button" onClick={previewAsStudent}>Refresh preview</button></div>{studentPreview ? studentPreview.length ? <div className="mt-4 space-y-3">{studentPreview.map(material => <article className="bordered p-3" key={material.id}><p className="font-semibold">{material.title}</p><p className="mt-1 font-mono text-xs text-[var(--muted)]">{material.material_type}{material.module ? ` · ${material.module}` : ""}</p><p className="mt-2 line-clamp-3 whitespace-pre-wrap text-sm text-[var(--muted)]">{material.preview}</p></article>)}</div> : <p className="mt-4 text-sm text-[var(--muted)]">No materials are currently eligible for student retrieval.</p> : null}</section>
        {materials.some(material => material.active) ? <div className="bordered mt-5 p-4"><label className="label" htmlFor="replace-source">Replace an existing source</label><div className="flex flex-wrap gap-3"><select id="replace-source" className="field flex-1" value={replaceTarget?.id ?? ""} onChange={event => setReplaceTarget(materials.find(material => material.id === event.target.value) ?? null)}><option value="">Upload a new source instead</option>{materials.filter(material => material.active).map(material => <option key={material.id} value={material.id}>{material.title} · version {material.version}</option>)}</select>{replaceTarget ? <button className="secondary text-sm" type="button" onClick={() => setReplaceTarget(null)}>Cancel replacement</button> : null}</div>{replaceTarget ? <p className="mt-2 text-sm text-[var(--muted)]">The next single file you upload will become version {replaceTarget.version + 1}. Version {replaceTarget.version} stays available only to students’ prior citations.</p> : null}</div> : null}
        {editing ? <section className="bordered mt-6 p-5"><div className="flex items-center justify-between gap-3"><h3 className="font-semibold">Review course material</h3><button className="text-sm underline" onClick={() => setEditing(null)}>Close</button></div><p className="mt-1 text-sm text-[var(--muted)]">Correct extracted text before students can use it. Saving re-chunks this source for retrieval.</p><div className="mt-4 grid gap-3 sm:grid-cols-2"><input aria-label="Material title" className="field" value={editTitle} onChange={event => setEditTitle(event.target.value)}/><select aria-label="Material type" className="field" value={editType} onChange={event => setEditType(event.target.value)}><option value="lecture">Lecture</option><option value="reading">Reading</option><option value="assignment">Assignment</option><option value="syllabus">Syllabus</option><option value="answer_key">Answer key</option></select><input aria-label="Module" className="field" value={editModule} onChange={event => setEditModule(event.target.value)} placeholder="Module or week"/><input aria-label="Release time" className="field" type="datetime-local" value={editReleaseAt} onChange={event => setEditReleaseAt(event.target.value)}/></div><textarea aria-label="Extracted source text" className="field mt-3 min-h-56" value={editText} onChange={event => setEditText(event.target.value)}/><button className="primary mt-4" onClick={saveMaterial} disabled={savingMaterial || !editTitle.trim() || !editText.trim()}>{savingMaterial ? "Saving…" : "Save reviewed source"}</button></section> : null}
      </section>
      <aside className="bordered h-fit p-6"><Users size={22}/><h2 className="mt-4 text-xl font-semibold">Enrollment</h2><p className="mt-2 text-sm leading-6 text-[var(--muted)]">{published ? "Enrollment access is published." : "Publish enrollment once sources are released or you acknowledge the no-source mode."}</p><button className="primary mt-5 w-full" onClick={publish} disabled={published}>{published ? "Published" : "Publish access"}</button><label className="label mt-5" htmlFor="enrollment-expiry">Code expiration</label><input id="enrollment-expiry" className="field" type="datetime-local" value={enrollmentExpiresAt} onChange={event => setEnrollmentExpiresAt(event.target.value)}/><p className="mt-1 text-xs text-[var(--muted)]">Optional. Leave blank for a code that remains open until revoked or rotated.</p><button className="secondary mt-3 w-full inline-flex items-center justify-center gap-2" onClick={enrollment}><Link2 size={16}/> Generate code</button>{code ? <div className="mt-4 bordered p-3"><p className="font-mono text-lg font-bold">{code}</p><button className="mt-2 text-sm underline" onClick={() => navigator.clipboard.writeText(code)}><Copy className="mr-1 inline" size={13}/> Copy</button></div> : null}<div className="mt-5 space-y-2 text-xs text-[var(--muted)]">{enrollments.slice(0, 5).map(item => <div className="flex items-center justify-between gap-2" key={item.id}><span>{item.revoked_at ? "Revoked" : item.expires_at && new Date(item.expires_at) <= new Date() ? "Expired" : "Active code"} · {item.expires_at ? `expires ${new Date(item.expires_at).toLocaleString()}` : `created ${new Date(item.created_at).toLocaleDateString()}`}</span>{item.revoked_at ? null : <button className="underline" onClick={() => revoke(item.id)}>Revoke</button>}</div>)}</div><button className="mt-6 text-sm underline" onClick={archive}>Archive course</button></aside>
    </div>
    <div className="mt-5 flex justify-end"><button className="secondary text-sm" onClick={rotateEnrollment}>Rotate all active enrollment codes</button></div>
    <section className="mt-10"><h2 className="text-2xl font-semibold">Course learning signals</h2><p className="mt-2 text-sm text-[var(--muted)]">Aggregated evidence only—no student chat transcripts are shown here. “Hint-assisted” means a successful event recorded after one or more hints; “independent” means a recorded success explicitly marked independent.</p><div className="mt-4 flex flex-wrap items-end gap-3"><label className="text-sm">From <input className="field mt-1 w-auto" type="date" value={since} onChange={event => setSince(event.target.value)}/></label><button className="secondary text-sm" onClick={refreshSignals}>Apply filter</button></div>{progress.length ? <div className="mt-5 grid gap-3 md:grid-cols-3">{progress.map(item => <article className="bordered p-4" key={item.concept}><p className="font-semibold">{item.concept}</p><p className="mt-3 text-sm">{item.students_with_evidence} students with evidence</p><p className="mt-1 text-xs text-[var(--muted)]">{item.independent_successes} independent · {item.hint_assisted_successes} hint-assisted successes</p></article>)}</div> : <p className="bordered mt-5 p-4 text-[var(--muted)]">No learning evidence yet.</p>}<h3 className="mt-8 font-semibold">Recent evidence</h3>{evidence.length ? <div className="mt-3 space-y-3">{evidence.slice(0, 12).map((item, index) => <article className="bordered p-4" key={`${item.student_name}-${item.concept}-${index}`}><p className="font-semibold">{item.concept} <span className="font-normal text-[var(--muted)]">· {item.student_name}</span></p><p className="mt-1 text-sm text-[var(--muted)]">{item.observed_behavior}</p><p className="mt-2 font-mono text-xs text-[var(--muted)]">{item.result} · {item.independence.replaceAll("_", " ")} · {item.hint_count} hints</p></article>)}</div> : <p className="bordered mt-3 p-4 text-[var(--muted)]">No recent evidence.</p>}</section>
    {error ? <p role="alert" className="mt-5">{error}</p> : null}
  </main>;
}
