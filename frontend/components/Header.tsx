"use client";

import React from "react";
import { Terminal, Cpu, CheckCircle2, AlertCircle, RefreshCw, SlidersHorizontal, BookOpen } from "lucide-react";
import { SystemHealth } from "../types";

interface HeaderProps {
  health: SystemHealth | null;
  isHealthLoading: boolean;
  onRefreshHealth: () => void;
  onToggleSettings: () => void;
  isSettingsOpen: boolean;
  onClearHistory: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  health,
  isHealthLoading,
  onRefreshHealth,
  onToggleSettings,
  isSettingsOpen,
  onClearHistory
}) => {
  return (
    <header className="sticky top-0 z-40 w-full border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-md px-4 py-3">
      <div className="max-w-6xl mx-auto flex items-center justify-between gap-4">
        {/* Brand / Logo */}
        <div className="flex items-center gap-3">
          <div className="h-9 w-9 rounded-xl bg-gradient-to-tr from-sky-500 via-indigo-500 to-purple-500 p-[1px] shadow-lg shadow-sky-500/20">
            <div className="h-full w-full bg-slate-950 rounded-[11px] flex items-center justify-center">
              <Terminal className="h-4.5 w-4.5 text-sky-400" />
            </div>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-base tracking-tight text-white flex items-center gap-1.5">
                CLI-Agent
                <span className="text-[10px] font-semibold uppercase tracking-wider px-1.5 py-0.5 rounded bg-sky-500/10 text-sky-400 border border-sky-500/20">
                  BuildSprint R2
                </span>
              </span>
            </div>
            <p className="text-xs text-slate-400 hidden sm:block">
              Natural Language to Real CLI Subprocess Execution
            </p>
          </div>
        </div>

        {/* Backend & AI status pill */}
        <div className="flex items-center gap-2">
          {health ? (
            <div className="hidden md:flex items-center gap-2 px-2.5 py-1 rounded-full bg-emerald-950/40 border border-emerald-500/30 text-emerald-400 text-xs">
              <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400 animate-pulse" />
              <span>Backend Ready</span>
              <span className="text-slate-500">|</span>
              <span className="text-slate-300 font-mono text-[11px] flex items-center gap-1">
                <Cpu className="h-3 w-3 text-sky-400" />
                {health.ai_engine.split("(")[0].trim()}
              </span>
            </div>
          ) : (
            <div className="hidden md:flex items-center gap-2 px-2.5 py-1 rounded-full bg-amber-950/40 border border-amber-500/30 text-amber-400 text-xs">
              <AlertCircle className="h-3.5 w-3.5" />
              <span>{isHealthLoading ? "Connecting..." : "Backend Standby"}</span>
            </div>
          )}

          {/* Docs link */}
          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noopener noreferrer"
            title="FastAPI Swagger API Documentation"
            className="flex items-center gap-1.5 px-2.5 py-1.5 text-xs text-slate-300 hover:text-white rounded-lg bg-slate-900 border border-slate-800 hover:border-slate-700 transition-colors"
          >
            <BookOpen className="h-3.5 w-3.5 text-sky-400" />
            <span className="hidden sm:inline">Swagger API</span>
          </a>

          {/* Settings Drawer Button */}
          <button
            onClick={onToggleSettings}
            className={`p-2 rounded-lg border text-xs flex items-center gap-1.5 transition-colors ${
              isSettingsOpen
                ? "bg-sky-500/20 border-sky-500/40 text-sky-400"
                : "bg-slate-900 border-slate-800 text-slate-300 hover:border-slate-700"
            }`}
            title="Crawl Parameters & Configuration"
          >
            <SlidersHorizontal className="h-4 w-4" />
          </button>

          {/* Clear History */}
          <button
            onClick={onClearHistory}
            className="p-2 rounded-lg bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-400 hover:text-rose-400 transition-colors"
            title="Clear Chat History"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
        </div>
      </div>
    </header>
  );
};
