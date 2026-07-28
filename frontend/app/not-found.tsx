"use client";

import Link from "next/link";
import { Brain } from "lucide-react";

export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center h-screen bg-bg">
      <div className="text-center animate-fade-in">
        <div className="w-16 h-16 rounded-3xl bg-bg-secondary border border-border flex items-center justify-center mx-auto mb-5 shadow-sm-soft">
          <Brain size={28} className="text-text-secondary" strokeWidth={1.5} />
        </div>
        <h2 className="text-[20px] font-semibold text-text-primary tracking-tight">
          Lost in the World Model
        </h2>
        <p className="text-[14px] text-text-secondary mt-2 max-w-[260px] mx-auto leading-relaxed">
          The page you are looking for does not exist in this engram.
        </p>
        <Link
          href="/"
          className="inline-flex items-center justify-center h-10 px-6 mt-6 rounded-xl bg-text-primary text-white text-[13px] font-medium hover:opacity-90 transition-opacity"
        >
          Return Home
        </Link>
      </div>
    </div>
  );
}
