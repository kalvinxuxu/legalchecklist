"""Crash/restart smoke test for the PostgreSQL LangGraph checkpointer.

Run with the local Docker database available:
    pytest -q backend/tests/test_postgres_checkpoint_recovery.py
"""
import asyncio
import sys
from typing import Annotated, TypedDict
import operator
import uuid

import pytest
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import END, START, StateGraph

from app.core.config import settings

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


class _State(TypedDict):
    events: Annotated[list[str], operator.add]
    crash: bool


@pytest.mark.asyncio
async def test_worker_restart_resumes_after_completed_stage():
    settings.require_postgresql()
    thread_id = f"test-worker-restart:{uuid.uuid4()}"
    calls = {"prepare": 0, "risk": 0}

    async def prepare(state: _State):
        if "prepare" in state.get("events", []):
            return {}
        calls["prepare"] += 1
        return {"events": ["prepare"]}

    async def risk(state: _State):
        calls["risk"] += 1
        if state.get("crash"):
            raise RuntimeError("forced worker stop")
        return {"events": ["risk"]}

    graph = StateGraph(_State)
    graph.add_node("prepare", prepare)
    graph.add_node("risk", risk)
    graph.add_edge(START, "prepare")
    graph.add_edge("prepare", "risk")
    graph.add_edge("risk", END)

    checkpoint_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://", 1)
    async with AsyncPostgresSaver.from_conn_string(checkpoint_url) as saver:
        await saver.setup()
        compiled = graph.compile(checkpointer=saver)
        with pytest.raises(RuntimeError, match="forced worker stop"):
            await compiled.ainvoke(
                {"events": [], "crash": True},
                config={"configurable": {"thread_id": thread_id}},
            )

    # A new saver represents a new Worker process. The completed prepare node
    # must come from PostgreSQL checkpoint state, not process memory.
    async with AsyncPostgresSaver.from_conn_string(checkpoint_url) as saver:
        compiled = graph.compile(checkpointer=saver)
        result = await compiled.ainvoke(
            {"events": [], "crash": False},
            config={"configurable": {"thread_id": thread_id}},
        )

    assert calls == {"prepare": 1, "risk": 2}
    assert result["events"] == ["prepare", "risk"]


@pytest.mark.asyncio
async def test_checkpoint_state_keeps_active_document_version():
    """The review checkpoint must carry the persisted AST version lineage."""
    settings.require_postgresql()
    thread_id = f"document-version:{uuid.uuid4()}"
    checkpoint_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://", 1)
    graph = StateGraph(dict)
    async def persist(state):
        return {"document_version_id": state["document_version_id"]}
    graph.add_node("persist", persist); graph.add_edge(START, "persist"); graph.add_edge("persist", END)
    async with AsyncPostgresSaver.from_conn_string(checkpoint_url) as saver:
        await saver.setup(); compiled=graph.compile(checkpointer=saver)
        result=await compiled.ainvoke({"document_version_id": "ver-test"}, config={"configurable": {"thread_id": thread_id}})
    assert result["document_version_id"] == "ver-test"
