import { useState, useEffect, useCallback } from 'react';
import type { FC } from 'react';
import {
  TrendingUp,
  TrendingDown,
  Minus,
  Clock,
  CheckCircle,
  XCircle,
  Coins,
  Activity,
  Download,
  RefreshCw,
} from 'lucide-react';

import { MainLayout } from '@/components/layout/MainLayout';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { analyticsService, AnalyticsQueryParams } from '@/services/analyticsService';
import {
  AnalyticsOverview,
  PaginatedExecutions,
  TopAgent,
  CostBreakdown,
  AgentExecutionSummary,
} from '@/types/analytics';

type Period = '24h' | '7d' | '30d' | '90d';

interface StatCardProps {
  title: string;
  value: string | number;
  change?: number | null;
  icon: React.ReactNode;
  trend?: 'up' | 'down' | 'neutral';
  subtitle?: string;
}

const StatCard: FC<StatCardProps> = ({ title, value, change, icon, trend, subtitle }) => {
  const getTrendIcon = () => {
    if (trend === 'up') return <TrendingUp className="w-4 h-4 text-green-500" />;
    if (trend === 'down') return <TrendingDown className="w-4 h-4 text-red-500" />;
    return <Minus className="w-4 h-4 text-gray-400" />;
  };

  const getChangeColor = () => {
    if (change === null || change === undefined) return 'text-gray-500';
    if (change > 0) return 'text-green-500';
    if (change < 0) return 'text-red-500';
    return 'text-gray-500';
  };

  return (
    <div className="bg-white rounded-lg shadow p-6 border border-gray-100">
      <div className="flex items-center justify-between mb-4">
        <span className="text-gray-500 text-sm font-medium">{title}</span>
        <div className="p-2 bg-gray-50 rounded-lg">{icon}</div>
      </div>
      <div className="flex items-end justify-between">
        <div>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
          {subtitle && <p className="text-xs text-gray-500 mt-1">{subtitle}</p>}
        </div>
        {change !== null && change !== undefined && (
          <div className={`flex items-center gap-1 ${getChangeColor()}`}>
            {getTrendIcon()}
            <span className="text-sm font-medium">
              {change > 0 ? '+' : ''}
              {change.toFixed(1)}%
            </span>
          </div>
        )}
      </div>
    </div>
  );
};

interface TopAgentsTableProps {
  agents: TopAgent[];
}

const TopAgentsTable: FC<TopAgentsTableProps> = ({ agents }) => {
  return (
    <div className="bg-white rounded-lg shadow border border-gray-100 overflow-hidden">
      <div className="px-6 py-4 border-b border-gray-100">
        <h3 className="text-lg font-semibold text-gray-900">Top Agents by Usage</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Agent
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Executions
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Success Rate
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Avg Time
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Cost
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {agents.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-6 py-8 text-center text-gray-500">
                  No agent data available
                </td>
              </tr>
            ) : (
              agents.map((agent, index) => (
                <tr key={agent.agent_id || index} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="w-8 h-8 rounded-full bg-primary-accent/10 flex items-center justify-center text-primary-accent font-medium">
                        {index + 1}
                      </div>
                      <div className="ml-3">
                        <p className="text-sm font-medium text-gray-900">{agent.agent_name}</p>
                        <p className="text-xs text-gray-500">{agent.agent_type || 'unknown'}</p>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-900">
                    {agent.execution_count.toLocaleString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right">
                    <span
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        agent.success_rate >= 90
                          ? 'bg-green-100 text-green-800'
                          : agent.success_rate >= 70
                            ? 'bg-yellow-100 text-yellow-800'
                            : 'bg-red-100 text-red-800'
                      }`}
                    >
                      {agent.success_rate.toFixed(1)}%
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-500">
                    {(agent.avg_execution_time_ms / 1000).toFixed(2)}s
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-900">
                    ${parseFloat(agent.total_cost_usd).toFixed(4)}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

interface CostBreakdownChartProps {
  data: CostBreakdown[];
  title: string;
}

const CostBreakdownChart: FC<CostBreakdownChartProps> = ({ data, title }) => {
  const colors = [
    'bg-blue-500',
    'bg-green-500',
    'bg-yellow-500',
    'bg-purple-500',
    'bg-pink-500',
    'bg-indigo-500',
    'bg-orange-500',
  ];

  return (
    <div className="bg-white rounded-lg shadow border border-gray-100 p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
      {data.length === 0 ? (
        <p className="text-gray-500 text-center py-8">No cost data available</p>
      ) : (
        <div className="space-y-4">
          {data.slice(0, 5).map((item, index) => (
            <div key={item.name} className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-700">{item.name}</span>
                <span className="text-gray-900 font-medium">
                  ${parseFloat(item.total_cost_usd).toFixed(4)} ({item.percentage.toFixed(1)}%)
                </span>
              </div>
              <div className="w-full bg-gray-100 rounded-full h-2">
                <div
                  className={`${colors[index % colors.length]} h-2 rounded-full transition-all duration-500`}
                  style={{ width: `${item.percentage}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

interface RecentExecutionsTableProps {
  executions: AgentExecutionSummary[];
  onViewDetails: (id: string) => void;
}

const RecentExecutionsTable: FC<RecentExecutionsTableProps> = ({
  executions,
  onViewDetails,
}) => {
  const getStatusBadge = (status: string) => {
    const statusConfig: Record<string, { bg: string; text: string }> = {
      success: { bg: 'bg-green-100', text: 'text-green-800' },
      failure: { bg: 'bg-red-100', text: 'text-red-800' },
      pending: { bg: 'bg-yellow-100', text: 'text-yellow-800' },
      running: { bg: 'bg-blue-100', text: 'text-blue-800' },
      timeout: { bg: 'bg-orange-100', text: 'text-orange-800' },
      cancelled: { bg: 'bg-gray-100', text: 'text-gray-800' },
    };
    const config = statusConfig[status] || statusConfig.pending;
    return (
      <span
        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${config.bg} ${config.text}`}
      >
        {status}
      </span>
    );
  };

  return (
    <div className="bg-white rounded-lg shadow border border-gray-100 overflow-hidden">
      <div className="px-6 py-4 border-b border-gray-100">
        <h3 className="text-lg font-semibold text-gray-900">Recent Executions</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Query
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Agent
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Duration
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Tokens
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Cost
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Time
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {executions.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-6 py-8 text-center text-gray-500">
                  No executions found
                </td>
              </tr>
            ) : (
              executions.map((execution) => (
                <tr
                  key={execution.id}
                  className="hover:bg-gray-50 cursor-pointer"
                  onClick={() => onViewDetails(execution.id)}
                >
                  <td className="px-6 py-4">
                    <p className="text-sm text-gray-900 truncate max-w-xs">
                      {execution.query_preview || 'No query preview'}
                    </p>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <p className="text-sm text-gray-900">{execution.agent_name || 'Unknown'}</p>
                    <p className="text-xs text-gray-500">{execution.model_name || 'No model'}</p>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {getStatusBadge(execution.status)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-500">
                    {(execution.execution_time_ms / 1000).toFixed(2)}s
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-500">
                    {execution.total_tokens.toLocaleString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-900">
                    ${parseFloat(execution.cost_usd).toFixed(4)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-500">
                    {new Date(execution.started_at).toLocaleTimeString()}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

const AnalyticsPage: FC = () => {
  const [period, setPeriod] = useState<Period>('24h');
  const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
  const [executions, setExecutions] = useState<PaginatedExecutions | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: AnalyticsQueryParams = { period };
      const [overviewData, executionsData] = await Promise.all([
        analyticsService.getOverview(params),
        analyticsService.getExecutions({ ...params, page_size: 10 }),
      ]);
      setOverview(overviewData);
      setExecutions(executionsData);
    } catch (err) {
      setError('Failed to load analytics data');
      console.error('Analytics error:', err);
    } finally {
      setLoading(false);
    }
  }, [period]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleExport = async (format: 'json' | 'csv') => {
    try {
      const blob = await analyticsService.exportData(format, { period });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `analytics_export.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      console.error('Export failed:', err);
    }
  };

  const handleViewDetails = (executionId: string) => {
    // Navigate to execution details
    window.location.href = `/analytics/executions/${executionId}`;
  };

  const formatNumber = (num: number): string => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toString();
  };

  const formatTime = (ms: number): string => {
    if (ms >= 1000) return `${(ms / 1000).toFixed(2)}s`;
    return `${ms}ms`;
  };

  const actionItems = (
    <div className="flex items-center gap-2">
      <Button variant="outline" size="sm" onClick={() => fetchData()}>
        <RefreshCw className="w-4 h-4 mr-2" />
        Refresh
      </Button>
      <Button variant="outline" size="sm" onClick={() => handleExport('csv')}>
        <Download className="w-4 h-4 mr-2" />
        Export CSV
      </Button>
    </div>
  );

  return (
    <MainLayout currentPage="Analytics" actionItems={actionItems}>
      <div className="p-6 space-y-6">
        {/* Period Selector */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Agent Analytics</h1>
            <p className="text-gray-500">Monitor performance, costs, and usage patterns</p>
          </div>
          <Tabs value={period} onValueChange={(v) => setPeriod(v as Period)}>
            <TabsList>
              <TabsTrigger value="24h">24h</TabsTrigger>
              <TabsTrigger value="7d">7d</TabsTrigger>
              <TabsTrigger value="30d">30d</TabsTrigger>
              <TabsTrigger value="90d">90d</TabsTrigger>
            </TabsList>
          </Tabs>
        </div>

        {loading && (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-accent"></div>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
            {error}
          </div>
        )}

        {!loading && !error && overview && (
          <>
            {/* Summary Stats */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <StatCard
                title="Total Executions"
                value={formatNumber(overview.total_executions)}
                change={overview.executions_change_percent}
                trend={
                  overview.executions_change_percent
                    ? overview.executions_change_percent > 0
                      ? 'up'
                      : 'down'
                    : 'neutral'
                }
                icon={<Activity className="w-5 h-5 text-blue-500" />}
                subtitle={`${overview.successful_executions} successful`}
              />
              <StatCard
                title="Success Rate"
                value={`${overview.success_rate.toFixed(1)}%`}
                change={overview.success_rate_change_percent}
                trend={
                  overview.success_rate_change_percent
                    ? overview.success_rate_change_percent > 0
                      ? 'up'
                      : 'down'
                    : 'neutral'
                }
                icon={<CheckCircle className="w-5 h-5 text-green-500" />}
                subtitle={`${overview.failed_executions} failures`}
              />
              <StatCard
                title="Avg Response Time"
                value={formatTime(overview.avg_execution_time_ms)}
                change={
                  overview.execution_time_change_percent
                    ? -overview.execution_time_change_percent
                    : null
                }
                trend={
                  overview.execution_time_change_percent
                    ? overview.execution_time_change_percent < 0
                      ? 'up'
                      : 'down'
                    : 'neutral'
                }
                icon={<Clock className="w-5 h-5 text-yellow-500" />}
                subtitle={`P95: ${formatTime(overview.p95_execution_time_ms)}`}
              />
              <StatCard
                title="Total Cost"
                value={`$${parseFloat(overview.total_cost_usd).toFixed(2)}`}
                change={overview.cost_change_percent}
                trend={
                  overview.cost_change_percent
                    ? overview.cost_change_percent > 0
                      ? 'up'
                      : 'down'
                    : 'neutral'
                }
                icon={<Coins className="w-5 h-5 text-purple-500" />}
                subtitle={`Est. monthly: $${parseFloat(overview.estimated_monthly_cost_usd).toFixed(2)}`}
              />
            </div>

            {/* Token Usage Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-white rounded-lg shadow border border-gray-100 p-6">
                <h3 className="text-sm font-medium text-gray-500 mb-2">Total Tokens</h3>
                <p className="text-3xl font-bold text-gray-900">
                  {formatNumber(overview.total_tokens)}
                </p>
                <div className="mt-4 flex gap-4 text-sm">
                  <div>
                    <span className="text-gray-500">Input:</span>{' '}
                    <span className="font-medium">
                      {formatNumber(overview.total_input_tokens)}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-500">Output:</span>{' '}
                    <span className="font-medium">
                      {formatNumber(overview.total_output_tokens)}
                    </span>
                  </div>
                </div>
              </div>
              <div className="bg-white rounded-lg shadow border border-gray-100 p-6">
                <h3 className="text-sm font-medium text-gray-500 mb-2">Active Agents</h3>
                <p className="text-3xl font-bold text-gray-900">
                  {overview.active_agents_count}
                </p>
                <p className="mt-4 text-sm text-gray-500">Unique agents used in this period</p>
              </div>
              <div className="bg-white rounded-lg shadow border border-gray-100 p-6">
                <h3 className="text-sm font-medium text-gray-500 mb-2">Response Time Percentiles</h3>
                <div className="space-y-2 mt-4">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">P50</span>
                    <span className="font-medium">
                      {formatTime(overview.p50_execution_time_ms)}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">P95</span>
                    <span className="font-medium">
                      {formatTime(overview.p95_execution_time_ms)}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">P99</span>
                    <span className="font-medium">
                      {formatTime(overview.p99_execution_time_ms)}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Top Agents and Cost Breakdown */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <TopAgentsTable agents={overview.top_agents} />
              <CostBreakdownChart data={overview.cost_by_model} title="Cost by Model" />
            </div>

            {/* Recent Executions */}
            {executions && (
              <RecentExecutionsTable
                executions={executions.items}
                onViewDetails={handleViewDetails}
              />
            )}
          </>
        )}
      </div>
    </MainLayout>
  );
};

export default AnalyticsPage;
