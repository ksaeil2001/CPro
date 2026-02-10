"use client";

import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";

interface ImageUploaderProps {
  onUpload: (file: File) => void;
  disabled?: boolean;
}

export default function ImageUploader({ onUpload, disabled }: ImageUploaderProps) {
  const [preview, setPreview] = useState<string | null>(null);

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      if (acceptedFiles.length === 0) return;
      const file = acceptedFiles[0];
      setPreview(URL.createObjectURL(file));
      onUpload(file);
    },
    [onUpload]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "image/png": [".png"],
      "image/jpeg": [".jpg", ".jpeg"],
      "image/webp": [".webp"],
    },
    maxFiles: 1,
    disabled,
  });

  return (
    <div className="w-full max-w-xl">
      <div
        {...getRootProps()}
        className={`flex min-h-[300px] cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed p-8 transition-colors ${
          isDragActive
            ? "border-blue-500 bg-blue-50"
            : disabled
              ? "cursor-not-allowed border-gray-200 bg-gray-50"
              : "border-gray-300 hover:border-blue-400 hover:bg-gray-50"
        }`}
      >
        <input {...getInputProps()} />

        {preview ? (
          <img
            src={preview}
            alt="Preview"
            className="max-h-[400px] rounded-lg object-contain"
          />
        ) : (
          <div className="text-center">
            <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-gray-100">
              <svg
                className="h-8 w-8 text-gray-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
                />
              </svg>
            </div>
            <p className="text-lg font-medium text-gray-700">
              {isDragActive ? "여기에 놓으세요" : "이미지를 드래그하거나 클릭하세요"}
            </p>
            <p className="mt-1 text-sm text-gray-500">
              PNG, JPG, WebP 지원
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
