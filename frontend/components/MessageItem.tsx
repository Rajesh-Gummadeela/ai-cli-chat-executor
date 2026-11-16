"use client";

import React, { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { User, Bot, Terminal, CheckCircle2, AlertTriangle, Clock, Layers, Globe, ExternalLink, ChevronDown, ChevronUp } from "lucide-react";
import { ChatMessage, ExecutionMeta } from "../types";
import { StatusStepper } from "./StatusStepper";
import { JsonViewer } from "./JsonViewer";
import { TerminalLogsModal } from "./TerminalLogsModal";

interface MessageItemProps {
  message: ChatMessage;
}

export const MessageItem: React.FC<MessageItemProps> = ({ message }) => {
  const isUser = message.role === "user";
  const [showLogsModal, setShowLogsModal] = useState(false);
  const [showPagesSection, setShowPagesSection] = useState(false);

  const data = message.data;
  const execution: ExecutionMeta | null | undefined = data?.execution;
  const pages = data?.pages || [];

  return (
    <div className={`py-4 px-4 sm:px-6 flex gap-3.5 transition-colors ${
      isUser ? "bg-slate-900/30" : "bg-slate-900/70 border-y border-slate-800/40"
    }`}>
      {/* Avatar Icon */}
      <div className="shrink-0 pt-0.5">
        {isUser ? (
          <div className="h-8 w-8 rounded-lg bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-300">
            <User className="h-4 w-4" />
          </div>
        ) : (
          <div className="h-8 w-8 rounded-lg bg-gradient-to-tr from-sky-500 to-indigo-600 flex items-center justify-center text-white shadow-md shadow-sky-500/10">
            <Bot className="h-4 w-4" />
          </div>
        )}
      </div>

      {/* Message Content Container */}
      <div className="flex-1 min-w-0 space-y-2.5">
        {/* Author Label & Timestamp */}
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-slate-200">
            {isUser ? "You" : "CLI Execution Agent"}
          </span>
          <span className="text-[11px] text-slate-400">
            {message.timestamp}
          </span>
          {!isUser && data?.ai_provider && (
            <span className="text-[10px] px-1.5 py-0.2 rounded bg-sky-500/10 text-sky-400 border border-sky-500/20 font-mono">
              {data.ai_provider.split("(")[0].trim()}
            </span>
          )}
        </div>

        {/* Live Steps Stepper */}
        {message.steps && message.steps.length > 0 && (
          <StatusStepper steps={message.steps} />
        )}

        {/* Main Content (Markdown for assistant, plain text for user) */}
        {isUser ? (
          <p className="text-sm text-slate-100 whitespace-pre-wrap leading-relaxed">
            {message.content}
          </p>
        ) : (
          <div className="prose-custom max-w-none">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {message.content}
            </ReactMarkdown>
          </div>
        )}

        {/* Execution Diagnostics Bar (when real CLI process was invoked) */}
        {execution && (
          <div className="mt-3 p-3 rounded-xl bg-slate-950/80 border border-slate-800/90 flex flex-wrap items-center justify-between gap-3 text-xs">
            <div className="flex flex-wrap items-center gap-2 font-mono">
              <span className="text-slate-400 font-sans font-medium text-[11px]">Execution:</span>

              {/* Exit Code */}
              {execution.exitCode === 0 ? (
                <span className="flex items-center gap-1 px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 font-semibold text-[11px]">
                  <CheckCircle2 className="h-3 w-3" />
                  Exit Code: 0 (SUCCESS)
                </span>
              ) : (
                <span className="flex items-center gap-1 px-2 py-0.5 rounded bg-rose-500/10 text-rose-400 border border-rose-500/30 font-semibold text-[11px]">
                  <AlertTriangle className="h-3 w-3" />
                  Exit Code: {execution.exitCode}
                </span>
              )}

              {/* Duration */}
              <span className="flex items-center gap-1 px-2 py-0.5 rounded bg-slate-900 text-slate-300 border border-slate-800 text-[11px]">
                <Clock className="h-3 w-3 text-sky-400" />
                Duration: {execution.duration}
              </span>

              {/* Pages Crawled */}
              {pages.length > 0 && (
                <span className="flex items-center gap-1 px-2 py-0.5 rounded bg-slate-900 text-slate-300 border border-slate-800 text-[11px]">
                  <Layers className="h-3 w-3 text-indigo-400" />
                  {pages.length} Page{pages.length > 1 ? "s" : ""}
                </span>
              )}
            </div>

            {/* Inspect Terminal Logs Button */}
            <div className="flex items-center gap-2">
              <button
                onClick={() => setShowLogsModal(true)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-sky-500/10 hover:bg-sky-500/20 text-sky-400 hover:text-sky-300 border border-sky-500/30 text-xs font-medium transition-colors"
              >
                <Terminal className="h-3.5 w-3.5" />
                <span>View CLI Logs & Subprocess Output</span>
              </button>
            </div>
          </div>
        )}

        {/* Crawled Pages Section (Collapsible) */}
        {pages.length > 0 && (
          <div className="mt-3 rounded-xl border border-slate-800/80 bg-slate-950/60 overflow-hidden">
            <button
              onClick={() => setShowPagesSection(!showPagesSection)}
              className="w-full flex items-center justify-between px-3.5 py-2.5 text-xs font-semibold text-slate-300 hover:text-white bg-slate-900/60 transition-colors"
            >
              <div className="flex items-center gap-2">
                <Globe className="h-4 w-4 text-sky-400" />
                <span>Crawled Pages Content ({pages.length})</span>
              </div>
              {showPagesSection ? (
                <ChevronUp className="h-4 w-4 text-slate-400" />
              ) : (
                <ChevronDown className="h-4 w-4 text-slate-400" />
              )}
            </button>

            {showPagesSection && (
              <div className="p-3.5 space-y-3 divide-y divide-slate-800">
                {pages.map((p, idx) => (
                  <div key={idx} className={idx > 0 ? "pt-3" : ""}>
                    <div className="flex items-start justify-between gap-2">
                      <h4 className="text-xs font-semibold text-white flex items-center gap-1.5">
                        <span className="text-sky-400">#{idx + 1}</span> {p.title || "Untitled"}
                      </h4>
                      <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-slate-800 text-slate-300">
                        {p.statusCode} OK ({p.contentLength} chars)
                      </span>
                    </div>

                    <a
                      href={p.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-[11px] text-sky-400 hover:underline flex items-center gap-1 mt-0.5"
                    >
                      {p.url}
                      <ExternalLink className="h-2.5 w-2.5" />
                    </a>

                    {p.description && (
                      <p className="text-[11px] text-slate-400 italic mt-1">
                        &quot;{p.description}&quot;
                      </p>
                    )}

                    {p.contentSnippet && (
                      <div className="mt-2 p-2 rounded bg-slate-900/90 text-[11px] text-slate-300 font-mono leading-relaxed max-h-36 overflow-y-auto">
                        {p.contentSnippet}
                      </div>
                    )}

                    {p.links && p.links.length > 0 && (
                      <div className="mt-2 text-[11px] text-slate-400">
                        <span className="text-slate-400 font-medium">Sample Discovered Links: </span>
                        {p.links.slice(0, 4).map((l, lIdx) => (
                          <span key={lIdx} className="inline-block mr-2 text-sky-400/90 font-mono">
                            {l.text || l.href.split("/").pop()}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Structured JSON Output */}
        {data?.structured_json && (
          <JsonViewer
            data={data.structured_json}
            title={data.intent?.url ? `Extracted JSON: ${data.intent.url}` : "Extracted Structured JSON"}
          />
        )}
      </div>

      {/* Terminal Logs Modal */}
      {execution && (
        <TerminalLogsModal
          isOpen={showLogsModal}
          onClose={() => setShowLogsModal(false)}
          execution={execution}
        />
      )}
    </div>
  );
};
