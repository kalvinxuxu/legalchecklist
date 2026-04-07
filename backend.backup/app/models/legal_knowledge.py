"""
法律知识库模型
"""
from sqlalchemy import Column, String, Text, JSON, Index
from app.models.base import Base, UUIDMixin, TimestampMixin


class LegalKnowledge(Base, UUIDMixin, TimestampMixin):
    """法律知识库表"""

    __tablename__ = "legal_knowledge"

    title = Column(String(255), nullable=False, comment="标题")
    content = Column(Text, nullable=False, comment="内容")
    content_type = Column(String(50), nullable=False, comment="内容类型 (law/case/template/rule)")
    metadata_json = Column(JSON, nullable=True, comment="元数据")
    tenant_id = Column(String(36), nullable=True, comment="租户 ID（私有库）")

    # 全文索引（MySQL）
    __table_args__ = (
        Index("ft_title_content", "title", "content", mysql_prefix="FULLTEXT"),
    )

    def __repr__(self):
        return f"<LegalKnowledge(id={self.id}, title={self.title})>"
