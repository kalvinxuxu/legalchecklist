"""
PDF 文本提取服务
提取 PDF 文本并记录位置信息
"""
import fitz  # pymupdf
from typing import List, Dict, Any, Optional
from pathlib import Path


class PdfReader:
    """PDF 文本读取器"""

    def extract_text_with_positions(
        self,
        file_path: str,
        min_text_length: int = 3
    ) -> Dict[str, Any]:
        """
        提取 PDF 文本及位置信息

        Args:
            file_path: PDF 文件路径
            min_text_length: 最小文本长度（过滤短文本）

        Returns:
            {
                "text": "完整文本",
                "pages": 页数,
                "text_positions": [
                    {
                        "text": "文本内容",
                        "page": 0,
                        "bbox": {"x0": 0, "y0": 0, "x1": 100, "y1": 20}
                    }
                ],
                "has_text": 是否包含可提取文字,
                "needs_ocr": 是否需要 OCR
            }
        """
        text_positions = []
        full_text_parts = []
        has_text = False

        try:
            doc = fitz.open(file_path)

            for page_num in range(len(doc)):
                page = doc[page_num]
                blocks = page.get_text("dict")["blocks"]

                for block in blocks:
                    # 只处理文本块
                    if block.get("type") != 0:
                        continue

                    for line in block.get("lines", []):
                        for span in line.get("spans", []):
                            text = span["text"].strip()
                            if len(text) < min_text_length:
                                continue

                            has_text = True
                            bbox = span["bbox"]

                            text_positions.append({
                                "text": text,
                                "page": page_num,
                                "bbox": {
                                    "x0": round(bbox[0], 1),
                                    "y0": round(bbox[1], 1),
                                    "x1": round(bbox[2], 1),
                                    "y1": round(bbox[3], 1)
                                }
                            })
                            full_text_parts.append(text)

            doc.close()

        except Exception as e:
            return {
                "text": "",
                "pages": 0,
                "text_positions": [],
                "has_text": False,
                "needs_ocr": True,
                "error": str(e)
            }

        full_text = "\n".join(full_text_parts)
        needs_ocr = not has_text or len(full_text.strip()) < 100

        return {
            "text": full_text,
            "pages": len(text_positions) > 0 and max(p["page"] for p in text_positions) + 1 or 0,
            "text_positions": text_positions,
            "has_text": has_text,
            "needs_ocr": needs_ocr
        }

    async def extract_with_ocr(
        self,
        file_path: str,
        lang: str = "chi_sim+eng"
    ) -> Dict[str, Any]:
        """
        使用 OCR 提取文本（扫描版 PDF）

        Args:
            file_path: PDF 文件路径
            lang: OCR 语言

        Returns:
            OCR 提取结果
        """
        try:
            import pytesseract
            from PIL import Image
            import fitz

            # 配置 tesseract 路径（Windows 安装路径）
            import os
            tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
            if os.path.exists(tesseract_path):
                pytesseract.pytesseract.tesseract_cmd = tesseract_path
        except ImportError as e:
            return {
                "text": "",
                "error": f"OCR 依赖库未安装: {e}",
                "needs_ocr": True
            }

        text_parts = []
        text_positions = []

        try:
            doc = fitz.open(file_path)

            for page_num in range(len(doc)):
                page = doc[page_num]
                # 将页面转换为图像
                mat = fitz.Matrix(2, 2)  # 2x 缩放以提高 OCR 准确率
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_data))

                # OCR
                text = pytesseract.image_to_string(img, lang=lang)
                if text.strip():
                    text_parts.append(text)
                    # OCR 结果不包含精确坐标，记录页码
                    text_positions.append({
                        "text": text.strip(),
                        "page": page_num,
                        "bbox": None  # OCR 模式下无精确坐标
                    })

            doc.close()

        except Exception as e:
            return {
                "text": "",
                "error": str(e),
                "needs_ocr": True
            }

        import io
        return {
            "text": "\n".join(text_parts),
            "pages": len(text_positions) > 0 and max(p["page"] for p in text_positions) + 1 or 0,
            "text_positions": text_positions,
            "has_text": True,
            "needs_ocr": False,
            "source": "ocr"
        }

    def extract_pages(self, file_path: str) -> List[Dict[str, Any]]:
        """
        提取每页的简要信息

        Returns:
            [{"page": 0, "width": 595, "height": 842, "text_length": 1234}]
        """
        pages_info = []

        try:
            doc = fitz.open(file_path)

            for page_num in range(len(doc)):
                page = doc[page_num]
                rect = page.rect
                text = page.get_text()

                pages_info.append({
                    "page": page_num,
                    "width": round(rect.width, 1),
                    "height": round(rect.height, 1),
                    "text_length": len(text.strip())
                })

            doc.close()

        except Exception as e:
            pass

        return pages_info


import io

# 全局实例
pdf_reader = PdfReader()
