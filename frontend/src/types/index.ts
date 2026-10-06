/* ── Type definitions for Bug Archaeologist ──────────────────────── */

export interface Repository {
  id: string;
  name: string;
  url: string | null;
  local_path: string | null;
  status: 'pending' | 'analyzing' | 'complete' | 'error';
  error_message: string | null;
  total_commits: number;
  total_files: number;
  total_bugs_detected: number;
  health_score: number;
  primary_language: string | null;
  analyzed_at: string | null;
  created_at: string;
}

export interface Commit {
  id: string;
  hash: string;
  short_hash: string;
  message: string;
  author_name: string;
  author_email: string;
  authored_date: string;
  is_fix_commit: boolean;
  is_bug_introducing: boolean;
  bug_intro_score: number;
  risk_explanation: string | null;
  files_changed: number;
  insertions: number;
  deletions: number;
  total_changes: number;
  avg_complexity: number;
  max_complexity: number;
}

export interface Bug {
  id: string;
  title: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  introducing_commit_hash: string;
  fix_commit_hash: string;
  introduction_date: string;
  fix_date: string;
  time_to_fix_days: number;
  affected_files: string[] | null;
  affected_functions: string[] | null;
  introducing_author: string | null;
  fix_author: string | null;
  complexity_before: number;
  complexity_after: number;
  explanation?: string | null;
  related_commit_hashes?: string[] | null;
}

export interface FileAnalysis {
  file_path: string;
  language: string;
  total_lines: number;
  functions_count: number;
  classes_count: number;
  avg_complexity: number;
  max_complexity: number;
  times_changed: number;
  times_in_fix_commit: number;
  bug_proneness_score: number;
}

export interface FunctionAnalysis {
  name: string;
  file_path: string;
  line_number: number;
  complexity: number;
  length_lines: number;
  parameter_count: number;
  nested_depth: number;
  has_docstring: boolean;
  has_error_handling: boolean;
  times_changed: number;
  times_in_fix_commit: number;
  is_bug_prone: boolean;
  bug_proneness_score: number;
}

export interface DeveloperStat {
  name: string;
  email: string;
  total_commits: number;
  fix_commits: number;
  bug_introducing_commits: number;
  avg_risk_score: number;
  files_touched: number;
}

export interface ComplexityTrend {
  date: string;
  avg_complexity: number;
  max_complexity: number;
  commit_hash: string;
}

export interface BugTimelinePoint {
  date: string;
  introductions: number;
  fixes: number;
  cumulative_open: number;
}

export interface RiskBucket {
  label: string;
  count: number;
  color: string;
}

export interface DashboardData {
  repository_name: string;
  total_commits: number;
  total_bugs: number;
  health_score: number;
  total_files: number;
  avg_complexity: number;
  total_developers: number;
  analysis_date: string | null;
  bug_timeline: BugTimelinePoint[];
  risk_distribution: RiskBucket[];
  top_problematic_files: FileAnalysis[];
  top_bug_prone_functions: FunctionAnalysis[];
  developer_stats: DeveloperStat[];
  complexity_trends: ComplexityTrend[];
}

export interface SearchResult {
  commits: Commit[];
  bugs: Bug[];
  total_commits: number;
  total_bugs: number;
}
