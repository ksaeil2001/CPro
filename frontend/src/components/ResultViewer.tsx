"use client";

interface ResultViewerProps {
  originalUrl: string;
  translatedUrl: string;
  showOriginal: boolean;
}

export default function ResultViewer({
  originalUrl,
  translatedUrl,
  showOriginal,
}: ResultViewerProps) {
  return (
    <div className="flex flex-col items-center gap-4">
      <div className="relative w-full overflow-hidden rounded-xl border bg-white shadow-sm">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={showOriginal ? originalUrl : translatedUrl}
          alt={showOriginal ? "원본" : "번역본"}
          className="w-full object-contain"
        />
        <div className="absolute left-3 top-3 rounded-full bg-black/60 px-3 py-1 text-xs text-white">
          {showOriginal ? "원본" : "번역본"}
        </div>
      </div>
    </div>
  );
}
