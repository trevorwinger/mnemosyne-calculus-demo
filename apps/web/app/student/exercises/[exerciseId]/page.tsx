"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { api, CodeLanguage, CodeRunResult, Exercise } from "../../../../lib/api";

type AttemptResult = { evaluation_status: "not_configured" | "matched" | "try_again" };
const codeLanguages: CodeLanguage[] = ["java", "python", "javascript", "c", "cpp"];
const languageLabel: Record<CodeLanguage, string> = { java: "Java 21", python: "Python", javascript: "JavaScript", c: "C", cpp: "C++" };
const starters: Record<CodeLanguage, string> = {
  java: `public class Main {
  public static void main(String[] args) {
    // Write your first small step here.
  }
}`,
  python: `def main():
    # Write your first small step here.
    pass

if __name__ == "__main__":
    main()`,
  javascript: `function main() {
  // Write your first small step here.
}

main();`,
  c: `#include <stdio.h>

int main(void) {
  // Write your first small step here.
  return 0;
}`,
  cpp: `#include <iostream>

int main() {
  // Write your first small step here.
  return 0;
}`,
};

function exerciseLanguage(exercise: Exercise | null): CodeLanguage | null {
  return exercise && codeLanguages.includes(exercise.exercise_type as CodeLanguage) ? exercise.exercise_type as CodeLanguage : null;
}

export default function StudentExercise({ params }: { params: Promise<{ exerciseId: string }> }) {
  const [exercise, setExercise] = useState<Exercise | null>(null);
  const [response, setResponse] = useState(""); const [assessment, setAssessment] = useState("needs_practice");
  const [code, setCode] = useState(starters.java); const [stdin, setStdin] = useState(""); const [runResult, setRunResult] = useState<CodeRunResult | null>(null); const [running, setRunning] = useState(false);
  const [saved, setSaved] = useState(false); const [evaluation, setEvaluation] = useState<AttemptResult["evaluation_status"]>("not_configured"); const [error, setError] = useState(""); const [saving, setSaving] = useState(false);
  useEffect(() => { params.then(({ exerciseId }) => api<Exercise>(`/v1/exercises/${exerciseId}`).then(item => { setExercise(item); const language = exerciseLanguage(item); if (language) setCode(starters[language]); }).catch(cause => setError(cause instanceof Error ? cause.message : "Could not load practice activity."))); }, [params]);
  const language = exerciseLanguage(exercise);
  async function runCode() {
    if (!exercise || !language || !code.trim()) return;
    setRunning(true); setError(""); setRunResult(null);
    try { setRunResult(await api<CodeRunResult>(`/v1/exercises/${exercise.id}/run-code`, { method: "POST", body: JSON.stringify({ language, source: code, stdin }) })); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "Could not run your code."); }
    finally { setRunning(false); }
  }
  async function submit(event: FormEvent) {
    event.preventDefault(); if (!exercise) return; setSaving(true);
    const savedResponse = language ? `${response.trim()}\n\n${languageLabel[language]} source:\n${code}`.trim() : response;
    try { const attempt = await api<AttemptResult>(`/v1/exercises/${exercise.id}/attempts`, { method: "POST", body: JSON.stringify({ response: savedResponse, self_assessment: assessment }) }); setEvaluation(attempt.evaluation_status); setSaved(true); setError(""); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "Could not save your attempt."); }
    finally { setSaving(false); }
  }
  if (!exercise) return <main className="grid min-h-[70vh] place-items-center">{error || "Loading practice activity…"}</main>;
  const feedback = evaluation === "matched" ? "Your short answer matches the instructor’s configured check. Continue explaining your reasoning with your tutor." : evaluation === "try_again" ? "This short answer does not match the configured check yet. Try another step or ask the tutor for a hint." : null;
  const resultLabel = runResult?.status === "completed" ? "Program finished" : runResult?.status === "compile_error" ? "Compilation needs attention" : runResult?.status === "runtime_error" ? "Program stopped with an error" : runResult?.status === "timeout" ? "Program timed out" : runResult?.status === "compile_timeout" ? "Compilation timed out" : "";
  return <main className="mx-auto max-w-3xl px-5 pb-16 pt-10"><Link href={`/student/courses/${exercise.course_id}/practice`} className="text-sm font-semibold">← Practice activities</Link><p className="mt-8 font-mono text-sm">{language ? `${languageLabel[language].toUpperCase()} CODE LAB` : "GUIDED PRACTICE"}</p><h1 className="mt-2 text-3xl font-semibold">{exercise.title}</h1><article className="bordered mt-6 whitespace-pre-wrap p-5 leading-7">{exercise.prompt}</article>{saved ? <div className="bordered mt-6 p-5"><p className="font-semibold">Attempt saved.</p>{feedback ? <p className="mt-2 text-sm">{feedback}</p> : null}<p className="mt-2 text-sm text-[var(--muted)]">Your course learning record will update if this activity is linked to a concept.</p><Link className="primary mt-4 inline-block" href={`/student/courses/${exercise.course_id}`}>Return to course</Link></div> : <form className="mt-6" onSubmit={submit}>{language ? <section className="bordered mb-6 p-5"><div className="flex flex-wrap items-baseline justify-between gap-3"><div><h2 className="font-semibold">{languageLabel[language]} editor</h2><p className="mt-1 text-sm text-[var(--muted)]">Running code uses a local, isolated sandbox with no network access. Run does not save your code.</p></div><button type="button" className="secondary" onClick={runCode} disabled={running || !code.trim()}>{running ? "Running…" : `Run ${languageLabel[language]}`}</button></div><label className="label mt-5" htmlFor="code-source">{languageLabel[language]} source</label><textarea id="code-source" spellCheck={false} className="field min-h-80 font-mono text-sm leading-6" value={code} onChange={event => setCode(event.target.value)} aria-describedby="runner-limits"/><p id="runner-limits" className="mt-2 text-xs text-[var(--muted)]">20,000 characters max · 4-second compile/check limit · 3-second run limit · isolated local container</p><label className="label mt-5" htmlFor="code-input">Console input <span className="font-normal text-[var(--muted)]">(optional)</span></label><textarea id="code-input" className="field min-h-24 font-mono text-sm" value={stdin} onChange={event => setStdin(event.target.value)} placeholder="One input value per line"/>{runResult ? <section className="mt-5 rounded-lg border border-black bg-black p-4 font-mono text-sm text-white" aria-live="polite"><p className="font-sans font-semibold text-[var(--accent)]">{resultLabel} · {runResult.elapsed_ms} ms</p>{runResult.stdout ? <><p className="mt-4 text-xs text-neutral-300">STANDARD OUTPUT</p><pre className="mt-1 overflow-x-auto whitespace-pre-wrap">{runResult.stdout}</pre></> : null}{runResult.stderr ? <><p className="mt-4 text-xs text-neutral-300">{runResult.status === "completed" ? "STANDARD ERROR" : "DETAILS"}</p><pre className="mt-1 overflow-x-auto whitespace-pre-wrap text-red-200">{runResult.stderr}</pre></> : null}{!runResult.stdout && !runResult.stderr ? <p className="mt-3 text-neutral-300">The program did not produce console output.</p> : null}</section> : null}</section> : null}<label className="label" htmlFor="attempt">{language ? "What did you observe or change?" : "Your attempt"}</label><textarea required id="attempt" className="field min-h-40" value={response} onChange={event => setResponse(event.target.value)} placeholder={language ? "Describe your result, a bug you found, or your next step…" : "Show your reasoning or your first attempt…"}/><label className="label mt-4" htmlFor="assessment">How did it go?</label><select id="assessment" className="field" value={assessment} onChange={event => setAssessment(event.target.value)}><option value="needs_practice">I need more practice</option><option value="success">I completed it</option></select>{error ? <p role="alert" className="mt-4">{error}</p> : null}<button className="primary mt-5" disabled={saving}>{saving ? "Saving…" : "Save attempt"}</button></form>}</main>;
}
