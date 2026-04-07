"""
合同结构分析服务
识别合同的主要章节和结构
"""
from typing import Dict, Any, List
from app.services.llm.client import zhipu_llm


class StructureAnalysisService:
    """合同结构分析服务"""

    # 合同类型对应的典型章节模板
    CHAPTER_TEMPLATES = {
        "NDA": ["前言", "定义", "保密范围", "保密义务", "保密期限", "违约责任", "争议解决", "其他"],
        "劳动合同": ["前言", "合同期限", "工作内容", "工作地点", "劳动报酬", "社会保险", "工作时间", "休息休假", "劳动保护", "变更解除", "违约责任", "争议解决"],
        "采购合同": ["前言", "定义", "标的物", "价格与支付", "交付与验收", "质量保证", "违约责任", "争议解决"],
        "销售合同": ["前言", "定义", "标的物", "价格与支付", "交付与验收", "质量保证", "违约责任", "争议解决"],
        "服务合同": ["前言", "定义", "服务内容", "服务期限", "服务费用", "双方义务", "违约责任", "争议解决"],
    }

    async def analyze_structure(
        self,
        contract_text: str,
        contract_type: str = "NDA"
    ) -> Dict[str, Any]:
        """
        分析合同结构

        Args:
            contract_text: 合同文本
            contract_type: 合同类型

        Returns:
            结构分析结果，包含：
            - contract_type: 合同类型
            - sections: 章节列表 [{title, content, start_pos, end_pos}]
            - structure_summary: 结构概要
        """
        # 构建分析 Prompt
        prompt = self._build_structure_prompt(contract_text, contract_type)

        # 调用 LLM
        result = await zhipu_llm.chat_with_json_output([
            {"role": "user", "content": prompt}
        ])

        return self._transform_result(result, contract_type)

    def _build_structure_prompt(
        self,
        contract_text: str,
        contract_type: str
    ) -> str:
        """构建结构分析 Prompt"""

        # 获取该合同类型的典型章节作为参考
        typical_chapters = self.CHAPTER_TEMPLATES.get(
            contract_type,
            self.CHAPTER_TEMPLATES["NDA"]
        )
        chapters_hint = "、".join(typical_chapters)

        return f"""你是一位专业律师，请分析以下{contract_type}合同的结构。

## 典型章节参考
{contract_type}合同通常包含以下章节：{chapters_hint}

## 待分析合同
{contract_text[:8000]}  # 限制长度

## 输出要求
请识别合同中的实际章节结构，并以 JSON 格式输出：

{{
  "contract_type": "{contract_type}",
  "sections": [
    {{
      "title": "章节标题",
      "content": "该章节的核心内容摘要（50字以内）",
      "start_pos": 0,
      "end_pos": 100
    }}
  ],
  "structure_summary": "整体结构概要描述（100字以内）",
  "total_chapters": 章节总数
}}

注意：
1. sections 中的 start_pos 和 end_pos 是估算的文本位置比例（0-1之间的小数），0 表示开头，1 表示结尾
2. 如果无法精确识别章节，可以根据内容推断
3. 只输出 JSON，不要有其他文字
"""

    def _transform_result(
        self,
        result: Dict[str, Any],
        contract_type: str
    ) -> Dict[str, Any]:
        """转换结果格式"""
        return {
            "contract_type": result.get("contract_type", contract_type),
            "sections": result.get("sections", []),
            "structure_summary": result.get("structure_summary", ""),
            "total_chapters": result.get("total_chapters", 0),
        }


# 全局服务实例
structure_analysis_service = StructureAnalysisService()
