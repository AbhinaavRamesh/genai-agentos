from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, case, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models import (
    AgentExecution,
    AnalyticsSnapshot,
    BudgetAlert,
    ExecutionTrace,
    TokenUsage,
)
from src.repositories.base import CRUDBase
from src.schemas.api.analytics.dto import (
    AgentExecutionDTO,
    AgentExecutionSummaryDTO,
    AgentStatsDTO,
    AnalyticsOverviewDTO,
    AnalyticsTimeSeriesDataPoint,
    CostBreakdownDTO,
    CostForecastDTO,
    PaginatedExecutionsDTO,
    TopAgentDTO,
)
from src.schemas.api.analytics.schemas import (
    AgentExecutionCreate,
    AgentExecutionUpdate,
    BudgetAlertCreate,
    BudgetAlertUpdate,
    ExecutionTraceCreate,
    TokenUsageCreate,
)
from src.utils.enums import ExecutionStatus


class AgentExecutionRepository(CRUDBase[AgentExecution, AgentExecutionCreate, AgentExecutionUpdate]):
    """Repository for agent execution analytics."""

    async def get_with_details(
        self, db: AsyncSession, execution_id: str
    ) -> Optional[AgentExecution]:
        """Get execution with traces and token usages."""
        result = await db.execute(
            select(self.model)
            .options(
                selectinload(AgentExecution.traces),
                selectinload(AgentExecution.token_usages),
            )
            .where(self.model.id == execution_id)
        )
        return result.scalars().first()

    async def get_by_request_id(
        self, db: AsyncSession, request_id: str
    ) -> List[AgentExecution]:
        """Get all executions for a request."""
        result = await db.execute(
            select(self.model)
            .where(self.model.request_id == request_id)
            .order_by(self.model.started_at)
        )
        return result.scalars().all()

    async def get_by_session_id(
        self, db: AsyncSession, session_id: str, limit: int = 100
    ) -> List[AgentExecution]:
        """Get all executions for a session."""
        result = await db.execute(
            select(self.model)
            .where(self.model.session_id == session_id)
            .order_by(desc(self.model.started_at))
            .limit(limit)
        )
        return result.scalars().all()

    async def list_paginated(
        self,
        db: AsyncSession,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        agent_type: Optional[str] = None,
        model_name: Optional[str] = None,
        status: Optional[ExecutionStatus] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "started_at",
        sort_order: str = "desc",
    ) -> PaginatedExecutionsDTO:
        """Get paginated list of executions with filters."""
        # Build filters
        filters = []
        if user_id:
            filters.append(self.model.user_id == user_id)
        if agent_id:
            filters.append(self.model.agent_id == agent_id)
        if agent_type:
            filters.append(self.model.agent_type == agent_type)
        if model_name:
            filters.append(self.model.model_name == model_name)
        if status:
            filters.append(self.model.status == status)
        if start_date:
            filters.append(self.model.started_at >= start_date)
        if end_date:
            filters.append(self.model.started_at <= end_date)

        # Count total
        count_query = select(func.count()).select_from(self.model)
        if filters:
            count_query = count_query.where(and_(*filters))
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # Get items
        query = select(self.model)
        if filters:
            query = query.where(and_(*filters))

        # Sort
        sort_column = getattr(self.model, sort_by, self.model.started_at)
        if sort_order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(sort_column)

        # Paginate
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await db.execute(query)
        items = result.scalars().all()

        return PaginatedExecutionsDTO(
            items=[
                AgentExecutionSummaryDTO(
                    id=str(item.id),
                    request_id=str(item.request_id),
                    session_id=str(item.session_id),
                    agent_name=item.agent_name,
                    agent_type=item.agent_type,
                    model_name=item.model_name,
                    status=item.status,
                    execution_time_ms=item.execution_time_ms,
                    total_tokens=item.total_tokens,
                    cost_usd=item.cost_usd,
                    started_at=item.started_at,
                    completed_at=item.completed_at,
                    query_preview=item.query_preview,
                )
                for item in items
            ],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size,
        )

    async def get_overview(
        self,
        db: AsyncSession,
        user_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> AnalyticsOverviewDTO:
        """Get analytics overview for dashboard."""
        # Default to last 24 hours if no dates specified
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(hours=24)

        # Build base filter
        filters = [
            self.model.started_at >= start_date,
            self.model.started_at <= end_date,
        ]
        if user_id:
            filters.append(self.model.user_id == user_id)

        # Get aggregate metrics
        metrics_query = select(
            func.count().label("total"),
            func.sum(case((self.model.status == ExecutionStatus.success, 1), else_=0)).label(
                "successful"
            ),
            func.sum(case((self.model.status == ExecutionStatus.failure, 1), else_=0)).label(
                "failed"
            ),
            func.avg(self.model.execution_time_ms).label("avg_time"),
            func.sum(self.model.input_tokens).label("input_tokens"),
            func.sum(self.model.output_tokens).label("output_tokens"),
            func.sum(self.model.total_tokens).label("total_tokens"),
            func.sum(self.model.cost_usd).label("total_cost"),
        ).where(and_(*filters))

        result = await db.execute(metrics_query)
        metrics = result.first()

        total_executions = metrics.total or 0
        successful_executions = metrics.successful or 0
        failed_executions = metrics.failed or 0
        success_rate = (
            (successful_executions / total_executions * 100)
            if total_executions > 0
            else 0.0
        )

        # Get percentile execution times
        time_query = select(self.model.execution_time_ms).where(
            and_(*filters, self.model.execution_time_ms > 0)
        ).order_by(self.model.execution_time_ms)
        time_result = await db.execute(time_query)
        times = [r[0] for r in time_result.fetchall()]

        p50 = times[len(times) // 2] if times else 0
        p95 = times[int(len(times) * 0.95)] if times else 0
        p99 = times[int(len(times) * 0.99)] if times else 0

        # Get top agents
        top_agents_query = (
            select(
                self.model.agent_name,
                self.model.agent_id,
                self.model.agent_type,
                func.count().label("count"),
                func.sum(case((self.model.status == ExecutionStatus.success, 1), else_=0)).label(
                    "success_count"
                ),
                func.sum(case((self.model.status == ExecutionStatus.failure, 1), else_=0)).label(
                    "failure_count"
                ),
                func.avg(self.model.execution_time_ms).label("avg_time"),
                func.sum(self.model.total_tokens).label("total_tokens"),
                func.sum(self.model.cost_usd).label("total_cost"),
            )
            .where(and_(*filters, self.model.agent_name.isnot(None)))
            .group_by(self.model.agent_name, self.model.agent_id, self.model.agent_type)
            .order_by(desc("count"))
            .limit(10)
        )
        top_agents_result = await db.execute(top_agents_query)
        top_agents = [
            TopAgentDTO(
                agent_name=row.agent_name or "Unknown",
                agent_id=str(row.agent_id) if row.agent_id else None,
                agent_type=row.agent_type,
                execution_count=row.count,
                success_count=row.success_count or 0,
                failure_count=row.failure_count or 0,
                success_rate=(row.success_count or 0) / row.count * 100 if row.count > 0 else 0,
                avg_execution_time_ms=float(row.avg_time or 0),
                total_tokens=row.total_tokens or 0,
                total_cost_usd=Decimal(str(row.total_cost or 0)),
            )
            for row in top_agents_result.fetchall()
        ]

        # Get cost breakdown by model
        model_cost_query = (
            select(
                self.model.model_name,
                func.sum(self.model.cost_usd).label("cost"),
                func.count().label("count"),
                func.sum(self.model.total_tokens).label("tokens"),
            )
            .where(and_(*filters, self.model.model_name.isnot(None)))
            .group_by(self.model.model_name)
            .order_by(desc("cost"))
        )
        model_cost_result = await db.execute(model_cost_query)
        total_cost = Decimal(str(metrics.total_cost or 0))
        cost_by_model = [
            CostBreakdownDTO(
                name=row.model_name or "Unknown",
                category="model",
                total_cost_usd=Decimal(str(row.cost or 0)),
                percentage=float(row.cost / total_cost * 100) if total_cost > 0 else 0,
                execution_count=row.count,
                total_tokens=row.tokens or 0,
            )
            for row in model_cost_result.fetchall()
        ]

        # Calculate comparison with previous period
        period_length = end_date - start_date
        prev_start = start_date - period_length
        prev_end = start_date

        prev_filters = [
            self.model.started_at >= prev_start,
            self.model.started_at < prev_end,
        ]
        if user_id:
            prev_filters.append(self.model.user_id == user_id)

        prev_query = select(
            func.count().label("total"),
            func.sum(case((self.model.status == ExecutionStatus.success, 1), else_=0)).label(
                "successful"
            ),
            func.avg(self.model.execution_time_ms).label("avg_time"),
            func.sum(self.model.cost_usd).label("total_cost"),
        ).where(and_(*prev_filters))

        prev_result = await db.execute(prev_query)
        prev_metrics = prev_result.first()

        prev_total = prev_metrics.total or 0
        prev_successful = prev_metrics.successful or 0
        prev_success_rate = (prev_successful / prev_total * 100) if prev_total > 0 else 0
        prev_avg_time = float(prev_metrics.avg_time or 0)
        prev_cost = Decimal(str(prev_metrics.total_cost or 0))

        def calc_change(current: float, previous: float) -> Optional[float]:
            if previous == 0:
                return None
            return ((current - previous) / previous) * 100

        # Count active agents
        active_agents_query = select(
            func.count(func.distinct(self.model.agent_id))
        ).where(and_(*filters, self.model.agent_id.isnot(None)))
        active_result = await db.execute(active_agents_query)
        active_agents = active_result.scalar() or 0

        return AnalyticsOverviewDTO(
            total_executions=total_executions,
            successful_executions=successful_executions,
            failed_executions=failed_executions,
            success_rate=success_rate,
            avg_execution_time_ms=float(metrics.avg_time or 0),
            p50_execution_time_ms=float(p50),
            p95_execution_time_ms=float(p95),
            p99_execution_time_ms=float(p99),
            total_input_tokens=metrics.input_tokens or 0,
            total_output_tokens=metrics.output_tokens or 0,
            total_tokens=metrics.total_tokens or 0,
            total_cost_usd=total_cost,
            estimated_monthly_cost_usd=total_cost * 30 if period_length.days == 1 else total_cost * 30 / max(period_length.days, 1),
            executions_change_percent=calc_change(float(total_executions), float(prev_total)),
            execution_time_change_percent=calc_change(float(metrics.avg_time or 0), prev_avg_time),
            success_rate_change_percent=calc_change(success_rate, prev_success_rate),
            cost_change_percent=calc_change(float(total_cost), float(prev_cost)),
            active_agents_count=active_agents,
            top_agents=top_agents,
            cost_by_model=cost_by_model,
        )

    async def get_agent_stats(
        self,
        db: AsyncSession,
        agent_id: str,
        user_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Optional[AgentStatsDTO]:
        """Get detailed statistics for a specific agent."""
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)

        filters = [
            self.model.agent_id == agent_id,
            self.model.started_at >= start_date,
            self.model.started_at <= end_date,
        ]
        if user_id:
            filters.append(self.model.user_id == user_id)

        # Get aggregate stats
        stats_query = select(
            self.model.agent_name,
            self.model.agent_type,
            func.count().label("total"),
            func.sum(case((self.model.status == ExecutionStatus.success, 1), else_=0)).label(
                "successful"
            ),
            func.sum(case((self.model.status == ExecutionStatus.failure, 1), else_=0)).label(
                "failed"
            ),
            func.sum(case((self.model.status == ExecutionStatus.timeout, 1), else_=0)).label(
                "timeout"
            ),
            func.avg(self.model.execution_time_ms).label("avg_time"),
            func.min(self.model.execution_time_ms).label("min_time"),
            func.max(self.model.execution_time_ms).label("max_time"),
            func.avg(self.model.input_tokens).label("avg_input"),
            func.avg(self.model.output_tokens).label("avg_output"),
            func.sum(self.model.total_tokens).label("total_tokens"),
            func.sum(self.model.cost_usd).label("total_cost"),
            func.max(self.model.started_at).label("last_executed"),
            func.min(self.model.started_at).label("first_executed"),
        ).where(and_(*filters)).group_by(self.model.agent_name, self.model.agent_type)

        result = await db.execute(stats_query)
        stats = result.first()

        if not stats:
            return None

        total = stats.total or 0
        successful = stats.successful or 0

        return AgentStatsDTO(
            agent_id=agent_id,
            agent_name=stats.agent_name or "Unknown",
            agent_type=stats.agent_type,
            total_executions=total,
            successful_executions=successful,
            failed_executions=stats.failed or 0,
            timeout_executions=stats.timeout or 0,
            success_rate=(successful / total * 100) if total > 0 else 0,
            avg_execution_time_ms=float(stats.avg_time or 0),
            min_execution_time_ms=stats.min_time or 0,
            max_execution_time_ms=stats.max_time or 0,
            avg_input_tokens=float(stats.avg_input or 0),
            avg_output_tokens=float(stats.avg_output or 0),
            total_tokens=stats.total_tokens or 0,
            total_cost_usd=Decimal(str(stats.total_cost or 0)),
            avg_cost_per_execution_usd=Decimal(str(stats.total_cost or 0)) / total if total > 0 else Decimal("0"),
            last_executed_at=stats.last_executed,
            first_executed_at=stats.first_executed,
        )

    async def get_cost_summary(
        self,
        db: AsyncSession,
        user_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> dict:
        """Get cost summary breakdown."""
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)

        filters = [
            self.model.started_at >= start_date,
            self.model.started_at <= end_date,
        ]
        if user_id:
            filters.append(self.model.user_id == user_id)

        # Total cost
        total_query = select(func.sum(self.model.cost_usd)).where(and_(*filters))
        total_result = await db.execute(total_query)
        total_cost = Decimal(str(total_result.scalar() or 0))

        # By model
        by_model_query = (
            select(
                self.model.model_name,
                func.sum(self.model.cost_usd).label("cost"),
                func.count().label("count"),
            )
            .where(and_(*filters))
            .group_by(self.model.model_name)
            .order_by(desc("cost"))
        )
        by_model_result = await db.execute(by_model_query)
        by_model = [
            {
                "model": row.model_name or "Unknown",
                "cost_usd": Decimal(str(row.cost or 0)),
                "execution_count": row.count,
                "percentage": float(row.cost / total_cost * 100) if total_cost > 0 else 0,
            }
            for row in by_model_result.fetchall()
        ]

        # By agent
        by_agent_query = (
            select(
                self.model.agent_name,
                self.model.agent_id,
                func.sum(self.model.cost_usd).label("cost"),
                func.count().label("count"),
            )
            .where(and_(*filters))
            .group_by(self.model.agent_name, self.model.agent_id)
            .order_by(desc("cost"))
        )
        by_agent_result = await db.execute(by_agent_query)
        by_agent = [
            {
                "agent_name": row.agent_name or "Unknown",
                "agent_id": str(row.agent_id) if row.agent_id else None,
                "cost_usd": Decimal(str(row.cost or 0)),
                "execution_count": row.count,
                "percentage": float(row.cost / total_cost * 100) if total_cost > 0 else 0,
            }
            for row in by_agent_result.fetchall()
        ]

        return {
            "total_cost_usd": total_cost,
            "period_days": (end_date - start_date).days,
            "by_model": by_model,
            "by_agent": by_agent,
        }

    async def get_cost_forecast(
        self,
        db: AsyncSession,
        user_id: Optional[str] = None,
    ) -> CostForecastDTO:
        """Get cost forecast based on recent usage."""
        now = datetime.utcnow()
        last_7_days = now - timedelta(days=7)
        prev_7_days = last_7_days - timedelta(days=7)

        filters_current = [self.model.started_at >= last_7_days]
        filters_prev = [
            self.model.started_at >= prev_7_days,
            self.model.started_at < last_7_days,
        ]
        if user_id:
            filters_current.append(self.model.user_id == user_id)
            filters_prev.append(self.model.user_id == user_id)

        # Current period cost
        current_query = select(func.sum(self.model.cost_usd)).where(and_(*filters_current))
        current_result = await db.execute(current_query)
        current_cost = Decimal(str(current_result.scalar() or 0))

        # Previous period cost
        prev_query = select(func.sum(self.model.cost_usd)).where(and_(*filters_prev))
        prev_result = await db.execute(prev_query)
        prev_cost = Decimal(str(prev_result.scalar() or 0))

        daily_avg = current_cost / 7
        weekly_projected = current_cost
        monthly_projected = daily_avg * 30

        # Determine trend
        if prev_cost > 0:
            change = float((current_cost - prev_cost) / prev_cost * 100)
            if change > 10:
                trend = "increasing"
            elif change < -10:
                trend = "decreasing"
            else:
                trend = "stable"
        else:
            change = 0.0
            trend = "stable"

        return CostForecastDTO(
            current_period_cost_usd=current_cost,
            projected_monthly_cost_usd=monthly_projected,
            projected_weekly_cost_usd=weekly_projected,
            daily_average_cost_usd=daily_avg,
            cost_trend=trend,
            trend_percentage=change,
        )


class TokenUsageRepository(CRUDBase[TokenUsage, TokenUsageCreate, TokenUsageCreate]):
    """Repository for token usage records."""

    async def get_by_execution(
        self, db: AsyncSession, execution_id: str
    ) -> List[TokenUsage]:
        """Get all token usage records for an execution."""
        result = await db.execute(
            select(self.model)
            .where(self.model.execution_id == execution_id)
            .order_by(self.model.step_number)
        )
        return result.scalars().all()


class ExecutionTraceRepository(CRUDBase[ExecutionTrace, ExecutionTraceCreate, ExecutionTraceCreate]):
    """Repository for execution trace records."""

    async def get_by_execution(
        self, db: AsyncSession, execution_id: str
    ) -> List[ExecutionTrace]:
        """Get all trace records for an execution."""
        result = await db.execute(
            select(self.model)
            .where(self.model.execution_id == execution_id)
            .order_by(self.model.step_number)
        )
        return result.scalars().all()


class BudgetAlertRepository(CRUDBase[BudgetAlert, BudgetAlertCreate, BudgetAlertUpdate]):
    """Repository for budget alerts."""

    async def get_active_by_user(
        self, db: AsyncSession, user_id: str
    ) -> List[BudgetAlert]:
        """Get all active budget alerts for a user."""
        result = await db.execute(
            select(self.model).where(
                and_(
                    self.model.user_id == user_id,
                    self.model.is_active == True,
                )
            )
        )
        return result.scalars().all()

    async def check_budget_exceeded(
        self, db: AsyncSession, user_id: str
    ) -> List[Tuple[BudgetAlert, Decimal]]:
        """Check if any budgets are exceeded and return alerts with current spend."""
        alerts = await self.get_active_by_user(db, user_id)
        exceeded = []

        for alert in alerts:
            # Calculate current spend for the period
            start_date = datetime.utcnow() - timedelta(days=alert.period_days)

            filters = [
                AgentExecution.user_id == user_id,
                AgentExecution.started_at >= start_date,
            ]

            if alert.scope.value == "agent" and alert.scope_id:
                filters.append(AgentExecution.agent_id == alert.scope_id)

            query = select(func.sum(AgentExecution.cost_usd)).where(and_(*filters))
            result = await db.execute(query)
            current_spend = Decimal(str(result.scalar() or 0))

            threshold = alert.threshold_usd * Decimal(str(alert.alert_at_percentage)) / 100

            if current_spend >= threshold:
                exceeded.append((alert, current_spend))

        return exceeded


# Repository instances
agent_execution_repo = AgentExecutionRepository(AgentExecution)
token_usage_repo = TokenUsageRepository(TokenUsage)
execution_trace_repo = ExecutionTraceRepository(ExecutionTrace)
budget_alert_repo = BudgetAlertRepository(BudgetAlert)
