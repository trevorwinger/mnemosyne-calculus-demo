"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, Exercise } from "../../../../../lib/api";

export default function PracticeList({ params }: { params: Promise<{ courseId: string }> }) {
  const [courseId, setCourseId] = useState(""); const [exercises, setExercises] = useState<Exercise[]>([]); const [error, setError] = useState("");
  useEffect(() => { params.then(async ({ courseId: id }) => { setCourseId(id); try { setExercises(await api<Exercise[]>(`/v1/courses/${id}/exercises`)); } catch (cause) { setError(cause instanceof Error ? cause.message : "Could not load practice activities."); } }); }, [params]);
  return <main className="mx-auto max-w-4xl px-5 pb-16 pt-10"><Link href={`/student/courses/${courseId}`} className="text-sm font-semibold">← Course home</Link><p className="mt-8 font-mono text-sm">PRACTICE</p><h1 className="mt-2 text-4xl font-semibold">Course practice activities</h1>{error ? <p role="alert" className="mt-6">{error}</p> : exercises.length ? <div className="mt-8 space-y-4">{exercises.map(exercise => <article className="bordered p-5" key={exercise.id}><p className="font-semibold">{exercise.title}</p><p className="mt-2 line-clamp-3 whitespace-pre-wrap text-sm text-[var(--muted)]">{exercise.prompt}</p><Link className="secondary mt-4 inline-block" href={`/student/exercises/${exercise.id}`}>Start activity</Link></article>)}</div> : <p className="bordered mt-8 p-5 text-[var(--muted)]">Your instructor has not released a practice activity yet. You can still start a tutoring session from the course home.</p>}</main>;
}
