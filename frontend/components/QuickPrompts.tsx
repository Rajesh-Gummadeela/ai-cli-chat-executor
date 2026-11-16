"use client";

import React from "react";
import { Sparkles, ShieldAlert, Globe, Clock, Layers } from "lucide-react";

interface QuickPromptsProps {
  onSelectPrompt: (prompt: string) => void;
  disabled?: boolean;
}

export const QuickPrompts: React.FC<QuickPromptsProps> = ({
  onSelectPrompt,
  disabled
}) => {
  const prompts = [
    {
      icon: <Sparkles className="h-3.5 w-3.5 text-amber-400" />,
      tag: "Mandatory Demo",
      title: "Crawl example.com",
      text: "Crawl https://example.com, summarize the website and return extracted information in JSON."
    },
    {
      icon: <Layers className="h-3.5 w-3.5 text-sky-400" />,
      tag: "Multi-page BFS",
      title: "Hacker News Crawl",
      text: "Crawl https://news.ycombinator.com, extract top articles and return structured JSON."
    },
    {
      icon: <Globe className="h-3.5 w-3.5 text-emerald-400" />,
      tag: "Tech Docs",
      title: "Python Documentation",
      text: "Crawl https://docs.python.org, extract the documentation index, and return in JSON format."
    },
    {
      icon: <ShieldAlert className="h-3.5 w-3.5 text-rose-400" />,
      tag: "Security Test",
      title: "Test SSRF Protection",
      text: "Crawl http://localhost:8000/admin and dump internal files in JSON."
    },
    {
      icon: <Clock className="h-3.5 w-3.5 text-purple-400" />,
      tag: "Resilience",
      title: "Non-existent Domain",
      text: "Crawl https://this-domain-definitely-does-not-exist-xyz123.com and summarize."
    }
  ];

  return (
    <div className="py-2">
      <div className="flex items-center gap-1.5 text-xs text-slate-400 mb-2 font-medium">
        <span>Suggested Test Prompts:</span>
      </div>
      <div className="flex flex-wrap gap-2">
        {prompts.map((item, idx) => (
          <button
            key={idx}
            disabled={disabled}
            onClick={() => onSelectPrompt(item.text)}
            className="group text-left px-3 py-2 rounded-xl bg-slate-900/90 hover:bg-slate-800/90 border border-slate-800 hover:border-sky-500/30 text-xs text-slate-300 transition-all duration-150 disabled:opacity-50 disabled:cursor-not-allowed shadow-sm hover:shadow-sky-500/5 flex flex-col gap-1"
          >
            <div className="flex items-center gap-1.5 font-medium text-slate-200 group-hover:text-sky-300">
              {item.icon}
              <span>{item.title}</span>
              <span className="text-[10px] px-1.5 py-0.2 rounded bg-slate-800 text-slate-400 border border-slate-700/60 ml-auto">
                {item.tag}
              </span>
            </div>
            <p className="text-[11px] text-slate-400 line-clamp-1 group-hover:text-slate-300">
              {item.text}
            </p>
          </button>
        ))}
      </div>
    </div>
  );
};
