import type { JobStatus } from "./types";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export async function uploadImage(
  file: File
): Promise<{ job_id: string }> {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_BASE}/translate`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`업로드 실패: ${detail}`);
  }

  return res.json();
}

export async function getJobStatus(jobId: string): Promise<JobStatus> {
  const res = await fetch(`${API_BASE}/jobs/${jobId}`);
  if (!res.ok) {
    throw new Error(`상태 조회 실패: ${res.statusText}`);
  }
  return res.json();
}

export function getJobResultUrl(jobId: string): string {
  return `${API_BASE}/jobs/${jobId}/result`;
}

export function getJobOriginalUrl(jobId: string): string {
  return `${API_BASE}/jobs/${jobId}/original`;
}
