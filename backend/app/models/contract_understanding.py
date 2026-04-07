"""
合同理解分析结果模型
"""
from sqlalchemy import Column, String, Text, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.models.base import Base, UUIDMixin, TimestampMixin


class ContractUnderstanding(Base, UUIDMixin, TimestampMixin):
    """合同理解分析结果表"""

    __tablename__ = "contract_understandings"

    contract_id = Column(
        String(36),
        ForeignKey("contracts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="合同 ID"
    )

    contract_type = Column(
        String(50),
        nullable=False,
        comment="合同类型"
    )

    # 结构分析结果
    structure = Column(
        JSON,
        nullable=True,
        comment="合同结构分析结果"
    )
    # 结构示例: {
    #   "sections": [{"title": "保密范围", "content": "...", "start_pos": 0.0, "end_pos": 0.1}],
    #   "structure_summary": "本合同为标准NDA协议，共8章",
    #   "total_chapters": 8
    # }

    # 条款摘要结果
    summary = Column(
        JSON,
        nullable=True,
        comment="关键条款摘要"
    )
    # 摘要示例: {
    #   "key_clauses": [{"title": "保密范围", "summary": "...", "category": "obligation", "risk_benefit": "neutral"}],
    #   "payment_terms": {"amount": "50万元", "payment_method": "银行转账", "payment_time": "签订后5日内"},
    #   "breach_liability": {"default_definitions": "...", "liability_content": "...", "compensation_range": "不超过合同金额"}
    # }

    # 快速理解卡片
    quick_cards = Column(
        JSON,
        nullable=True,
        comment="快速理解卡片数据"
    )
    # 快速卡片示例: {
    #   "contract_purpose": "技术秘密保护",
    #   "key_dates": ["合同生效: 2024-01-01", "保密期限: 3年"],
    #   "payment_summary": "技术服务费50万元，分3期支付",
    #   "breach_summary": "违约方承担合同金额20%的违约金",
    #   "core_obligations": ["甲方: 提供技术资料", "乙方: 保密义务"]
    # }

    # 关联关系
    contract = relationship("Contract", back_populates="understanding")
    clause_locations = relationship(
        "ClauseLocation",
        back_populates="understanding",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_contract_understanding_contract_id", "contract_id"),
    )

    def __repr__(self):
        return f"<ContractUnderstanding(contract_id={self.contract_id})>"
