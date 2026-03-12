import React, { useRef, useState } from "react";
import { Upload, FileText } from "lucide-react";

const PdfUploadZone = ({ onUploadPdf, disabled }) => {
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef(null);

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (!disabled) setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    if (disabled) return;

    const file = e.dataTransfer.files?.[0];
    if (file && isValidPdf(file)) {
      onUploadPdf(file);
    }
  };

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file && isValidPdf(file)) {
      onUploadPdf(file);
    }
    e.target.value = "";
  };

  const isValidPdf = (file) => {
    return file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf");
  };

  const handleClick = () => {
    if (!disabled) fileInputRef.current?.click();
  };

  return (
    <div
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={handleClick}
      className={`
        flex flex-col items-center justify-center gap-3 p-8 rounded-lg border-2 border-dashed
        cursor-pointer transition-colors
        ${disabled
          ? "border-gray-200 bg-gray-50 cursor-not-allowed opacity-50"
          : isDragging
            ? "border-blue-500 bg-blue-50"
            : "border-gray-300 bg-gray-100 hover:border-blue-400 hover:bg-blue-50"
        }
      `}
    >
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,application/pdf"
        onChange={handleFileChange}
        className="hidden"
      />
      <div className={`p-3 rounded-full ${isDragging ? "bg-blue-100" : "bg-gray-200"}`}>
        {isDragging ? (
          <FileText className="h-6 w-6 text-blue-600" />
        ) : (
          <Upload className="h-6 w-6 text-gray-500" />
        )}
      </div>
      <div className="text-center">
        <p className={`text-sm font-medium ${isDragging ? "text-blue-600" : "text-gray-700"}`}>
          Drop a PDF invoice here
        </p>
        <p className="text-xs text-gray-500 mt-1">or click to browse</p>
      </div>
    </div>
  );
};

export default PdfUploadZone;
