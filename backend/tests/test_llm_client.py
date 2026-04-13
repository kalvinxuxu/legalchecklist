"""
LLM 客户端单元测试
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.llm.client import zhipu_llm, DeepSeekLLMClient


@pytest.fixture
def llm_client():
    """创建 LLM 客户端实例"""
    return DeepSeekLLMClient()


@pytest.mark.asyncio
class TestZhipuLLMClient:
    """测试智谱 LLM 客户端"""

    async def test_client_initialization(self, llm_client):
        """测试客户端初始化"""
        assert llm_client is not None
        assert hasattr(llm_client, 'api_key')
        assert hasattr(llm_client, 'base_url')
        assert hasattr(llm_client, 'model')
        assert hasattr(llm_client, 'timeout')

    async def test_chat_basic(self, llm_client, monkeypatch):
        """测试基础对话功能"""
        # Mock httpx.AsyncClient
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{
                "message": {"content": "这是测试回复"}
            }]
        }
        mock_response.raise_for_status = MagicMock()

        async def mock_post(*args, **kwargs):
            return mock_response

        with patch('httpx.AsyncClient.post', new=mock_post):
            result = await llm_client.chat([
                {"role": "user", "content": "你好"}
            ])

            assert result == "这是测试回复"

    async def test_chat_with_temperature(self, llm_client, monkeypatch):
        """测试带温度参数的对话"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{
                "message": {"content": "测试回复"}
            }]
        }
        mock_response.raise_for_status = MagicMock()

        captured_json = {}

        async def mock_post(*args, **kwargs):
            nonlocal captured_json
            captured_json = kwargs.get('json', {})
            return mock_response

        with patch('httpx.AsyncClient.post', new=mock_post):
            await llm_client.chat(
                [{"role": "user", "content": "你好"}],
                temperature=0.5,
                max_tokens=2048
            )

            assert captured_json.get('temperature') == 0.5
            assert captured_json.get('max_tokens') == 2048

    async def test_chat_with_json_output(self, llm_client, monkeypatch):
        """测试 JSON 格式输出"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{
                "message": {"content": '{"key": "value", "number": 123}'}
            }]
        }
        mock_response.raise_for_status = MagicMock()

        async def mock_post(*args, **kwargs):
            return mock_response

        with patch('httpx.AsyncClient.post', new=mock_post):
            result = await llm_client.chat_with_json_output([
                {"role": "user", "content": "请返回 JSON"}
            ])

            assert isinstance(result, dict)
            assert result.get("key") == "value"
            assert result.get("number") == 123

    async def test_chat_json_output_with_markdown(self, llm_client, monkeypatch):
        """测试 JSON 输出处理 markdown 代码块"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{
                "message": {"content": '```json\n{"result": "success"}\n```'}
            }]
        }
        mock_response.raise_for_status = MagicMock()

        async def mock_post(*args, **kwargs):
            return mock_response

        with patch('httpx.AsyncClient.post', new=mock_post):
            result = await llm_client.chat_with_json_output([
                {"role": "user", "content": "请返回 JSON"}
            ])

            assert isinstance(result, dict)
            assert result.get("result") == "success"

    async def test_chat_json_output_invalid_json(self, llm_client, monkeypatch):
        """测试 JSON 输出处理无效 JSON"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{
                "message": {"content": '这不是有效的 JSON {invalid'}
            }]
        }
        mock_response.raise_for_status = MagicMock()

        async def mock_post(*args, **kwargs):
            return mock_response

        with patch('httpx.AsyncClient.post', new=mock_post):
            # 应该抛出 ValueError 或返回部分解析结果
            with pytest.raises(ValueError):
                await llm_client.chat_with_json_output([
                    {"role": "user", "content": "请返回 JSON"}
                ])

    async def test_chat_error_handling(self, llm_client, monkeypatch):
        """测试错误处理"""
        async def mock_post_error(*args, **kwargs):
            raise httpx.HTTPStatusError("模拟错误", request=MagicMock(), response=MagicMock())

        import httpx
        with patch('httpx.AsyncClient.post', new=mock_post_error):
            with pytest.raises(httpx.HTTPStatusError):
                await llm_client.chat([
                    {"role": "user", "content": "你好"}
                ])


@pytest.mark.asyncio
class TestZhipuLLMConfiguration:
    """测试 LLM 配置"""

    async def test_default_model(self, llm_client):
        """测试默认模型配置"""
        # 验证模型已配置（即使为空字符串）
        assert llm_client.model is not None

    async def test_default_timeout(self, llm_client):
        """测试默认超时设置"""
        assert llm_client.timeout == 180.0

    async def test_default_temperature(self, llm_client):
        """测试默认温度值"""
        # chat 方法的默认温度是 0.7
        # 这里验证方法签名
        import inspect
        sig = inspect.signature(llm_client.chat)
        assert sig.parameters['temperature'].default == 0.7
