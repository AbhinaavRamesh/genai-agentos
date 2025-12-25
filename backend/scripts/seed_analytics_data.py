"""
Seed script to populate analytics tables with synthetic data for testing.

Run with: python -m scripts.seed_analytics_data
Or via docker: docker exec -it genai-backend python -m scripts.seed_analytics_data
"""

import asyncio
import random
import uuid
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Configuration - use localhost for running outside Docker
DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"

# Sample data
AGENT_NAMES = [
    "CustomerSupportAgent",
    "DataAnalysisAgent",
    "CodeReviewAgent",
    "ResearchAssistant",
    "ContentWriterAgent",
    "TranslationAgent",
    "SummarizationAgent",
    "QATestingAgent",
]

AGENT_TYPES = ["genai", "a2a", "mcp"]

MODEL_NAMES = [
    "gpt-4o",
    "gpt-4o-mini",
    "claude-3-5-sonnet",
    "claude-3-haiku",
    "gemini-1.5-pro",
    "gemini-1.5-flash",
]

# Cost per 1K tokens (input/output)
MODEL_COSTS = {
    "gpt-4o": (0.005, 0.015),
    "gpt-4o-mini": (0.00015, 0.0006),
    "claude-3-5-sonnet": (0.003, 0.015),
    "claude-3-haiku": (0.00025, 0.00125),
    "gemini-1.5-pro": (0.00125, 0.005),
    "gemini-1.5-flash": (0.000075, 0.0003),
}

SAMPLE_QUERIES = [
    "What are the quarterly sales figures?",
    "Summarize this document for me",
    "Help me debug this Python code",
    "Translate this text to Spanish",
    "Write a blog post about AI trends",
    "Analyze customer feedback sentiment",
    "Review this pull request",
    "Generate test cases for this function",
    "Explain this concept in simple terms",
    "Create a marketing email template",
]

ERROR_TYPES = ["timeout", "rate_limit", "context_length", "api_error", "validation_error"]
ERROR_MESSAGES = [
    "Request timed out after 30 seconds",
    "Rate limit exceeded, please retry",
    "Context length exceeded maximum tokens",
    "API returned unexpected error",
    "Input validation failed",
]


def random_datetime_in_range(start: datetime, end: datetime) -> datetime:
    """Generate a random datetime between start and end."""
    delta = end - start
    random_seconds = random.randint(0, int(delta.total_seconds()))
    return start + timedelta(seconds=random_seconds)


async def get_user_id(session: AsyncSession) -> uuid.UUID:
    """Get a user ID from the database, or create a test user."""
    result = await session.execute(text("SELECT id FROM users LIMIT 1"))
    row = result.fetchone()
    if row:
        return row[0]

    # Create a test user if none exists
    user_id = uuid.uuid4()
    await session.execute(
        text("""
            INSERT INTO users (id, username, password_hash, created_at, updated_at)
            VALUES (:id, :username, :password, NOW(), NOW())
            ON CONFLICT (username) DO NOTHING
        """),
        {"id": user_id, "username": "test_analytics_user", "password": "hashed_password"}
    )
    await session.commit()
    return user_id


async def seed_executions(session: AsyncSession, user_id: uuid.UUID, count: int = 200):
    """Seed agent execution records."""
    print(f"Seeding {count} agent executions...")

    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=90)

    executions = []
    for i in range(count):
        execution_id = uuid.uuid4()
        agent_name = random.choice(AGENT_NAMES)
        agent_type = random.choice(AGENT_TYPES)
        model_name = random.choice(MODEL_NAMES)

        # Determine status (80% success, 15% failure, 5% other)
        status_roll = random.random()
        if status_roll < 0.80:
            status = "success"
            error_type = None
            error_message = None
        elif status_roll < 0.95:
            status = "failure"
            error_idx = random.randint(0, len(ERROR_TYPES) - 1)
            error_type = ERROR_TYPES[error_idx]
            error_message = ERROR_MESSAGES[error_idx]
        else:
            status = random.choice(["timeout", "cancelled"])
            error_type = status
            error_message = f"Execution {status}"

        # Generate realistic token counts
        input_tokens = random.randint(100, 8000)
        output_tokens = random.randint(50, 4000)
        total_tokens = input_tokens + output_tokens

        # Calculate cost based on model
        input_cost_per_1k, output_cost_per_1k = MODEL_COSTS.get(model_name, (0.001, 0.002))
        cost = (input_tokens / 1000 * input_cost_per_1k) + (output_tokens / 1000 * output_cost_per_1k)

        # Generate timestamps
        started_at = random_datetime_in_range(start_date, end_date)
        execution_time_ms = random.randint(500, 30000)
        llm_time_ms = int(execution_time_ms * random.uniform(0.6, 0.9))
        completed_at = started_at + timedelta(milliseconds=execution_time_ms)

        executions.append({
            "id": execution_id,
            "user_id": user_id,
            "request_id": uuid.uuid4(),
            "session_id": uuid.uuid4(),
            "agent_id": uuid.uuid4(),
            "agent_name": agent_name,
            "agent_type": agent_type,
            "model_name": model_name,
            "status": status,
            "query_preview": random.choice(SAMPLE_QUERIES)[:100],
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "cost_usd": round(cost, 6),
            "execution_time_ms": execution_time_ms,
            "llm_time_ms": llm_time_ms,
            "started_at": started_at,
            "completed_at": completed_at if status == "success" else None,
            "error_type": error_type,
            "error_message": error_message,
        })

    # Insert executions
    for exec_data in executions:
        await session.execute(
            text("""
                INSERT INTO agentexecutions (
                    id, user_id, request_id, session_id, agent_id, agent_name, agent_type,
                    model_name, status, query_preview, input_tokens, output_tokens, total_tokens,
                    cost_usd, execution_time_ms, llm_time_ms, started_at, completed_at,
                    error_type, error_message, created_at, updated_at
                ) VALUES (
                    :id, :user_id, :request_id, :session_id, :agent_id, :agent_name, :agent_type,
                    :model_name, :status, :query_preview, :input_tokens, :output_tokens, :total_tokens,
                    :cost_usd, :execution_time_ms, :llm_time_ms, :started_at, :completed_at,
                    :error_type, :error_message, NOW(), NOW()
                )
            """),
            exec_data
        )

    await session.commit()
    print(f"  Created {count} executions")
    return executions


async def seed_token_usages(session: AsyncSession, executions: list):
    """Seed token usage records for executions."""
    print("Seeding token usage records...")

    count = 0
    for exec_data in executions:
        # Create 1-5 token usage records per execution
        num_usages = random.randint(1, 5)
        components = ["main_agent", "sub_agent", "tool_call", "retrieval", "summarizer"]

        for i in range(num_usages):
            input_tokens = random.randint(50, 2000)
            output_tokens = random.randint(25, 1000)
            input_cost_per_1k, output_cost_per_1k = MODEL_COSTS.get(exec_data["model_name"], (0.001, 0.002))
            cost = (input_tokens / 1000 * input_cost_per_1k) + (output_tokens / 1000 * output_cost_per_1k)

            await session.execute(
                text("""
                    INSERT INTO tokenusages (
                        id, execution_id, component, model, input_tokens, output_tokens,
                        cost_usd, step_number, created_at
                    ) VALUES (
                        :id, :execution_id, :component, :model, :input_tokens, :output_tokens,
                        :cost_usd, :step_number, NOW()
                    )
                """),
                {
                    "id": uuid.uuid4(),
                    "execution_id": exec_data["id"],
                    "component": random.choice(components),
                    "model": exec_data["model_name"],
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "cost_usd": round(cost, 6),
                    "step_number": i + 1,
                }
            )
            count += 1

    await session.commit()
    print(f"  Created {count} token usage records")


async def seed_execution_traces(session: AsyncSession, executions: list):
    """Seed execution trace records for ReAct loop visualization."""
    print("Seeding execution traces...")

    step_types = ["thought", "action", "observation", "tool_call", "final_answer"]
    sample_contents = {
        "thought": [
            "I need to analyze the user's request and determine the best approach.",
            "Let me break down this problem into smaller steps.",
            "I should first gather more information before proceeding.",
            "Based on the context, I'll need to use a specific tool.",
        ],
        "action": [
            "Calling the search API with the user's query.",
            "Executing database lookup for relevant records.",
            "Invoking the code analysis tool.",
            "Sending request to external service.",
        ],
        "observation": [
            "Received 5 relevant results from the search.",
            "Database returned 12 matching records.",
            "Code analysis completed with no critical issues.",
            "External service responded with success status.",
        ],
        "tool_call": [
            "Tool: web_search | Args: {'query': 'latest AI trends'}",
            "Tool: code_executor | Args: {'language': 'python', 'code': '...'}",
            "Tool: file_reader | Args: {'path': '/data/report.csv'}",
        ],
        "final_answer": [
            "Based on my analysis, here are the key findings...",
            "I've completed the task. The results show that...",
            "Here's the summary of what I found...",
        ],
    }

    count = 0
    for exec_data in executions:
        if exec_data["status"] != "success":
            continue

        # Create 3-8 trace steps per successful execution
        num_steps = random.randint(3, 8)
        base_time = exec_data["started_at"]

        for i in range(num_steps):
            step_type = step_types[i % len(step_types)]
            if i == num_steps - 1:
                step_type = "final_answer"

            duration_ms = random.randint(100, 3000)
            timestamp = base_time + timedelta(milliseconds=i * 1000)

            await session.execute(
                text("""
                    INSERT INTO executiontraces (
                        id, execution_id, step_number, step_type, content,
                        input_tokens, output_tokens, duration_ms, timestamp
                    ) VALUES (
                        :id, :execution_id, :step_number, :step_type, :content,
                        :input_tokens, :output_tokens, :duration_ms, :timestamp
                    )
                """),
                {
                    "id": uuid.uuid4(),
                    "execution_id": exec_data["id"],
                    "step_number": i + 1,
                    "step_type": step_type,
                    "content": random.choice(sample_contents.get(step_type, ["Processing..."])),
                    "input_tokens": random.randint(50, 500) if step_type in ["thought", "action"] else 0,
                    "output_tokens": random.randint(25, 300) if step_type in ["thought", "final_answer"] else 0,
                    "duration_ms": duration_ms,
                    "timestamp": timestamp,
                }
            )
            count += 1

    await session.commit()
    print(f"  Created {count} execution traces")


async def seed_budget_alerts(session: AsyncSession, user_id: uuid.UUID):
    """Seed budget alert records."""
    print("Seeding budget alerts...")

    alerts = [
        {"threshold": 50.00, "period_days": 7, "alert_type": "warning", "percentage": 80},
        {"threshold": 200.00, "period_days": 30, "alert_type": "warning", "percentage": 90},
        {"threshold": 500.00, "period_days": 30, "alert_type": "hard_stop", "percentage": 100},
    ]

    for alert in alerts:
        await session.execute(
            text("""
                INSERT INTO budgetalerts (
                    id, user_id, scope, threshold_usd, period_days, alert_type,
                    alert_at_percentage, is_active, email_notification, current_spend_usd, created_at, updated_at
                ) VALUES (
                    :id, :user_id, 'user', :threshold_usd, :period_days, :alert_type,
                    :alert_at_percentage, true, true, 0.00, NOW(), NOW()
                )
            """),
            {
                "id": uuid.uuid4(),
                "user_id": user_id,
                "threshold_usd": alert["threshold"],
                "period_days": alert["period_days"],
                "alert_type": alert["alert_type"],
                "alert_at_percentage": alert["percentage"],
            }
        )

    await session.commit()
    print(f"  Created {len(alerts)} budget alerts")


async def main():
    print("=" * 50)
    print("Analytics Data Seeder")
    print("=" * 50)

    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Get or create user
        user_id = await get_user_id(session)
        print(f"Using user ID: {user_id}")

        # Clear existing analytics data
        print("\nClearing existing analytics data...")
        await session.execute(text("DELETE FROM executiontraces"))
        await session.execute(text("DELETE FROM tokenusages"))
        await session.execute(text("DELETE FROM agentexecutions"))
        await session.execute(text("DELETE FROM budgetalerts"))
        await session.commit()

        # Seed data
        print("\nSeeding new data...")
        executions = await seed_executions(session, user_id, count=250)
        await seed_token_usages(session, executions)
        await seed_execution_traces(session, executions)
        await seed_budget_alerts(session, user_id)

        print("\n" + "=" * 50)
        print("Seeding complete!")
        print("=" * 50)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
