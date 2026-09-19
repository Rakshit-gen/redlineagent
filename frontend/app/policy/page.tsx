"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { createPolicyRule, fetchPolicyRules, type PolicyRule } from "@/lib/api";

const SEVERITY_STYLES: Record<PolicyRule["severity"], string> = {
  high: "bg-red-200 text-red-900 dark:bg-red-800 dark:text-red-100",
  medium: "bg-amber-200 text-amber-900 dark:bg-amber-800 dark:text-amber-100",
  low: "bg-zinc-200 text-zinc-900 dark:bg-zinc-800 dark:text-zinc-100",
};

const EMPTY_FORM = {
  topic: "",
  guidance: "",
  severity: "medium" as PolicyRule["severity"],
  risk_keywords: "",
  fallback_language: "",
};

export default function PolicyPlaybook() {
  const [rules, setRules] = useState<PolicyRule[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [submitting, setSubmitting] = useState(false);

  function reload() {
    fetchPolicyRules().then(setRules).catch((err) => setError(err.message));
  }

  useEffect(reload, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await createPolicyRule(form);
      setForm(EMPTY_FORM);
      reload();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="mx-auto max-w-3xl px-5 py-10">
      <Link href="/" className="text-sm underline">
        ← Back to contracts
      </Link>
      <h1 className="mt-4 mb-1 text-2xl font-semibold">Policy playbook</h1>
      <p className="mb-8 text-zinc-500">
        The topics the agent checks every contract against, and the fallback language it proposes.
      </p>

      {error && <p className="mb-4 text-red-600 dark:text-red-400">{error}</p>}

      <form onSubmit={handleSubmit} className="mb-8 space-y-2 rounded border border-zinc-200 p-4 dark:border-zinc-800">
        <h2 className="font-medium">Add a policy topic</h2>
        <input
          value={form.topic}
          onChange={(e) => setForm({ ...form, topic: e.target.value })}
          placeholder="Topic (e.g. indemnification)"
          required
          className="w-full rounded border border-zinc-300 px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-900"
        />
        <input
          value={form.guidance}
          onChange={(e) => setForm({ ...form, guidance: e.target.value })}
          placeholder="Why this matters"
          required
          className="w-full rounded border border-zinc-300 px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-900"
        />
        <input
          value={form.risk_keywords}
          onChange={(e) => setForm({ ...form, risk_keywords: e.target.value })}
          placeholder="Risk keywords, comma-separated"
          required
          className="w-full rounded border border-zinc-300 px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-900"
        />
        <input
          value={form.fallback_language}
          onChange={(e) => setForm({ ...form, fallback_language: e.target.value })}
          placeholder="Suggested fallback language"
          required
          className="w-full rounded border border-zinc-300 px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-900"
        />
        <select
          value={form.severity}
          onChange={(e) => setForm({ ...form, severity: e.target.value as PolicyRule["severity"] })}
          className="w-full rounded border border-zinc-300 px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-900"
        >
          <option value="low">low</option>
          <option value="medium">medium</option>
          <option value="high">high</option>
        </select>
        <button
          type="submit"
          disabled={submitting}
          className="rounded bg-zinc-900 px-3 py-1.5 text-sm text-white disabled:opacity-50 dark:bg-zinc-100 dark:text-zinc-900"
        >
          {submitting ? "Adding..." : "Add topic"}
        </button>
      </form>

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
