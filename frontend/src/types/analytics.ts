// Execution status types
export type ExecutionStatus =
  | 'pending'
  | 'running'
  | 'success'
  | 'failure'
  | 'timeout'
  | 'cancelled';

// Execution trace step types
export type ExecutionTraceStepType =
  | 'thought'
  | 'action'
  | 'observation'
  | 'agent_invoke'
  | 'tool_call'
  | 'final_answer';

// Budget types
export type BudgetAlertType = 'warning' | 'hard_stop';
export type BudgetScope = 'user' | 'agent' | 'flow' | 'global';

// Token usage for a single component
export interface TokenUsage {
  id: string;
  execution_id: string;
  component: string;
  step_number?: number;
  input_tokens: number;
  output_tokens: number;
  model?: string;
  cost_usd: string;
  created_at: string;
}

// Execution trace step
export interface ExecutionTrace {
  id: string;
  execution_id: string;
  step_number: number;
  step_type: ExecutionTraceStepType;
  content?: string;
  invoked_agent_id?: string;
  invoked_agent_name?: string;
  timestamp: string;
  duration_ms: number;
  input_tokens?: number;
  output_tokens?: number;
}

// Full execution details
export interface AgentExecution {
  id: string;
  request_id: string;
  session_id: string;
  agent_id?: string;
  agent_type?: string;
  agent_name?: string;
  user_id?: string;
  model_config_id?: string;
  model_name?: string;
  started_at: string;
  completed_at?: string;
  status: ExecutionStatus;
  error_message?: string;
  error_type?: string;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  execution_time_ms: number;
  llm_time_ms?: number;
  cost_usd: string;
  parent_execution_id?: string;
  query_preview?: string;
  created_at: string;
  updated_at: string;
  traces?: ExecutionTrace[];
  token_usages?: TokenUsage[];
}

// Lightweight execution summary for list views
export interface AgentExecutionSummary {
  id: string;
  request_id: string;
  session_id: string;
  agent_name?: string;
  agent_type?: string;
  model_name?: string;
  status: ExecutionStatus;
  execution_time_ms: number;
  total_tokens: number;
  cost_usd: string;
  started_at: string;
  completed_at?: string;
  query_preview?: string;
}

// Paginated executions response
export interface PaginatedExecutions {
  items: AgentExecutionSummary[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// Top agent by usage
export interface TopAgent {
  agent_id?: string;
  agent_name: string;
  agent_type?: string;
  execution_count: number;
  success_count: number;
  failure_count: number;
  success_rate: number;
  avg_execution_time_ms: number;
  total_tokens: number;
  total_cost_usd: string;
}

// Cost breakdown
export interface CostBreakdown {
  name: string;
  category: string;
  total_cost_usd: string;
  percentage: number;
  execution_count: number;
  total_tokens: number;
}

// Time series data point
export interface TimeSeriesDataPoint {
  timestamp: string;
  value: number;
  label?: string;
}

// Analytics overview for dashboard
export interface AnalyticsOverview {
  total_executions: number;
  successful_executions: number;
  failed_executions: number;
  success_rate: number;
  avg_execution_time_ms: number;
  p50_execution_time_ms: number;
  p95_execution_time_ms: number;
  p99_execution_time_ms: number;
  total_input_tokens: number;
  total_output_tokens: number;
  total_tokens: number;
  total_cost_usd: string;
  estimated_monthly_cost_usd: string;
  executions_change_percent?: number;
  execution_time_change_percent?: number;
  success_rate_change_percent?: number;
  cost_change_percent?: number;
  active_agents_count: number;
  top_agents: TopAgent[];
  cost_by_model: CostBreakdown[];
  cost_by_agent: CostBreakdown[];
  execution_time_trend: TimeSeriesDataPoint[];
  executions_trend: TimeSeriesDataPoint[];
  cost_trend: TimeSeriesDataPoint[];
}

// Agent statistics
export interface AgentStats {
  agent_id?: string;
  agent_name: string;
  agent_type?: string;
  total_executions: number;
  successful_executions: number;
  failed_executions: number;
  timeout_executions: number;
  success_rate: number;
  avg_execution_time_ms: number;
  p50_execution_time_ms: number;
  p95_execution_time_ms: number;
  min_execution_time_ms: number;
  max_execution_time_ms: number;
  avg_input_tokens: number;
  avg_output_tokens: number;
  total_tokens: number;
  total_cost_usd: string;
  avg_cost_per_execution_usd: string;
  last_executed_at?: string;
  first_executed_at?: string;
  common_error_types: string[];
  execution_trend: TimeSeriesDataPoint[];
}

// Cost summary
export interface CostSummary {
  total_cost_usd: string;
  period_days: number;
  by_model: {
    model: string;
    cost_usd: string;
    execution_count: number;
    percentage: number;
  }[];
  by_agent: {
    agent_name: string;
    agent_id?: string;
    cost_usd: string;
    execution_count: number;
    percentage: number;
  }[];
}

// Cost forecast
export interface CostForecast {
  current_period_cost_usd: string;
  projected_monthly_cost_usd: string;
  projected_weekly_cost_usd: string;
  daily_average_cost_usd: string;
  cost_trend: 'increasing' | 'decreasing' | 'stable';
  trend_percentage: number;
  by_model: CostBreakdown[];
  by_agent: CostBreakdown[];
}

// Budget alert
export interface BudgetAlert {
  id: string;
  user_id: string;
  scope: BudgetScope;
  scope_id?: string;
  threshold_usd: string;
  period_days: number;
  alert_type: BudgetAlertType;
  alert_at_percentage: number;
  webhook_url?: string;
  email_notification: boolean;
  is_active: boolean;
  last_alert_sent_at?: string;
  current_spend_usd: string;
  created_at: string;
  updated_at: string;
}

// Budget alert creation
export interface BudgetAlertCreate {
  scope?: BudgetScope;
  scope_id?: string;
  threshold_usd: number;
  period_days?: number;
  alert_type?: BudgetAlertType;
  alert_at_percentage?: number;
  webhook_url?: string;
  email_notification?: boolean;
}

// Budget alert update
export interface BudgetAlertUpdate {
  threshold_usd?: number;
  period_days?: number;
  alert_type?: BudgetAlertType;
  alert_at_percentage?: number;
  webhook_url?: string;
  email_notification?: boolean;
  is_active?: boolean;
}

// Model comparison
export interface ModelComparison {
  model_name: string;
  execution_count: number;
  success_count: number;
  success_rate: number;
  avg_execution_time_ms: number;
  avg_tokens: number;
  total_tokens: number;
  total_cost_usd: string;
}
