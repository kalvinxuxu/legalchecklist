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

    async def test_review_contract_with_mock_llm(self, review_svc, monkeypatch):
        """测试合同审查（模拟 LLM）"""
        mock_llm_response = {
            "risk_clauses": [
                {
                    "original_text": "保密期限为永久",
                    "risk_level": "high",
                    "risk_description": "保密期限过长",
                    "suggestion": "建议修改为 3-5 年",
                }
            ],
            "missing_clauses": [],
            "suggestions": [],
            "legal_references": []
        }

        async def mock_chat_with_json_output(*args, **kwargs):
            return mock_llm_response

        async def mock_retrieve_all(*args, **kwargs):
            return {"law": [], "company_policy": []}

        # Patch zhipu_llm at the import source (app.services.llm.client)
        mock_llm = MagicMock()
        mock_llm.chat_with_json_output = mock_chat_with_json_output
        monkeypatch.setattr('app.services.llm.client.zhipu_llm', mock_llm)
        # Patch knowledge_manager
        monkeypatch.setattr(review_svc.knowledge_manager, 'retrieve_all', mock_retrieve_all)

        result = await review_svc.review_contract(
            contract_text="这是一份测试合同",
            contract_type="NDA"
        )

        assert result is not None
        assert "risk_clauses" in result
        assert "confidence_score" in result

    async def test_review_contract_labor(self, review_svc, monkeypatch):
        """测试劳动合同审查"""
        mock_llm_response = {
            "risk_clauses": [],
            "missing_clauses": [],
            "suggestions": [],
            "legal_references": []
        }

        async def mock_chat_with_json_output(*args, **kwargs):
            return mock_llm_response

        async def mock_retrieve_all(*args, **kwargs):
            return {"law": [], "company_policy": []}

        mock_llm = MagicMock()
        mock_llm.chat_with_json_output = mock_chat_with_json_output
        monkeypatch.setattr('app.services.llm.client.zhipu_llm', mock_llm)
        monkeypatch.setattr(review_svc.knowledge_manager, 'retrieve_all', mock_retrieve_all)

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

        async def mock_chat_with_json_output(*args, **kwargs):
            return mock_llm_response

        async def mock_retrieve_all(*args, **kwargs):
            return {"law": [], "company_policy": []}

        mock_llm = MagicMock()
        mock_llm.chat_with_json_output = mock_chat_with_json_output
        monkeypatch.setattr('app.services.llm.client.zhipu_llm', mock_llm)
        monkeypatch.setattr(review_svc.knowledge_manager, 'retrieve_all', mock_retrieve_all)

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

        confidence = review_svc._calculate_confidence({}, review_result)

        assert confidence == 0.3

    async def test_calculate_confidence_with_context(self, review_svc):
        """测试有检索结果时的置信度"""
        review_result = {
            "risk_clauses": [{}],
            "missing_clauses": [{}],
            "suggestions": [{}],
            "legal_references": [{}]
        }
        context = {
            "law": [{"score": 0.9}, {"score": 0.8}],
            "company_policy": [{"score": 0.7}]
        }

        confidence = review_svc._calculate_confidence(context, review_result)

        assert 0.5 <= confidence <= 1.0

    async def test_check_response_completeness(self, review_svc):
        """测试响应完整性检查"""
        complete_result = {
            "risk_clauses": [{}],
            "missing_clauses": [{}],
            "suggestions": [{}],
            "legal_references": [{}],
            "policy_references": [{}]
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
        assert completeness == 0.2  # 1/5

    async def test_build_review_prompt_exists(self, review_svc):
        """测试 PromptBuilder 类存在"""
        from app.services.review.prompt_builder import EnhancedPromptBuilder

        assert EnhancedPromptBuilder is not None
        assert hasattr(EnhancedPromptBuilder, 'build_review_prompt')


@pytest.mark.asyncio
class TestReviewServiceIntegration:
    """测试审查服务集成"""

    async def test_global_service_instance(self):
        """测试全局服务实例"""
        from app.services.review.service import review_service

        assert review_service is not None
        assert isinstance(review_service, ContractReviewService)
