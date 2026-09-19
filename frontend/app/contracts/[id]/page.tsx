"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import {
  dismissFlag,
  fetchContract,
  fetchRuns,
  type AgentRun,
  type Contract,
  type Flag,
} from "@/lib/api";

const SEVERITY_STYLES: Record<Flag["severity"], string> = {
  high: "border-red-500 bg-red-50 dark:bg-red-950",
  medium: "border-amber-500 bg-amber-50 dark:bg-amber-950",
  low: "border-zinc-400 bg-zinc-50 dark:bg-zinc-900",
};

export default function ContractDetail() {
  const params = useParams<{ id: string }>();
  const contractId = Number(params.id);

  const [contract, setContract] = useState<Contract | null>(null);
  const [run, setRun] = useState<AgentRun | null>(null);
  const [error, setError] = useState<string | null>(null);

  function reload() {
    fetchContract(contractId).then(setContract).catch((err) => setError(err.message));
    fetchRuns()
      .then((runs) => setRun(runs.find((r) => r.contract_id === contractId) ?? null))
      .catch((err) => setError(err.message));
  }

  useEffect(reload, [contractId]);

  async function handleDismissToggle(flag: Flag) {
    try {
      await dismissFlag(flag.id, !flag.dismissed);
      reload();
    } catch (err) {
      setError((err as Error).message);
    }
  }

  if (!contract) {
    return (
      <main className="mx-auto max-w-3xl px-5 py-10">
        {error ? <p className="text-red-600 dark:text-red-400">{error}</p> : <p>Loading...</p>}
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-3xl px-5 py-10">
      <Link href="/" className="text-sm underline">
        ← Back to contracts
      </Link>
      <h1 className="mt-4 mb-1 text-2xl font-semibold">{contract.vendor_name}</h1>
      <p className="mb-6 whitespace-pre-wrap text-sm text-zinc-600 dark:text-zinc-400">{contract.raw_text}</p>

      {error && <p className="mb-4 text-red-600 dark:text-red-400">{error}</p>}

      {!run && <p className="text-zinc-500">Not analyzed yet.</p>}

      {run && (
        <>
          <h2 className="mb-3 text-lg font-medium">Flagged clauses</h2>
          <div className="mb-8 space-y-3">
            {run.flags.map((f) => (
              <div key={f.id} className={`rounded border-l-4 p-3 text-sm ${SEVERITY_STYLES[f.severity]} ${f.dismissed ? "opacity-50" : ""}`}>
                <div className="flex items-center justify-between">
                  <p className="font-medium">
                    {f.topic.replace(/_/g, " ")} · {f.severity}
                  </p>
                  <button onClick={() => handleDismissToggle(f)} className="text-xs underline">
                    {f.dismissed ? "Restore" : "Dismiss"}
                  </button>
                </div>
                <p className="mt-1 italic text-zinc-700 dark:text-zinc-300">&ldquo;{f.clause_excerpt}&rdquo;</p>
                <p className="mt-1 text-zinc-600 dark:text-zinc-400">{f.note}</p>
                <p className="mt-1 text-zinc-600 dark:text-zinc-400">
                  <span className="font-medium">Suggested fallback:</span> {f.suggested_language}
                </p>
              </div>
            ))}
            {run.flags.length === 0 && <p className="text-zinc-500">No risky clauses found.</p>}
          </div>

          <h2 className="mb-3 text-lg font-medium">Agent trace</h2>
          <ol className="space-y-3">
            {run.steps.map((s) => (
              <li key={s.id} className="rounded border border-zinc-200 p-3 text-sm dark:border-zinc-800">
                <p className="font-medium">
                  Step {s.step_number} · {s.tool_name}
                </p>
                <p className="text-zinc-600 dark:text-zinc-400">{s.thought}</p>
              </li>
            ))}
          </ol>
        </>
      )}
    </main>
  );
}
