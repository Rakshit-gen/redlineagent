"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { fetchPolicyRules, type PolicyRule } from "@/lib/api";

const SEVERITY_STYLES: Record<PolicyRule["severity"], string> = {
  high: "bg-red-200 text-red-900 dark:bg-red-800 dark:text-red-100",
  medium: "bg-amber-200 text-amber-900 dark:bg-amber-800 dark:text-amber-100",
  low: "bg-zinc-200 text-zinc-900 dark:bg-zinc-800 dark:text-zinc-100",
};

export default function PolicyPlaybook() {
  const [rules, setRules] = useState<PolicyRule[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchPolicyRules().then(setRules).catch((err) => setError(err.message));
  }, []);

  return (
    <main className="mx-auto max-w-3xl px-5 py-10">
      <Link href="/" className="text-sm underline">
        ← Back to contracts
      </Link>
      <h1 className="mt-4 mb-1 text-2xl font-semibold">Policy playbook</h1>
      <p className="mb-8 text-zinc-500">
        The topics the agent checks every contract against, and the fallback language it proposes.
      </p>

      {error && <p className="text-red-600 dark:text-red-400">{error}</p>}

      <div className="space-y-4">
        {rules.map((r) => (
          <div key={r.id} className="rounded border border-zinc-200 p-4 text-sm dark:border-zinc-800">
            <div className="flex items-center justify-between">
              <p className="font-medium">{r.topic.replace(/_/g, " ")}</p>
              <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${SEVERITY_STYLES[r.severity]}`}>
                {r.severity}
              </span>
            </div>
            <p className="mt-1 text-zinc-600 dark:text-zinc-400">{r.guidance}</p>
            <p className="mt-1 text-zinc-600 dark:text-zinc-400">
              <span className="font-medium">Fallback:</span> {r.fallback_language}
            </p>
          </div>
        ))}
        {rules.length === 0 && <p className="text-zinc-500">No policy rules yet.</p>}
      </div>
    </main>
  );
}
