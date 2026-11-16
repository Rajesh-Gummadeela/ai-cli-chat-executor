"use client";

import React from "react";
import { X, Sliders, Shield, Zap, Globe } from "lucide-react";

interface SettingsDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  maxPages: number;
  setMaxPages: (val: number) => void;
  maxDepth: number;
  setMaxDepth: (val: number) => void;
  timeoutSec: number;
  setTimeoutSec: (val: number) => void;
  backendUrl: string;
  setBackendUrl: (val: string) => void;
}

export const SettingsDrawer: React.FC<SettingsDrawerProps> = ({
  isOpen,
  onClose,
  maxPages,
  setMaxPages,
  maxDepth,
  setMaxDepth,
  timeoutSec,
  setTimeoutSec,
  backendUrl,
  setBackendUrl
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-y-0 right-0 z-50 w-full max-w-sm bg-slate-950 border-l border-slate-800 p-5 shadow-2xl flex flex-col animate-in slide-in-from-right duration-200">
      <div className="flex items-center justify-between pb-4 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <Sliders className="h-4 w-4 text-sky-400" />
          <h3 className="font-semibold text-sm text-white">Crawler & CLI Settings</h3>
        </div>
        <button
          onClick={onClose}
          className="p-1 rounded-md text-slate-400 hover:text-white hover:bg-slate-800"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      <div className="flex-1 py-4 space-y-5 overflow-y-auto text-xs">
        {/* Backend API Endpoint */}
        <div>
          <label className="block text-slate-300 font-medium mb-1.5 flex items-center gap-1.5">
            <Globe className="h-3.5 w-3.5 text-sky-400" />
            Backend API URL
          </label>
          <input
            type="text"
            value={backendUrl}
            onChange={(e) => setBackendUrl(e.target.value)}
            className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-700 text-slate-200 focus:outline-none focus:border-sky-500 font-mono text-xs"
            placeholder="http://localhost:8000"
          />
          <p className="text-[11px] text-slate-400 mt-1">
            FastAPI endpoint hosting `/chat` and `/api/health`.
          </p>
        </div>

        {/* Max Pages */}
        <div>
          <div className="flex items-center justify-between text-slate-300 font-medium mb-1.5">
            <span className="flex items-center gap-1.5">
              <Zap className="h-3.5 w-3.5 text-amber-400" />
              Max Pages to Crawl
            </span>
            <span className="font-mono text-sky-400 font-semibold">{maxPages}</span>
          </div>
          <input
            type="range"
            min={1}
            max={10}
            step={1}
            value={maxPages}
            onChange={(e) => setMaxPages(Number(e.target.value))}
            className="w-full accent-sky-400 cursor-pointer"
          />
          <div className="flex justify-between text-[10px] text-slate-400 mt-0.5">
            <span>1 page</span>
            <span>5 pages</span>
            <span>10 pages (max)</span>
          </div>
        </div>

        {/* Max Depth */}
        <div>
          <div className="flex items-center justify-between text-slate-300 font-medium mb-1.5">
            <span className="flex items-center gap-1.5">
              <Shield className="h-3.5 w-3.5 text-indigo-400" />
              Link Traversal Depth
            </span>
            <span className="font-mono text-indigo-400 font-semibold">{maxDepth}</span>
          </div>
          <input
            type="range"
            min={0}
            max={3}
            step={1}
            value={maxDepth}
            onChange={(e) => setMaxDepth(Number(e.target.value))}
            className="w-full accent-indigo-400 cursor-pointer"
          />
          <div className="flex justify-between text-[10px] text-slate-400 mt-0.5">
            <span>0 (single page)</span>
            <span>1 (depth 1)</span>
            <span>2</span>
            <span>3 (max)</span>
          </div>
        </div>

        {/* Timeout */}
        <div>
          <div className="flex items-center justify-between text-slate-300 font-medium mb-1.5">
            <span>Subprocess Timeout (seconds)</span>
            <span className="font-mono text-emerald-400 font-semibold">{timeoutSec}s</span>
          </div>
          <input
            type="range"
            min={5}
            max={60}
            step={5}
            value={timeoutSec}
            onChange={(e) => setTimeoutSec(Number(e.target.value))}
            className="w-full accent-emerald-400 cursor-pointer"
          />
          <div className="flex justify-between text-[10px] text-slate-400 mt-0.5">
            <span>5s</span>
            <span>20s (default)</span>
            <span>60s</span>
          </div>
        </div>

        {/* Security Guardrails Note */}
        <div className="p-3 rounded-xl bg-slate-900 border border-slate-800 text-[11px] text-slate-400 space-y-1.5">
          <div className="font-semibold text-slate-300 flex items-center gap-1">
            <Shield className="h-3 w-3 text-emerald-400" />
            Security Guardrails Enforced:
          </div>
          <ul className="list-disc list-inside space-y-0.5 text-slate-400">
            <li>Strict URL schema verification (http/https only)</li>
            <li>Zero shell execution (arguments array via exec)</li>
            <li>SSRF protection: Private IPs & cloud metadata blocked</li>
            <li>Untrusted HTML content sanitized for AI processing</li>
          </ul>
        </div>
      </div>

      <div className="pt-3 border-t border-slate-800">
        <button
          onClick={onClose}
          className="w-full py-2 px-3 rounded-lg bg-sky-500 hover:bg-sky-400 text-slate-950 font-semibold text-xs transition-colors"
        >
          Apply & Close
        </button>
      </div>
    </div>
  );
};
