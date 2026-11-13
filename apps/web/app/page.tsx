"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, Course, TutoringSession } from "../lib/api";

export default function CalculusChatEntry() {
  const router = useRouter();
  const [error, setError] = useState("");
  useEffect(() => {
    void (async () => {
      try {
        const [course] = await api<Course[]>("/v1/courses");
        if (!course) throw new Error("The Calculus III prototype has not finished seeding yet.");
        const sessions = await api<TutoringSession[]>(`/v1/courses/${course.id}/sessions`);
        const session = sessions[0] ?? await api<TutoringSession>(`/v1/courses/${course.id}/sessions`, { method: "POST", body: "{}" });
        router.replace(`/student/chat/${session.id}`);
      } catch (cause) { setError(cause instanceof Error ? cause.message : "Could not open the Calculus chat."); }
    })();
  }, [router]);
  return <main className="grid min-h-[70vh] place-items-center px-5 text-center"><div><p className="font-mono text-sm">MNEMOSYNE · CALCULUS III</p><h1 className="mt-3 text-3xl font-semibold">Opening your tutoring workspace…</h1><p role={error ? "alert" : undefined} className="mt-3 max-w-xl text-[var(--muted)]">{error || "Loading the course sections and your most recent chat."}</p></div></main>;
}
