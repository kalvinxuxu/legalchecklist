#!/usr/bin/env python3
"""
历史法律知识批量向量化脚本

用途：将 SQLite 中已有的 legal_knowledge 记录的 embedding 字段填充

使用方法:
    # 激活虚拟环境
    cd backend
    .\venv\Scripts\activate

    # 运行脚本
    python scripts/backfill_embeddings.py

前置条件:
    1. 已安装 PostgreSQL + pgvector
    2. 已将 .env 配置为 DATABASE_TYPE=postgresql
    3. legal_knowledge 表已添加 embedding 列
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.session import db
from app.services.rag.embedder import embedder
from app.models.legal_knowledge import LegalKnowledge
from app.core.config import settings
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def get_knowledge_without_embedding(limit: int = 1000):
    """获取尚未生成向量的知识记录"""
    from sqlalchemy import select

    async with db.async_session_maker() as session:
        if settings.is_postgresql:
            # PostgreSQL: embedding IS NULL
            stmt = select(LegalKnowledge).where(LegalKnowledge.embedding == None).limit(limit)
        else:
            # SQLite: 不支持 vector，暂跳过
            logger.warning("当前数据库不是 PostgreSQL，无法使用 pgvector 向量功能")
            return []

        result = await session.execute(stmt)
        return list(result.scalars().all())


async def update_knowledge_embedding(knowledge_id: str, embedding: list):
    """更新单条知识的向量"""
    from sqlalchemy import update

    async with db.async_session_maker() as session:
        await session.execute(
            update(LegalKnowledge)
            .where(LegalKnowledge.id == knowledge_id)
            .values(embedding=embedding)
        )
        await session.commit()


async def backfill_embeddings(batch_size: int = 32, dry_run: bool = False):
    """
    批量为历史法律知识生成向量

    Args:
        batch_size: 每批处理的记录数
        dry_run: True 则只统计数量不实际更新
    """
    logger.info("=" * 60)
    logger.info("法律知识向量化脚本启动")
    logger.info(f"数据库类型: {settings.DATABASE_TYPE}")
    logger.info(f"Embedding 维度: {settings.EMBEDDING_DIMENSION}")
    logger.info(f"批次大小: {batch_size}")
    logger.info(f"模拟运行: {dry_run}")
    logger.info("=" * 60)

    # 检查数据库类型
    if not settings.is_postgresql:
        logger.error("错误：此脚本需要 PostgreSQL + pgvector 数据库")
        logger.error(f"当前数据库类型: {settings.DATABASE_TYPE}")
        logger.error("请在 .env 中设置 DATABASE_TYPE=postgresql")
        return

    # 连接数据库
    db.connect()
    logger.info("数据库连接成功")

    total_processed = 0
    total_embedding_tokens = 0  # 估算 API 调用 token 成本

    while True:
        # 获取待处理记录
        records = await get_knowledge_without_embedding(limit=batch_size)
        if not records:
            logger.info("没有更多待处理记录")
            break

        if dry_run:
            logger.info(f"[模拟] 发现 {len(records)} 条待处理记录")
            total_processed += len(records)
            continue

        logger.info(f"处理批次: {len(records)} 条记录")

        # 准备批量向量化
        texts_to_embed = []
        record_ids = []

        for record in records:
            text = f"{record.title} {record.content}"
            # 估算 token（中文约 1 token/字符，英文约 1 token/单词）
            total_embedding_tokens += len(text) // 2
            texts_to_embed.append(text)
            record_ids.append(record.id)

        # 批量生成向量
        try:
            embeddings = await embedder.embed_batch(texts_to_embed)

            # 批量更新
            for record_id, embedding in zip(record_ids, embeddings):
                await update_knowledge_embedding(record_id, embedding)
                total_processed += 1

            logger.info(f"成功处理 {len(records)} 条记录 (累计: {total_processed})")

        except Exception as e:
            logger.error(f"批次处理出错: {e}")
            # 单条重试
            for record_id, text in zip(record_ids, texts_to_embed):
                try:
                    embedding = await embedder.embed(text)
                    await update_knowledge_embedding(record_id, embedding)
                    total_processed += 1
                    total_embedding_tokens += len(text) // 2
                except Exception as e2:
                    logger.error(f"记录 {record_id} 向量化失败: {e2}")

    logger.info("=" * 60)
    logger.info(f"处理完成！")
    logger.info(f"总处理记录数: {total_processed}")
    logger.info(f"估算 Embedding API 消耗: ~{total_embedding_tokens} tokens")
    logger.info("=" * 60)

    await db.disconnect()


async def check_embedding_status():
    """检查向量化进度"""
    from sqlalchemy import select, func

    db.connect()

    async with db.async_session_maker() as session:
        # 总记录数
        total_result = await session.execute(select(func.count()).select_from(LegalKnowledge))
        total_count = total_result.scalar()

        # 已向量化记录数（PostgreSQL）
        if settings.is_postgresql:
            vectored_result = await session.execute(
                select(func.count()).select_from(LegalKnowledge)
                .where(LegalKnowledge.embedding != None)
            )
            vectored_count = vectored_result.scalar()
        else:
            vectored_count = 0

    logger.info("=" * 60)
    logger.info("向量化状态检查")
    logger.info(f"总记录数: {total_count}")
    logger.info(f"已向量化: {vectored_count}")
    logger.info(f"待向量化: {total_count - vectored_count}")
    logger.info(f"完成进度: {vectored_count/total_count*100:.1f}%" if total_count > 0 else "N/A")
    logger.info("=" * 60)

    await db.disconnect()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="法律知识批量向量化脚本")
    parser.add_argument("--batch-size", type=int, default=32, help="每批处理数量")
    parser.add_argument("--dry-run", action="store_true", help="仅统计不实际更新")
    parser.add_argument("--status", action="store_true", help="检查向量化状态")
    args = parser.parse_args()

    if args.status:
        asyncio.run(check_embedding_status())
    else:
        asyncio.run(backfill_embeddings(
            batch_size=args.batch_size,
            dry_run=args.dry_run
        ))
