"use client";

import { FormEvent, KeyboardEvent, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api, ChatMessage, Model, ModelProviderStatus, SessionDetail, TutoringSession } from "../../../../lib/api";
import { MessageContent } from "../../../../components/message-content";

type Material = { id: string; title: string; material_type: string; module: string | null; preview: string };

export default function CalculusChat({ params }: { params: Promise<{ sessionId: string }> }) {
  const router = useRouter();
  const requestController = useRef<AbortController | null>(null);
  const [id, setId] = useState(""); const [session, setSession] = useState<SessionDetail | null>(null);
  const [models, setModels] = useState<Model[]>([]); const [provider, setProvider] = useState<ModelProviderStatus | null>(null);
  const [materials, setMaterials] = useState<Material[]>([]); const [scope, setScope] = useState<string[] | null>(null); const [history, setHistory] = useState<TutoringSession[]>([]);
  const [module, setModule] = useState(""); const [text, setText] = useState(""); const [sending, setSending] = useState(false); const [opening, setOpening] = useState(false); const [error, setError] = useState("");

  useEffect(() => { void params.then(value => setId(value.sessionId)); }, [params]);
  useEffect(() => {
    if (!id) return;
    void api<SessionDetail>(`/v1/sessions/${id}`).then(async detail => {
      setSession(detail); setScope(detail.material_scope?.material_ids ?? null);
      const [availableModels, sources, sessions, status] = await Promise.all([api<Model[]>("/v1/models"), api<Material[]>(`/v1/courses/${detail.course_id}/released-materials`), api<TutoringSession[]>(`/v1/courses/${detail.course_id}/sessions`), api<ModelProviderStatus>("/v1/models/status")]);
      setModels(availableModels.filter(model => model.approved)); setMaterials(sources); setHistory(sessions); setProvider(status);
    }).catch(cause => setError(cause instanceof Error ? cause.message : "Could not open the Calculus chat."));
  }, [id]);

  async function send(event?: FormEvent) {
    event?.preventDefault(); if (!session || !text.trim() || sending) return;
    const content = text; const controller = new AbortController(); requestController.current = controller;
    setText(""); setError(""); setSending(true);
    const pending: ChatMessage = { id: "pending", role: "user", content, created_at: new Date().toISOString(), citations: [] };
    setSession(current => current ? { ...current, messages: [...current.messages, pending] } : current);
    try {
      const reply = await api<ChatMessage[]>(`/v1/sessions/${session.id}/messages`, { method: "POST", signal: controller.signal, body: JSON.stringify({ content, model_name: session.model_name, material_ids: scope }) });
      setSession(current => current ? { ...current, messages: [...current.messages.filter(message => message.id !== "pending"), ...reply] } : current);
    } catch (cause) {
      setText(content); setSession(current => current ? { ...current, messages: current.messages.filter(message => message.id !== "pending") } : current);
      setError(cause instanceof Error && cause.name === "AbortError" ? "Reply stopped. Your draft was restored." : cause instanceof Error ? cause.message : "Request failed; draft restored.");
    } finally { requestController.current = null; setSending(false); }
  }

  function selectModule(value: string) {
    setModule(value);
    setScope(value ? materials.filter(material => material.module === value).map(material => material.id) : null);
  }
  async function newChat() {
    if (!session) return;
    setOpening(true);
    try {
      const next = await api<TutoringSession>(`/v1/courses/${session.course_id}/sessions`, { method: "POST", body: JSON.stringify({ model_name: session.model_name, material_ids: scope }) });
      router.push(`/student/chat/${next.id}`);
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Could not start a new chat."); setOpening(false); }
  }
  function key(event: KeyboardEvent<HTMLTextAreaElement>) { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); void send(); } }

  if (!session) return <main className="grid min-h-[70vh] place-items-center">{error || "Opening Calculus chat…"}</main>;
  const modules = [...new Set(materials.flatMap(material => material.module ? [material.module] : []))].sort();
  const providerLabel = provider?.reachable ? `${provider.approved_model_count} local chat model${provider.approved_model_count === 1 ? "" : "s"} available` : provider?.detail ?? "Checking local models…";

  return <main className="mx-auto min-h-[calc(100vh-76px)] max-w-4xl border-t border-[var(--line)] px-5 pb-8"><header className="border-b border-[var(--line)] py-5"><div className="flex flex-wrap items-start justify-between gap-4"><div><p className="font-mono text-xs text-[var(--muted)]">ALEX · MATH 242 · APEX CALCULUS</p><h1 className="mt-1 text-2xl font-semibold">Calculus III tutoring</h1><p className="mt-2 text-sm text-[var(--muted)]">Choose a textbook topic or ask about any Calc III concept.</p></div><button type="button" className="secondary text-sm" onClick={newChat} disabled={opening}>{opening ? "Opening…" : "+ New chat"}</button></div><div className="mt-4 flex flex-wrap items-center gap-3"><label className="text-xs text-[var(--muted)]" htmlFor="chat-history">Chat history</label><select id="chat-history" className="bordered bg-[var(--canvas)] px-2 py-1 text-sm" value={session.id} onChange={event => router.push(`/student/chat/${event.target.value}`)}>{history.map(item => <option value={item.id} key={item.id}>{item.title || "New chat"}</option>)}</select></div></header><section className="border-b border-[var(--line)] py-4"><div className="flex flex-wrap items-center gap-3"><label className="text-sm font-semibold" htmlFor="topic">Textbook focus</label><select id="topic" className="bordered bg-[var(--canvas)] px-2 py-1 text-sm" value={module} onChange={event => selectModule(event.target.value)}><option value="">All imported sections</option>{modules.map(item => <option value={item} key={item}>{item}</option>)}</select><span className="text-xs text-[var(--muted)]">{scope === null ? `${materials.length} sections` : `${scope.length} sections`} in scope</span><button type="button" className="text-sm underline" onClick={() => setText(`Help me practice the topics from ${module || "this Calculus III course"} with one new example at a time: `)}>Practice this chapter</button></div></section><div className="flex min-h-[48vh] flex-col gap-6 py-7">{session.messages.length ? session.messages.map(message => <article className={message.role === "user" ? "ml-auto max-w-[85%] rounded-2xl bg-[var(--surface)] p-4" : "max-w-[85%]"} key={message.id}><p className="mb-2 font-mono text-xs text-[var(--muted)]">{message.role === "user" ? "ALEX" : message.role === "system" ? "SESSION" : "MNEMOSYNE"}</p><MessageContent content={message.content}/>{message.citations.length ? <p className="mt-3 text-xs text-[var(--muted)]">Sources: {message.citations.map((citation, index) => <span key={`${citation.material_id}-${citation.location}`}><Link className="underline" href={`/student/materials/${citation.material_id}?location=${encodeURIComponent(citation.location)}`}>{citation.title} · {citation.location}</Link>{index < message.citations.length - 1 ? " · " : ""}</span>)}</p> : null}</article>) : <div className="bordered p-5"><h2 className="text-xl font-semibold">What are you working on?</h2><p className="mt-2 text-[var(--muted)]">Try “Help me practice the topics from this chapter” or ask about vectors, multivariable derivatives, or multiple integration.</p></div>}</div>{sending ? <div className="flex items-center gap-3 border-t border-[var(--line)] py-3 text-sm text-[var(--muted)]"><span className="flex gap-1" aria-hidden="true"><i className="h-2 w-2 animate-bounce rounded-full bg-black"/><i className="h-2 w-2 animate-bounce rounded-full bg-black [animation-delay:-.15s]"/><i className="h-2 w-2 animate-bounce rounded-full bg-black [animation-delay:-.3s]"/></span>Thinking… <button type="button" className="underline" onClick={() => requestController.current?.abort()}>Stop reply</button></div> : null}<form className="border-t border-[var(--line)] pt-4" onSubmit={send}><div className="mb-3 flex flex-wrap items-center gap-3 text-xs"><select aria-label="Tutor model" className="bordered bg-[var(--canvas)] px-2 py-1" value={session.model_name} onChange={event => setSession({ ...session, model_name: event.target.value })}>{models.map(model => <option key={model.name} value={model.name}>{model.name}{model.parameter_size ? ` · ${model.parameter_size}` : ""}</option>)}</select><span className="text-[var(--muted)]">{providerLabel}</span></div><textarea className="field min-h-28" value={text} onChange={event => setText(event.target.value)} onKeyDown={key} aria-label="Message Mnemosyne" placeholder="Ask a Calculus III question or share an attempt…" disabled={sending}/>{error ? <p role="alert" className="mt-2 text-sm">{error}</p> : null}<div className="mt-3 flex justify-between"><p className="text-xs text-[var(--muted)]">Enter to send · Shift+Enter for a new line</p><button className="primary" disabled={!text.trim() || sending}>{sending ? "Thinking…" : "Send"}</button></div></form></main>;
}
