"use client";

import React, { useState } from "react";
import { Terminal, Copy, Check, X, CheckCircle2, AlertTriangle, Clock } from "lucide-react";
import { ExecutionMeta } from "../types";

interface TerminalLogsModalProps {
  isOpen: boolean;
  onClose: () => void;
  execution?: ExecutionMeta | null;
}

export const TerminalLogsModal: React.FC<TerminalLogsModalProps> = ({
  isOpen,
  onClose,
  execution
}) => {
  const [activeTab, setActiveTab] = useState<"all" | "stdout" | "stderr">("all");
  const [copied, setCopied] = useState(false);

  if (!isOpen || !execution) return null;

  const fullLogs = [
    `=== CLI PROCESS EXECUTION LOGS ===`,
    `Command:   ${execution.command || "N/A"}`,
    `Exit Code: ${execution.exitCode} (${execution.exitCode === 0 ? "SUCCESS" : "ERROR / FAILED"})`,
    `Duration:  ${execution.duration}`,
    `Timed Out: ${execution.timedOut ? "YES" : "NO"}`,
    ``,
    `--- STDERR STREAM ---`,
    execution.stderr ? execution.stderr.trim() : "[No stderr emitted]",
    ``,
    `--- STDOUT STREAM ---`,
    execution.stdout ? execution.stdout.trim() : "[No stdout emitted]"
  ].join("\n");

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(fullLogs);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // fallback
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="w-full max-w-3xl rounded-2xl border border-slate-700 bg-slate-950 shadow-2xl overflow-hidden flex flex-col max-h-[85vh]">
        {/* Terminal Titlebar */}
        <div className="flex items-center justify-between px-4 py-3 bg-slate-900 border-b border-slate-800">
          <div className="flex items-center gap-2.5">
            {/* Window control dots */}
            <div className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-full bg-rose-500/80 inline-block" />
              <span className="w-3 h-3 rounded-full bg-amber-500/80 inline-block" />
              <span className="w-3 h-3 rounded-full bg-emerald-500/80 inline-block" />
            </div>
            <div className="flex items-center gap-2 ml-2">
              <Terminal className="h-4 w-4 text-sky-400" />
              <span className="text-xs font-mono font-semibold text-slate-200">
                CLI Subprocess Diagnostics
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleCopy}
              className="flex items-center gap-1 px-2.5 py-1 text-xs text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 rounded-md border border-slate-700 transition-colors"
            >
              {copied ? (
                <>
                  <Check className="h-3.5 w-3.5 text-emerald-400" />
                  <span className="text-emerald-400">Copied</span>
                </>
              ) : (
                <>
                  <Copy className="h-3.5 w-3.5" />
                  <span>Copy Logs</span>
                </>
              )}
            </button>
            <button
              onClick={onClose}
              className="p-1 rounded-md text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>

        {/* Execution Metadata Pill Bar */}
        <div className="flex flex-wrap items-center gap-2 px-4 py-2 bg-slate-900/60 border-b border-slate-800 text-xs font-mono">
          <span className="text-slate-400">Status:</span>
          {execution.exitCode === 0 ? (
            <span className="flex items-center gap-1 px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 font-semibold">
              <CheckCircle2 className="h-3 w-3" />
              EXIT 0 (SUCCESS)
            </span>
          ) : (
            <span className="flex items-center gap-1 px-2 py-0.5 rounded bg-rose-500/10 text-rose-400 border border-rose-500/30 font-semibold">
              <AlertTriangle className="h-3 w-3" />
              EXIT {execution.exitCode} (FAILED)
            </span>
          )}

          <span className="flex items-center gap-1 px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
            <Clock className="h-3 w-3 text-sky-400" />
            Duration: {execution.duration}
          </span>

          {execution.timedOut && (
            <span className="px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/30">
              TIMED OUT
            </span>
          )}
        </div>

        {/* Subprocess Command */}
        {execution.command && (
          <div className="px-4 py-2 bg-slate-950 border-b border-slate-800/80">
            <div className="text-[10px] uppercase font-mono tracking-wider text-slate-400 mb-1">
              Executed Command:
            </div>
            <div className="p-2 rounded bg-slate-900/90 font-mono text-xs text-sky-300 border border-slate-800 break-all select-all">
              $ {execution.command}
            </div>
          </div>
        )}

        {/* Stream Tabs */}
        <div className="flex items-center gap-2 px-4 pt-2 bg-slate-950 border-b border-slate-800 text-xs">
          <button
            onClick={() => setActiveTab("all")}
            className={`pb-2 px-1 font-medium transition-colors border-b-2 ${
              activeTab === "all"
                ? "border-sky-400 text-sky-400"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            Combined Output
          </button>
          <button
            onClick={() => setActiveTab("stdout")}
            className={`pb-2 px-1 font-medium transition-colors border-b-2 ${
              activeTab === "stdout"
                ? "border-sky-400 text-sky-400"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            stdout ({execution.stdout ? execution.stdout.length : 0} bytes)
          </button>
          <button
            onClick={() => setActiveTab("stderr")}
            className={`pb-2 px-1 font-medium transition-colors border-b-2 ${
              activeTab === "stderr"
                ? "border-sky-400 text-sky-400"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            stderr ({execution.stderr ? execution.stderr.length : 0} bytes)
          </button>
        </div>

        {/* Terminal Body */}
        <div className="flex-1 p-4 overflow-y-auto font-mono text-xs leading-relaxed bg-[#0a0e17] text-slate-300">
          {activeTab === "all" && (
            <div className="space-y-4">
              {execution.stderr && (
                <div>
                  <div className="text-amber-400 text-[11px] font-semibold mb-1">
                    [STDERR STREAM - Process Logs]
                  </div>
                  <pre className="text-amber-200/90 bg-amber-950/20 p-2.5 rounded border border-amber-900/30 whitespace-pre-wrap">
                    {execution.stderr}
                  </pre>
                </div>
              )}
              {execution.stdout && (
                <div>
                  <div className="text-sky-400 text-[11px] font-semibold mb-1">
                    [STDOUT STREAM - JSON / Data Output]
                  </div>
                  <pre className="text-sky-200 bg-sky-950/20 p-2.5 rounded border border-sky-900/30 whitespace-pre-wrap">
                    {execution.stdout}
                  </pre>
                </div>
              )}
              {!execution.stderr && !execution.stdout && (
                <div className="text-slate-400 italic">No console output recorded.</div>
              )}
            </div>
          )}

          {activeTab === "stdout" && (
            <pre className="text-sky-200 whitespace-pre-wrap">
              {execution.stdout || "[Empty stdout]"}
            </pre>
          )}

          {activeTab === "stderr" && (
            <pre className="text-amber-200/90 whitespace-pre-wrap">
              {execution.stderr || "[Empty stderr]"}
            </pre>
          )}
        </div>
      </div>
    </div>
  );
};
