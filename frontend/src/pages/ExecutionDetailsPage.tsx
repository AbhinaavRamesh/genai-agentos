import { useState, useEffect } from 'react';
import type { FC } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Clock,
  Coins,
  CheckCircle,
  XCircle,
  AlertCircle,
  Brain,
  Zap,
  Eye,
  MessageSquare,
  Bot,
} from 'lucide-react';

import { MainLayout } from '@/components/layout/MainLayout';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { analyticsService } from '@/services/analyticsService';
import {
  AgentExecution,
  ExecutionTrace,
  TokenUsage,
  ExecutionTraceStepType,
} from '@/types/analytics';

interface TimelineStepProps {
  step: ExecutionTrace;
  isLast: boolean;
}

const TimelineStep: FC<TimelineStepProps> = ({ step, isLast }) => {
  const getStepIcon = (stepType: ExecutionTraceStepType) => {
    switch (stepType) {
      case 'thought':
        return <Brain className="w-4 h-4" />;
      case 'action':
        return <Zap className="w-4 h-4" />;
      case 'observation':
        return <Eye className="w-4 h-4" />;
      case 'agent_invoke':
        return <Bot className="w-4 h-4" />;
      case 'tool_call':
        return <MessageSquare className="w-4 h-4" />;
      case 'final_answer':
        return <CheckCircle className="w-4 h-4" />;
      default:
        return <AlertCircle className="w-4 h-4" />;
    }
  };

  const getStepColor = (stepType: ExecutionTraceStepType) => {
    switch (stepType) {
      case 'thought':
        return 'bg-blue-100 text-blue-700 border-blue-200';
      case 'action':
        return 'bg-purple-100 text-purple-700 border-purple-200';
      case 'observation':
        return 'bg-green-100 text-green-700 border-green-200';
      case 'agent_invoke':
        return 'bg-orange-100 text-orange-700 border-orange-200';
      case 'tool_call':
        return 'bg-yellow-100 text-yellow-700 border-yellow-200';
      case 'final_answer':
        return 'bg-emerald-100 text-emerald-700 border-emerald-200';
      default:
        return 'bg-gray-100 text-gray-700 border-gray-200';
    }
  };

  return (
    <div className="flex gap-4">
      {/* Timeline line */}
      <div className="flex flex-col items-center">
        <div
          className={`w-8 h-8 rounded-full flex items-center justify-center ${getStepColor(step.step_type)}`}
        >
          {getStepIcon(step.step_type)}
        </div>
        {!isLast && <div className="w-0.5 flex-1 bg-gray-200 min-h-8" />}
      </div>

      {/* Step content */}
      <div className="flex-1 pb-6">
        <div className="flex items-center gap-2 mb-2">
          <span
            className={`px-2 py-0.5 rounded text-xs font-medium ${getStepColor(step.step_type)}`}
          >
            {step.step_type.replace('_', ' ').toUpperCase()}
          </span>
          <span className="text-xs text-gray-500">Step {step.step_number}</span>
          <span className="text-xs text-gray-400">|</span>
          <span className="text-xs text-gray-500">{step.duration_ms}ms</span>
          {step.input_tokens !== undefined && step.output_tokens !== undefined && (
            <>
              <span className="text-xs text-gray-400">|</span>
              <span className="text-xs text-gray-500">
                {step.input_tokens} / {step.output_tokens} tokens
              </span>
            </>
          )}
        </div>

        {step.invoked_agent_name && (
          <div className="mb-2 text-sm font-medium text-gray-700">
            Invoked: {step.invoked_agent_name}
          </div>
        )}

        {step.content && (
          <div className="bg-gray-50 rounded-lg p-3 text-sm text-gray-700 whitespace-pre-wrap font-mono">
            {step.content}
          </div>
        )}

        <div className="mt-2 text-xs text-gray-400">
          {new Date(step.timestamp).toLocaleString()}
        </div>
      </div>
    </div>
  );
};

interface TokenUsageTableProps {
  tokenUsages: TokenUsage[];
}

const TokenUsageTable: FC<TokenUsageTableProps> = ({ tokenUsages }) => {
  const totalInput = tokenUsages.reduce((sum, t) => sum + t.input_tokens, 0);
  const totalOutput = tokenUsages.reduce((sum, t) => sum + t.output_tokens, 0);
  const totalCost = tokenUsages.reduce((sum, t) => sum + parseFloat(t.cost_usd), 0);

  return (
    <div className="bg-white rounded-lg shadow border border-gray-100 overflow-hidden">
      <div className="px-6 py-4 border-b border-gray-100">
        <h3 className="text-lg font-semibold text-gray-900">Token Usage Breakdown</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Component
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Model
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Input Tokens
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Output Tokens
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Cost
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {tokenUsages.map((usage) => (
              <tr key={usage.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {usage.component}
                  {usage.step_number !== null && (
                    <span className="text-gray-400 ml-1">(step {usage.step_number})</span>
                  )}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {usage.model || 'N/A'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-900">
                  {usage.input_tokens.toLocaleString()}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-900">
                  {usage.output_tokens.toLocaleString()}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-900">
                  ${parseFloat(usage.cost_usd).toFixed(6)}
                </td>
              </tr>
            ))}
            <tr className="bg-gray-50 font-semibold">
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900" colSpan={2}>
                Total
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-900">
                {totalInput.toLocaleString()}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-900">
                {totalOutput.toLocaleString()}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-900">
                ${totalCost.toFixed(6)}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
};

const ExecutionDetailsPage: FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [execution, setExecution] = useState<AgentExecution | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchExecution = async () => {
      if (!id) return;

      setLoading(true);
      setError(null);
      try {
        const data = await analyticsService.getExecutionDetails(id);
        setExecution(data);
      } catch (err) {
        setError('Failed to load execution details');
        console.error('Error loading execution:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchExecution();
  }, [id]);

  const getStatusBadge = (status: string) => {
    const statusConfig: Record<
      string,
      { bg: string; text: string; icon: React.ReactNode }
    > = {
      success: {
        bg: 'bg-green-100',
        text: 'text-green-800',
        icon: <CheckCircle className="w-4 h-4" />,
      },
      failure: {
        bg: 'bg-red-100',
        text: 'text-red-800',
        icon: <XCircle className="w-4 h-4" />,
      },
      pending: {
        bg: 'bg-yellow-100',
        text: 'text-yellow-800',
        icon: <Clock className="w-4 h-4" />,
      },
      running: {
        bg: 'bg-blue-100',
        text: 'text-blue-800',
        icon: <Clock className="w-4 h-4 animate-spin" />,
      },
      timeout: {
        bg: 'bg-orange-100',
        text: 'text-orange-800',
        icon: <AlertCircle className="w-4 h-4" />,
      },
      cancelled: {
        bg: 'bg-gray-100',
        text: 'text-gray-800',
        icon: <XCircle className="w-4 h-4" />,
      },
    };
    const config = statusConfig[status] || statusConfig.pending;
    return (
      <span
        className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-medium ${config.bg} ${config.text}`}
      >
        {config.icon}
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </span>
    );
  };

  return (
    <MainLayout currentPage="Execution Details">
      <div className="p-6 space-y-6">
        {/* Header */}
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="sm" onClick={() => navigate('/analytics')}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Analytics
          </Button>
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

        {!loading && !error && execution && (
          <>
            {/* Execution Header */}
            <div className="bg-white rounded-lg shadow border border-gray-100 p-6">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h1 className="text-xl font-bold text-gray-900 mb-2">
                    {execution.query_preview || 'Execution Details'}
                  </h1>
                  <div className="flex items-center gap-4 text-sm text-gray-500">
                    <span>Request: {execution.request_id.slice(0, 8)}...</span>
                    <span>Session: {execution.session_id.slice(0, 8)}...</span>
                    <span>{new Date(execution.started_at).toLocaleString()}</span>
                  </div>
                </div>
                {getStatusBadge(execution.status)}
              </div>

              {/* Summary Stats */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="flex items-center gap-2 text-gray-500 text-sm mb-1">
                    <Bot className="w-4 h-4" />
                    Agent
                  </div>
                  <p className="font-semibold text-gray-900">
                    {execution.agent_name || 'Unknown'}
                  </p>
                  <p className="text-xs text-gray-500">{execution.agent_type || 'N/A'}</p>
                </div>

                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="flex items-center gap-2 text-gray-500 text-sm mb-1">
                    <Clock className="w-4 h-4" />
                    Duration
                  </div>
                  <p className="font-semibold text-gray-900">
                    {(execution.execution_time_ms / 1000).toFixed(2)}s
                  </p>
                  {execution.llm_time_ms && (
                    <p className="text-xs text-gray-500">
                      LLM: {(execution.llm_time_ms / 1000).toFixed(2)}s
                    </p>
                  )}
                </div>

                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="flex items-center gap-2 text-gray-500 text-sm mb-1">
                    <MessageSquare className="w-4 h-4" />
                    Tokens
                  </div>
                  <p className="font-semibold text-gray-900">
                    {execution.total_tokens.toLocaleString()}
                  </p>
                  <p className="text-xs text-gray-500">
                    In: {execution.input_tokens.toLocaleString()} / Out:{' '}
                    {execution.output_tokens.toLocaleString()}
                  </p>
                </div>

                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="flex items-center gap-2 text-gray-500 text-sm mb-1">
                    <Coins className="w-4 h-4" />
                    Cost
                  </div>
                  <p className="font-semibold text-gray-900">
                    ${parseFloat(execution.cost_usd).toFixed(6)}
                  </p>
                  <p className="text-xs text-gray-500">{execution.model_name || 'N/A'}</p>
                </div>
              </div>

              {/* Error Message */}
              {execution.error_message && (
                <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-4">
                  <div className="flex items-center gap-2 text-red-800 font-medium mb-1">
                    <XCircle className="w-4 h-4" />
                    Error: {execution.error_type || 'Unknown'}
                  </div>
                  <p className="text-red-700 text-sm">{execution.error_message}</p>
                </div>
              )}
            </div>

            {/* Tabs */}
            <Tabs defaultValue="timeline">
              <TabsList>
                <TabsTrigger value="timeline">Execution Timeline</TabsTrigger>
                <TabsTrigger value="tokens">Token Usage</TabsTrigger>
              </TabsList>

              <TabsContent value="timeline" className="mt-4">
                <div className="bg-white rounded-lg shadow border border-gray-100 p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-6">
                    ReAct Loop Timeline
                  </h3>
                  {execution.traces && execution.traces.length > 0 ? (
                    <div className="space-y-2">
                      {execution.traces
                        .sort((a, b) => a.step_number - b.step_number)
                        .map((trace, index) => (
                          <TimelineStep
                            key={trace.id}
                            step={trace}
                            isLast={index === execution.traces!.length - 1}
                          />
                        ))}
                    </div>
                  ) : (
                    <p className="text-gray-500 text-center py-8">
                      No trace data available for this execution
                    </p>
                  )}
                </div>
              </TabsContent>

              <TabsContent value="tokens" className="mt-4">
                {execution.token_usages && execution.token_usages.length > 0 ? (
                  <TokenUsageTable tokenUsages={execution.token_usages} />
                ) : (
                  <div className="bg-white rounded-lg shadow border border-gray-100 p-8 text-center text-gray-500">
                    No token usage data available
                  </div>
                )}
              </TabsContent>
            </Tabs>
          </>
        )}
      </div>
    </MainLayout>
  );
};

export default ExecutionDetailsPage;
