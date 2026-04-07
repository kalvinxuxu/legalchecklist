"""
PDF 高亮服务
生成带高亮的 PDF 文件
"""
import fitz  # pymupdf
from typing import List, Dict, Any, Tuple
from io import BytesIO
from pathlib import Path


class PdfHighlighter:
    """PDF 高亮生成器"""

    # 高亮颜色配置
    HIGHLIGHT_COLORS = {
        "high": (1, 0.2, 0.2),      # 红色 - 高风险
        "medium": (1, 0.6, 0),       # 橙色 - 中风险
        "low": (1, 1, 0),            # 黄色 - 低风险
        "benefit": (0.2, 0.8, 0.2),  # 绿色 - 利好
        "neutral": (0, 0.6, 1),      # 蓝色 - 中性
    }

    # 风险等级到颜色映射
    RISK_COLORS = {
        "high": (1, 0.2, 0.2, 0.3),    # RGBA
        "medium": (1, 0.6, 0, 0.3),
        "low": (1, 1, 0, 0.3),
    }

    def highlight_clauses(
        self,
        file_path: str,
        clause_positions: List[Dict[str, Any]],
        output_path: str = None
    ) -> bytes:
        """
        在 PDF 上高亮标注条款

        Args:
            file_path: 源 PDF 文件路径
            clause_positions: 条款位置列表 [
                {
                    "text": "条款原文",
                    "page": 0,
                    "bbox": {"x0": 0, "y0": 0, "x1": 100, "y1": 20},
                    "risk_level": "high",
                    "clause_id": "xxx"
                }
            ]
            output_path: 输出路径（可选）

        Returns:
            高亮 PDF 的字节流
        """
        doc = fitz.open(file_path)
        highlighted_count = 0

        for clause in clause_positions:
            page_num = clause.get("page")
            bbox = clause.get("bbox")
            risk_level = clause.get("risk_level", "medium")

            if page_num is None or not bbox:
                continue

            if page_num >= len(doc):
                continue

            page = doc[page_num]

            # 检查 bbox 是否有效
            if not self._is_valid_bbox(bbox, page.rect):
                continue

            # 获取颜色
            color = self.RISK_COLORS.get(risk_level, (1, 0.6, 0, 0.3))

            # 添加高亮
            try:
                x0 = bbox["x0"]
                y0 = bbox["y0"]
                x1 = bbox["x1"]
                y1 = bbox["y1"]

                # 扩展高亮区域
                padding = 2
                rect = fitz.Rect(
                    x0 - padding,
                    y0 - padding,
                    x1 + padding,
                    y1 + padding
                )

                # 添加高亮批注
                highlight = page.add_highlight_annot(rect)
                highlight.set_colors({"stroke": color[:3]})
                highlight.set_opacity(color[3] if len(color) > 3 else 0.3)

                # 添加链接批注（点击跳转）
                if clause.get("clause_id"):
                    # 创建链接锚点
                    link = page.add_link({
                        "kind": fitz.LINK_FLAG_BEST_EFFORT,
                        "from": rect,
                    })

                highlighted_count += 1

            except Exception as e:
                print(f"高亮失败: {e}")
                continue

        # 保存
        if output_path:
            doc.save(output_path)

        doc.close()

        # 返回字节流
        doc = fitz.open(file_path)
        for clause in clause_positions:
            page_num = clause.get("page")
            bbox = clause.get("bbox")
            risk_level = clause.get("risk_level", "medium")

            if page_num is None or not bbox:
                continue
            if page_num >= len(doc):
                continue

            page = doc[page_num]

            if not self._is_valid_bbox(bbox, page.rect):
                continue

            color = self.RISK_COLORS.get(risk_level, (1, 0.6, 0, 0.3))

            try:
                rect = fitz.Rect(
                    bbox["x0"] - 2,
                    bbox["y0"] - 2,
                    bbox["x1"] + 2,
                    bbox["y1"] + 2
                )
                highlight = page.add_highlight_annot(rect)
                highlight.set_colors({"stroke": color[:3]})
                highlight.set_opacity(0.3)
            except:
                continue

        output = BytesIO()
        doc.save(output)
        doc.close()

        return output.getvalue()

    def get_highlighted_pdf_stream(
        self,
        file_path: str,
        clause_positions: List[Dict[str, Any]]
    ) -> BytesIO:
        """
        获取高亮 PDF 的流

        Args:
            file_path: 源 PDF 文件路径
            clause_positions: 条款位置列表

        Returns:
            BytesIO 对象
        """
        pdf_bytes = self.highlight_clauses(file_path, clause_positions)
        return BytesIO(pdf_bytes)

    def add_annotation(
        self,
        file_path: str,
        page_num: int,
        text: str,
        annotation_type: str = "text",
        position: Tuple[float, float] = None
    ) -> bytes:
        """
        添加注释到 PDF

        Args:
            file_path: PDF 文件路径
            page_num: 页码
            text: 注释文本
            annotation_type: 注释类型 (text, comment, note)
            position: 位置 (x, y)

        Returns:
            修改后的 PDF 字节流
        """
        doc = fitz.open(file_path)

        if page_num >= len(doc):
            doc.close()
            return open(file_path, "rb").read()

        page = doc[page_num]

        if position is None:
            # 默认位置
            position = (page.rect.width - 100, 50)

        if annotation_type == "text":
            annot = page.add_text_annot(
                fitz.Point(*position),
                text,
                fill=(1, 1, 0)
            )
        elif annotation_type == "comment":
            annot = page.add_freetext_annot(
                fitz.Rect(position[0], position[1], position[0] + 200, position[1] + 50),
                text,
                fill=(1, 1, 0)
            )

        output = BytesIO()
        doc.save(output)
        doc.close()

        return output.getvalue()

    def _convert_to_float(self, value):
        """将值转换为 float，处理 bytes 类型（SQLite 兼容）"""
        if isinstance(value, (int, float)):
            return float(value)
        elif isinstance(value, bytes):
            # 处理 SQLite 返回的 bytes 类型
            try:
                import struct
                return struct.unpack('f', value[:4])[0]
            except:
                return 0.0
        elif isinstance(value, str):
            try:
                return float(value)
            except:
                return 0.0
        return 0.0

    def _is_valid_bbox(
        self,
        bbox: Dict[str, float],
        page_rect: fitz.Rect
    ) -> bool:
        """检查 bbox 是否有效"""
        if not bbox:
            return False

        x0 = self._convert_to_float(bbox.get("x0", 0))
        y0 = self._convert_to_float(bbox.get("y0", 0))
        x1 = self._convert_to_float(bbox.get("x1", 0))
        y1 = self._convert_to_float(bbox.get("y1", 0))

        # 检查是否为空
        if x0 == x1 or y0 == y1:
            return False

        # 检查是否在页面范围内（允许适当超出）
        margin = 50
        if x0 < -margin or y0 < -margin or x1 > page_rect.width + margin or y1 > page_rect.height + margin:
            return False

        return True


# 全局实例
pdf_highlighter = PdfHighlighter()
