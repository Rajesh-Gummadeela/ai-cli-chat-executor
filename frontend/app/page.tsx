"use client";

import React, { useState, useEffect, useRef } from "react";
import { Header } from "../components/Header";
import { MessageItem } from "../components/MessageItem";
import { ChatInput } from "../components/ChatInput";
import { QuickPrompts } from "../components/QuickPrompts";
import { SettingsDrawer } from "../components/SettingsDrawer";
import { ChatMessage, ExecutionStep, SystemHealth, ChatResponseData } from "../types";
import { Terminal, ShieldCheck, Sparkles, Cpu, Layers } from "lucide-react";

const DEFAULT_BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

const INITIAL_WELCOME_MESSAGE: ChatMessage = {
  id: "welcome-1",
  role: "assistant",
  timestamp: "Just now",
  content: `### Welcome to the CLI-Driven AI Execution Assistant!

I translate natural language instructions into **actual CLI process executions** via backend subprocesses.

#### Primary Use Case:
Ask me to crawl any public website:
> *"Crawl https://example.com, summarize the website and return extracted information in JSON."*

#### What Happens Under the Hood:
1. **Intent Extraction**: Identifies the target URL and requested operation.
2. **Security & SSRF Validation**: Validates protocol, checks DNS, and blocks private/cloud-metadata networks.
3. **Subprocess Spawning**: Spawns an approved CLI crawler (\`python services/crawler_cli.py\`) with argument sanitization.
4. **Output Capture**: Collects \`stdout\`, \`stderr\`, execution duration, and exit code.
5. **AI Synthesis**: Generates a clean Markdown summary and structured JSON.

Click any of the suggested test prompts below to start!`
};

export default function Home() {
  const [messages, setMessages] = useState<ChatMessage[]>([INITIAL_WELCOME_MESSAGE]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [isHealthLoading, setIsHealthLoading] = useState(false);

  // Settings state
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [backendUrl, setBackendUrl] = useState(DEFAULT_BACKEND_URL);
  const [maxPages, setMaxPages] = useState(3);
  const [maxDepth, setMaxDepth] = useState(1);
  const [timeoutSec, setTimeoutSec] = useState(20);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Fetch backend health
  const fetchHealth = async () => {
    setIsHealthLoading(true);
    try {
      const res = await fetch(`${backendUrl}/api/health`, { method: "GET" });
      if (res.ok) {
        const data = await res.json();
        setHealth(data);
      } else {
        setHealth(null);
      }
    } catch {
      setHealth(null);
    } finally {
      setIsHealthLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, 30000);
    return () => clearInterval(interval);
  }, [backendUrl]);

  // Send Chat Request
  const handleSendMessage = async (textToSend?: string) => {
    const prompt = (textToSend || input).trim();
    if (!prompt || isLoading) return;

    setInput("");

    const userMessageId = `user-${Date.now()}`;
    const assistantMessageId = `assistant-${Date.now()}`;

    const userMsg: ChatMessage = {
      id: userMessageId,
      role: "user",
      content: prompt,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
    };

    const initialAssistantMsg: ChatMessage = {
      id: assistantMessageId,
      role: "assistant",
      content: "Initializing execution pipeline...",
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      isLoading: true,
      steps: [
        { step: "intent", status: "running", label: "Interpreting natural language request..." },
        { step: "validate", status: "pending", label: "Security & SSRF URL verification" },
        { step: "cli", status: "pending", label: "Backend CLI subprocess invocation" },
        { step: "llm", status: "pending", label: "AI synthesis & structured JSON formatting" }
      ]
    };

    setMessages((prev) => [...prev, userMsg, initialAssistantMsg]);
    setIsLoading(true);

    try {
      // Execute via backend POST /chat endpoint
      const response = await fetch(`${backendUrl}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: prompt,
          options: {
            max_pages: maxPages,
            max_depth: maxDepth,
            timeout: timeoutSec
          }
        })
      });

      if (!response.ok) {
        throw new Error(`Backend responded with HTTP ${response.status}: ${response.statusText}`);
      }

      const resData: ChatResponseData = await response.json();

      // Build completed steps based on execution outcome
      const completedSteps: ExecutionStep[] = [
        {
          step: "intent",
          status: "done",
          label: resData.intent?.url
            ? `Target: ${resData.intent.url} (${resData.intent.task})`
            : "Request parsed"
        },
        {
          step: "validate",
          status: resData.status === "error" && resData.execution?.exitCode === 2 ? "error" : "done",
          label: resData.status === "error" && resData.execution?.exitCode === 2
            ? "Validation Rejected"
            : "SSRF Check Passed"
        },
        {
          step: "cli",
          status: resData.execution?.exitCode === 0 ? "done" : resData.execution ? "error" : "pending",
          label: resData.execution
            ? `CLI exited with code ${resData.execution.exitCode} in ${resData.execution.duration}`
            : "CLI skipped"
        },
        {
          step: "llm",
          status: resData.status === "success" ? "done" : "error",
          label: resData.ai_provider ? `Synthesized by ${resData.ai_provider}` : "Synthesis completed"
        }
      ];

      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessageId
            ? {
                ...msg,
                content: resData.summary || "Execution completed.",
                isLoading: false,
                data: resData,
                steps: completedSteps
              }
            : msg
        )
      );
    } catch (err: any) {
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessageId
            ? {
                ...msg,
                content: `### Execution Pipeline Error\n\nCould not connect to the backend CLI service at \`${backendUrl}\`.\n\n**Error:** ${err?.message || "Network Error"}\n\n*Make sure the backend is running via \`uvicorn backend.main:app --reload\` on port 8000.*`,
                isLoading: false,
                steps: [
                  { step: "intent", status: "error", label: "Connection Failed" }
                ]
              }
            : msg
        )
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleClearHistory = () => {
    setMessages([INITIAL_WELCOME_MESSAGE]);
  };

  return (
    <div className="flex flex-col min-h-screen bg-slate-950 text-slate-100">
      {/* Top Header */}
      <Header
        health={health}
        isHealthLoading={isHealthLoading}
        onRefreshHealth={fetchHealth}
        onToggleSettings={() => setIsSettingsOpen(!isSettingsOpen)}
        isSettingsOpen={isSettingsOpen}
        onClearHistory={handleClearHistory}
      />

      {/* Main Chat Scroll Area */}
      <main className="flex-1 w-full max-w-5xl mx-auto flex flex-col justify-between">
        <div className="flex-1 divide-y divide-slate-800/60 pb-36">
          {messages.map((message) => (
            <MessageItem key={message.id} message={message} />
          ))}
          <div ref={messagesEndRef} />
        </div>
      </main>

      {/* Sticky Bottom Input & Quick Prompts Area */}
      <footer className="fixed bottom-0 left-0 right-0 z-30 bg-gradient-to-t from-slate-950 via-slate-950/95 to-transparent pt-6 pb-4 px-4 border-t border-slate-800/40">
        <div className="max-w-4xl mx-auto space-y-2">
          {/* Quick prompt suggestion chips */}
          <QuickPrompts
            onSelectPrompt={(prompt) => handleSendMessage(prompt)}
            disabled={isLoading}
          />

          {/* Interactive Chat Input Box */}
          <ChatInput
            value={input}
            onChange={setInput}
            onSubmit={() => handleSendMessage()}
            isLoading={isLoading}
            onSelectPrompt={(prompt) => handleSendMessage(prompt)}
          />
        </div>
      </footer>

      {/* Slide-out Settings Drawer */}
      <SettingsDrawer
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        maxPages={maxPages}
        setMaxPages={setMaxPages}
        maxDepth={maxDepth}
        setMaxDepth={setMaxDepth}
        timeoutSec={timeoutSec}
        setTimeoutSec={setTimeoutSec}
        backendUrl={backendUrl}
        setBackendUrl={setBackendUrl}
      />
    </div>
  );
}
