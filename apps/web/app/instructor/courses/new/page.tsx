"use client";
import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Check, ChevronRight, Save } from "lucide-react";
import { api } from "../../../../lib/api";

const steps = ["Course details", "Materials", "Review & publish"];
const draftKey = "office-hours-course-draft";
type CourseDraft = { title: string; course_code: string; description: string; term: string; objectives: string; preferences: string };
const emptyCourse = { title: "", course_code: "", description: "", term: "", objectives: "", preferences: "Guide with questions and graduated hints." };
export default function NewCourse() {
  const router = useRouter(); const [step, setStep] = useState(0); const [error, setError] = useState(""); const [saving, setSaving] = useState(false);
  const [data, setData] = useState<CourseDraft>(emptyCourse);
  useEffect(() => {
    const restore = window.setTimeout(() => {
      try { setData({ ...emptyCourse, ...JSON.parse(localStorage.getItem(draftKey) ?? "{}") }); } catch { setData(emptyCourse); }
      const savedStep = Number(localStorage.getItem(`${draftKey}:step`) ?? 0);
      if (Number.isInteger(savedStep) && savedStep >= 0 && savedStep < steps.length) setStep(savedStep);
    }, 0);
    return () => window.clearTimeout(restore);
  }, []);
  function update(field: keyof typeof data, value: string) { setData(prev => { const next = { ...prev, [field]: value }; localStorage.setItem(draftKey, JSON.stringify(next)); return next; }); }
  function moveTo(nextStep: number) { setStep(nextStep); localStorage.setItem(`${draftKey}:step`, String(nextStep)); }
  async function submit(event: FormEvent) {
    event.preventDefault(); setError("");
    if (step < 2) { moveTo(step + 1); return; }
    setSaving(true);
    try { await api("/v1/courses", { method: "POST", body: JSON.stringify({ title: data.title, course_code: data.course_code || null, description: data.description, term: data.term || null, learning_objectives: data.objectives.split("\n").map(x => x.trim()).filter(Boolean), tutoring_preferences: { guidance: data.preferences } }) }); localStorage.removeItem(draftKey); localStorage.removeItem(`${draftKey}:step`); router.push("/workspace"); }
    catch (e) { setError(e instanceof Error ? e.message : "Could not save course."); }
    finally { setSaving(false); }
  }
  return <main className="mx-auto max-w-3xl px-5 pb-16 pt-8"><p className="font-mono text-sm">INSTRUCTOR SETUP</p><h1 className="mt-3 text-4xl font-semibold">Create your course.</h1><ol className="my-10 flex gap-2 text-sm" aria-label="Course setup progress">{steps.map((label, index) => <li className={`flex items-center gap-2 ${index === step ? "font-bold" : "text-[var(--muted)]"}`} key={label}><span className={`grid h-6 w-6 place-items-center rounded-full border ${index <= step ? "border-black bg-[var(--accent)] text-black" : "border-[var(--line)]"}`}>{index < step ? <Check size={14}/> : index + 1}</span><span className="hidden sm:inline">{label}</span>{index !== steps.length - 1 && <ChevronRight size={15}/>}</li>)}</ol><form className="bordered p-5 md:p-7" onSubmit={submit}>{step === 0 && <div className="space-y-5"><div><label className="label" htmlFor="title">Course title</label><input required id="title" className="field" value={data.title} onChange={e => update("title", e.target.value)} placeholder="Introduction to Programming in Java"/></div><div className="grid gap-5 sm:grid-cols-2"><div><label className="label" htmlFor="code">Course code <span className="font-normal text-[var(--muted)]">(optional)</span></label><input id="code" className="field" value={data.course_code} onChange={e => update("course_code", e.target.value)} placeholder="CSCI-201"/></div><div><label className="label" htmlFor="term">Term <span className="font-normal text-[var(--muted)]">(optional)</span></label><input id="term" className="field" value={data.term} onChange={e => update("term", e.target.value)} placeholder="Fall 2026"/></div></div><div><label className="label" htmlFor="description">Description</label><textarea id="description" className="field min-h-28" value={data.description} onChange={e => update("description", e.target.value)} placeholder="What should students expect in this course?"/></div></div>}{step === 1 && <div className="space-y-5"><h2 className="text-2xl font-semibold">Learning objectives</h2><p className="text-[var(--muted)]">One objective per line. You can refine concepts and upload materials after saving this draft.</p><div><label className="label" htmlFor="objectives">Objectives</label><textarea id="objectives" className="field min-h-40" value={data.objectives} onChange={e => update("objectives", e.target.value)} placeholder={"Trace a loop\nUse methods\nReason about arrays"}/></div><div className="bordered bg-[var(--surface)] p-4 text-sm"><b>Materials come next.</b><p className="mt-1 text-[var(--muted)]">New uploads will default to draft and must be reviewed before student release.</p></div></div>}{step === 2 && <div className="space-y-5"><h2 className="text-2xl font-semibold">Tutoring preference</h2><p className="text-[var(--muted)]">This is an instructional preference, not a way to bypass the tutoring policy.</p><div><label className="label" htmlFor="preference">How should tutoring feel?</label><textarea id="preference" className="field min-h-28" value={data.preferences} onChange={e => update("preferences", e.target.value)}/></div><div className="bordered bg-[var(--surface)] p-4 text-sm"><b>Saved as a draft.</b><p className="mt-1 text-[var(--muted)]">Publishing enrollment will require a student-visible ready resource or your later confirmation to operate without sources.</p></div></div>}{error && <p role="alert" className="mt-5 text-sm font-semibold">{error}</p>}<div className="mt-8 flex justify-between gap-3">{step > 0 ? <button type="button" className="secondary" onClick={() => moveTo(step - 1)}>Back</button> : <span/>}<button className="primary inline-flex items-center gap-2" disabled={saving}>{step === 2 ? <><Save size={17}/>{saving ? "Saving…" : "Save course draft"}</> : <>Continue <ChevronRight size={17}/></>}</button></div></form></main>;
}
