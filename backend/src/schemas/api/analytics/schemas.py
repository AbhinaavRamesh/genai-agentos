from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from src.utils.enums import (
    BudgetAlertType,
    BudgetScope,
    ExecutionStatus,
    ExecutionTraceStepType,
)


class AgentExecutionCreate(BaseModel):
    """Create a new agent execution record."""

    request_id: UUID
    session_id: UUID
    agent_id: Optional[UUID] = None
    agent_type: Optional[str] = None
    agent_name: Optional[str] = None
    user_id: Optional[UUID] = None
    model_config_id: Optional[UUID] = None
    model_name: Optional[str] = None
    parent_execution_id: Optional[UUID] = None
    query_preview: Optional[str] = None
    status: ExecutionStatus = ExecutionStatus.pending


class AgentExecutionUpdate(BaseModel):
    """Update an agent execution record."""

    completed_at: Optional[datetime] = None
    status: Optional[ExecutionStatus] = None
    error_message: Optional[str] = None
    error_type: Optional[str] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    execution_time_ms: Optional[int] = None
    llm_time_ms: Optional[int] = None
    cost_usd: Optional[Decimal] = None


class TokenUsageCreate(BaseModel):
    """Create a token usage record."""

    execution_id: UUID
    component: str
    step_number: Optional[int] = None
    input_tokens: int = 0
    output_tokens: int = 0
    model: Optional[str] = None
    cost_usd: Decimal = Decimal("0.000000")


class ExecutionTraceCreate(BaseModel):
    """Create an execution trace step."""

    execution_id: UUID
    step_number: int
    step_type: ExecutionTraceStepType
    content: Optional[str] = None
    invoked_agent_id: Optional[UUID] = None
    invoked_agent_name: Optional[str] = None
    duration_ms: int = 0
    input_tokens: Optional[int] = 0
    output_tokens: Optional[int] = 0


class BudgetAlertCreate(BaseModel):
    """Create a budget alert."""

    scope: BudgetScope = BudgetScope.user
    scope_id: Optional[UUID] = None
    threshold_usd: Decimal
    period_days: int = 30
    alert_type: BudgetAlertType = BudgetAlertType.warning
    alert_at_percentage: int = Field(default=80, ge=1, le=100)
    webhook_url: Optional[str] = None
    email_notification: bool = True


class BudgetAlertUpdate(BaseModel):
    """Update a budget alert."""

    threshold_usd: Optional[Decimal] = None
    period_days: Optional[int] = None
    alert_type: Optional[BudgetAlertType] = None
    alert_at_percentage: Optional[int] = Field(default=None, ge=1, le=100)
    webhook_url: Optional[str] = None
    email_notification: Optional[bool] = None
    is_active: Optional[bool] = None


class AnalyticsQueryParams(BaseModel):
    """Query parameters for analytics endpoints."""

    # Time range
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    period: Optional[str] = "24h"  # 24h, 7d, 30d, custom

    # Filters
    agent_id: Optional[UUID] = None
    agent_type: Optional[str] = None
    model_name: Optional[str] = None
    status: Optional[ExecutionStatus] = None

    # Pagination
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)

    # Sorting
    sort_by: Optional[str] = "started_at"
    sort_order: Optional[str] = "desc"  # asc, desc


class ExportFormat(BaseModel):
    """Export format specification."""

    format: str = "json"  # json, csv
    include_traces: bool = False
    include_token_details: bool = False
