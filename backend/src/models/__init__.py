import uuid
from datetime import datetime
from typing import List

from sqlalchemy import ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional

from src.db.annotations import (
    created_at,
    int_pk,
    last_invoked_at,
    not_null_json_array_column,
    not_null_json_column,
    nullable_json_column,
    updated_at,
    uuid_pk,
)
from decimal import Decimal

from src.db.base import Base
from src.utils.enums import (
    BudgetAlertType,
    BudgetScope,
    ExecutionStatus,
    ExecutionTraceStepType,
    SenderType,
)


class UserProjectAssociation(Base):
    __tablename__ = "user_project_associations"
    id: Mapped[int] = mapped_column(autoincrement=True, index=True, primary_key=True)

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )


class UserTeamAssociation(Base):
    __tablename__ = "user_team_associations"
    id: Mapped[int] = mapped_column(autoincrement=True, index=True, primary_key=True)

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    team_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True
    )


class AgentProjectAssociation(Base):
    __tablename__ = "agent_project_associations"
    id: Mapped[int] = mapped_column(autoincrement=True, index=True, primary_key=True)

    agent_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )


class AgentFlowProjectAssociation(Base):
    __tablename__ = "agentflow_project_associations"
    id: Mapped[int] = mapped_column(autoincrement=True, index=True, primary_key=True)

    flow_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("agentworkflows.id", ondelete="CASCADE"), nullable=False, index=True
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )


class User(Base):
    id: Mapped[uuid_pk]
    username: Mapped[str] = mapped_column(index=True, unique=True)
    password: Mapped[str]  # hash
    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]

    agents: Mapped[List["Agent"]] = relationship(  # noqa: F821
        back_populates="creator",
    )

    workflows: Mapped[List["AgentWorkflow"]] = relationship(  # noqa: F821
        back_populates="creator",
    )

    projects: Mapped[List["Project"]] = relationship(
        secondary="user_project_associations", back_populates="users"
    )

    teams: Mapped[List["Team"]] = relationship(
        secondary="user_team_associations", back_populates="members"
    )

    logs: Mapped[List["Log"]] = relationship(
        back_populates="creator",
    )

    files: Mapped[List["File"]] = relationship(
        back_populates="creator",
    )

    model_providers: Mapped[List["ModelProvider"]] = relationship(
        back_populates="creator",
    )
    model_configs: Mapped[List["ModelConfig"]] = relationship(
        back_populates="creator",
    )

    conversations: Mapped[List["ChatConversation"]] = relationship(
        back_populates="creator"
    )
    mcpservers: Mapped[List["MCPServer"]] = relationship(back_populates="creator")
    a2acards: Mapped[List["A2ACard"]] = relationship(back_populates="creator")
    profile: Mapped["UserProfile"] = relationship(back_populates="user")

    def __repr__(self) -> str:
        return f"<User(uuid={self.id!r}, username={self.username!r})>"


class Agent(Base):
    id: Mapped[uuid_pk]

    alias: Mapped[str] = mapped_column(nullable=False, unique=True)
    name: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(nullable=False)

    jwt: Mapped[str] = mapped_column(unique=True)
    creator_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    creator: Mapped["User"] = relationship(back_populates="agents")  # noqa: F821

    input_parameters: Mapped[not_null_json_column]

    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]
    last_invoked_at: Mapped[last_invoked_at]
    is_active: Mapped[bool] = mapped_column(nullable=False)

    projects: Mapped[List["Project"]] = relationship(
        secondary="agent_project_associations", back_populates="agents"
    )


class AgentWorkflow(Base):
    id: Mapped[uuid_pk]

    alias: Mapped[str] = mapped_column(nullable=False, unique=True)
    name: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(nullable=False)

    flow: Mapped[not_null_json_array_column]

    creator_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    creator: Mapped["User"] = relationship(back_populates="workflows")  # noqa: F821

    is_active: Mapped[bool]
    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]

    projects: Mapped[List["Project"]] = relationship(
        secondary="agentflow_project_associations", back_populates="flows"
    )


class Project(Base):
    id: Mapped[uuid_pk]

    name: Mapped[str] = mapped_column(nullable=False)

    users: Mapped[List["User"]] = relationship(
        secondary="user_project_associations", back_populates="projects"
    )

    agents: Mapped[List["Agent"]] = relationship(
        secondary="agent_project_associations", back_populates="projects"
    )

    flows: Mapped[List["AgentWorkflow"]] = relationship(
        secondary="agentflow_project_associations", back_populates="projects"
    )


class Team(Base):
    id: Mapped[uuid_pk]
    name: Mapped[str] = mapped_column(unique=True, nullable=False)

    members: Mapped[List["User"]] = relationship(
        secondary="user_team_associations", back_populates="teams"
    )


class Log(Base):
    id: Mapped[int_pk]

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), index=True, nullable=False
    )
    request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), index=True, nullable=False
    )
    agent_id: Mapped[str] = mapped_column(index=True, nullable=True)
    creator_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    creator: Mapped["User"] = relationship(back_populates="logs")

    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]

    message: Mapped[str] = mapped_column(nullable=False)
    log_level: Mapped[str] = mapped_column(nullable=False)  # TODO: enum


class File(Base):
    id: Mapped[uuid_pk]

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), index=True, nullable=True
    )
    request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), index=True, nullable=True
    )
    creator_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    creator: Mapped["User"] = relationship(back_populates="files")
    mimetype: Mapped[str]
    original_name: Mapped[str]
    internal_name: Mapped[str]
    internal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), index=True, nullable=False
    )
    from_agent: Mapped[bool]


class ModelProvider(Base):
    id: Mapped[uuid_pk]
    name: Mapped[str]
    api_key: Mapped[str] = mapped_column(nullable=True)  # encrypted in pydantic models

    provider_metadata: Mapped[not_null_json_column]
    configs: Mapped[List["ModelConfig"]] = relationship(  # noqa: F821
        back_populates="provider",
    )

    creator_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    creator: Mapped["User"] = relationship(back_populates="model_providers")
    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]

    __table_args__ = (UniqueConstraint("creator_id", "name", name="uq_user_item_name"),)


class ModelConfig(Base):
    id: Mapped[uuid_pk]
    name: Mapped[str] = mapped_column(unique=True)
    model: Mapped[str] = mapped_column(nullable=False, index=True)

    provider_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("modelproviders.id", ondelete="CASCADE"), nullable=True, index=True
    )
    provider: Mapped["ModelProvider"] = relationship(back_populates="configs")  # noqa: F821

    system_prompt: Mapped[str]
    user_prompt: Mapped[str] = mapped_column(nullable=True)
    max_last_messages: Mapped[int] = mapped_column(default=5, nullable=False)
    temperature: Mapped[float] = mapped_column(default=0.7)

    credentials: Mapped[not_null_json_column]

    creator_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    creator: Mapped["User"] = relationship(back_populates="model_configs")

    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]


class MCPServer(Base):
    id: Mapped[uuid_pk]

    name: Mapped[str] = mapped_column(nullable=True)
    description: Mapped[str] = mapped_column(nullable=True)

    server_url: Mapped[str] = mapped_column(nullable=False)

    mcp_tools: Mapped[List["MCPTool"]] = relationship(back_populates="mcp_server")

    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]

    creator: Mapped["User"] = relationship(back_populates="mcpservers")  # noqa: F821

    creator_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )

    is_active: Mapped[bool]

    __table_args__ = (
        UniqueConstraint("creator_id", "server_url", name="uq_mcp_server_url"),
    )

    def __repr__(self) -> str:
        return f"<MCPServer(host={self.server_url!r}>"


class MCPTool(Base):
    id: Mapped[uuid_pk]
    name: Mapped[str]
    description: Mapped[str] = mapped_column(nullable=True)
    inputSchema: Mapped[not_null_json_column]
    annotations: Mapped[nullable_json_column]

    alias: Mapped[str] = mapped_column(nullable=True)

    mcp_server: Mapped["MCPServer"] = relationship(back_populates="mcp_tools")  # noqa: F821

    mcp_server_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("mcpservers.id", ondelete="CASCADE"), nullable=True, index=True
    )

    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]


class A2ACard(Base):
    id: Mapped[uuid_pk]

    name: Mapped[str] = mapped_column(nullable=True)
    alias: Mapped[str] = mapped_column(nullable=True)
    description: Mapped[str] = mapped_column(nullable=True)

    server_url: Mapped[str] = mapped_column(nullable=False)
    card_content: Mapped[not_null_json_column]

    is_active: Mapped[bool]

    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]

    creator: Mapped["User"] = relationship(back_populates="a2acards")  # noqa: F821

    creator_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    __table_args__ = (
        UniqueConstraint("creator_id", "server_url", name="uq_a2a_card_server_url"),
    )


class ChatMessage(Base):
    id: Mapped[uuid_pk]

    request_id: Mapped[uuid.UUID] = mapped_column(nullable=True)

    sender_type: Mapped[SenderType]
    content: Mapped[str]

    # 'metadata' is a reserved word by alembic
    extra_metadata: Mapped[nullable_json_column]

    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("chatconversations.session_id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    conversation: Mapped["ChatConversation"] = relationship(back_populates="messages")


class ChatConversation(Base):
    """Chat history"""

    session_id: Mapped[uuid_pk] = mapped_column(nullable=False, index=True)
    title: Mapped[str]

    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]

    creator_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    creator: Mapped["User"] = relationship(back_populates="conversations")

    messages: Mapped[List["ChatMessage"]] = relationship(
        back_populates="conversation", cascade="all, delete"
    )


class UserProfile(Base):
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4, index=True
    )

    first_name: Mapped[str] = mapped_column(nullable=True)
    last_name: Mapped[str] = mapped_column(nullable=True)
    # TODO: other fields like address, avatar, bio, company_name, etc

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    user: Mapped["User"] = relationship(back_populates="profile", single_parent=True)

    # TODO: config fields, other credentials, etc


# ============================================================================
# Analytics Models
# ============================================================================


class AgentExecution(Base):
    """Tracks individual agent execution instances for analytics."""

    __tablename__ = "agentexecutions"

    id: Mapped[uuid_pk]
    request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), index=True, nullable=False
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), index=True, nullable=False
    )

    # The agent that was executed (can be genai agent, mcp tool, or a2a card)
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), index=True, nullable=True
    )
    agent_type: Mapped[str] = mapped_column(nullable=True)  # genai, mcp, a2a, flow
    agent_name: Mapped[str] = mapped_column(nullable=True)

    # User who triggered the execution
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Model configuration used
    model_config_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("modelconfigs.id", ondelete="SET NULL"), nullable=True, index=True
    )
    model_name: Mapped[str] = mapped_column(nullable=True)

    # Timing
    started_at: Mapped[created_at]
    completed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # Status
    status: Mapped[ExecutionStatus] = mapped_column(default=ExecutionStatus.pending)
    error_message: Mapped[str] = mapped_column(nullable=True)
    error_type: Mapped[str] = mapped_column(nullable=True)

    # Token usage
    input_tokens: Mapped[int] = mapped_column(default=0)
    output_tokens: Mapped[int] = mapped_column(default=0)
    total_tokens: Mapped[int] = mapped_column(default=0)

    # Execution metrics
    execution_time_ms: Mapped[int] = mapped_column(default=0)
    llm_time_ms: Mapped[int] = mapped_column(default=0, nullable=True)

    # Cost (stored in USD)
    cost_usd: Mapped[Decimal] = mapped_column(
        Numeric(precision=10, scale=6), default=Decimal("0.000000")
    )

    # Parent execution for nested agent calls
    parent_execution_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("agentexecutions.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Query/input summary (truncated for privacy)
    query_preview: Mapped[str] = mapped_column(nullable=True)

    # Relationships
    traces: Mapped[List["ExecutionTrace"]] = relationship(
        back_populates="execution", cascade="all, delete-orphan"
    )
    token_usages: Mapped[List["TokenUsage"]] = relationship(
        back_populates="execution", cascade="all, delete-orphan"
    )

    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]

    def __repr__(self) -> str:
        return f"<AgentExecution(id={self.id}, agent={self.agent_name}, status={self.status})>"


class TokenUsage(Base):
    """Detailed token usage tracking per component within an execution."""

    __tablename__ = "tokenusages"

    id: Mapped[uuid_pk]
    execution_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("agentexecutions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    execution: Mapped["AgentExecution"] = relationship(back_populates="token_usages")

    # Which component used the tokens
    component: Mapped[str] = mapped_column(nullable=False)  # master_agent, agent_{name}, mcp_tool, etc.
    step_number: Mapped[int] = mapped_column(nullable=True)

    # Token counts
    input_tokens: Mapped[int] = mapped_column(default=0)
    output_tokens: Mapped[int] = mapped_column(default=0)

    # Model used
    model: Mapped[str] = mapped_column(nullable=True)

    # Cost
    cost_usd: Mapped[Decimal] = mapped_column(
        Numeric(precision=10, scale=6), default=Decimal("0.000000")
    )

    created_at: Mapped[created_at]


class ExecutionTrace(Base):
    """Step-by-step trace of execution for debugging and visualization."""

    __tablename__ = "executiontraces"

    id: Mapped[uuid_pk]
    execution_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("agentexecutions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    execution: Mapped["AgentExecution"] = relationship(back_populates="traces")

    step_number: Mapped[int] = mapped_column(nullable=False)
    step_type: Mapped[ExecutionTraceStepType]

    # Content of the step (thought, action, observation, etc.)
    content: Mapped[str] = mapped_column(nullable=True)

    # For agent invocations
    invoked_agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    invoked_agent_name: Mapped[str] = mapped_column(nullable=True)

    # Timing
    timestamp: Mapped[created_at]
    duration_ms: Mapped[int] = mapped_column(default=0)

    # Token usage for this step
    input_tokens: Mapped[int] = mapped_column(default=0, nullable=True)
    output_tokens: Mapped[int] = mapped_column(default=0, nullable=True)


class BudgetAlert(Base):
    """Budget alerts and spending limits."""

    __tablename__ = "budgetalerts"

    id: Mapped[uuid_pk]

    # Who owns this budget
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # What the budget applies to
    scope: Mapped[BudgetScope] = mapped_column(default=BudgetScope.user)
    scope_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )  # agent_id, flow_id, etc.

    # Budget configuration
    threshold_usd: Mapped[Decimal] = mapped_column(
        Numeric(precision=10, scale=2), nullable=False
    )
    period_days: Mapped[int] = mapped_column(default=30)  # Rolling window

    # Alert settings
    alert_type: Mapped[BudgetAlertType] = mapped_column(default=BudgetAlertType.warning)
    alert_at_percentage: Mapped[int] = mapped_column(default=80)  # Alert at 80% of budget
    webhook_url: Mapped[str] = mapped_column(nullable=True)
    email_notification: Mapped[bool] = mapped_column(default=True)

    # Status
    is_active: Mapped[bool] = mapped_column(default=True)
    last_alert_sent_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    current_spend_usd: Mapped[Decimal] = mapped_column(
        Numeric(precision=10, scale=2), default=Decimal("0.00")
    )

    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]


class AnalyticsSnapshot(Base):
    """Pre-aggregated analytics data for fast dashboard queries."""

    __tablename__ = "analyticssnapshots"

    id: Mapped[uuid_pk]

    # Snapshot period
    snapshot_date: Mapped[datetime] = mapped_column(index=True, nullable=False)
    period_type: Mapped[str] = mapped_column(nullable=False)  # hourly, daily, weekly, monthly

    # Scope
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    agent_name: Mapped[str] = mapped_column(nullable=True)
    model_name: Mapped[str] = mapped_column(nullable=True)

    # Execution metrics
    total_executions: Mapped[int] = mapped_column(default=0)
    successful_executions: Mapped[int] = mapped_column(default=0)
    failed_executions: Mapped[int] = mapped_column(default=0)
    timeout_executions: Mapped[int] = mapped_column(default=0)

    # Timing metrics (in ms)
    avg_execution_time_ms: Mapped[int] = mapped_column(default=0)
    p50_execution_time_ms: Mapped[int] = mapped_column(default=0)
    p95_execution_time_ms: Mapped[int] = mapped_column(default=0)
    p99_execution_time_ms: Mapped[int] = mapped_column(default=0)

    # Token metrics
    total_input_tokens: Mapped[int] = mapped_column(default=0)
    total_output_tokens: Mapped[int] = mapped_column(default=0)
    total_tokens: Mapped[int] = mapped_column(default=0)

    # Cost metrics
    total_cost_usd: Mapped[Decimal] = mapped_column(
        Numeric(precision=10, scale=2), default=Decimal("0.00")
    )

    created_at: Mapped[created_at]


# Import datetime at the module level for type hints
from datetime import datetime  # noqa: E402
