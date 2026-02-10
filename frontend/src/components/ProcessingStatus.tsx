"use client";

interface ProcessingStatusProps {
  status: string;
  currentStage?: string | null;
  warnings?: string[];
}

const PIPELINE_STAGES = [
  { key: "pending", label: "대기 중" },
  { key: "preprocessing", label: "이미지 전처리" },
  { key: "detection", label: "텍스트 감지" },
  { key: "ocr", label: "문자 인식 (OCR)" },
  { key: "translation", label: "번역" },
  { key: "inpainting", label: "텍스트 제거" },
  { key: "typesetting", label: "식자" },
  { key: "postprocessing", label: "후처리" },
];

// Map backend stage names to frontend stage keys
const STAGE_MAP: Record<string, string> = {
  preprocessor: "preprocessing",
  detector: "detection",
  balloon_parser: "detection",
  ocr_engine: "ocr",
  translation_prep: "translation",
  translator: "translation",
  translation_mapper: "translation",
  inpainter: "inpainting",
  typesetter: "typesetting",
  postprocessor: "postprocessing",
};

export default function ProcessingStatus({
  status,
  currentStage,
  warnings,
}: ProcessingStatusProps) {
  const isProcessing = status === "processing" || status === "pending";
  const isCompleted = status === "completed";

  // Determine the current frontend stage index based on backend stage name
  const mappedStage = currentStage ? STAGE_MAP[currentStage] : null;
  const currentIndex = mappedStage
    ? PIPELINE_STAGES.findIndex((s) => s.key === mappedStage)
    : -1;

  return (
    <div className="w-full max-w-md">
      <h2 className="mb-6 text-center text-xl font-semibold">
        {isProcessing ? "번역 처리 중..." : "처리 완료"}
      </h2>

      <div className="space-y-3">
        {PIPELINE_STAGES.map((stage, index) => {
          const isActive = isProcessing && index === currentIndex;
          const isDone =
            isCompleted || (isProcessing && currentIndex > 0 && index < currentIndex);

          return (
            <div key={stage.key} className="flex items-center gap-3">
              <div
                className={`flex h-8 w-8 items-center justify-center rounded-full text-sm font-medium ${
                  isActive
                    ? "bg-blue-100 text-blue-600"
                    : isDone
                      ? "bg-green-100 text-green-600"
                      : "bg-gray-100 text-gray-400"
                }`}
              >
                {isDone ? "✓" : index + 1}
              </div>
              <span
                className={`text-sm ${
                  isActive
                    ? "font-medium text-gray-900"
                    : isDone
                      ? "text-gray-700"
                      : "text-gray-500"
                }`}
              >
                {stage.label}
              </span>
              {isActive && (
                <div className="ml-auto h-4 w-4 animate-spin rounded-full border-2 border-gray-300 border-t-blue-600" />
              )}
            </div>
          );
        })}
      </div>

      {isProcessing && (
        <p className="mt-6 text-center text-sm text-gray-500">
          잠시만 기다려주세요. 페이지 복잡도에 따라 시간이 다를 수 있습니다.
        </p>
      )}

      {warnings && warnings.length > 0 && (
        <div className="mt-4 space-y-2">
          {warnings.map((warning, idx) => (
            <div
              key={idx}
              className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-2 text-sm text-amber-800"
            >
              {warning}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
