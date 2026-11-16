"use client";

import React, { useState } from "react";
import { Copy, Check, Download, ChevronDown, ChevronRight, Code } from "lucide-react";

interface JsonViewerProps {
  data: Record<string, unknown> | null | undefined;
  title?: string;
}

export const JsonViewer: React.FC<JsonViewerProps> = ({
  data,
  title = "Extracted Structured JSON"
}) => {
  const [copied, setCopied] = useState(false);
  const [isExpanded, setIsExpanded] = useState(true);

  if (!data) return null;

  const jsonString = JSON.stringify(data, null, 2);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(jsonString);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // fallback
    }
  };

  const handleDownload = () => {
    const blob = new Blob([jsonString], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `crawl_extracted_${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="mt-3 rounded-xl border border-slate-800 bg-slate-950/90 overflow-hidden shadow-lg">
      {/* Header bar */}
      <div className="flex items-center justify-between px-3.5 py-2.5 bg-slate-900/80 border-b border-slate-800/80">
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="flex items-center gap-2 text-xs font-semibold text-slate-200 hover:text-white transition-colors"
        >
          {isExpanded ? (
            <ChevronDown className="h-4 w-4 text-sky-400" />
          ) : (
            <ChevronRight className="h-4 w-4 text-sky-400" />
          )}
          <Code className="h-4 w-4 text-sky-400" />
          <span>{title}</span>
          <span className="text-[11px] font-mono text-slate-400 font-normal">
            ({Object.keys(data).length} root keys, {(jsonString.length / 1024).toFixed(1)} KB)
          </span>
        </button>

        <div className="flex items-center gap-1.5">
          <button
            onClick={handleCopy}
            className="flex items-center gap-1 px-2.5 py-1 text-[11px] font-medium text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700/80 rounded-md border border-slate-700 transition-colors"
            title="Copy JSON to clipboard"
          >
            {copied ? (
              <>
                <Check className="h-3.5 w-3.5 text-emerald-400" />
                <span className="text-emerald-400">Copied!</span>
              </>
            ) : (
              <>
                <Copy className="h-3.5 w-3.5" />
                <span>Copy</span>
              </>
            )}
          </button>

          <button
            onClick={handleDownload}
            className="flex items-center gap-1 px-2.5 py-1 text-[11px] font-medium text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700/80 rounded-md border border-slate-700 transition-colors"
            title="Download JSON file"
          >
            <Download className="h-3.5 w-3.5" />
            <span>Download</span>
          </button>
        </div>
      </div>

      {/* Code body */}
      {isExpanded && (
        <div className="p-3.5 overflow-x-auto max-h-96 text-xs font-mono leading-relaxed bg-[#0b0f19] text-sky-200 selection:bg-sky-500/30">
          <pre>{jsonString}</pre>
        </div>
      )}
    </div>
  );
};
