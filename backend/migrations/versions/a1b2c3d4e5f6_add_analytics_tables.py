"""Add analytics tables

Revision ID: a1b2c3d4e5f6
Revises: 8403bb364491
Create Date: 2024-12-24 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "8403bb364491"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create execution status enum
    execution_status_enum = postgresql.ENUM(
        'pending', 'running', 'success', 'failure', 'timeout', 'cancelled',
        name='executionstatus',
        create_type=False
    )
    execution_status_enum.create(op.get_bind(), checkfirst=True)

    # Create execution trace step type enum
    trace_step_type_enum = postgresql.ENUM(
        'thought', 'action', 'observation', 'agent_invoke', 'tool_call', 'final_answer',
        name='executiontracesteptype',
        create_type=False
    )
    trace_step_type_enum.create(op.get_bind(), checkfirst=True)

    # Create budget alert type enum
    budget_alert_type_enum = postgresql.ENUM(
        'warning', 'hard_stop',
        name='budgetalerttype',
        create_type=False
    )
    budget_alert_type_enum.create(op.get_bind(), checkfirst=True)

    # Create budget scope enum
    budget_scope_enum = postgresql.ENUM(
        'user', 'agent', 'flow', 'global',
        name='budgetscope',
        create_type=False
    )
    budget_scope_enum.create(op.get_bind(), checkfirst=True)

    # Create agentexecutions table
    op.create_table(
        'agentexecutions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('request_id', sa.UUID(), nullable=False),
        sa.Column('session_id', sa.UUID(), nullable=False),
        sa.Column('agent_id', sa.UUID(), nullable=True),
        sa.Column('agent_type', sa.String(), nullable=True),
        sa.Column('agent_name', sa.String(), nullable=True),
        sa.Column('user_id', sa.UUID(), nullable=True),
        sa.Column('model_config_id', sa.UUID(), nullable=True),
        sa.Column('model_name', sa.String(), nullable=True),
        sa.Column('started_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('status', postgresql.ENUM('pending', 'running', 'success', 'failure', 'timeout', 'cancelled', name='executionstatus', create_type=False), nullable=False),
        sa.Column('error_message', sa.String(), nullable=True),
        sa.Column('error_type', sa.String(), nullable=True),
        sa.Column('input_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('output_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('execution_time_ms', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('llm_time_ms', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('cost_usd', sa.Numeric(precision=10, scale=6), nullable=False, server_default='0.000000'),
        sa.Column('parent_execution_id', sa.UUID(), nullable=True),
        sa.Column('query_preview', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['model_config_id'], ['modelconfigs.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['parent_execution_id'], ['agentexecutions.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_agentexecutions_id'), 'agentexecutions', ['id'], unique=False)
    op.create_index(op.f('ix_agentexecutions_request_id'), 'agentexecutions', ['request_id'], unique=False)
    op.create_index(op.f('ix_agentexecutions_session_id'), 'agentexecutions', ['session_id'], unique=False)
    op.create_index(op.f('ix_agentexecutions_agent_id'), 'agentexecutions', ['agent_id'], unique=False)
    op.create_index(op.f('ix_agentexecutions_user_id'), 'agentexecutions', ['user_id'], unique=False)
    op.create_index(op.f('ix_agentexecutions_model_config_id'), 'agentexecutions', ['model_config_id'], unique=False)
    op.create_index(op.f('ix_agentexecutions_parent_execution_id'), 'agentexecutions', ['parent_execution_id'], unique=False)

    # Create tokenusages table
    op.create_table(
        'tokenusages',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('execution_id', sa.UUID(), nullable=False),
        sa.Column('component', sa.String(), nullable=False),
        sa.Column('step_number', sa.Integer(), nullable=True),
        sa.Column('input_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('output_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('model', sa.String(), nullable=True),
        sa.Column('cost_usd', sa.Numeric(precision=10, scale=6), nullable=False, server_default='0.000000'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['execution_id'], ['agentexecutions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tokenusages_id'), 'tokenusages', ['id'], unique=False)
    op.create_index(op.f('ix_tokenusages_execution_id'), 'tokenusages', ['execution_id'], unique=False)

    # Create executiontraces table
    op.create_table(
        'executiontraces',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('execution_id', sa.UUID(), nullable=False),
        sa.Column('step_number', sa.Integer(), nullable=False),
        sa.Column('step_type', postgresql.ENUM('thought', 'action', 'observation', 'agent_invoke', 'tool_call', 'final_answer', name='executiontracesteptype', create_type=False), nullable=False),
        sa.Column('content', sa.String(), nullable=True),
        sa.Column('invoked_agent_id', sa.UUID(), nullable=True),
        sa.Column('invoked_agent_name', sa.String(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('duration_ms', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('input_tokens', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('output_tokens', sa.Integer(), nullable=True, server_default='0'),
        sa.ForeignKeyConstraint(['execution_id'], ['agentexecutions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_executiontraces_id'), 'executiontraces', ['id'], unique=False)
    op.create_index(op.f('ix_executiontraces_execution_id'), 'executiontraces', ['execution_id'], unique=False)

    # Create budgetalerts table
    op.create_table(
        'budgetalerts',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('scope', postgresql.ENUM('user', 'agent', 'flow', 'global', name='budgetscope', create_type=False), nullable=False),
        sa.Column('scope_id', sa.UUID(), nullable=True),
        sa.Column('threshold_usd', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('period_days', sa.Integer(), nullable=False, server_default='30'),
        sa.Column('alert_type', postgresql.ENUM('warning', 'hard_stop', name='budgetalerttype', create_type=False), nullable=False),
        sa.Column('alert_at_percentage', sa.Integer(), nullable=False, server_default='80'),
        sa.Column('webhook_url', sa.String(), nullable=True),
        sa.Column('email_notification', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('last_alert_sent_at', sa.DateTime(), nullable=True),
        sa.Column('current_spend_usd', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0.00'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_budgetalerts_id'), 'budgetalerts', ['id'], unique=False)
    op.create_index(op.f('ix_budgetalerts_user_id'), 'budgetalerts', ['user_id'], unique=False)

    # Create analyticssnapshots table
    op.create_table(
        'analyticssnapshots',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('snapshot_date', sa.DateTime(), nullable=False),
        sa.Column('period_type', sa.String(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=True),
        sa.Column('agent_id', sa.UUID(), nullable=True),
        sa.Column('agent_name', sa.String(), nullable=True),
        sa.Column('model_name', sa.String(), nullable=True),
        sa.Column('total_executions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('successful_executions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('failed_executions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('timeout_executions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('avg_execution_time_ms', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('p50_execution_time_ms', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('p95_execution_time_ms', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('p99_execution_time_ms', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_input_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_output_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_cost_usd', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0.00'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_analyticssnapshots_id'), 'analyticssnapshots', ['id'], unique=False)
    op.create_index(op.f('ix_analyticssnapshots_snapshot_date'), 'analyticssnapshots', ['snapshot_date'], unique=False)
    op.create_index(op.f('ix_analyticssnapshots_user_id'), 'analyticssnapshots', ['user_id'], unique=False)
    op.create_index(op.f('ix_analyticssnapshots_agent_id'), 'analyticssnapshots', ['agent_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop tables
    op.drop_index(op.f('ix_analyticssnapshots_agent_id'), table_name='analyticssnapshots')
    op.drop_index(op.f('ix_analyticssnapshots_user_id'), table_name='analyticssnapshots')
    op.drop_index(op.f('ix_analyticssnapshots_snapshot_date'), table_name='analyticssnapshots')
    op.drop_index(op.f('ix_analyticssnapshots_id'), table_name='analyticssnapshots')
    op.drop_table('analyticssnapshots')

    op.drop_index(op.f('ix_budgetalerts_user_id'), table_name='budgetalerts')
    op.drop_index(op.f('ix_budgetalerts_id'), table_name='budgetalerts')
    op.drop_table('budgetalerts')

    op.drop_index(op.f('ix_executiontraces_execution_id'), table_name='executiontraces')
    op.drop_index(op.f('ix_executiontraces_id'), table_name='executiontraces')
    op.drop_table('executiontraces')

    op.drop_index(op.f('ix_tokenusages_execution_id'), table_name='tokenusages')
    op.drop_index(op.f('ix_tokenusages_id'), table_name='tokenusages')
    op.drop_table('tokenusages')

    op.drop_index(op.f('ix_agentexecutions_parent_execution_id'), table_name='agentexecutions')
    op.drop_index(op.f('ix_agentexecutions_model_config_id'), table_name='agentexecutions')
    op.drop_index(op.f('ix_agentexecutions_user_id'), table_name='agentexecutions')
    op.drop_index(op.f('ix_agentexecutions_agent_id'), table_name='agentexecutions')
    op.drop_index(op.f('ix_agentexecutions_session_id'), table_name='agentexecutions')
    op.drop_index(op.f('ix_agentexecutions_request_id'), table_name='agentexecutions')
    op.drop_index(op.f('ix_agentexecutions_id'), table_name='agentexecutions')
    op.drop_table('agentexecutions')

    # Drop enums
    sa.Enum(name='budgetscope').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='budgetalerttype').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='executiontracesteptype').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='executionstatus').drop(op.get_bind(), checkfirst=True)
