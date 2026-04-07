"""
条款定位服务
在 PDF 中定位风险条款的位置
"""
from typing import List, Dict, Any, Optional
from difflib import SequenceMatcher


class ClauseLocator:
    """条款定位器"""

    def __init__(self, similarity_threshold: float = 0.75):
        """
        Args:
            similarity_threshold: 相似度阈值，默认 0.75
        """
        self.similarity_threshold = similarity_threshold

    def locate_clause(
        self,
        clause_text: str,
        pdf_text_positions: List[Dict[str, Any]],
        max_results: int = 3
    ) -> List[Dict[str, Any]]:
        """
        在 PDF 文本位置列表中定位条款

        Args:
            clause_text: 条款原文
            pdf_text_positions: PDF 提取的文本位置列表
            max_results: 最大返回结果数

        Returns:
            匹配结果 [{"text", "page", "bbox", "similarity", "match_type}]
        """
        if not clause_text or not pdf_text_positions:
            return []

        # 清理条款文本
        clean_clause = self._clean_text(clause_text)
        if len(clean_clause) < 5:
            return []

        results = []

        for pos in pdf_text_positions:
            pos_text = self._clean_text(pos.get("text", ""))

            if not pos_text:
                continue

            # 计算相似度
            similarity = self._calculate_similarity(clean_clause, pos_text)

            # 考虑子串匹配
            if clean_clause in pos_text:
                similarity = max(similarity, 0.9)
            elif pos_text in clean_clause:
                similarity = max(similarity, 0.85)

            if similarity >= self.similarity_threshold:
                results.append({
                    "text": pos.get("text"),
                    "page": pos.get("page"),
                    "bbox": pos.get("bbox"),
                    "similarity": round(similarity, 3),
                    "match_type": "exact" if similarity > 0.9 else "fuzzy"
                })

        # 按相似度排序
        results.sort(key=lambda x: x["similarity"], reverse=True)

        return results[:max_results]

    def locate_clause_in_ocr(
        self,
        clause_text: str,
        ocr_result: Dict[str, Any],
        max_results: int = 3
    ) -> List[Dict[str, Any]]:
        """
        在 OCR 结果中定位条款（无精确坐标）

        Args:
            clause_text: 条款原文
            ocr_result: OCR 提取结果
            max_results: 最大返回结果数

        Returns:
            匹配结果 [{"text", "page", "bbox", "similarity", "match_type}]
        """
        if not clause_text:
            return []

        clean_clause = self._clean_text(clause_text)
        if len(clean_clause) < 5:
            return []

        text_positions = ocr_result.get("text_positions", [])
        results = []

        for pos in text_positions:
            pos_text = self._clean_text(pos.get("text", ""))

            if not pos_text:
                continue

            similarity = self._calculate_similarity(clean_clause, pos_text)

            if similarity >= self.similarity_threshold:
                results.append({
                    "text": pos.get("text"),
                    "page": pos.get("page"),
                    "bbox": pos.get("bbox"),  # OCR 模式可能为 None
                    "similarity": round(similarity, 3),
                    "match_type": "ocr_fuzzy"
                })

        results.sort(key=lambda x: x["similarity"], reverse=True)

        return results[:max_results]

    def batch_locate(
        self,
        clauses: List[str],
        pdf_text_positions: List[Dict[str, Any]],
        is_ocr: bool = False,
        ocr_result: Dict[str, Any] = None
    ) -> List[List[Dict[str, Any]]]:
        """
        批量定位条款

        Args:
            clauses: 条款原文列表
            pdf_text_positions: PDF 文本位置列表
            is_ocr: 是否为 OCR 模式
            ocr_result: OCR 结果

        Returns:
            每条条款的定位结果列表
        """
        if is_ocr and ocr_result:
            return [
                self.locate_clause_in_ocr(clause, ocr_result)
                for clause in clauses
            ]
        else:
            return [
                self.locate_clause(clause, pdf_text_positions)
                for clause in clauses
            ]

    def _clean_text(self, text: str) -> str:
        """清理文本，去除多余空白"""
        if not text:
            return ""
        # 去除多余空白
        import re
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """计算两个文本的相似度"""
        # 限制长度避免性能问题
        max_len = 200
        t1 = text1[:max_len]
        t2 = text2[:max_len]

        return SequenceMatcher(None, t1, t2).ratio()


# 全局实例
clause_locator = ClauseLocator()
