"""
条款定位模型
存储风险条款在 PDF 中的位置信息
"""
from sqlalchemy import Column, String, Integer, JSON, Float, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.models.base import Base, UUIDMixin, TimestampMixin


class ClauseLocation(Base, UUIDMixin, TimestampMixin):
    """条款 PDF 定位表"""

    __tablename__ = "clause_locations"

    contract_id = Column(
        String(36),
        ForeignKey("contracts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="合同 ID"
    )

    understanding_id = Column(
        String(36),
        ForeignKey("contract_understandings.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="理解分析结果 ID"
    )

    # 关联的风险条款信息
    clause_hash = Column(
        String(64),
        nullable=True,
        comment="条款内容哈希（用于去重和关联）"
    )

    clause_title = Column(
        String(200),
        nullable=True,
        comment="条款标题"
    )

    clause_text = Column(
        Text,
        nullable=True,
        comment="条款原文"
    )

    risk_level = Column(
        String(20),
        nullable=True,
        comment="风险等级: high, medium, low"
    )

    # PDF 位置信息
    page_number = Column(
        Integer,
        nullable=True,
        comment="PDF 页码（从 0 开始）"
    )

    bbox_x0 = Column(
        Float,
        nullable=True,
        comment="边界框左上角 X 坐标"
    )

    bbox_y0 = Column(
        Float,
        nullable=True,
        comment="边界框左上角 Y 坐标"
    )

    bbox_x1 = Column(
        Float,
        nullable=True,
        comment="边界框右下角 X 坐标"
    )

    bbox_y1 = Column(
        Float,
        nullable=True,
        comment="边界框右下角 Y 坐标"
    )

    # 匹配信息
    similarity = Column(
        Float,
        nullable=True,
        comment="匹配相似度 0-1"
    )

    match_type = Column(
        String(20),
        nullable=True,
        comment="匹配类型: exact, fuzzy, ocr_fuzzy"
    )

    # 扩展信息
    extra_data = Column(
        JSON,
        nullable=True,
        comment="额外数据（如 OCR 模式下的原文等）"
    )

    # 关联关系
    contract = relationship("Contract", back_populates="clause_locations")
    understanding = relationship("ContractUnderstanding", back_populates="clause_locations")

    @property
    def bbox(self):
        """返回 bbox 字典"""
        if all([self.bbox_x0 is not None, self.bbox_y0 is not None,
                self.bbox_x1 is not None, self.bbox_y1 is not None]):
            return {
                "x0": self.bbox_x0,
                "y0": self.bbox_y0,
                "x1": self.bbox_x1,
                "y1": self.bbox_y1
            }
        return None

    def __repr__(self):
        return f"<ClauseLocation(contract_id={self.contract_id}, page={self.page_number})>"
