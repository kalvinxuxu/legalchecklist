"""
MiniMax 多模态客户端 - 支持视觉理解
API Key: sk-cp-Q3t0o9fRZ6w62yP4IyocV__6iSKa7MnGfCkxxU_3HQwTohkB8kvJ1pSa9-exe9E-Y-UNBC3lfHfIrcM-hnaBJqXJvscX1tLx3nK-SEvEQn3e1yH3gj32llA
"""
import httpx
import base64
import json
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

# MiniMax API 配置
MINIMAX_API_KEY = "sk-cp-Q3t0o9fRZ6w62yP4IyocV__6iSKa7MnGfCkxxU_3HQwTohkB8kvJ1pSa9-exe9E-Y-UNBC3lfHfIrcM-hnaBJqXJvscX1tLx3nK-SEvEQn3e1yH3gj32llA"
MINIMAX_BASE_URL = "https://api.minimax.chat/v1"


class MiniMaxVision:
    """MiniMax 多模态 API 客户端"""

    def __init__(self):
        self.api_key = MINIMAX_API_KEY
        self.base_url = MINIMAX_BASE_URL
        self.model = "MiniMax-VL-01"  # MiniMax 视觉模型
        self.timeout = 120.0

    def encode_image(self, image_path: str) -> str:
        """将图片编码为 base64"""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    async def analyze_image(
        self,
        image_path: str,
        prompt: str = "描述这张图片的内容"
    ) -> str:
        """
        分析单张图片

        Args:
            image_path: 图片路径
            prompt: 分析提示词

        Returns:
            图片分析结果
        """
        image_base64 = self.encode_image(image_path)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/multimodal_generation",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{image_base64}"
                                    }
                                }
                            ]
                        }
                    ]
                }
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def analyze_tables(
        self,
        image_path: str
    ) -> List[List[str]]:
        """
        提取图片中的表格数据

        Returns:
            二维数组表示的表格
        """
        prompt = """请仔细分析这张图片中的表格，提取所有单元格的内容。
以 JSON 数组格式返回，每个子数组代表一行。
示例：[["姓名", "年龄"], ["张三", "25"], ["李四", "30"]]

只返回 JSON，不要其他文字。"""

        result = await self.analyze_image(image_path, prompt)

        # 尝试解析 JSON
        try:
            # 移除非 JSON 内容
            import re
            match = re.search(r'\[.*\]', result, re.DOTALL)
            if match:
                return json.loads(match.group())
        except:
            pass

        return [[result]]  # 返回单单元格

    async def analyze_chart(
        self,
        image_path: str
    ) -> Dict[str, Any]:
        """
        分析图表图片，返回图表类型和数据摘要

        Returns:
            {"type": "柱状图/折线图/饼图", "summary": "数据摘要"}
        """
        prompt = """分析这张图表图片：
1. 判断图表类型（柱状图/折线图/饼图/散点图）
2. 提取关键数据点和趋势
3. 用中文简要总结图表传达的主要信息

请用 JSON 格式返回：{"type": "图表类型", "summary": "简要总结"}"""

        result = await self.analyze_image(image_path, prompt)

        try:
            import re
            match = re.search(r'\{.*\}', result, re.DOTALL)
            if match:
                return json.loads(match.group())
        except:
            pass

        return {"type": "未知", "summary": result}

    async def extract_text_from_image(
        self,
        image_path: str
    ) -> str:
        """
        从图片（扫描件、截图等）中提取文字

        Returns:
            提取的文本内容
        """
        prompt = "请准确提取这张图片中的所有文字内容，保持原有格式。用中文返回。"
        return await self.analyze_image(image_path, prompt)

    async def describe_document_page(
        self,
        image_path: str,
        page_context: str = ""
    ) -> str:
        """
        描述文档页面内容，结合上下文理解

        Args:
            image_path: 页面截图路径
            page_context: 前一页内容（可选）

        Returns:
            页面描述
        """
        context_hint = f"\n\n前文内容供参考：{page_context}" if page_context else ""
        prompt = f"""请描述这张文档页面的主要内容，包括：
1. 文档类型（合同/发票/表格等）
2. 主要内容摘要
3. 关键数据或条款（如果适用）{context_hint}"""

        return await self.analyze_image(image_path, prompt)


# 全局实例
minimax_vision = MiniMaxVision()
