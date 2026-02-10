"use client";

import { use, useState } from "react";
import { useJobPolling } from "@/hooks/useJobPolling";
import { getJobResultUrl, getJobOriginalUrl } from "@/lib/api";
import ProcessingStatus from "@/components/ProcessingStatus";
import ResultViewer from "@/components/ResultViewer";

export default function ResultPage({
  params,
}: {
  params: Promise<{ jobId: string }>;
}) {
  const { jobId } = use(params);
  const { status, error } = useJobPolling(jobId);
  const [showOriginal, setShowOriginal] = useState(false);

  if (error) {
    return (
      <div className="flex flex-col items-center gap-4">
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-red-700">
          오류: {error}
        </div>
        <a href="/" className="text-blue-600 hover:underline">
          다시 시도
        </a>
      </div>
    );
  }

  if (!status) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-gray-300 border-t-blue-600" />
      </div>
    );
  }

  if (status.status === "failed") {
    return (
      <div className="flex flex-col items-center gap-4">
        <div className="rounded-lg border border-red-200 bg-red-50 px-6 py-4 text-red-700">
          <h2 className="font-semibold">번역 실패</h2>
          <p className="mt-1 text-sm">{status.error_message || "알 수 없는 오류"}</p>
        </div>
        <a href="/" className="text-blue-600 hover:underline">
          다시 시도
        </a>
      </div>
    );
  }

  if (status.status === "completed") {
    return (
      <div className="flex flex-col gap-6">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold">번역 결과</h2>
          <div className="flex items-center gap-4">
            <button
              onClick={() => setShowOriginal(!showOriginal)}
              className="rounded-lg border px-3 py-1.5 text-sm hover:bg-gray-50"
            >
              {showOriginal ? "번역본 보기" : "원본 보기"}
            </button>
            <a
              href={getJobResultUrl(jobId)}
              download
              className="rounded-lg bg-blue-600 px-3 py-1.5 text-sm text-white hover:bg-blue-700"
            >
              다운로드
            </a>
          </div>
        </div>

        <ResultViewer
          originalUrl={getJobOriginalUrl(jobId)}
          translatedUrl={getJobResultUrl(jobId)}
          showOriginal={showOriginal}
        />

        <div className="rounded-lg border bg-gray-50 px-4 py-3 text-sm text-gray-600">
          <div className="flex gap-6">
            <span>비용: {status.total_cost_krw.toFixed(2)}원</span>
            {status.processing_time_ms && (
              <span>처리 시간: {(status.processing_time_ms / 1000).toFixed(1)}초</span>
            )}
          </div>
        </div>

        <a href="/" className="text-blue-600 hover:underline">
          ← 새로운 번역
        </a>
      </div>
    );
  }

  // Processing state
  return (
    <div className="flex flex-col items-center gap-6 py-10">
      <ProcessingStatus status={status.status} />
      <p className="text-sm text-gray-500">작업 ID: {jobId}</p>
    </div>
  );
}
