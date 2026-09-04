"""Durable LangGraph workflow for contract review.

The graph is deliberately kept at business-stage granularity. Each node writes
its progress to the application database while LangGraph writes the full state
to its checkpointer, so a worker can resume with the same thread id.
"""
import asyncio
import contextlib
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, TypedDict

from langgraph.graph import END, START, StateGraph
from sqlalchemy import select
from sqlalchemy.orm.attributes import flag_modified

from app.db.session import db
from app.core.config import settings
from app.models.contract import Contract, ContractType as ContractTypeEnum, ReviewStatus as ReviewStatusEnum
from app.models.review_run import ReviewRun, ReviewRunStatus, ReviewStep, ReviewStepStatus
from app.models.workspace import Workspace
from app.services.analysis.understanding import understanding_service
from app.services.document.parser import document_parser
from app.services.review.knowledge_manager import KnowledgeRetrievalManager
from app.services.review.service import review_service

logger = logging.getLogger(__name__)

STAGES = (
    "validate_and_prepare",
    "parse_document",
    "understand_contract",
    "retrieve_legal_context",
    "review_risks",
    "finalize_report",
)
STAGE_LABELS = {
    "validate_and_prepare": "合同准备",
    "parse_document": "文档解析",
    "understand_contract": "合同理解",
    "retrieve_legal_context": "法规检索",
    "review_risks": "风险审查",
    "finalize_report": "报告生成",
}
STAGE_PROGRESS = {stage: round(index / len(STAGES) * 100, 1) for index, stage in enumerate(STAGES, 1)}
def _resolve_contract_file_path(file_path: str) -> Path:
    from app.core.config import settings
    path = Path(file_path)
    if path.is_absolute():
        return path
    return Path(settings.STORAGE_PATH) / file_path


def _detect_contract_type(text: str) -> str:
    lower = (text or "").lower()
    keywords = {
        "NDA": ["保密协议", "保密合同", "confidentiality", "nda"],
        "劳动合同": ["劳动合同", "雇佣合同", "员工", "工资"],
        "采购合同": ["采购合同", "采购协议", "供应商"],
        "销售合同": ["销售合同", "销售协议", "买方", "卖方"],
        "服务合同": ["服务合同", "服务协议", "服务方"],
    }
    for contract_type, terms in keywords.items():
        if any(term.lower() in lower for term in terms):
            return contract_type
    return "其他"


class ReviewGraphState(TypedDict, total=False):
    contract_id: str
    run_id: str
    file_path: str
    contract_text: str
    contract_type: str
    tenant_id: Optional[str]
    review_config: Dict[str, Any]
    partitioned_context: Dict[str, List[Dict[str, Any]]]
    review_result: Dict[str, Any]
    completed_stages: List[str]


def stage_label(stage: Optional[str]) -> Optional[str]:
    return STAGE_LABELS.get(stage) if stage else None


async def create_review_run(contract_id: str, *, force_new: bool = False) -> ReviewRun:
    """Create or reuse a run. Reuse is what makes resume idempotent."""
    async with db.async_session_maker() as session:
        if not force_new:
            existing = await session.execute(
                select(ReviewRun)
                .where(ReviewRun.contract_id == contract_id)
                .where(ReviewRun.status.in_([ReviewRunStatus.queued, ReviewRunStatus.running, ReviewRunStatus.failed, ReviewRunStatus.stalled]))
                .order_by(ReviewRun.created_at.desc())
            )
            run = existing.scalars().first()
            if run:
                # A terminal run that exhausted retries must not leave the
                # contract pending forever; a fresh start gets a new run/id.
                if run.status in {ReviewRunStatus.failed, ReviewRunStatus.stalled} and (run.attempt or 0) >= 3:
                    run = None
                else:
                    return run

        run_id = str(uuid.uuid4())
        run = ReviewRun(
            id=run_id,
            contract_id=contract_id,
            status=ReviewRunStatus.queued,
            current_stage="validate_and_prepare",
            progress=0,
            checkpoint_thread_id=f"contract-review:{contract_id}:{run_id}",
        )
        session.add(run)
        for stage in STAGES:
            session.add(ReviewStep(run_id=run_id, stage=stage, status=ReviewStepStatus.waiting))
        await session.commit()
        await session.refresh(run)
        return run


async def _update_stage(run_id: str, stage: str, status: ReviewStepStatus, *, error: Optional[str] = None) -> None:
    now = datetime.utcnow()
    async with db.async_session_maker() as session:
        run = await session.get(ReviewRun, run_id)
        step_result = await session.execute(
            select(ReviewStep).where(ReviewStep.run_id == run_id, ReviewStep.stage == stage)
        )
        step = step_result.scalar_one_or_none()
        if not run or not step:
            return

        run.current_stage = stage
        run.last_heartbeat_at = now
        if status == ReviewStepStatus.running:
            run.status = ReviewRunStatus.running
            run.started_at = run.started_at or now
            step.attempt = (step.attempt or 0) + 1
            step.started_at = now
        elif status == ReviewStepStatus.completed:
            run.progress = STAGE_PROGRESS[stage]
            step.completed_at = now
            step.error = None
        elif status == ReviewStepStatus.failed:
            run.status = ReviewRunStatus.failed
            run.last_error = error
            step.error = error
        step.status = status
        await session.commit()


async def _heartbeat_loop(run_id: str, stage: str) -> None:
    while True:
        await asyncio.sleep(30)
        async with db.async_session_maker() as session:
            run = await session.get(ReviewRun, run_id)
            if run:
                run.current_stage = stage
                run.last_heartbeat_at = datetime.utcnow()
                await session.commit()


async def _load_contract(contract_id: str) -> Contract:
    async with db.async_session_maker() as session:
        result = await session.execute(select(Contract).where(Contract.id == contract_id))
        contract = result.scalar_one_or_none()
        if not contract:
            raise ValueError("合同不存在")
        return contract


async def _initial_state(run: ReviewRun) -> ReviewGraphState:
    """Rehydrate enough application state to resume even when local fallback memory was lost."""
    contract = await _load_contract(run.contract_id)
    completed = []
    async with db.async_session_maker() as session:
        result = await session.execute(select(ReviewStep).where(ReviewStep.run_id == run.id))
        completed = [step.stage for step in result.scalars().all() if step.status == ReviewStepStatus.completed]
        workspace = await session.get(Workspace, contract.workspace_id)
    return {
        "contract_id": run.contract_id,
        "run_id": run.id,
        "file_path": str(_resolve_contract_file_path(contract.file_path)),
        "contract_text": contract.content_text or "",
        "contract_type": contract.contract_type.value if contract.contract_type else "其他",
        "tenant_id": workspace.tenant_id if workspace else None,
        "review_config": contract.review_config or {},
        "completed_stages": completed,
    }


def build_review_graph(run_id: str):
    async def node(stage: str, fn, state: ReviewGraphState) -> ReviewGraphState:
        if stage in state.get("completed_stages", []):
            return state
        await _update_stage(run_id, stage, ReviewStepStatus.running)
        heartbeat_task = asyncio.create_task(_heartbeat_loop(run_id, stage))
        try:
            result = await fn(state)
            completed = list(result.get("completed_stages", state.get("completed_stages", [])))
            if stage not in completed:
                completed.append(stage)
            result["completed_stages"] = completed
            await _update_stage(run_id, stage, ReviewStepStatus.completed)
            return result
        except Exception as exc:
            await _update_stage(run_id, stage, ReviewStepStatus.failed, error=str(exc))
            raise
        finally:
            heartbeat_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await heartbeat_task

    async def validate(state):
        contract = await _load_contract(state["contract_id"])
        file_path = str(_resolve_contract_file_path(contract.file_path))
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"合同文件不存在: {file_path}")
        async with db.async_session_maker() as session:
            workspace = await session.get(Workspace, contract.workspace_id)
        return {
            **state,
            "file_path": file_path,
            "contract_type": contract.contract_type.value if contract.contract_type else "其他",
            "tenant_id": workspace.tenant_id if workspace else None,
            "review_config": contract.review_config or {},
        }

    async def parse(state):
        if state["file_path"].lower().endswith(".pdf"):
            # Reuse the active version created by document ingestion whenever
            # available; parsing here remains a compatibility fallback.
            from app.models.document import DocumentRecord, DocumentVersion
            async with db.async_session_maker() as session:
                record = (await session.execute(select(DocumentRecord).where(DocumentRecord.contract_id == state["contract_id"]))).scalar_one_or_none()
                version = await session.get(DocumentVersion, record.current_version_id) if record and record.current_version_id else None
            if version and version.status == "completed" and version.ast_snapshot:
                parsed = {"text": version.ast_snapshot.get("text", ""), "unified_document": version.ast_snapshot,
                          "document_id": record.id, "version_id": version.id}
            else:
                from app.services.document.ingestion_service import document_ingestion_service
                async with db.async_session_maker() as session:
                    contract = await session.get(Contract, state["contract_id"])
                    if not contract:
                        raise ValueError("合同不存在")
                    ingested = await document_ingestion_service.ingest_contract(session, contract, state["file_path"])
                    await session.commit()
                parsed = {"text": ingested["text"], "document_id": ingested["document_id"],
                          "version_id": ingested["version_id"]}
        else:
            from app.services.document.ingestion_service import document_ingestion_service
            async with db.async_session_maker() as session:
                contract = await session.get(Contract, state["contract_id"])
                if not contract:
                    raise ValueError("合同不存在")
                ingested = await document_ingestion_service.ingest_contract(session, contract, state["file_path"])
                await session.commit()
            parsed = {"text": ingested["text"], "document_id": ingested["document_id"],
                      "version_id": ingested["version_id"]}
        text = parsed.get("text", "")
        if not text.strip():
            raise ValueError("未能从合同中提取有效文本")
        contract_type = state.get("contract_type") or "其他"
        if contract_type == "其他":
            contract_type = _detect_contract_type(text)
        async with db.async_session_maker() as session:
            contract = await session.get(Contract, state["contract_id"])
            contract.content_text = text
            contract.contract_type = ContractTypeEnum(contract_type)
            contract.review_status = ReviewStatusEnum.processing
            await session.commit()
        return {**state, "contract_text": text, "contract_type": contract_type,
                "document_id": parsed.get("document_id"), "document_version_id": parsed.get("version_id"),
                "document_ast": parsed.get("unified_document")}

    async def understand(state):
        await understanding_service.generate_understanding(
            contract_id=state["contract_id"],
            contract_text=state["contract_text"],
            contract_type=state["contract_type"],
            review_result=None,
        )
        return state

    async def retrieve(state):
        context = await KnowledgeRetrievalManager().retrieve_all(
            contract_type=state["contract_type"], tenant_id=state.get("tenant_id")
        )
        from app.services.rag.retriever import retriever
        contract_context = await retriever.retrieve_contract_chunks(
            query=f"{state['contract_type']} 合同付款 违约责任 期限 解除 保密",
            contract_id=state["contract_id"], tenant_id=state.get("tenant_id"),
            top_k=settings.RAG_CONTRACT_TOP_K,
        )
        return {**state, "partitioned_context": context, "contract_context": contract_context}

    async def review(state):
        config = state.get("review_config") or {}
        result = await review_service.review_contract(
            contract_text=state["contract_text"],
            contract_type=state["contract_type"],
            tenant_id=state.get("tenant_id"),
            party_position=config.get("party_position"),
            contract_amount=config.get("contract_amount"),
            risk_preference=config.get("risk_preference"),
            partitioned_context=state.get("partitioned_context"),
            contract_context=state.get("contract_context"),
        )
        return {**state, "review_result": result}

    async def finalize(state):
        result = state["review_result"]
        risk_clauses = result.get("risk_clauses", [])
        if state["file_path"].lower().endswith(".pdf") and risk_clauses:
            from app.services.review.evidence_locator import locate_clauses_in_pdf
            evidence_map = await locate_clauses_in_pdf(state["contract_id"], state["file_path"], risk_clauses)
            for index, clause in enumerate(risk_clauses[:10]):
                evidence = evidence_map.get(str(index))
                if evidence:
                    clause["evidence_id"] = evidence["evidence_id"]
                    clause["evidence_locations"] = evidence["locations"]
                    clause["evidence_resolution_status"] = evidence["resolution_status"]

            # 综合建议没有独立坐标时，按对应风险条款的建议文本回填 evidence ID，
            # 让“修改建议”点击后也能回到原文。
            for suggestion in result.get("suggestions", []):
                content = str(suggestion.get("content", ""))
                matched = next((clause for clause in risk_clauses
                                if clause.get("suggestion") and
                                (clause["suggestion"] in content or content in clause["suggestion"])), None)
                if matched and matched.get("evidence_id"):
                    suggestion["evidence_id"] = matched["evidence_id"]
        risk = "high" if any(c.get("risk_level") == "high" for c in risk_clauses) else "medium" if any(c.get("risk_level") == "medium" for c in risk_clauses) else "low"
        # 补充带审查结果的理解摘要；服务本身按 contract_id 幂等更新。
        await understanding_service.generate_understanding(
            contract_id=state["contract_id"],
            contract_text=state["contract_text"],
            contract_type=state["contract_type"],
            review_result=result,
        )
        async with db.async_session_maker() as session:
            contract = await session.get(Contract, state["contract_id"])
            contract.review_result = result
            flag_modified(contract, "review_result")
            contract.risk_level = risk
            contract.review_status = ReviewStatusEnum.completed
            await session.commit()
        return state

    async def validate_node(s): return await node("validate_and_prepare", validate, s)
    async def parse_node(s): return await node("parse_document", parse, s)
    async def understand_node(s): return await node("understand_contract", understand, s)
    async def retrieve_node(s): return await node("retrieve_legal_context", retrieve, s)
    async def review_node(s): return await node("review_risks", review, s)
    async def finalize_node(s): return await node("finalize_report", finalize, s)

    graph = StateGraph(ReviewGraphState)
    graph.add_node("validate_and_prepare", validate_node)
    graph.add_node("parse_document", parse_node)
    graph.add_node("understand_contract", understand_node)
    graph.add_node("retrieve_legal_context", retrieve_node)
    graph.add_node("review_risks", review_node)
    graph.add_node("finalize_report", finalize_node)
    graph.add_edge(START, "validate_and_prepare")
    for first, second in zip(STAGES, STAGES[1:]):
        graph.add_edge(first, second)
    graph.add_edge("finalize_report", END)
    return graph


async def run_review_graph(run: ReviewRun, *, resume: bool = False) -> None:
    from app.core.config import settings

    settings.require_postgresql()
    initial = await _initial_state(run)
    graph = build_review_graph(run.id)

    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
    checkpoint_url = settings.DATABASE_URL
    checkpoint_url = checkpoint_url.replace("postgresql+asyncpg://", "postgresql://", 1).replace("postgres://", "postgresql://", 1)
    async with AsyncPostgresSaver.from_conn_string(checkpoint_url) as saver:
        await saver.setup()
        compiled = graph.compile(checkpointer=saver)
        await compiled.ainvoke(initial, config={"configurable": {"thread_id": run.checkpoint_thread_id}})

    async with db.async_session_maker() as session:
        current = await session.get(ReviewRun, run.id)
        if current:
            current.status = ReviewRunStatus.completed
            current.current_stage = "finalize_report"
            current.progress = 100
            current.completed_at = datetime.utcnow()
            current.last_heartbeat_at = datetime.utcnow()
            await session.commit()
