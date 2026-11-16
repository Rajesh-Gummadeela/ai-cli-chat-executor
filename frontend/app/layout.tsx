import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CLI-Driven AI Chat Execution | BuildSprint Round 2",
  description: "A production-grade conversational AI platform that translates natural language requests into real backend CLI subprocess executions.",
  keywords: ["AI", "CLI", "Web Crawler", "Next.js", "FastAPI", "Subprocess", "BuildSprint"],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="antialiased bg-[#090d16] text-slate-100 min-h-screen selection:bg-sky-500/30 selection:text-white">
        {children}
      </body>
    </html>
  );
}
