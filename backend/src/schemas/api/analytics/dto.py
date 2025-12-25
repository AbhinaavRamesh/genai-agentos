from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field

from src.utils.enums import (
    BudgetAlertType,
    BudgetScope,
    ExecutionStatus,
    ExecutionTraceStepType,
)


class TokenUsageDTO(BaseModel):
    """Token usage details for a single component."""

    id: str
    execution_id: str
    component: str
    step_number: Optional[int] = None
    input_tokens: int = 0
    output_tokens: int = 0
    model: Optional[str] = None
    cost_usd: Decimal = Decimal("0.000000")
    created_at: datetime

    class Config:
        from_attributes = True


class ExecutionTraceDTO(BaseModel):
    """Step-by-step trace entry."""

    id: str
    execution_id: str
    step_number: int
    step_type: ExecutionTraceStepType
    content: Optional[str] = None
    invoked_agent_id: Optional[str] = None
    invoked_agent_name: Optional[str] = None
    timestamp: datetime
    duration_ms: int = 0
    input_tokens: Optional[int] = 0
    output_tokens: Optional[int] = 0

    class Config:
        from_attributes = True


class AgentExecutionDTO(BaseModel):
    """Detailed execution information."""

    id: str
    request_id: str
    session_id: str
    agent_id: Optional[str] = None
    agent_type: Optional[str] = None
    agent_name: Optional[str] = None
    user_id: Optional[str] = None
    model_config_id: Optional[str] = None
    model_name: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: ExecutionStatus
    error_message: Optional[str] = None
    error_type: Optional[str] = None
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    execution_time_ms: int = 0
    llm_time_ms: Optional[int] = 0
    cost_usd: Decimal = Decimal("0.000000")
    parent_execution_id: Optional[str] = None
    query_preview: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    # Related data (optional, loaded on detail view)
    traces: Optional[List[ExecutionTraceDTO]] = None
    token_usages: Optional[List[TokenUsageDTO]] = None

    class Config:
        from_attributes = True


class AgentExecutionSummaryDTO(BaseModel):
    """Lightweight execution summary for list views."""

    id: str
    request_id: str
    session_id: str
    agent_name: Optional[str] = None
    agent_type: Optional[str] = None
    model_name: Optional[str] = None
    status: ExecutionStatus
    execution_time_ms: int = 0
    total_tokens: int = 0
    cost_usd: Decimal = Decimal("0.000000")
    started_at: datetime
    completed_at: Optional[datetime] = None
    query_preview: Optional[str] = None

    class Config:
        from_attributes = True


class BudgetAlertDTO(BaseModel):
    """Budget alert configuration."""

    id: str
    user_id: str
    scope: BudgetScope
    scope_id: Optional[str] = None
    threshold_usd: Decimal
    period_days: int = 30
    alert_type: BudgetAlertType
    alert_at_percentage: int = 80
    webhook_url: Optional[str] = None
    email_notification: bool = True
    is_active: bool = True
    last_alert_sent_at: Optional[datetime] = None
    current_spend_usd: Decimal = Decimal("0.00")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TopAgentDTO(BaseModel):
    """Top agent by usage."""

    agent_id: Optional[str] = None
    agent_name: str
    agent_type: Optional[str] = None
    execution_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    success_rate: float = 0.0
    avg_execution_time_ms: float = 0.0
    total_tokens: int = 0
    total_cost_usd: Decimal = Decimal("0.00")


class CostBreakdownDTO(BaseModel):
    """Cost breakdown by model or agent."""

    name: str
    category: str  # 'model' or 'agent'
    total_cost_usd: Decimal = Decimal("0.00")
    percentage: float = 0.0
    execution_count: int = 0
    total_tokens: int = 0


class AnalyticsTimeSeriesDataPoint(BaseModel):
    """Single data point for time series charts."""

    timestamp: datetime
    value: float = 0.0
    label: Optional[str] = None


class AnalyticsOverviewDTO(BaseModel):
    """Dashboard overview statistics."""

    # Summary metrics
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    success_rate: float = 0.0

    # Execution time metrics
    avg_execution_time_ms: float = 0.0
    p50_execution_time_ms: float = 0.0
    p95_execution_time_ms: float = 0.0
    p99_execution_time_ms: float = 0.0

    # Token metrics
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_tokens: int = 0

    # Cost metrics
    total_cost_usd: Decimal = Decimal("0.00")
    estimated_monthly_cost_usd: Decimal = Decimal("0.00")

    # Comparison with previous period
    executions_change_percent: Optional[float] = None
    execution_time_change_percent: Optional[float] = None
    success_rate_change_percent: Optional[float] = None
    cost_change_percent: Optional[float] = None

    # Active resources
    active_agents_count: int = 0

    # Top agents
    top_agents: List[TopAgentDTO] = Field(default_factory=list)

    # Cost breakdown
    cost_by_model: List[CostBreakdownDTO] = Field(default_factory=list)
    cost_by_agent: List[CostBreakdownDTO] = Field(default_factory=list)

    # Time series data
    execution_time_trend: List[AnalyticsTimeSeriesDataPoint] = Field(default_factory=list)
    executions_trend: List[AnalyticsTimeSeriesDataPoint] = Field(default_factory=list)
    cost_trend: List[AnalyticsTimeSeriesDataPoint] = Field(default_factory=list)


class CostForecastDTO(BaseModel):
    """Cost forecast based on current usage patterns."""

    current_period_cost_usd: Decimal = Decimal("0.00")
    projected_monthly_cost_usd: Decimal = Decimal("0.00")
    projected_weekly_cost_usd: Decimal = Decimal("0.00")
    daily_average_cost_usd: Decimal = Decimal("0.00")

    # Trend
    cost_trend: str = "stable"  # increasing, decreasing, stable
    trend_percentage: float = 0.0

    # Breakdown projections
    by_model: List[CostBreakdownDTO] = Field(default_factory=list)
    by_agent: List[CostBreakdownDTO] = Field(default_factory=list)


class AgentStatsDTO(BaseModel):
    """Statistics for a specific agent."""

    agent_id: Optional[str] = None
    agent_name: str
    agent_type: Optional[str] = None

    # Execution metrics
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    timeout_executions: int = 0
    success_rate: float = 0.0

    # Timing
    avg_execution_time_ms: float = 0.0
    p50_execution_time_ms: float = 0.0
    p95_execution_time_ms: float = 0.0
    min_execution_time_ms: int = 0
    max_execution_time_ms: int = 0

    # Tokens
    avg_input_tokens: float = 0.0
    avg_output_tokens: float = 0.0
    total_tokens: int = 0

    # Cost
    total_cost_usd: Decimal = Decimal("0.00")
    avg_cost_per_execution_usd: Decimal = Decimal("0.00")

    # Usage pattern
    last_executed_at: Optional[datetime] = None
    first_executed_at: Optional[datetime] = None

    # Error analysis
    common_error_types: List[str] = Field(default_factory=list)

    # Time series
    execution_trend: List[AnalyticsTimeSeriesDataPoint] = Field(default_factory=list)


class PaginatedExecutionsDTO(BaseModel):
    """Paginated list of executions."""

    items: List[AgentExecutionSummaryDTO]
    total: int
    page: int
    page_size: int
    total_pages: int
