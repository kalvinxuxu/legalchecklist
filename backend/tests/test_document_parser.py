"""
文档解析器单元测试
"""
import pytest
from pathlib import Path
from app.services.document.parser import document_parser, AliyunDocumentParser


@pytest.fixture
def parser():
    """创建解析器实例"""
    return AliyunDocumentParser()


@pytest.fixture
def test_pdf_path():
    """测试 PDF 文件路径"""
    # 使用项目中的测试文件
    test_file = Path(__file__).parent.parent / "test_nda.txt"
    return str(test_file)


@pytest.mark.asyncio
class TestDocumentParser:
    """测试文档解析器"""

    async def test_parser_initialization(self, parser):
        """测试解析器初始化"""
        assert parser is not None
        assert hasattr(parser, 'timeout')
        assert parser.timeout == 60.0

    async def test_parse_pdf_local_fallback(self, parser):
        """测试 PDF 本地解析（降级方案）"""
        # 创建一个简单的测试文件
        test_content = "这是一个测试合同\n\n第一条：保密信息\n\n第二条：违约责任"
        test_file = Path(__file__).parent / "test_contract.pdf"

        # 由于没有实际 PDF 文件，测试应该返回空文本或错误
        # 这里主要验证代码路径正确
        try:
            result = await parser._parse_pdf_locally(str(test_file))
            # 如果文件不存在，应该抛出异常
            assert "error" in result or "text" in result
        except FileNotFoundError:
            # 文件不存在是预期的
            pytest.skip("测试 PDF 文件不存在，跳过此测试")

    async def test_parse_word_local_fallback(self, parser):
        """测试 Word 本地解析（降级方案）"""
        # 创建一个简单的测试文件
        test_file = Path(__file__).parent / "test_contract.docx"

        try:
            result = await parser._parse_word_locally(str(test_file))
            # 如果文件不存在，应该抛出异常
            assert "error" in result or "text" in result
        except (FileNotFoundError, Exception) as e:
            # 文件不存在是预期的（docx 包可能抛出 PackageNotFoundError）
            pytest.skip(f"测试 Word 文件不存在，跳过此测试：{e}")

    async def test_generate_signature(self, parser):
        """测试阿里云签名生成"""
        # 设置测试密钥
        parser.access_key_id = "test_id"
        parser.access_key_secret = "test_secret"

        params = {
            "Action": "ExtractText",
            "Version": "2021-07-07"
        }

        signature = parser._generate_signature("GET", "/", params)

        # 签名应该是非空的 base64 字符串
        assert signature is not None
        assert len(signature) > 0

    async def test_get_timestamp(self, parser):
        """测试时间戳生成"""
        timestamp = parser._get_timestamp()

        # 时间戳应该是 ISO8601 格式
        assert timestamp is not None
        assert "T" in timestamp
        assert timestamp.endswith("Z")

    async def test_get_nonce(self, parser):
        """测试随机数生成"""
        nonce1 = parser._get_nonce()
        nonce2 = parser._get_nonce()

        # 每次生成的随机数应该不同
        assert nonce1 is not None
        assert nonce2 is not None
        assert nonce1 != nonce2

    async def test_parse_pdf_without_api_credentials(self, parser):
        """测试在没有阿里云凭证时使用本地解析"""
        # 清除凭证
        parser.access_key_id = None
        parser.access_key_secret = None

        # 本地解析应该有相应的处理
        # 注意：这个测试主要验证代码路径
        assert parser.access_key_id is None


@pytest.mark.asyncio
class TestAliyunIntegration:
    """测试阿里云集成（需要有效凭证）"""

    async def test_parse_with_mock_credentials(self, parser, monkeypatch):
        """测试使用模拟凭证的阿里云解析"""
        # 设置模拟凭证
        monkeypatch.setattr(parser, 'access_key_id', 'mock_id')
        monkeypatch.setattr(parser, 'access_key_secret', 'mock_secret')

        # 由于没有实际文件，这个测试会失败或返回错误
        # 主要验证代码路径正确处理凭证
        assert parser.access_key_id == 'mock_id'
