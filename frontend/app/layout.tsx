import type { Metadata } from "next";
import { GeistSans } from "geist/font/sans";
import { GeistMono } from "geist/font/mono";
import "./globals.css";

export const metadata: Metadata = {
  title: "Engram — Memory OS",
  description: "Structured world models for AI agents. Every conversation builds a richer understanding.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${GeistSans.variable} ${GeistMono.variable}`}>
      <body className="bg-bg text-text-primary font-sans overflow-hidden h-screen">
        {children}
      </body>
    </html>
  );
}
