import { apiService } from './apiService';
import {
  AnalyticsOverview,
  PaginatedExecutions,
  AgentExecution,
  AgentStats,
  CostSummary,
  CostForecast,
  BudgetAlert,
  BudgetAlertCreate,
  BudgetAlertUpdate,
  ModelComparison,
} from '../types/analytics';

export interface AnalyticsQueryParams {
  period?: '24h' | '7d' | '30d' | '90d';
  start_date?: string;
  end_date?: string;
  agent_id?: string;
  agent_type?: string;
  model_name?: string;
  status?: string;
  page?: number;
  page_size?: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

export const analyticsService = {
  /**
   * Get analytics overview for the dashboard
   */
  async getOverview(params: AnalyticsQueryParams = {}): Promise<AnalyticsOverview> {
    const queryParams: Record<string, string> = {};
    if (params.period) queryParams.period = params.period;
    if (params.start_date) queryParams.start_date = params.start_date;
    if (params.end_date) queryParams.end_date = params.end_date;

    const response = await apiService.get<AnalyticsOverview>('/api/analytics/overview', {
      params: queryParams,
    });
    return response.data;
  },

  /**
   * Get paginated list of executions
   */
  async getExecutions(params: AnalyticsQueryParams = {}): Promise<PaginatedExecutions> {
    const queryParams: Record<string, string> = {};
    if (params.period) queryParams.period = params.period;
    if (params.start_date) queryParams.start_date = params.start_date;
    if (params.end_date) queryParams.end_date = params.end_date;
    if (params.agent_id) queryParams.agent_id = params.agent_id;
    if (params.agent_type) queryParams.agent_type = params.agent_type;
    if (params.model_name) queryParams.model_name = params.model_name;
    if (params.status) queryParams.status = params.status;
    if (params.page) queryParams.page = params.page.toString();
    if (params.page_size) queryParams.page_size = params.page_size.toString();
    if (params.sort_by) queryParams.sort_by = params.sort_by;
    if (params.sort_order) queryParams.sort_order = params.sort_order;

    const response = await apiService.get<PaginatedExecutions>('/api/analytics/executions', {
      params: queryParams,
    });
    return response.data;
  },

  /**
   * Get detailed information about a specific execution
   */
  async getExecutionDetails(executionId: string): Promise<AgentExecution> {
    const response = await apiService.get<AgentExecution>(
      `/api/analytics/executions/${executionId}`,
    );
    return response.data;
  },

  /**
   * Get statistics for a specific agent
   */
  async getAgentStats(
    agentId: string,
    params: AnalyticsQueryParams = {},
  ): Promise<AgentStats> {
    const queryParams: Record<string, string> = {};
    if (params.period) queryParams.period = params.period;
    if (params.start_date) queryParams.start_date = params.start_date;
    if (params.end_date) queryParams.end_date = params.end_date;

    const response = await apiService.get<AgentStats>(
      `/api/analytics/agents/${agentId}/stats`,
      { params: queryParams },
    );
    return response.data;
  },

  /**
   * Get cost breakdown summary
   */
  async getCostSummary(params: AnalyticsQueryParams = {}): Promise<CostSummary> {
    const queryParams: Record<string, string> = {};
    if (params.period) queryParams.period = params.period;
    if (params.start_date) queryParams.start_date = params.start_date;
    if (params.end_date) queryParams.end_date = params.end_date;

    const response = await apiService.get<CostSummary>('/api/analytics/costs/summary', {
      params: queryParams,
    });
    return response.data;
  },

  /**
   * Get cost forecast
   */
  async getCostForecast(): Promise<CostForecast> {
    const response = await apiService.get<CostForecast>('/api/analytics/costs/forecast');
    return response.data;
  },

  /**
   * Get all budget alerts
   */
  async getBudgetAlerts(): Promise<BudgetAlert[]> {
    const response = await apiService.get<BudgetAlert[]>('/api/analytics/budgets');
    return response.data;
  },

  /**
   * Create a new budget alert
   */
  async createBudgetAlert(alert: BudgetAlertCreate): Promise<BudgetAlert> {
    const response = await apiService.post<BudgetAlert>('/api/analytics/budgets', alert);
    return response.data;
  },

  /**
   * Update a budget alert
   */
  async updateBudgetAlert(alertId: string, update: BudgetAlertUpdate): Promise<BudgetAlert> {
    const response = await apiService.patch<BudgetAlert>(
      `/api/analytics/budgets/${alertId}`,
      update,
    );
    return response.data;
  },

  /**
   * Delete a budget alert
   */
  async deleteBudgetAlert(alertId: string): Promise<void> {
    await apiService.delete(`/api/analytics/budgets/${alertId}`);
  },

  /**
   * Compare model performance
   */
  async compareModels(params: AnalyticsQueryParams = {}): Promise<ModelComparison[]> {
    const queryParams: Record<string, string> = {};
    if (params.period) queryParams.period = params.period;
    if (params.start_date) queryParams.start_date = params.start_date;
    if (params.end_date) queryParams.end_date = params.end_date;

    const response = await apiService.get<ModelComparison[]>(
      '/api/analytics/comparison/models',
      { params: queryParams },
    );
    return response.data;
  },

  /**
   * Export analytics data
   */
  async exportData(
    format: 'json' | 'csv' = 'json',
    params: AnalyticsQueryParams = {},
  ): Promise<Blob> {
    const queryParams: Record<string, string> = { format };
    if (params.period) queryParams.period = params.period;
    if (params.start_date) queryParams.start_date = params.start_date;
    if (params.end_date) queryParams.end_date = params.end_date;

    const token = localStorage.getItem('token');
    if (!token) {
      throw new Error('Authentication token is missing. Please log in again.');
    }

    const response = await fetch(
      `/api/analytics/export?${new URLSearchParams(queryParams).toString()}`,
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      },
    );

    if (!response.ok) {
      throw new Error('Export failed');
    }

    return response.blob();
  },
};
