"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  analyzeContract,
  createContract,
  fetchContracts,
  fetchRuns,
  runsExportUrl,
  type AgentRun,
  type Contract,
} from "@/lib/api";

const STATUS_STYLES: Record<Contract["status"], string> = {
  pending: "bg-amber-200 text-amber-900 dark:bg-amber-800 dark:text-amber-100",
  reviewed: "bg-emerald-200 text-emerald-900 dark:bg-emerald-800 dark:text-emerald-100",
};

const FILTERS: Array<{ label: string; value: Contract["status"] | "all" }> = [
  { label: "All", value: "all" },
  { label: "Pending", value: "pending" },
  { label: "Reviewed", value: "reviewed" },
];

export default function Home() {
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [runs, setRuns] = useState<AgentRun[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [analyzing, setAnalyzing] = useState<number | null>(null);
  const [filter, setFilter] = useState<Contract["status"] | "all">("all");
  const [vendorName, setVendorName] = useState("");
  const [rawText, setRawText] = useState("");
  const [uploading, setUploading] = useState(false);

  function reload() {
    fetchContracts().then(setContracts).catch((err) => setError(err.message));
    fetchRuns().then(setRuns).catch((err) => setError(err.message));
  }

  useEffect(reload, []);

  function flagCountFor(contractId: number): number {
    const run = runs.find((r) => r.contract_id === contractId);
    return run ? run.flags.filter((f) => !f.dismissed).length : 0;
  }

  const visibleContracts = filter === "all" ? contracts : contracts.filter((c) => c.status === filter);

  async function handleAnalyze(id: number) {
    setAnalyzing(id);
    try {
      await analyzeContract(id);
      reload();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setAnalyzing(null);
    }
  }

  async function handleUpload(e: React.FormEvent) {
    e.preventDefault();
    setUploading(true);
    try {
      await createContract(vendorName, rawText);
      setVendorName("");
      setRawText("");
      reload();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setUploading(false);
    }
  }

  return (
    <main className="mx-auto max-w-4xl px-5 py-10">
      <header className="mb-8">
        <h1 className="text-3xl font-semibold">redlineagent</h1>
        <p className="mt-1 text-zinc-600 dark:text-zinc-400">
          Agent checks vendor contracts against a policy playbook and flags risky clauses with a fallback rewrite.
        </p>
        <div className="mt-2 flex gap-4 text-sm">
          <a href={runsExportUrl()} className="underline">
            Export review audit trail (CSV)
          </a>
          <Link href="/policy" className="underline">
            Policy playbook
          </Link>
        </div>
      </header>

      {error && <p className="mb-4 text-red-600 dark:text-red-400">{error}</p>}

      <form onSubmit={handleUpload} className="mb-8 space-y-2 rounded border border-zinc-200 p-4 dark:border-zinc-800">
        <h2 className="font-medium">Upload a contract</h2>
        <input
          value={vendorName}
          onChange={(e) => setVendorName(e.target.value)}
          placeholder="Vendor name"
          required
          className="w-full rounded border border-zinc-300 px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-900"
        />
        <textarea
          value={rawText}
          onChange={(e) => setRawText(e.target.value)}
          placeholder="Paste the contract text"
          required
          rows={4}
          className="w-full rounded border border-zinc-300 px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-900"
        />
        <button
          type="submit"
          disabled={uploading}
          className="rounded bg-zinc-900 px-3 py-1.5 text-sm text-white disabled:opacity-50 dark:bg-zinc-100 dark:text-zinc-900"
        >
          {uploading ? "Uploading..." : "Upload"}
        </button>
      </form>

      <div className="mb-6 flex flex-wrap gap-2">
        {FILTERS.map((f) => {
          const count = f.value === "all" ? contracts.length : contracts.filter((c) => c.status === f.value).length;
          return (
            <button
              key={f.value}
              onClick={() => setFilter(f.value)}
              className={`rounded-full px-3 py-1 text-sm ${
                filter === f.value
                  ? "bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900"
                  : "border border-zinc-300 dark:border-zinc-700"
              }`}
            >
              {f.label} ({count})
            </button>
          );
        })}
      </div>

      <div className="divide-y divide-zinc-200 dark:divide-zinc-800">
        {visibleContracts.map((c) => (
          <div key={c.id} className="flex items-center justify-between gap-4 py-4">
            <div>
              <Link href={`/contracts/${c.id}`} className="font-medium hover:underline">
                {c.vendor_name}
              </Link>
              <p className="line-clamp-1 text-sm text-zinc-500">{c.raw_text}</p>
              {c.status === "reviewed" && (
                <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-400">
                  {flagCountFor(c.id)} open flag{flagCountFor(c.id) === 1 ? "" : "s"}
                </p>
              )}
            </div>
            <div className="flex items-center gap-3">
              <span className={`rounded-full px-3 py-1 text-xs font-medium ${STATUS_STYLES[c.status]}`}>
                {c.status}
              </span>
              {c.status === "pending" && (
                <button
                  onClick={() => handleAnalyze(c.id)}
                  disabled={analyzing === c.id}
                  className="rounded border border-zinc-300 px-3 py-1 text-sm hover:bg-zinc-100 disabled:opacity-50 dark:border-zinc-700 dark:hover:bg-zinc-800"
                >
                  {analyzing === c.id ? "Analyzing..." : "Analyze"}
                </button>
              )}
            </div>
          </div>
        ))}
        {visibleContracts.length === 0 && <p className="py-8 text-zinc-500">No contracts in this view.</p>}
      </div>
    </main>
  );
}
