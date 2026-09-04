"""
动态审查阈值配置 - 根据甲乙方立场和风险偏好调整判定标准

使用场景：
- 甲方（买方）：希望更严格的付款条件、更高的违约金保护
- 乙方（卖方）：希望更宽松的付款条件、更低的违约金压力
- 低风险偏好：零容忍，严格保护
- 高风险偏好：可接受合理风险
"""
from typing import Dict, Any


class DynamicThresholds:
    """动态阈值管理器"""

    # 付款周期阈值（天）
    PAYMENT_PERIOD_THRESHOLDS = {
        # 甲方立场（希望快速回款）
        "party_a": {
            "low": {
                "compliant_max": 15,      # ≤15 天 ✅ 合规
                "approval_max": 30,       # 15-30 天 ⚠️ 需要审批
                "violation_above": 30     # >30 天 ❌ 违反政策
            },
            "medium": {
                "compliant_max": 30,      # ≤30 天 ✅ 合规
                "approval_max": 45,       # 30-45 天 ⚠️ 需要审批
                "violation_above": 45     # >45 天 ❌ 违反政策
            },
            "high": {
                "compliant_max": 45,      # ≤45 天 ✅ 合规
                "approval_max": 60,       # 45-60 天 ⚠️ 需要审批
                "violation_above": 60     # >60 天 ❌ 违反政策
            },
        },
        # 乙方立场（可以接受慢回款）
        "party_b": {
            "low": {
                "compliant_max": 30,      # ≤30 天 ✅ 合规
                "approval_max": 45,       # 30-45 天 ⚠️ 需要审批
                "violation_above": 45     # >45 天 ❌ 违反政策
            },
            "medium": {
                "compliant_max": 45,      # ≤45 天 ✅ 合规
                "approval_max": 60,       # 45-60 天 ⚠️ 需要审批
                "violation_above": 60     # >60 天 ❌ 违反政策
            },
            "high": {
                "compliant_max": 60,      # ≤60 天 ✅ 合规
                "approval_max": 90,       # 60-90 天 ⚠️ 需要审批
                "violation_above": 90     # >90 天 ❌ 违反政策
            },
        },
    }

    # 违约金比例阈值（%）
    PENALTY_RATE_THRESHOLDS = {
        # 甲方立场（希望高违约金保护）
        "party_a": {
            "low": {
                "compliant_min": 20,      # ≥20% ✅ 合规（保护充足）
                "approval_min": 15,       # 15-20% ⚠️ 保护不足
                "violation_below": 15     # <15% ❌ 保护严重不足
            },
            "medium": {
                "compliant_min": 15,      # ≥15% ✅ 合规
                "approval_min": 10,       # 10-15% ⚠️ 保护不足
                "violation_below": 10     # <10% ❌ 保护严重不足
            },
            "high": {
                "compliant_min": 10,      # ≥10% ✅ 合规
                "approval_min": 5,        # 5-10% ⚠️ 保护不足
                "violation_below": 5      # <5% ❌ 保护严重不足
            },
        },
        # 乙方立场（不希望高违约金压力）
        "party_b": {
            "low": {
                "compliant_max": 10,      # ≤10% ✅ 合规
                "approval_max": 15,       # 10-15% ⚠️ 需要审批
                "violation_above": 15     # >15% ❌ 压力过大
            },
            "medium": {
                "compliant_max": 15,      # ≤15% ✅ 合规
                "approval_max": 20,       # 15-20% ⚠️ 需要审批
                "violation_above": 20     # >20% ❌ 压力过大
            },
            "high": {
                "compliant_max": 20,      # ≤20% ✅ 合规
                "approval_max": 25,       # 20-25% ⚠️ 需要审批
                "violation_above": 25     # >25% ❌ 压力过大
            },
        },
    }

    # 保密期限阈值（年）
    CONFIDENTIALITY_PERIOD_THRESHOLDS = {
        # 甲方立场（希望长期保密）
        "party_a": {
            "low": {
                "compliant_max": 3,       # ≤3 年 ✅ 合规
                "approval_max": 5,        # 3-5 年 ⚠️ 需要审批
                "violation_above": 5      # >5 年 ❌ 太长（注意：这里甲方希望保密，但太长也不合理）
            },
            "medium": {
                "compliant_max": 5,       # ≤5 年 ✅ 合规
                "approval_max": 10,       # 5-10 年 ⚠️ 需要审批
                "violation_above": 10     # >10 年 ❌ 太长
            },
            "high": {
                "compliant_max": 10,      # ≤10 年 ✅ 合规
                "approval_max": 15,       # 10-15 年 ⚠️ 需要审批
                "violation_above": 15     # >15 年 ❌ 太长
            },
        },
        # 乙方立场（不希望长期保密负担）
        "party_b": {
            "low": {
                "compliant_max": 2,       # ≤2 年 ✅ 合规
                "approval_max": 3,        # 2-3 年 ⚠️ 需要审批
                "violation_above": 3      # >3 年 ❌ 负担过重
            },
            "medium": {
                "compliant_max": 3,       # ≤3 年 ✅ 合规
                "approval_max": 5,        # 3-5 年 ⚠️ 需要审批
                "violation_above": 5      # >5 年 ❌ 负担过重
            },
            "high": {
                "compliant_max": 5,       # ≤5 年 ✅ 合规
                "approval_max": 10,       # 5-10 年 ⚠️ 需要审批
                "violation_above": 10     # >10 年 ❌ 负担过重
            },
        },
    }

    # 合同金额倍数阈值（用于大额合同更严格审查）
    AMOUNT_MULTIPLIER_THRESHOLDS = {
        "low_risk_amount": 1000000,       # 100 万以上视为大额合同
        "medium_risk_amount": 5000000,    # 500 万以上视为重大合同
        "high_risk_amount": 10000000,     # 1000 万以上视为特大合同
    }

    @classmethod
    def get_payment_period_thresholds(
        cls,
        party_position: str,
        risk_preference: str
    ) -> Dict[str, int]:
        """
        获取付款周期阈值

        Args:
            party_position: "party_a" | "party_b"
            risk_preference: "low" | "medium" | "high"

        Returns:
            {"compliant_max": int, "approval_max": int, "violation_above": int}
        """
        return cls.PAYMENT_PERIOD_THRESHOLDS.get(
            party_position, cls.PAYMENT_PERIOD_THRESHOLDS["party_a"]
        ).get(
            risk_preference, cls.PAYMENT_PERIOD_THRESHOLDS["party_a"]["medium"]
        )

    @classmethod
    def get_penalty_rate_thresholds(
        cls,
        party_position: str,
        risk_preference: str
    ) -> Dict[str, int]:
        """
        获取违约金比例阈值

        Args:
            party_position: "party_a" | "party_b"
            risk_preference: "low" | "medium" | "high"

        Returns:
            {"compliant_min/max": int, "approval_min/max": int, "violation_below/above": int}
        """
        return cls.PENALTY_RATE_THRESHOLDS.get(
            party_position, cls.PENALTY_RATE_THRESHOLDS["party_a"]
        ).get(
            risk_preference, cls.PENALTY_RATE_THRESHOLDS["party_a"]["medium"]
        )

    @classmethod
    def get_confidentiality_period_thresholds(
        cls,
        party_position: str,
        risk_preference: str
    ) -> Dict[str, int]:
        """
        获取保密期限阈值

        Args:
            party_position: "party_a" | "party_b"
            risk_preference: "low" | "medium" | "high"

        Returns:
            {"compliant_max": int, "approval_max": int, "violation_above": int}
        """
        return cls.CONFIDENTIALITY_PERIOD_THRESHOLDS.get(
            party_position, cls.CONFIDENTIALITY_PERIOD_THRESHOLDS["party_a"]
        ).get(
            risk_preference, cls.CONFIDENTIALITY_PERIOD_THRESHOLDS["party_a"]["medium"]
        )

    @classmethod
    def get_amount_risk_level(cls, contract_amount: float) -> str:
        """
        根据合同金额获取风险等级

        Args:
            contract_amount: 合同金额（元）

        Returns:
            "low" | "medium" | "high"
        """
        if contract_amount >= cls.AMOUNT_MULTIPLIER_THRESHOLDS["high_risk_amount"]:
            return "high"
        elif contract_amount >= cls.AMOUNT_MULTIPLIER_THRESHOLDS["medium_risk_amount"]:
            return "medium"
        else:
            return "low"

    @classmethod
    def get_review_strictness_multiplier(cls, contract_amount: float) -> float:
        """
        获取审查严格度乘数（用于调整阈值）

        大额合同需要更严格的审查

        Args:
            contract_amount: 合同金额（元）

        Returns:
            乘数（0.8-1.2，越小越严格）
        """
        if contract_amount >= cls.AMOUNT_MULTIPLIER_THRESHOLDS["high_risk_amount"]:
            return 0.8  # 更严格 20%
        elif contract_amount >= cls.AMOUNT_MULTIPLIER_THRESHOLDS["medium_risk_amount"]:
            return 0.9  # 更严格 10%
        elif contract_amount >= cls.AMOUNT_MULTIPLIER_THRESHOLDS["low_risk_amount"]:
            return 0.95  # 更严格 5%
        else:
            return 1.0  # 标准


# 全局实例
dynamic_thresholds = DynamicThresholds()
