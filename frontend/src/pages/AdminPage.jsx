import React, { useState, useRef, useCallback } from "react";
import {
  Upload,
  FileSpreadsheet,
  ArrowLeft,
  CheckCircle,
  AlertCircle,
  Package,
} from "lucide-react";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8080";

const AdminPage = () => {
  const [file, setFile] = useState(null);
  const [dragging, setDragging] = useState(false);
  const [status, setStatus] = useState("idle"); // idle | uploading | success | error
  const [result, setResult] = useState(null);
  const [errorMsg, setErrorMsg] = useState("");
  const inputRef = useRef(null);

  const handleFile = (f) => {
    if (f && f.name.endsWith(".csv")) {
      setFile(f);
      setStatus("idle");
      setResult(null);
      setErrorMsg("");
    }
  };

  const onDrop = useCallback((e) => {
    e.preventDefault();
    setDragging(false);
    const dropped = e.dataTransfer.files[0];
    handleFile(dropped);
  }, []);

  const onDragOver = useCallback((e) => {
    e.preventDefault();
    setDragging(true);
  }, []);

  const onDragLeave = useCallback(() => {
    setDragging(false);
  }, []);

  const onFileChange = (e) => {
    handleFile(e.target.files[0]);
  };

  const handleUpload = async () => {
    if (!file) return;

    setStatus("uploading");
    setResult(null);
    setErrorMsg("");

    try {
      const formData = new FormData();
      formData.append("file", file);

      const res = await fetch(`${API_BASE_URL}/api/update-csv`, {
        method: "POST",
        body: formData,
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.error || `Server error ${res.status}`);
      }

      setStatus("success");
      setResult(data);
    } catch (err) {
      setStatus("error");
      setErrorMsg(err.message);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-2xl mx-auto px-4 sm:px-6">
          <div className="flex items-center justify-between h-14">
            <div className="flex items-center gap-2.5">
              <div className="flex items-center justify-center w-8 h-8 bg-blue-600 rounded-lg">
                <Package className="h-4 w-4 text-white" />
              </div>
              <div>
                <h1 className="text-base font-bold text-gray-900">
                  HTS Oracle
                </h1>
                <p className="text-xs text-gray-500">Admin</p>
              </div>
            </div>
            <a
              href="/"
              className="flex items-center gap-1.5 text-sm text-blue-600 hover:text-blue-800 font-medium"
            >
              <ArrowLeft className="h-4 w-4" />
              Back to Chat
            </a>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-2xl mx-auto px-4 sm:px-6 py-10">
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 sm:p-8">
          <div className="flex items-center gap-3 mb-2">
            <FileSpreadsheet className="h-6 w-6 text-blue-600" />
            <h2 className="text-lg font-semibold text-gray-900">
              Update HTS Data
            </h2>
          </div>
          <p className="text-sm text-gray-500 mb-6">
            Upload a new HTS codes CSV file to update the classification
            database. This will re-embed all entries and update the Pinecone
            index.
          </p>

          {/* Drop zone */}
          <div
            onDrop={onDrop}
            onDragOver={onDragOver}
            onDragLeave={onDragLeave}
            onClick={() => inputRef.current?.click()}
            className={`
              border-2 border-dashed rounded-lg p-8 text-center cursor-pointer
              transition-colors
              ${
                dragging
                  ? "border-blue-400 bg-blue-50"
                  : "border-gray-300 hover:border-gray-400 bg-gray-50"
              }
            `}
          >
            <input
              ref={inputRef}
              type="file"
              accept=".csv"
              onChange={onFileChange}
              className="hidden"
            />
            <Upload className="h-8 w-8 text-gray-400 mx-auto mb-3" />
            {file ? (
              <div>
                <p className="text-sm font-medium text-gray-700">
                  {file.name}
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  {(file.size / 1024).toFixed(1)} KB — Click or drop to replace
                </p>
              </div>
            ) : (
              <div>
                <p className="text-sm font-medium text-gray-700">
                  Drop your CSV file here, or click to browse
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  Accepts .csv files only
                </p>
              </div>
            )}
          </div>

          {/* Upload button */}
          <button
            onClick={handleUpload}
            disabled={!file || status === "uploading"}
            className="mt-5 w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-white text-sm font-medium rounded-lg px-4 py-2.5 transition-colors"
          >
            <Upload className="h-4 w-4" />
            Upload &amp; Update
          </button>

          <p className="text-xs text-gray-400 text-center mt-3">
            This operation may take several minutes for large files.
          </p>

          {/* Status banners */}
          {status === "uploading" && (
            <div className="mt-5 flex items-center gap-3 bg-blue-50 border border-blue-200 text-blue-700 text-sm rounded-lg px-4 py-3">
              <svg
                className="animate-spin h-4 w-4 text-blue-600 shrink-0"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                />
              </svg>
              Updating index… This may take a while.
            </div>
          )}

          {status === "success" && result && (
            <div className="mt-5 flex items-center gap-3 bg-green-50 border border-green-200 text-green-700 text-sm rounded-lg px-4 py-3">
              <CheckCircle className="h-4 w-4 shrink-0" />
              Update complete. {result.records_processed?.toLocaleString()}{" "}
              records processed.
            </div>
          )}

          {status === "error" && (
            <div className="mt-5 flex items-center gap-3 bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg px-4 py-3">
              <AlertCircle className="h-4 w-4 shrink-0" />
              {errorMsg}
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default AdminPage;
