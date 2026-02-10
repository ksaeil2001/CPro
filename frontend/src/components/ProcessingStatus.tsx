"use client";

interface ProcessingStatusProps {
  status: string;
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

export default function ProcessingStatus({ status }: ProcessingStatusProps) {
  const isProcessing = status === "processing" || status === "pending";

  return (
    <div className="w-full max-w-md">
      <h2 className="mb-6 text-center text-xl font-semibold">
        {isProcessing ? "번역 처리 중..." : "처리 완료"}
      </h2>

      <div className="space-y-3">
        {PIPELINE_STAGES.map((stage, index) => (
          <div key={stage.key} className="flex items-center gap-3">
            <div
              className={`flex h-8 w-8 items-center justify-center rounded-full text-sm font-medium ${
                isProcessing && index === 0
                  ? "bg-blue-100 text-blue-600"
                  : "bg-gray-100 text-gray-400"
              }`}
            >
              {index + 1}
            </div>
            <span
              className={`text-sm ${
                isProcessing && index === 0
                  ? "font-medium text-gray-900"
                  : "text-gray-500"
              }`}
            >
              {stage.label}
            </span>
            {isProcessing && index === 0 && (
              <div className="ml-auto h-4 w-4 animate-spin rounded-full border-2 border-gray-300 border-t-blue-600" />
            )}
          </div>
        ))}
      </div>

      {isProcessing && (
        <p className="mt-6 text-center text-sm text-gray-500">
          잠시만 기다려주세요. 페이지 복잡도에 따라 시간이 다를 수 있습니다.
        </p>
      )}
    </div>
  );
}
