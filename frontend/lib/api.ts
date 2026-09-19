const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://127.0.0.1:8000/api";

export type PolicyRule = {
  id: number;
  topic: string;
  guidance: string;
  severity: "low" | "medium" | "high";
  risk_keywords: string;
  fallback_language: string;
};

export type Contract = {
  id: number;
  vendor_name: string;
  raw_text: string;
  status: "pending" | "reviewed";
  uploaded_at: string;
};

export type AgentStep = {
  id: number;
  step_number: number;
  thought: string;
  tool_name: string;
  tool_args: Record<string, unknown>;
  observation: Record<string, unknown>;
};

export type Flag = {
  id: number;
  topic: string;
  clause_excerpt: string;
  severity: "low" | "medium" | "high";
  note: string;
  suggested_language: string;
  dismissed: boolean;
};

export type AgentRun = {
  id: number;
  contract_id: number;
  status: "running" | "completed";
  started_at: string;
  decided_at: string | null;
  steps: AgentStep[];
  flags: Flag[];
};

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Request failed: ${res.status}`);
  return res.json();
}

async function postJson<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) throw new Error(`Request failed: ${res.status}`);
  return res.json();
}

export const fetchContracts = () => getJson<Contract[]>("/contracts/");
export const fetchContract = (id: number) => getJson<Contract>(`/contracts/${id}/`);
export const fetchPolicyRules = () => getJson<PolicyRule[]>("/policy-rules/");
export const fetchRuns = () => getJson<AgentRun[]>("/runs/");
export const fetchRun = (id: number) => getJson<AgentRun>(`/runs/${id}/`);

export const createContract = (vendor_name: string, raw_text: string) =>
  postJson<Contract>("/contracts/", { vendor_name, raw_text });

export const createPolicyRule = (rule: Omit<PolicyRule, "id">) =>
  postJson<PolicyRule>("/policy-rules/", rule);

export const analyzeContract = (contractId: number) =>
  postJson<AgentRun>(`/contracts/${contractId}/analyze/`);

export const dismissFlag = (flagId: number, dismissed: boolean) =>
  postJson<Flag>(`/flags/${flagId}/dismiss/`, { dismissed });

export const runsExportUrl = () => `${API_BASE}/runs/export/`;
export const contractReportUrl = (contractId: number) => `${API_BASE}/contracts/${contractId}/report/`;
