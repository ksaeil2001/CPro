"use client";

import { useEffect, useState } from "react";
import { getJobStatus } from "@/lib/api";
import type { JobStatus } from "@/lib/types";

export function useJobPolling(jobId: string, intervalMs = 2000) {
  const [status, setStatus] = useState<JobStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let timer: ReturnType<typeof setInterval> | null = null;

    const poll = async () => {
      try {
        const s = await getJobStatus(jobId);
        setStatus(s);
        if (s.status === "completed" || s.status === "failed") {
          if (timer) clearInterval(timer);
        }
      } catch (e) {
        setError(e instanceof Error ? e.message : "폴링 실패");
        if (timer) clearInterval(timer);
      }
    };

    // Immediate first call
    poll();
    timer = setInterval(poll, intervalMs);

    return () => {
      if (timer) clearInterval(timer);
    };
  }, [jobId, intervalMs]);

  return { status, error };
}
