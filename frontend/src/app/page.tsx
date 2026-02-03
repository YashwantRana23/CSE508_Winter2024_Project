"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    const token = localStorage.getItem("legal_lens_token");
    if (token) {
      router.replace("/dashboard");
    }
  }, [router]);

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-gradient-to-br from-slate-100 to-slate-200 px-4">
      <div className="w-full max-w-md rounded-2xl bg-white p-8 shadow-xl">
        <h1 className="mb-2 text-center text-2xl font-bold text-slate-800">
          Legal Lens
        </h1>
        <p className="mb-8 text-center text-slate-600">
          Legal search, knowledge graph & domain-specific assistant
        </p>
        <div className="flex flex-col gap-4">
          <Link
            href="/login"
            className="rounded-xl bg-indigo-600 py-3 text-center font-medium text-white hover:bg-indigo-700"
          >
            Sign in
          </Link>
          <Link
            href="/register"
            className="rounded-xl border border-slate-300 py-3 text-center font-medium text-slate-700 hover:bg-slate-50"
          >
            Sign up
          </Link>
        </div>
      </div>
    </div>
  );
}
