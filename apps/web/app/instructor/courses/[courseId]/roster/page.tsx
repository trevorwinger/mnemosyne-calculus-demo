"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, RosterMember } from "../../../../../lib/api";

export default function Roster({ params }: { params: Promise<{ courseId: string }> }) {
  const [courseId, setCourseId] = useState(""); const [members, setMembers] = useState<RosterMember[]>([]); const [error, setError] = useState("");
  useEffect(() => { params.then(async ({ courseId: id }) => { setCourseId(id); try { setMembers(await api<RosterMember[]>(`/v1/courses/${id}/roster`)); } catch (cause) { setError(cause instanceof Error ? cause.message : "Could not load roster."); } }); }, [params]);
  async function remove(member: RosterMember) { if (!window.confirm(`Remove ${member.display_name} from this course? Their course access will end.`)) return; try { await api<void>(`/v1/courses/${courseId}/roster/${member.id}`, { method: "DELETE" }); setMembers(items => items.filter(item => item.id !== member.id)); } catch (cause) { setError(cause instanceof Error ? cause.message : "Could not remove this student."); } }
  return <main className="mx-auto max-w-3xl px-5 pb-16 pt-10"><Link href={`/instructor/courses/${courseId}`} className="text-sm font-semibold">← Course tools</Link><p className="mt-8 font-mono text-sm">INSTRUCTOR COURSE</p><h1 className="mt-2 text-4xl font-semibold">Course roster</h1><p className="mt-3 text-[var(--muted)]">Membership roles and enrollment dates only. Student chat transcripts are not shown here.</p>{error ? <p role="alert" className="bordered mt-6 p-4">{error}</p> : <div className="mt-8 space-y-3">{members.map(member => <article className="bordered flex items-center justify-between gap-4 p-4" key={member.id}><div><p className="font-semibold">{member.display_name}</p><p className="mt-1 text-sm text-[var(--muted)]">{member.email}</p></div><div className="text-right"><p className="font-mono text-xs text-[var(--muted)]">{member.role} · {new Date(member.joined_at).toLocaleDateString()}</p>{member.role === "student" ? <button className="mt-2 text-sm underline" onClick={() => remove(member)}>Remove</button> : null}</div></article>)}</div>}</main>;
}
