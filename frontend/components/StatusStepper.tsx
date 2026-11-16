"use client";

import React from "react";
import { CheckCircle2, Loader2, AlertCircle, Circle, Terminal, ShieldCheck, Sparkles, Compass } from "lucide-react";
import { ExecutionStep } from "../types";

interface StatusStepperProps {
  steps?: ExecutionStep[];
}

export const StatusStepper: React.FC<StatusStepperProps> = ({ steps }) => {
  if (!steps || steps.length === 0) return null;

  const getStepIcon = (stepType: string) => {
    switch (stepType) {
      case "intent":
        return <Compass className="h-3.5 w-3.5" />;
      case "validate":
        return <ShieldCheck className="h-3.5 w-3.5" />;
      case "cli":
        return <Terminal className="h-3.5 w-3.5" />;
      case "llm":
        return <Sparkles className="h-3.5 w-3.5" />;
      default:
        return <Terminal className="h-3.5 w-3.5" />;
    }
  };

  return (
    <div className="my-3 p-3 rounded-xl bg-slate-900/90 border border-slate-800/80 shadow-inner">
      <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2 flex items-center justify-between">
        <span>Execution Pipeline</span>
        <span className="text-slate-500 font-mono">Backend Subprocess Workflow</span>
      </div>

      <div className="space-y-2">
        {steps.map((st, idx) => (
          <div key={idx} className="flex items-start gap-2.5 text-xs">
            {/* Status Icon */}
            <div className="mt-0.5 shrink-0">
              {st.status === "running" && (
                <Loader2 className="h-4 w-4 text-sky-400 animate-spin" />
              )}
              {st.status === "done" && (
                <CheckCircle2 className="h-4 w-4 text-emerald-400" />
              )}
              {st.status === "error" && (
                <AlertCircle className="h-4 w-4 text-rose-400" />
              )}
              {st.status === "pending" && (
                <Circle className="h-4 w-4 text-slate-600" />
              )}
            </div>

            {/* Label & Detail */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-1.5 font-medium">
                <span className={`text-[11px] px-1.5 py-0.2 rounded border flex items-center gap-1 ${
                  st.status === "running"
                    ? "bg-sky-500/10 text-sky-400 border-sky-500/30"
                    : st.status === "done"
                    ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                    : st.status === "error"
                    ? "bg-rose-500/10 text-rose-400 border-rose-500/30"
                    : "bg-slate-800 text-slate-400 border-slate-700"
                }`}>
                  {getStepIcon(st.step)}
                  {st.step.toUpperCase()}
                </span>
                <span className={st.status === "running" ? "text-sky-300 font-medium" : "text-slate-300"}>
                  {st.label}
                </span>
              </div>
              {st.detail && (
                <p className="text-[11px] text-slate-400 font-mono mt-0.5 truncate">
                  {st.detail}
                </p>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
