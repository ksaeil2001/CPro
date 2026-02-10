"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import ImageUploader from "@/components/ImageUploader";
import { uploadImage } from "@/lib/api";

export default function Home() {
  const router = useRouter();
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleUpload = async (file: File) => {
    setUploading(true);
    setError(null);
    try {
      const { job_id } = await uploadImage(file);
      router.push(`/result/${job_id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "업로드에 실패했습니다");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="flex flex-col items-center gap-8">
      <div className="text-center">
        <h1 className="text-3xl font-bold">만화 번역</h1>
        <p className="mt-2 text-gray-600">
          만화 이미지를 업로드하면 자동으로 한국어로 번역합니다
        </p>
      </div>

      <ImageUploader onUpload={handleUpload} disabled={uploading} />

      {uploading && (
        <div className="flex items-center gap-2 text-gray-600">
          <div className="h-5 w-5 animate-spin rounded-full border-2 border-gray-300 border-t-blue-600" />
          <span>업로드 중...</span>
        </div>
      )}

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-red-700">
          {error}
        </div>
      )}
    </div>
  );
}
