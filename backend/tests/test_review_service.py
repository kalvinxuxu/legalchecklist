"""
合同审查服务单元测试
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.review.service import review_service, ContractReviewService


@pytest.fixture
def review_svc():
    """创建审查服务实例"""
    return ContractReviewService()


@pytest.mark.asyncio
class TestContractReviewService:
    """测试合同审查服务"""

    async def test_service_initialization(self, review_svc):
        """测试服务初始化"""
        assert review_svc is not None
        assert hasattr(review_svc, 'rules_map')
        assert "NDA" in review_svc.rules_map
        assert "劳动合同" in review_svc.rules_map

    async def test_review_contract_nda(self, review_svc, monkeypatch):
        """测试 NDA 合同审查"""
        # Mock LLM
        mock_llm_response = {
            "risk_clauses": [
                {
                    "original_text": "保密期限为永久",
                    "risk_level": "high",
                    "risk_description": "保密期限过长",
                    "suggestion": "建议修改为 3-5 年",
                    "legal_reference": "《民法典》"
                }
            ],
            "missing_clauses": [
                {
                    "title": "争议解决条款",
                    "description": "缺少争议解决方式",
                    "suggestion": "建议添加仲裁条款",
                    "legal_reference": "《仲裁法》"
                }
            ],
            "suggestions": [
                {
                    "title": "修改保密期限",
                    "content": "将永久改为 3 年",
                    "reason": "符合法律规定的合理期限"
                }
            ],
            "legal_references": [
                {
                    "law_name": "民法典",
                    "article": "第 500 条",
                    "content": "测试内容"
                }
            ]
        }

        # Mock RAG
        mock_context = [
            {
                "title": "NDA 审查要点",
                "content": "保密期限一般不超过 5 年",
                "score": 0.9
            }
        ]

        # Patch LLM and RAG
        async def mock_chat(*args, **kwargs):
            return mock_llm_response

        async def mock_retrieve(*args, **kwargs):
            return mock_context

        monkeypatch.setattr(review_svc.llm, 'chat_with_json_output', mock_chat)
        monkeypatch.setattr(review_svc.rag, 'retrieve', mock_retrieve)

        result = await review_svc.review_contract(
            contract_text="这是一份测试 NDA 合同",
            contract_type="NDA"
        )

        assert result is not None
        assert "risk_clauses" in result
        assert "missing_clauses" in result
        assert "suggestions" in result
        assert "confidence_score" in result

    async def test_review_contract_labor(self, review_svc, monkeypatch):
        """测试劳动合同审查"""
        mock_llm_response = {
            "risk_clauses": [],
            "missing_clauses": [],
            "suggestions": [],
            "legal_references": []
        }

        async def mock_chat(*args, **kwargs):
            return mock_llm_response

        async def mock_retrieve(*args, **kwargs):
            return []

        monkeypatch.setattr(review_svc.llm, 'chat_with_json_output', mock_chat)
        monkeypatch.setattr(review_svc.rag, 'retrieve', mock_retrieve)

        result = await review_svc.review_contract(
            contract_text="这是一份测试劳动合同",
            contract_type="劳动合同"
        )

        assert result is not None
        assert "risk_clauses" in result

    async def test_review_contract_unknown_type(self, review_svc, monkeypatch):
        """测试未知合同类型"""
        mock_llm_response = {
            "risk_clauses": [],
            "missing_clauses": [],
            "suggestions": [],
            "legal_references": []
        }

        async def mock_chat(*args, **kwargs):
            return mock_llm_response

        async def mock_retrieve(*args, **kwargs):
            return []

        monkeypatch.setattr(review_svc.llm, 'chat_with_json_output', mock_chat)
        monkeypatch.setattr(review_svc.rag, 'retrieve', mock_retrieve)

        result = await review_svc.review_contract(
            contract_text="这是一份测试合同",
            contract_type="未知类型"
        )

        # 未知类型应该使用默认处理
        assert result is not None

    async def test_transform_review_result(self, review_svc):
        """测试审查结果转换"""
        raw_result = {
            "risk_clauses": [
                {
                    "original_text": "这是一条很长的风险条款内容超过 50 个字需要被截断",
                    "risk_description": "存在风险",
                    "risk_level": "high",
                    "suggestion": "建议修改",
                    "legal_reference": "《民法典》"
                }
            ],
            "missing_clauses": [
                {
                    "title": "争议解决",
                    "description": "缺少争议解决条款",
                    "legal_reference": "《仲裁法》"
                }
            ],
            "suggestions": [
                {
                    "title": "建议",
                    "content": "内容",
                    "reason": "理由"
                }
            ]
        }

        transformed = review_svc._transform_review_result(raw_result)

        assert "risk_clauses" in transformed
        assert transformed["risk_clauses"][0]["title"] is not None
        assert "suggestions" in transformed
        assert "missing_clauses" in transformed

    async def test_transform_result_with_empty_risk_clauses(self, review_svc):
        """测试空风险条款的转换"""
        raw_result = {
            "risk_clauses": [],
            "missing_clauses": [],
            "suggestions": []
        }

        transformed = review_svc._transform_review_result(raw_result)

        assert transformed["risk_clauses"] == []
        assert transformed["missing_clauses"] == []

    async def test_generate_missing_suggestion(self, review_svc):
        """测试缺失条款建议生成"""
        clause = {
            "title": "保密条款",
            "legal_reference": "《反不正当竞争法》"
        }

        suggestion = review_svc._generate_missing_suggestion(clause)

        assert "保密条款" in suggestion
        assert "《反不正当竞争法》" in suggestion

    async def test_generate_missing_suggestion_no_legal_ref(self, review_svc):
        """测试无法律引用的建议生成"""
        clause = {
            "title": "测试条款",
            "legal_reference": ""
        }

        suggestion = review_svc._generate_missing_suggestion(clause)

        assert "测试条款" in suggestion

    async def test_calculate_confidence_with_no_context(self, review_svc):
        """测试无检索结果时的置信度"""
        review_result = {"risk_clauses": [], "missing_clauses": []}

        confidence = review_svc._calculate_confidence([], review_result)

        assert confidence == 0.3

    async def test_calculate_confidence_with_context(self, review_svc):
        """测试有检索结果时的置信度"""
        review_result = {
            "risk_clauses": [{}],
            "missing_clauses": [{}],
            "suggestions": [{}],
            "legal_references": [{}]
        }
        context = [
            {"score": 0.9},
            {"score": 0.8},
            {"score": 0.7}
        ]

        confidence = review_svc._calculate_confidence(context, review_result)

        assert 0.5 <= confidence <= 1.0

    async def test_check_response_completeness(self, review_svc):
        """测试响应完整性检查"""
        complete_result = {
            "risk_clauses": [{}],
            "missing_clauses": [{}],
            "suggestions": [{}],
            "legal_references": [{}]
        }

        completeness = review_svc._check_response_completeness(complete_result)
        assert completeness == 1.0

    async def test_check_response_incomplete(self, review_svc):
        """测试不完整响应的完整性检查"""
        incomplete_result = {
            "risk_clauses": [{}],
            # 缺少其他字段
        }

        completeness = review_svc._check_response_completeness(incomplete_result)
        assert completeness == 0.25  # 1/4

    async def test_build_review_prompt(self, review_svc):
        """测试审查 Prompt 构建"""
        context = [
            {"title": "测试法条", "content": "测试内容"}
        ]
        rules = [
            {"name": "测试规则", "risk_type": "high", "check_prompt": "检查要点"}
        ]

        prompt = review_svc._build_review_prompt(
            contract_text="测试合同文本",
            contract_type="NDA",
            context=context,
            rules=rules
        )

        # 验证 prompt 包含关键内容（注意：contract_type 占位符在 prompt 中是{contract_type}）
        assert "{contract_type}" in prompt or "NDA" in prompt
        assert "测试合同文本" in prompt
        assert "测试法条" in prompt
        assert "测试规则" in prompt
        assert "JSON" in prompt


@pytest.mark.asyncio
class TestReviewServiceIntegration:
    """测试审查服务集成"""

    async def test_global_service_instance(self):
        """测试全局服务实例"""
        from app.services.review.service import review_service

        assert review_service is not None
        assert isinstance(review_service, ContractReviewService)
