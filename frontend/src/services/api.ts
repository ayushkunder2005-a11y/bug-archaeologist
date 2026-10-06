/* ── API service layer ───────────────────────────────────────────── */

import type { Repository, DashboardData, Bug, Commit, SearchResult } from '../types';

const API_BASE = '/api';

async function fetchJson<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${url}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `API error: ${res.status}`);
  }
  if (res.status === 204) return {} as T;
  return res.json();
}

/* ── Repositories ────────────────────────────────────────────────── */

export async function createRepository(
  url?: string,
  localPath?: string,
  maxCommits = 500,
): Promise<Repository> {
  return fetchJson<Repository>('/repositories', {
    method: 'POST',
    body: JSON.stringify({
      url: url || undefined,
      local_path: localPath || undefined,
      max_commits: maxCommits,
    }),
  });
}

export async function listRepositories(): Promise<{
  repositories: Repository[];
  total: number;
}> {
  return fetchJson('/repositories');
}

export async function getRepository(id: string): Promise<Repository> {
  return fetchJson(`/repositories/${id}`);
}

export async function getRepositoryStatus(
  id: string,
): Promise<{ id: string; status: string; error_message: string | null }> {
  return fetchJson(`/repositories/${id}/status`);
}

export async function deleteRepository(id: string): Promise<void> {
  await fetchJson(`/repositories/${id}`, { method: 'DELETE' });
}

/* ── Analysis / Dashboard ────────────────────────────────────────── */

export async function getDashboard(repoId: string): Promise<DashboardData> {
  return fetchJson(`/repositories/${repoId}/dashboard`);
}

export async function getBugs(repoId: string): Promise<{ bugs: Bug[]; total: number }> {
  return fetchJson(`/repositories/${repoId}/bugs`);
}

export async function getBugDetail(repoId: string, bugId: string): Promise<Bug> {
  return fetchJson(`/repositories/${repoId}/bugs/${bugId}`);
}

export async function getCommits(
  repoId: string,
  page = 1,
  perPage = 50,
): Promise<{ commits: Commit[]; total: number; page: number; per_page: number }> {
  return fetchJson(`/repositories/${repoId}/commits?page=${page}&per_page=${perPage}`);
}

/* ── Search ──────────────────────────────────────────────────────── */

export async function search(params: Record<string, string>): Promise<SearchResult> {
  const qs = new URLSearchParams(params).toString();
  return fetchJson(`/search?${qs}`);
}
