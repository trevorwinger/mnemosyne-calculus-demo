export type Course = { id: string; title: string; course_code: string | null; description: string; term: string | null; status: string; allow_without_sources: boolean; role: "instructor" | "student" | null };
export type TutoringPreferences = { guidance?: string; standard_tutor_model?: string; memory_enabled_default?: boolean; prerequisites?: string[]; learning_evidence_retention_days?: number | null } & Record<string, unknown>;
export type CourseSettings = Course & { learning_objectives: string[]; tutoring_preferences: TutoringPreferences };
export type Model = { name: string; digest: string | null; size: number | null; parameter_size: string | null; quantization: string | null; provider: string; approved: boolean; reason: string | null };
export type ModelProviderStatus = { reachable: boolean; approved_model_count: number; detail: string };
export type IngestionCapabilities = { max_upload_mb: number; extensions: string[] };
export type QueueStatus = { kind: string; status: string; count: number; oldest_created_at: string };
export type SourceCitation = { material_id: string; title: string; location: string };
export type ChatMessage = { id: string; role: "user" | "assistant" | "system"; content: string; created_at: string; citations: SourceCitation[] };
export type TutoringSession = { id: string; course_id: string; title: string; model_name: string; memory_enabled: boolean; material_scope: { material_ids?: string[] }; created_at: string; updated_at: string };
export type SessionDetail = TutoringSession & { messages: ChatMessage[] };
export type CourseSuggestion = { prompt: string; basis: string; material_title: string };
export type Concept = { id: string; name: string; slug: string };
export type ProgressItem = { concept: string; status: string; recent_evidence_count: number };
export type MemoryObservation = { id: string; concept: string; observed_behavior: string; result: string; independence: string; evidence_type: string; created_at: string; source_session_id: string | null };
export type InstructorConceptProgress = { concept: string; students_with_evidence: number; hint_assisted_successes: number; independent_successes: number };
export type InstructorStudentEvidence = { student_name: string; concept: string; observed_behavior: string; result: string; hint_count: number; independence: string; created_at: string };
export type RosterMember = { id: string; display_name: string; email: string; role: string; joined_at: string };
export type Exercise = { id: string; course_id: string; concept_id: string | null; title: string; prompt: string; exercise_type: string; automatic_check_configured: boolean; student_visible: boolean; created_at: string };
export type CodeLanguage = "java" | "python" | "javascript" | "c" | "cpp";
export type CodeRunResult = { status: "completed" | "compile_error" | "compile_timeout" | "runtime_error" | "timeout"; stdout: string; stderr: string; elapsed_ms: number };
const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const hasForm = typeof FormData !== "undefined" && options.body instanceof FormData;
  const response = await fetch(`${apiUrl}${path}`, { ...options, headers: { ...(hasForm ? {} : { "Content-Type": "application/json" }), ...options.headers } });
  if (!response.ok) { const error = await response.json().catch(() => null); throw new Error(error?.detail ?? "Something went wrong. Please retry."); }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export async function apiBlob(path: string): Promise<Blob> {
  const response = await fetch(`${apiUrl}${path}`);
  if (!response.ok) { const error = await response.json().catch(() => null); throw new Error(error?.detail ?? "Could not load the file."); }
  return response.blob();
}

export function apiUpload<T>(path: string, body: FormData, options: { signal?: AbortSignal; onProgress?: (progress: { loaded: number; total: number }) => void } = {}): Promise<T> {
  return new Promise((resolve, reject) => {
    const request = new XMLHttpRequest();
    const abort = () => request.abort();
    const cleanup = () => options.signal?.removeEventListener("abort", abort);
    request.open("POST", `${apiUrl}${path}`);
    request.responseType = "json";
    request.upload.onprogress = event => {
      if (event.lengthComputable) options.onProgress?.({ loaded: event.loaded, total: event.total });
    };
    request.onerror = () => { cleanup(); reject(new Error("Network error. Please retry.")); };
    request.onabort = () => { cleanup(); reject(new DOMException("The upload was canceled.", "AbortError")); };
    request.onload = () => {
      cleanup();
      const response = request.response as { detail?: string } | null;
      if (request.status < 200 || request.status >= 300) { reject(new Error(response?.detail ?? "Something went wrong. Please retry.")); return; }
      resolve(request.status === 204 ? undefined as T : request.response as T);
    };
    options.signal?.addEventListener("abort", abort, { once: true });
    if (options.signal?.aborted) { cleanup(); reject(new DOMException("The upload was canceled.", "AbortError")); return; }
    request.send(body);
  });
}
