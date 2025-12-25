from datetime import datetime, timedelta
from typing import Annotated, List, Optional, Union
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
import csv
import io
import json

from src.auth.dependencies import CurrentUserDependency
from src.db.session import AsyncDBSession
from src.repositories.analytics import (
    agent_execution_repo,
    budget_alert_repo,
    execution_trace_repo,
    token_usage_repo,
)
from src.schemas.api.analytics.dto import (
    AgentExecutionDTO,
    AgentStatsDTO,
    AnalyticsOverviewDTO,
    BudgetAlertDTO,
    CostForecastDTO,
    ExecutionTraceDTO,
    PaginatedExecutionsDTO,
    TokenUsageDTO,
)
from src.schemas.api.analytics.schemas import (
    AnalyticsQueryParams,
    BudgetAlertCreate,
    BudgetAlertUpdate,
)
from src.utils.enums import ExecutionStatus

analytics_router = APIRouter(tags=["Analytics"], prefix="/analytics")


def parse_period(period: str) -> tuple[datetime, datetime]:
    """Parse period string into start and end dates."""
    now = datetime.utcnow()
    if period == "24h":
        return now - timedelta(hours=24), now
    elif period == "7d":
        return now - timedelta(days=7), now
    elif period == "30d":
        return now - timedelta(days=30), now
    elif period == "90d":
        return now - timedelta(days=90), now
    else:
        # Default to 24h
        return now - timedelta(hours=24), now


@analytics_router.get("/overview", response_model=AnalyticsOverviewDTO)
async def get_analytics_overview(
    db: AsyncDBSession,
    user: CurrentUserDependency,
    period: Annotated[str, Query(description="Time period: 24h, 7d, 30d, 90d")] = "24h",
    start_date: Annotated[Optional[datetime], Query()] = None,
    end_date: Annotated[Optional[datetime], Query()] = None,
) -> AnalyticsOverviewDTO:
    """
    Get analytics overview for the dashboard.

    Returns summary statistics including:
    - Total executions and success rate
    - Execution time metrics (avg, p50, p95, p99)
    - Token usage totals
    - Cost summary
    - Top agents by usage
    - Cost breakdown by model
    """
    if start_date and end_date:
        pass  # Use provided dates
    else:
        start_date, end_date = parse_period(period)

    return await agent_execution_repo.get_overview(
        db=db,
        user_id=str(user.id),
        start_date=start_date,
        end_date=end_date,
    )


@analytics_router.get("/executions", response_model=PaginatedExecutionsDTO)
async def list_executions(
    db: AsyncDBSession,
    user: CurrentUserDependency,
    period: Annotated[str, Query()] = "24h",
    start_date: Annotated[Optional[datetime], Query()] = None,
    end_date: Annotated[Optional[datetime], Query()] = None,
    agent_id: Annotated[Optional[UUID], Query()] = None,
    agent_type: Annotated[Optional[str], Query()] = None,
    model_name: Annotated[Optional[str], Query()] = None,
    status: Annotated[Optional[ExecutionStatus], Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    sort_by: Annotated[str, Query()] = "started_at",
    sort_order: Annotated[str, Query()] = "desc",
) -> PaginatedExecutionsDTO:
    """
    Get paginated list of agent executions.

    Supports filtering by:
    - Time period
    - Agent ID and type
    - Model name
    - Execution status
    """
    if start_date and end_date:
        pass
    else:
        start_date, end_date = parse_period(period)

    return await agent_execution_repo.list_paginated(
        db=db,
        user_id=str(user.id),
        agent_id=str(agent_id) if agent_id else None,
        agent_type=agent_type,
        model_name=model_name,
        status=status,
        start_date=start_date,
        end_date=end_date,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@analytics_router.get("/executions/{execution_id}", response_model=AgentExecutionDTO)
async def get_execution_details(
    db: AsyncDBSession,
    user: CurrentUserDependency,
    execution_id: UUID,
) -> AgentExecutionDTO:
    """
    Get detailed information about a specific execution.

    Includes:
    - Full execution metadata
    - Step-by-step trace
    - Token usage breakdown
    """
    execution = await agent_execution_repo.get_with_details(
        db=db, execution_id=str(execution_id)
    )

    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    # Check user access
    if execution.user_id and str(execution.user_id) != str(user.id):
        raise HTTPException(status_code=403, detail="Access denied")

    traces = [
        ExecutionTraceDTO(
            id=str(t.id),
            execution_id=str(t.execution_id),
            step_number=t.step_number,
            step_type=t.step_type,
            content=t.content,
            invoked_agent_id=str(t.invoked_agent_id) if t.invoked_agent_id else None,
            invoked_agent_name=t.invoked_agent_name,
            timestamp=t.timestamp,
            duration_ms=t.duration_ms,
            input_tokens=t.input_tokens,
            output_tokens=t.output_tokens,
        )
        for t in execution.traces
    ]

    token_usages = [
        TokenUsageDTO(
            id=str(tu.id),
            execution_id=str(tu.execution_id),
            component=tu.component,
            step_number=tu.step_number,
            input_tokens=tu.input_tokens,
            output_tokens=tu.output_tokens,
            model=tu.model,
            cost_usd=tu.cost_usd,
            created_at=tu.created_at,
        )
        for tu in execution.token_usages
    ]

    return AgentExecutionDTO(
        id=str(execution.id),
        request_id=str(execution.request_id),
        session_id=str(execution.session_id),
        agent_id=str(execution.agent_id) if execution.agent_id else None,
        agent_type=execution.agent_type,
        agent_name=execution.agent_name,
        user_id=str(execution.user_id) if execution.user_id else None,
        model_config_id=str(execution.model_config_id) if execution.model_config_id else None,
        model_name=execution.model_name,
        started_at=execution.started_at,
        completed_at=execution.completed_at,
        status=execution.status,
        error_message=execution.error_message,
        error_type=execution.error_type,
        input_tokens=execution.input_tokens,
        output_tokens=execution.output_tokens,
        total_tokens=execution.total_tokens,
        execution_time_ms=execution.execution_time_ms,
        llm_time_ms=execution.llm_time_ms,
        cost_usd=execution.cost_usd,
        parent_execution_id=str(execution.parent_execution_id) if execution.parent_execution_id else None,
        query_preview=execution.query_preview,
        created_at=execution.created_at,
        updated_at=execution.updated_at,
        traces=traces,
        token_usages=token_usages,
    )


@analytics_router.get("/agents/{agent_id}/stats", response_model=AgentStatsDTO)
async def get_agent_stats(
    db: AsyncDBSession,
    user: CurrentUserDependency,
    agent_id: UUID,
    period: Annotated[str, Query()] = "30d",
    start_date: Annotated[Optional[datetime], Query()] = None,
    end_date: Annotated[Optional[datetime], Query()] = None,
) -> AgentStatsDTO:
    """
    Get detailed statistics for a specific agent.

    Includes:
    - Execution counts and success rate
    - Timing metrics (avg, min, max, percentiles)
    - Token usage averages
    - Cost totals and averages
    - Error analysis
    """
    if start_date and end_date:
        pass
    else:
        start_date, end_date = parse_period(period)

    stats = await agent_execution_repo.get_agent_stats(
        db=db,
        agent_id=str(agent_id),
        user_id=str(user.id),
        start_date=start_date,
        end_date=end_date,
    )

    if not stats:
        raise HTTPException(status_code=404, detail="No data found for this agent")

    return stats


@analytics_router.get("/costs/summary")
async def get_cost_summary(
    db: AsyncDBSession,
    user: CurrentUserDependency,
    period: Annotated[str, Query()] = "30d",
    start_date: Annotated[Optional[datetime], Query()] = None,
    end_date: Annotated[Optional[datetime], Query()] = None,
) -> dict:
    """
    Get cost breakdown summary.

    Returns:
    - Total cost for the period
    - Cost breakdown by model
    - Cost breakdown by agent
    """
    if start_date and end_date:
        pass
    else:
        start_date, end_date = parse_period(period)

    return await agent_execution_repo.get_cost_summary(
        db=db,
        user_id=str(user.id),
        start_date=start_date,
        end_date=end_date,
    )


@analytics_router.get("/costs/forecast", response_model=CostForecastDTO)
async def get_cost_forecast(
    db: AsyncDBSession,
    user: CurrentUserDependency,
) -> CostForecastDTO:
    """
    Get cost forecast based on recent usage patterns.

    Returns:
    - Current period cost
    - Projected weekly and monthly costs
    - Daily average
    - Cost trend (increasing/decreasing/stable)
    """
    return await agent_execution_repo.get_cost_forecast(
        db=db,
        user_id=str(user.id),
    )


# Budget Alerts


@analytics_router.get("/budgets", response_model=List[BudgetAlertDTO])
async def list_budget_alerts(
    db: AsyncDBSession,
    user: CurrentUserDependency,
) -> List[BudgetAlertDTO]:
    """Get all budget alerts for the current user."""
    alerts = await budget_alert_repo.get_active_by_user(db, str(user.id))
    return [
        BudgetAlertDTO(
            id=str(a.id),
            user_id=str(a.user_id),
            scope=a.scope,
            scope_id=str(a.scope_id) if a.scope_id else None,
            threshold_usd=a.threshold_usd,
            period_days=a.period_days,
            alert_type=a.alert_type,
            alert_at_percentage=a.alert_at_percentage,
            webhook_url=a.webhook_url,
            email_notification=a.email_notification,
            is_active=a.is_active,
            last_alert_sent_at=a.last_alert_sent_at,
            current_spend_usd=a.current_spend_usd,
            created_at=a.created_at,
            updated_at=a.updated_at,
        )
        for a in alerts
    ]


@analytics_router.post("/budgets", response_model=BudgetAlertDTO)
async def create_budget_alert(
    db: AsyncDBSession,
    user: CurrentUserDependency,
    alert_data: BudgetAlertCreate,
) -> BudgetAlertDTO:
    """Create a new budget alert."""
    from src.models import BudgetAlert

    alert = BudgetAlert(
        user_id=user.id,
        scope=alert_data.scope,
        scope_id=alert_data.scope_id,
        threshold_usd=alert_data.threshold_usd,
        period_days=alert_data.period_days,
        alert_type=alert_data.alert_type,
        alert_at_percentage=alert_data.alert_at_percentage,
        webhook_url=alert_data.webhook_url,
        email_notification=alert_data.email_notification,
    )

    created = await budget_alert_repo.create(db, obj_in=alert)

    return BudgetAlertDTO(
        id=str(created.id),
        user_id=str(created.user_id),
        scope=created.scope,
        scope_id=str(created.scope_id) if created.scope_id else None,
        threshold_usd=created.threshold_usd,
        period_days=created.period_days,
        alert_type=created.alert_type,
        alert_at_percentage=created.alert_at_percentage,
        webhook_url=created.webhook_url,
        email_notification=created.email_notification,
        is_active=created.is_active,
        last_alert_sent_at=created.last_alert_sent_at,
        current_spend_usd=created.current_spend_usd,
        created_at=created.created_at,
        updated_at=created.updated_at,
    )


@analytics_router.patch("/budgets/{alert_id}", response_model=BudgetAlertDTO)
async def update_budget_alert(
    db: AsyncDBSession,
    user: CurrentUserDependency,
    alert_id: UUID,
    alert_data: BudgetAlertUpdate,
) -> BudgetAlertDTO:
    """Update a budget alert."""
    alert = await budget_alert_repo.get(db, id_=str(alert_id))

    if not alert:
        raise HTTPException(status_code=404, detail="Budget alert not found")

    if str(alert.user_id) != str(user.id):
        raise HTTPException(status_code=403, detail="Access denied")

    updated = await budget_alert_repo.update(db, db_obj=alert, obj_in=alert_data)

    return BudgetAlertDTO(
        id=str(updated.id),
        user_id=str(updated.user_id),
        scope=updated.scope,
        scope_id=str(updated.scope_id) if updated.scope_id else None,
        threshold_usd=updated.threshold_usd,
        period_days=updated.period_days,
        alert_type=updated.alert_type,
        alert_at_percentage=updated.alert_at_percentage,
        webhook_url=updated.webhook_url,
        email_notification=updated.email_notification,
        is_active=updated.is_active,
        last_alert_sent_at=updated.last_alert_sent_at,
        current_spend_usd=updated.current_spend_usd,
        created_at=updated.created_at,
        updated_at=updated.updated_at,
    )


@analytics_router.delete("/budgets/{alert_id}")
async def delete_budget_alert(
    db: AsyncDBSession,
    user: CurrentUserDependency,
    alert_id: UUID,
) -> dict:
    """Delete a budget alert."""
    alert = await budget_alert_repo.get(db, id_=str(alert_id))

    if not alert:
        raise HTTPException(status_code=404, detail="Budget alert not found")

    if str(alert.user_id) != str(user.id):
        raise HTTPException(status_code=403, detail="Access denied")

    await budget_alert_repo.delete(db, id_=str(alert_id))
    return {"status": "deleted", "id": str(alert_id)}


# Export


@analytics_router.get("/export")
async def export_analytics_data(
    db: AsyncDBSession,
    user: CurrentUserDependency,
    format: Annotated[str, Query(description="Export format: json or csv")] = "json",
    period: Annotated[str, Query()] = "7d",
    start_date: Annotated[Optional[datetime], Query()] = None,
    end_date: Annotated[Optional[datetime], Query()] = None,
    include_traces: Annotated[bool, Query()] = False,
):
    """
    Export analytics data in JSON or CSV format.
    """
    if start_date and end_date:
        pass
    else:
        start_date, end_date = parse_period(period)

    # Get executions
    paginated = await agent_execution_repo.list_paginated(
        db=db,
        user_id=str(user.id),
        start_date=start_date,
        end_date=end_date,
        page=1,
        page_size=10000,  # Export all
    )

    if format == "csv":
        # Create CSV
        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=[
                "id",
                "request_id",
                "session_id",
                "agent_name",
                "agent_type",
                "model_name",
                "status",
                "execution_time_ms",
                "total_tokens",
                "cost_usd",
                "started_at",
                "completed_at",
                "query_preview",
            ],
        )
        writer.writeheader()
        for item in paginated.items:
            writer.writerow({
                "id": item.id,
                "request_id": item.request_id,
                "session_id": item.session_id,
                "agent_name": item.agent_name,
                "agent_type": item.agent_type,
                "model_name": item.model_name,
                "status": item.status.value if item.status else "",
                "execution_time_ms": item.execution_time_ms,
                "total_tokens": item.total_tokens,
                "cost_usd": str(item.cost_usd),
                "started_at": item.started_at.isoformat() if item.started_at else "",
                "completed_at": item.completed_at.isoformat() if item.completed_at else "",
                "query_preview": item.query_preview,
            })

        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=analytics_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
            },
        )
    else:
        # JSON format
        data = {
            "export_date": datetime.utcnow().isoformat(),
            "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
            "total_records": paginated.total,
            "executions": [
                {
                    "id": item.id,
                    "request_id": item.request_id,
                    "session_id": item.session_id,
                    "agent_name": item.agent_name,
                    "agent_type": item.agent_type,
                    "model_name": item.model_name,
                    "status": item.status.value if item.status else None,
                    "execution_time_ms": item.execution_time_ms,
                    "total_tokens": item.total_tokens,
                    "cost_usd": str(item.cost_usd),
                    "started_at": item.started_at.isoformat() if item.started_at else None,
                    "completed_at": item.completed_at.isoformat() if item.completed_at else None,
                    "query_preview": item.query_preview,
                }
                for item in paginated.items
            ],
        }

        output = io.StringIO()
        json.dump(data, output, indent=2)
        output.seek(0)

        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=analytics_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
            },
        )


# Model Comparison


@analytics_router.get("/comparison/models")
async def compare_models(
    db: AsyncDBSession,
    user: CurrentUserDependency,
    period: Annotated[str, Query()] = "7d",
    start_date: Annotated[Optional[datetime], Query()] = None,
    end_date: Annotated[Optional[datetime], Query()] = None,
) -> List[dict]:
    """
    Compare performance across different models.

    Returns metrics for each model:
    - Execution count
    - Success rate
    - Average execution time
    - Average tokens
    - Total cost
    """
    if start_date and end_date:
        pass
    else:
        start_date, end_date = parse_period(period)

    from sqlalchemy import and_, case, desc, func, select
    from src.models import AgentExecution

    filters = [
        AgentExecution.user_id == str(user.id),
        AgentExecution.started_at >= start_date,
        AgentExecution.started_at <= end_date,
        AgentExecution.model_name.isnot(None),
    ]

    query = (
        select(
            AgentExecution.model_name,
            func.count().label("execution_count"),
            func.sum(case((AgentExecution.status == ExecutionStatus.success, 1), else_=0)).label(
                "success_count"
            ),
            func.avg(AgentExecution.execution_time_ms).label("avg_execution_time_ms"),
            func.avg(AgentExecution.total_tokens).label("avg_tokens"),
            func.sum(AgentExecution.total_tokens).label("total_tokens"),
            func.sum(AgentExecution.cost_usd).label("total_cost"),
        )
        .where(and_(*filters))
        .group_by(AgentExecution.model_name)
        .order_by(desc("execution_count"))
    )

    result = await db.execute(query)
    models = result.fetchall()

    return [
        {
            "model_name": row.model_name,
            "execution_count": row.execution_count,
            "success_count": row.success_count or 0,
            "success_rate": (row.success_count or 0) / row.execution_count * 100
            if row.execution_count > 0
            else 0,
            "avg_execution_time_ms": float(row.avg_execution_time_ms or 0),
            "avg_tokens": float(row.avg_tokens or 0),
            "total_tokens": row.total_tokens or 0,
            "total_cost_usd": str(row.total_cost or 0),
        }
        for row in models
    ]
