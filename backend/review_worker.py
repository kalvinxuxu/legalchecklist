"""Durable contract review worker.

Run with: python review_worker.py
The API only enqueues review runs; this process owns execution and recovery.
"""
import asyncio
import logging
import sys
from datetime import datetime, timedelta

from sqlalchemy import select

from app.core.config import settings
from app.db.session import db
from app.models.contract import Contract, ReviewStatus as ContractReviewStatus
from app.models.review_run import ReviewRun, ReviewRunStatus, ReviewStep, ReviewStepStatus
from app.services.review.durable_graph import run_review_graph

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)
POLL_SECONDS = 2
STALE_AFTER_MINUTES = 5
MAX_ATTEMPTS = 3

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def mark_stale_runs() -> None:
    cutoff = datetime.utcnow() - timedelta(minutes=STALE_AFTER_MINUTES)
    async with db.async_session_maker() as session:
        result = await session.execute(
            select(ReviewRun).where(
                ReviewRun.status == ReviewRunStatus.running,
                ReviewRun.last_heartbeat_at < cutoff,
            )
        )
        for run in result.scalars().all():
            run.status = ReviewRunStatus.stalled
            run.last_error = "任务心跳超时，已保留断点，可从断点继续"
        await session.commit()


async def claim_run() -> tuple[ReviewRun | None, bool]:
    async with db.async_session_maker() as session:
        result = await session.execute(
            select(ReviewRun)
            .where(ReviewRun.status.in_([ReviewRunStatus.queued, ReviewRunStatus.stalled, ReviewRunStatus.failed]))
            .where(ReviewRun.attempt < MAX_ATTEMPTS)
            .order_by(ReviewRun.created_at)
            .limit(1)
        )
        run = result.scalars().first()
        if not run:
            return None, False
        step_result = await session.execute(select(ReviewStep).where(ReviewStep.run_id == run.id))
        steps = step_result.scalars().all()
        resume = run.status != ReviewRunStatus.queued or any(
            step.status in {ReviewStepStatus.completed, ReviewStepStatus.failed} for step in steps
        )
        run.status = ReviewRunStatus.running
        run.attempt = (run.attempt or 0) + 1
        run.last_heartbeat_at = datetime.utcnow()
        await session.commit()
        await session.refresh(run)
        return run, resume


async def process_one() -> bool:
    run, resume = await claim_run()
    if not run:
        return False
    logger.info("Starting review run %s for contract %s", run.id, run.contract_id)
    try:
        await run_review_graph(run, resume=resume)
        logger.info("Completed review run %s", run.id)
    except Exception as exc:
        logger.exception("Review run %s failed: %s", run.id, exc)
        async with db.async_session_maker() as session:
            current = await session.get(ReviewRun, run.id)
            if current:
                current.status = ReviewRunStatus.failed
                current.last_error = str(exc)
                current.last_heartbeat_at = datetime.utcnow()
                contract = await session.get(Contract, current.contract_id)
                if contract:
                    contract.review_status = ContractReviewStatus.failed
                    contract.review_error = str(exc)
                await session.commit()
    return True


async def worker_loop() -> None:
    settings.require_postgresql()
    db.connect()
    await db.create_all_tables()
    logger.info("Review worker started")
    while True:
        await mark_stale_runs()
        processed = await process_one()
        if not processed:
            await asyncio.sleep(POLL_SECONDS)


if __name__ == "__main__":
    asyncio.run(worker_loop())
