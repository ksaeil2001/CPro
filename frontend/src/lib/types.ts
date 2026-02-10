export interface JobStatus {
  job_id: string;
  status: "pending" | "processing" | "completed" | "failed";
  page_count: number;
  total_cost_krw: number;
  processing_time_ms: number | null;
  error_message: string | null;
  created_at: string | null;
}

export interface PipelineLog {
  stage: string;
  duration_ms: number;
  cost_krw: number;
  tokens_used: number | null;
  success: boolean;
  failure_type: string | null;
}
