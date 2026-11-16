"use client";

import React, { useRef, useEffect } from "react";
import { Send, Loader2, Sparkles } from "lucide-react";

interface ChatInputProps {
  value: string;
  onChange: (val: string) => void;
  onSubmit: () => void;
  isLoading: boolean;
  onSelectPrompt: (p: string) => void;
}

export const ChatInput: React.FC<ChatInputProps> = ({
  value,
  onChange,
  onSubmit,
  isLoading,
  onSelectPrompt
}) => {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 180)}px`;
    }
  }, [value]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (!isLoading && value.trim()) {
        onSubmit();
      }
    }
  };

  return (
    <div className="w-full">
      <div className="relative rounded-2xl bg-slate-900 border border-slate-700/80 shadow-2xl focus-within:border-sky-500/80 focus-within:ring-2 focus-within:ring-sky-500/20 transition-all duration-200">
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Enter a task (e.g. Crawl https://example.com, summarize the website and return extracted information in JSON)..."
          rows={1}
          disabled={isLoading}
          className="w-full px-4 py-3.5 pr-14 bg-transparent text-sm text-slate-100 placeholder:text-slate-400 focus:outline-none resize-none disabled:opacity-50 min-h-[52px] max-h-[180px]"
        />

        <button
          onClick={onSubmit}
          disabled={isLoading || !value.trim()}
          className="absolute right-2.5 bottom-2.5 p-2 rounded-xl bg-sky-500 hover:bg-sky-400 disabled:bg-slate-800 disabled:text-slate-600 text-slate-950 font-semibold transition-all duration-150 shadow-md shadow-sky-500/20 disabled:shadow-none flex items-center justify-center cursor-pointer disabled:cursor-not-allowed"
          title="Send task"
        >
          {isLoading ? (
            <Loader2 className="h-4 w-4 animate-spin text-sky-400" />
          ) : (
            <Send className="h-4 w-4" />
          )}
        </button>
      </div>

      <div className="flex items-center justify-between text-[11px] text-slate-400 px-2 pt-2">
        <span>Press <kbd className="px-1 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300 font-mono text-[10px]">Enter</kbd> to execute &bull; <kbd className="px-1 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300 font-mono text-[10px]">Shift+Enter</kbd> for newline</span>
        <span className="text-slate-400 hidden sm:inline">Invokes real backend CLI subprocess</span>
      </div>
    </div>
  );
};
