"""
法律知识库模型
"""
from sqlalchemy import Column, String, Text, JSON, Index
from app.models.base import Base, UUIDMixin, TimestampMixin
from app.core.config import settings

# pgvector 支持（可选，PostgreSQL 专用）
try:
    from pgvector.sqlalchemy import Vector
    HAS_PGVECTOR = True
except ImportError:
    HAS_PGVECTOR = False
    Vector = None


# 动态构建索引策略
def _get_table_args():
    args = [
        # MySQL: 全文索引（所有数据库通用）
        Index("ft_title_content", "title", "content", mysql_prefix="FULLTEXT"),
    ]
    # PostgreSQL: HNSW 向量索引
    if HAS_PGVECTOR:
        args.insert(0, Index(
            "idx_legal_knowledge_embedding",
            "embedding",
            postgresql_using="hnsw",
            postgresql_ops={"embedding": "vector_cosine_ops"}
        ))
    return tuple(args)


class LegalKnowledge(Base, UUIDMixin, TimestampMixin):
    """法律知识库表"""

    __tablename__ = "legal_knowledge"

    title = Column(String(255), nullable=False, comment="标题")
    content = Column(Text, nullable=False, comment="内容")
    content_type = Column(String(50), nullable=False, comment="内容类型 (law/case/template/rule)")
    metadata_json = Column(JSON, nullable=True, comment="元数据")
    tenant_id = Column(String(36), nullable=True, comment="租户 ID（私有库）")

    # 向量嵌入（PostgreSQL + pgvector 专用）
    # SQLite/MySQL 下此列为 NULL，不影响功能
    embedding = Column(
        Vector(settings.EMBEDDING_DIMENSION),
        nullable=True,
        comment=f"向量嵌入 ({settings.EMBEDDING_DIMENSION}维)"
    ) if HAS_PGVECTOR else Column(JSON, nullable=True)

    # 索引策略
    __table_args__ = _get_table_args()

    def __repr__(self):
        return f"<LegalKnowledge(id={self.id}, title={self.title})>"
