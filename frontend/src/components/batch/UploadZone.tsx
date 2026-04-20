/**
 * UploadZone — drag-and-drop PDF upload area.
 *
 * Accepts PDF files via drag-and-drop or file picker.
 * Shows a visual indicator when a file is being dragged over.
 */

import { useState, useRef, useCallback } from "react";
import { Upload, FileText } from "lucide-react";
import { cn } from "@/lib/utils";

interface UploadZoneProps {
  onUpload: (file: File) => void;
  isLoading: boolean;
}

export function UploadZone({ onUpload, isLoading }: UploadZoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback(() => {
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);

      const file = e.dataTransfer.files[0];
      if (file && file.type === "application/pdf") {
        onUpload(file);
      }
    },
    [onUpload]
  );

  const handleFileSelect = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) {
        onUpload(file);
        // Reset the input so the same file can be selected again
        e.target.value = "";
      }
    },
    [onUpload]
  );

  return (
    <div
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={() => !isLoading && fileInputRef.current?.click()}
      className={cn(
        "relative flex flex-col items-center justify-center gap-3",
        "rounded-xl border-2 border-dashed p-12 cursor-pointer",
        "transition-colors",
        isDragging
          ? "border-primary bg-primary/5"
          : "border-border hover:border-primary/40 hover:bg-muted/30",
        isLoading && "opacity-50 cursor-not-allowed"
      )}
    >
      {isDragging ? (
        <FileText className="w-10 h-10 text-primary" />
      ) : (
        <Upload className="w-10 h-10 text-muted-foreground" />
      )}

      <div className="text-center">
        <p className="text-sm font-medium">
          {isDragging ? "Drop your PDF here" : "Upload a PDF invoice"}
        </p>
        <p className="mt-1 text-xs text-muted-foreground">
          Drag and drop, or click to select. Max 10MB.
        </p>
      </div>

      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf"
        onChange={handleFileSelect}
        className="hidden"
        aria-label="Upload PDF"
      />
    </div>
  );
}