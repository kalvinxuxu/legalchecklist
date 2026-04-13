"""
法律知识库模型
向量数据已迁移到 Chroma，此表仅存储原始数据和元数据
"""
from sqlalchemy import Column, String, Text, JSON, Index
from app.models.base import Base, UUIDMixin, TimestampMixin

# Chroma 负责向量存储，无需在关系数据库中存储向量
# embedding 字段保留用于兼容，但不再使用


class LegalKnowledge(Base, UUIDMixin, TimestampMixin):
    """法律知识库表"""

    __tablename__ = "legal_knowledge"

    title = Column(String(255), nullable=False, comment="标题")
    content = Column(Text, nullable=False, comment="内容")
    content_type = Column(String(50), nullable=False, comment="内容类型 (law/case/template/rule/company_policy)")
    metadata_json = Column(JSON, nullable=True, comment="元数据")
    tenant_id = Column(String(36), nullable=True, comment="租户 ID（私有库）")

    # 向量嵌入已迁移到 Chroma，此字段仅保留用于向后兼容
    # 新增数据不再写入此字段
    embedding = Column(JSON, nullable=True, comment="向量嵌入（已迁移到 Chroma，仅兼容保留）")

    # 索引策略
    __table_args__ = (
        Index("ft_title_content", "title", "content", mysql_prefix="FULLTEXT"),
        Index("idx_content_type", "content_type"),
        Index("idx_tenant_id", "tenant_id"),
    )

    def __repr__(self):
        return f"<LegalKnowledge(id={self.id}, title={self.title})>"
