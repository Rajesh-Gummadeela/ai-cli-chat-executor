export interface DiscoveredLink {
  text: string;
  href: string;
  isExternal: boolean;
}

export interface PageHeading {
  level: number;
  text: string;
}

export interface CrawledPage {
  url: string;
  statusCode: number;
  durationMs?: number;
  title: string;
  description?: string;
  author?: string;
  headings: PageHeading[];
  contentSnippet: string;
  contentLength: number;
  fullContent?: string;
  linksCount?: number;
  links?: DiscoveredLink[];
  imagesCount?: number;
  metadata?: Record<string, string>;
}

export interface ExecutionMeta {
  exitCode: number;
  duration: string;
  command?: string;
  stdout?: string;
  stderr?: string;
  timedOut?: boolean;
}

export interface ExecutionStep {
  step: "intent" | "validate" | "cli" | "llm";
  status: "pending" | "running" | "done" | "error";
  label: string;
  detail?: string;
}

export interface ChatResponseData {
  status: "success" | "error" | "clarification" | "timeout";
  summary: string;
  pages: CrawledPage[];
  structured_json?: Record<string, unknown> | null;
  execution?: ExecutionMeta | null;
  intent?: {
    task: string;
    url?: string;
    expected_output?: string;
    max_pages?: number;
    max_depth?: number;
    timeout?: number;
  };
  ai_provider?: string;
  error?: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  data?: ChatResponseData;
  steps?: ExecutionStep[];
  isLoading?: boolean;
}

export interface SystemHealth {
  status: string;
  service: string;
  python_version: string;
  platform: string;
  ai_engine: string;
  cli_executor: {
    default_timeout: number;
    whitelisted_tools: string[];
  };
}
