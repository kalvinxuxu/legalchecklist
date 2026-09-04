"""
修订模式 Word 文档生成器

使用 python-docx + XML 操作实现 Track Changes 功能
支持插入（insert）和删除（delete）修订
支持真正的 Word 批注功能（OOXML comments）
"""
import io
import re
import zipfile
import os
import shutil
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn, nsmap
from docx.shared import RGBColor
from lxml import etree


class RevisionDocGenerator:
    """修订模式 Word 文档生成器"""

    # Word OOXML 命名空间
    W_NS = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
    W14_NS = 'http://schemas.microsoft.com/office/word/2010/wordml'
    R_NS = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
    OPC_NS = 'http://schemas.openxmlformats.org/package/2006/relationships'
    CT_NS = 'http://schemas.openxmlformats.org/package/2006/content-types'

    def __init__(self):
        self._comment_id = 0
        self._document = None  # 当前文档引用
        self._comments = []  # 存储批注数据 [(id, author, date, content), ...]
        self._temp_dir = None  # 临时目录用于处理 ZIP

    def _generate_comment_id(self) -> int:
        """生成唯一的批注 ID"""
        self._comment_id += 1
        return self._comment_id

    def _add_comment_to_docx(
        self,
        docx_bytes: bytes,
        comments_data: List[Tuple[int, str, str, str]]
    ) -> bytes:
        """
        向 Word 文档添加批注（使用 OOXML 格式）

        Args:
            docx_bytes: 原始 Word 文档字节
            comments_data: 批注数据列表 [(comment_id, author, date, content), ...]

        Returns:
            添加批注后的 Word 文档字节
        """
        if not comments_data:
            return docx_bytes

        # 创建临时文件
        import tempfile
        temp_dir = tempfile.mkdtemp()
        input_path = os.path.join(temp_dir, 'input.docx')
        output_path = os.path.join(temp_dir, 'output.docx')

        try:
            # 写入输入文件
            with open(input_path, 'wb') as f:
                f.write(docx_bytes)

            # 复制 ZIP 内容
            with zipfile.ZipFile(input_path, 'r') as zin:
                zin.extractall(temp_dir)

            # 创建 comments.xml
            comments_xml = self._create_comments_xml(comments_data)
            comments_path = os.path.join(temp_dir, 'word', 'comments.xml')

            with open(comments_path, 'w', encoding='utf-8') as f:
                f.write(comments_xml)

            # 更新 [Content_Types].xml
            ct_path = os.path.join(temp_dir, '[Content_Types].xml')
            self._update_content_types(ct_path)

            # 更新 word/_rels/document.xml.rels
            rels_path = os.path.join(temp_dir, 'word', '_rels', 'document.xml.rels')
            self._update_document_rels(rels_path)

            # 重新打包为 docx
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zout:
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        if file == 'input.docx' or file == 'output.docx':
                            continue
                        file_path = os.path.join(root, file)
                        arc_name = os.path.relpath(file_path, temp_dir)
                        zout.write(file_path, arc_name)

            # 读取输出
            with open(output_path, 'rb') as f:
                return f.read()

        finally:
            # 清理临时目录
            shutil.rmtree(temp_dir, ignore_errors=True)

    def _create_comments_xml(self, comments_data: List[Tuple[int, str, str, str]]) -> str:
        """
        创建 comments.xml 内容

        Args:
            comments_data: [(id, author, date, content), ...]

        Returns:
            comments.xml 字符串
        """
        nsmap = {
            'w': self.W_NS,
            'w14': self.W14_NS,
            'r': self.R_NS,
        }

        root = etree.Element(qn('w:comments'), nsmap=nsmap)

        for comment_id, author, date, content in comments_data:
            comment = etree.SubElement(root, qn('w:comment'))
            comment.set(qn('w:id'), str(comment_id))
            comment.set(qn('w:author'), author)
            comment.set(qn('w:date'), date)
            comment.set(qn('w:initials'), author[:1] if author else 'A')

            # 创建段落
            para = etree.SubElement(comment, qn('w:p'))

            # 创建段落属性
            pPr = etree.SubElement(para, qn('w:pPr'))
            pStyle = etree.SubElement(pPr, qn('w:pStyle'))
            pStyle.set(qn('w:val'), 'CommentText')

            # 创建 run
            run = etree.SubElement(para, qn('w:r'))

            # 创建文本
            t = etree.SubElement(run, qn('w:t'))
            t.set(qn('xml:space'), 'preserve')
            t.text = content

        return etree.tostring(root, xml_declaration=True, encoding='UTF-8', pretty_print=True).decode('utf-8')

    def _update_content_types(self, ct_path: str) -> None:
        """更新 [Content_Types].xml 添加 comments 内容类型"""
        tree = etree.parse(ct_path)
        root = tree.getroot()

        # [Content_Types].xml 使用默认命名空间，不需要前缀
        # 检查是否已有 comments override
        for override in root.findall('Override'):
            if override.get('PartName') == '/word/comments.xml':
                return  # 已存在

        # 添加 comments override
        override = etree.SubElement(root, 'Override')
        override.set('PartName', '/word/comments.xml')
        override.set('ContentType', 'application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml')

        tree.write(ct_path, xml_declaration=True, encoding='UTF-8', pretty_print=True)

    def _update_document_rels(self, rels_path: str) -> None:
        """更新 document.xml.rels 添加 comments 关系"""
        tree = etree.parse(rels_path)
        root = tree.getroot()

        # 检查是否已有 comments 关系
        for rel in root.findall('Relationship'):
            if rel.get('Target') == 'comments.xml':
                return  # 已存在

        # 添加 comments 关系
        # 找到最大的 rId
        max_id = 0
        for rel in root.findall('Relationship'):
            rid = rel.get('Id')
            if rid and rid.startswith('rId'):
                try:
                    num = int(rid[3:])
                    max_id = max(max_id, num)
                except ValueError:
                    pass

        new_id = f'rId{max_id + 1}'

        relationship = etree.SubElement(root, 'Relationship')
        relationship.set('Id', new_id)
        relationship.set('Type', 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments')
        relationship.set('Target', 'comments.xml')

        tree.write(rels_path, xml_declaration=True, encoding='UTF-8', pretty_print=True)

    def create_revision_document(
        self,
        original_file_path: str,
        revisions: List[Dict[str, Any]]
    ) -> bytes:
        """
        创建带修订模式的 Word 文档

        Args:
            original_file_path: 原始 Word 文件路径
            revisions: 修订列表
                [{
                    "paragraph_index": 5,  # 段落索引
                    "type": "replace",      # replace / insert / delete
                    "original_text": "xxx", # 原文本（用于定位）
                    "new_text": "yyy",      # 新文本
                    "author": "AI 助手",
                    "comment": "风险修改建议",
                    "risk_description": "风险说明"
                }]

        Returns:
            修改后的 Word 文档字节流
        """
        # 重置批注数据
        self._comment_id = 0
        self._comments = []

        doc = Document(original_file_path)

        # 按段落索引分组修订
        revisions_by_para: Dict[int, List[Dict[str, Any]]] = {}
        for rev in revisions:
            idx = rev.get("paragraph_index", 0)
            if idx not in revisions_by_para:
                revisions_by_para[idx] = []
            revisions_by_para[idx].append(rev)

        # 处理每个段落的修订
        for para_idx, para_revisions in revisions_by_para.items():
            if para_idx >= len(doc.paragraphs):
                continue

            para = doc.paragraphs[para_idx]
            self._apply_revisions_to_paragraph(para, para_revisions)

        # 保存到字节流
        output = io.BytesIO()
        doc.save(output)
        output.seek(0)
        doc_bytes = output.read()

        # 如果有批注，添加到文档中
        if self._comments:
            doc_bytes = self._add_comment_to_docx(doc_bytes, self._comments)
            self._comments = []  # 清空批注数据

        return doc_bytes

    def _apply_revisions_to_paragraph(
        self,
        para,
        revisions: List[Dict[str, Any]]
    ) -> None:
        """
        将修订应用到单个段落

        使用 Word Track Changes (修订模式):
        - 删除的内容用 <w:del> 包裹
        - 新增的内容用 <w:ins> 包裹
        - 建议/评论作为批注添加
        """
        para_xml = para._p

        for rev in revisions:
            rev_type = rev.get("type", "replace")
            original_text = rev.get("original_text", "")
            new_text = rev.get("new_text", "")
            author = rev.get("author", "AI 助手")
            comment = rev.get("comment") or rev.get("risk_description", "")
            risk_level = rev.get("risk_level", "")

            if not original_text:
                continue

            if rev_type == "delete":
                # 删除：标记原文为删除，添加建议批注
                self._mark_text_as_deleted(para, original_text, author, comment)
            elif rev_type == "insert":
                # 插入：在原文后添加新文本
                self._add_inserted_text(para, original_text, new_text, author, comment)
            else:
                # replace：删除原文，插入新文本，并添加建议批注
                self._replace_text_with_revision(
                    para, original_text, new_text, author, comment, risk_level
                )

    def _find_text_in_paragraph(
        self,
        para,
        search_text: str
    ) -> List[Tuple[OxmlElement, str]]:
        """
        在段落中查找包含指定文本的所有 run 元素

        Returns:
            [(run_element, run_text), ...]
        """
        results = []
        for run in para.runs:
            if search_text in run.text:
                results.append((run._r, run.text))
        return results

    def _mark_text_as_deleted(
        self,
        para,
        text: str,
        author: str,
        comment: str
    ) -> None:
        """
        将指定文本标记为删除（Track Changes）
        """
        # 查找包含文本的 run
        runs = self._find_text_in_paragraph(para, text)
        if not runs:
            return

        # 获取段落的 XML 元素
        para_xml = para._p

        for run_elem, run_text in runs:
            # 创建 <w:del> 元素
            del_elem = OxmlElement('w:del')
            del_elem.set(qn('w:id'), str(self._generate_revision_id()))
            del_elem.set(qn('w:author'), author)
            del_elem.set(qn('w:date'), self._get_current_time())

            # 创建 <w:r> 元素
            r_elem = OxmlElement('w:r')

            # 创建 <w:delText> 元素
            del_text_elem = OxmlElement('w:delText')
            del_text_elem.set(qn('xml:space'), 'preserve')
            del_text_elem.text = text
            r_elem.append(del_text_elem)

            del_elem.append(r_elem)

            # 替换原 run 元素
            run_elem.addnext(del_elem)
            run_elem.getparent().remove(run_elem)

        # 添加批注
        if comment:
            self._add_comment_to_paragraph(para, author, comment, risk_level="high")

    def _add_inserted_text(
        self,
        para,
        before_text: str,
        new_text: str,
        author: str,
        comment: str
    ) -> None:
        """
        在指定文本后添加插入内容
        """
        runs = self._find_text_in_paragraph(para, before_text)
        if not runs:
            # 如果找不到原文，直接在段落末尾添加
            self._insert_text_at_run(para.runs[-1]._r if para.runs else para._p, new_text, author, comment)
            return

        # 在最后一个匹配的 run 后插入
        last_run_elem = runs[-1][0]
        self._insert_text_at_run(last_run_elem, new_text, author, comment)

    def _insert_text_at_run(
        self,
        after_elem,
        text: str,
        author: str,
        comment: str
    ) -> None:
        """
        在指定元素后插入带修订标记的文本
        """
        # 创建 <w:ins> 元素
        ins_elem = OxmlElement('w:ins')
        ins_elem.set(qn('w:id'), str(self._generate_revision_id()))
        ins_elem.set(qn('w:author'), author)
        ins_elem.set(qn('w:date'), self._get_current_time())

        # 创建 <w:r> 元素
        r_elem = OxmlElement('w:r')

        # 创建 <w:t> 元素
        t_elem = OxmlElement('w:t')
        t_elem.set(qn('xml:space'), 'preserve')
        t_elem.text = text
        r_elem.append(t_elem)

        ins_elem.append(r_elem)

        # 插入到段落中
        after_elem.addnext(ins_elem)

        # 添加批注
        if comment:
            self._add_comment_to_element(after_elem, author, comment)

    def _replace_text_with_revision(
        self,
        para,
        original_text: str,
        new_text: str,
        author: str,
        comment: str,
        risk_level: str = ""
    ) -> None:
        """
        用修订模式替换文本
        1. 将原文标记为删除
        2. 在删除内容后插入新文本
        3. 添加批注说明
        """
        runs = self._find_text_in_paragraph(para, original_text)
        if not runs:
            return

        # 获取段落 XML
        para_xml = para._p

        # 处理每个匹配的 run
        for i, (run_elem, run_text) in enumerate(runs):
            is_first = (i == 0)
            is_last = (i == len(runs) - 1)

            # 1. 创建 <w:del> 包裹原文
            del_elem = OxmlElement('w:del')
            del_elem.set(qn('w:id'), str(self._generate_revision_id()))
            del_elem.set(qn('w:author'), author)
            del_elem.set(qn('w:date'), self._get_current_time())

            r_del = OxmlElement('w:r')
            del_text = OxmlElement('w:delText')
            del_text.set(qn('xml:space'), 'preserve')
            del_text.text = original_text
            r_del.append(del_text)
            del_elem.append(r_del)

            # 2. 创建 <w:ins> 包裹新文本
            ins_elem = OxmlElement('w:ins')
            ins_elem.set(qn('w:id'), str(self._generate_revision_id() + 1))
            ins_elem.set(qn('w:author'), author)
            ins_elem.set(qn('w:date'), self._get_current_time())

            r_ins = OxmlElement('w:r')
            t_ins = OxmlElement('w:t')
            t_ins.set(qn('xml:space'), 'preserve')
            t_ins.text = new_text if is_last else ""
            r_ins.append(t_ins)
            ins_elem.append(r_ins)

            # 3. 替换原 run 元素
            run_elem.addnext(del_elem)
            run_elem.addnext(ins_elem)
            run_elem.getparent().remove(run_elem)

        # 4. 添加批注
        if comment:
            self._add_comment_to_paragraph(para, author, comment, risk_level)

    def _add_comment_to_paragraph(
        self,
        para,
        author: str,
        comment: str,
        risk_level: str = ""
    ) -> None:
        """
        为段落添加真正的 Word 批注

        这个方法会在段落中添加批注范围标记（commentRangeStart/End）
        并将批注数据存储在 self._comments 中，等待后续处理

        Args:
            para: 段落对象
            author: 批注作者
            comment: 批注内容
            risk_level: 风险等级（high/medium/low）
        """
        # 生成唯一批注ID
        comment_id = self._generate_comment_id()

        # 获取当前时间
        date_str = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

        # 记录批注数据
        self._comments.append((comment_id, author, date_str, comment))

        # 在段落 XML 中插入批注范围标记
        para_xml = para._p

        # 创建 commentRangeStart
        comment_range_start = OxmlElement('w:commentRangeStart')
        comment_range_start.set(qn('w:id'), str(comment_id))

        # 创建 commentRangeEnd
        comment_range_end = OxmlElement('w:commentRangeEnd')
        comment_range_end.set(qn('w:id'), str(comment_id))

        # 创建包含 commentReference 的 run
        comment_ref_run = OxmlElement('w:r')
        comment_ref = etree.SubElement(comment_ref_run, qn('w:commentReference'))
        comment_ref.set(qn('w:id'), str(comment_id))

        # 插入到段落开头（在 pPr 之后，如果没有 pPr 就插入到开头）
        pPr = para_xml.find(qn('w:pPr'))
        if pPr is not None:
            pPr.addnext(comment_range_start)
            comment_range_start.addnext(comment_range_end)
            comment_range_end.addnext(comment_ref_run)
        else:
            # 在段落开头插入
            para_xml.insert(0, comment_range_end)
            para_xml.insert(0, comment_ref_run)
            para_xml.insert(0, comment_range_start)

    def _add_comment_to_element(
        self,
        elem,
        author: str,
        comment: str
    ) -> None:
        """为元素添加简单批注"""
        # 找到父段落
        para = elem.getparent()
        while para is not None and para.tag != qn('w:p'):
            para = para.getparent()

        if para is not None:
            self._add_comment_to_paragraph(para, author, comment)

    def _generate_revision_id(self) -> int:
        """生成唯一的修订 ID"""
        import random
        return random.randint(100000, 999999)

    def _get_current_time(self) -> str:
        """获取当前时间（ISO 格式）"""
        from datetime import datetime
        return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    def apply_suggestions_to_document(
        self,
        original_file_path: str,
        suggestions: List[Dict[str, Any]]
    ) -> bytes:
        """
        将建议应用到文档，生成带修订的文档

        这是对外的主要接口

        Args:
            original_file_path: 原始文件路径
            suggestions: 建议列表，每条建议包含：
                - paragraph_index: 段落索引
                - type: "replace" | "insert" | "delete"
                - original_text: 原文本
                - new_text: 新文本
                - risk_description: 风险描述
                - author: 建议作者

        Returns:
            修改后的 Word 字节流
        """
        return self.create_revision_document(original_file_path, suggestions)

    def add_review_comments_to_document(
        self,
        original_file_path: str,
        review_result: Dict[str, Any]
    ) -> bytes:
        """
        将审查批注添加到原始Word文档

        Args:
            original_file_path: 原始 Word 文件路径
            review_result: 审查结果字典，包含：
                - risk_clauses: 风险条款列表
                - missing_clauses: 缺失条款列表
                - suggestions: 修改建议列表

        Returns:
            带批注的 Word 文档字节流
        """
        import logging
        logger = logging.getLogger(__name__)

        # 重置批注数据
        self._comment_id = 0
        self._comments = []

        logger.info(f"[RevisionDoc] Loading document: {original_file_path}")

        doc = Document(original_file_path)
        logger.info(f"[RevisionDoc] Document loaded, paragraphs: {len(doc.paragraphs)}")

        # 用于记录每个段落已添加的批注文本，避免重复
        para_comments: Dict[int, List[str]] = {}

        # 统计匹配情况
        risk_matched = 0
        missing_matched = 0
        suggestion_matched = 0

        # 处理风险条款
        for clause in review_result.get("risk_clauses", []):
            paragraph_index = clause.get("paragraph_index")
            if paragraph_index is None:
                # 如果没有段落索引，通过 original_text 查找
                original_text = clause.get("original_text", "")
                paragraph_index = self._find_paragraph_index_by_text(
                    doc, original_text
                )
                logger.info(f"[RevisionDoc] Risk clause '{clause.get('title', 'N/A')}' - found paragraph_index: {paragraph_index}")

            if paragraph_index is not None and paragraph_index < len(doc.paragraphs):
                risk_matched += 1
                comment_text = self._format_risk_clause_comment(clause)
                if paragraph_index not in para_comments:
                    para_comments[paragraph_index] = []
                if comment_text not in para_comments[paragraph_index]:
                    para_comments[paragraph_index].append(comment_text)
                    self._add_comment_to_paragraph(
                        doc.paragraphs[paragraph_index],
                        "AI 审查",
                        comment_text,
                        "high"
                    )

        # 处理缺失条款
        for clause in review_result.get("missing_clauses", []):
            paragraph_index = clause.get("paragraph_index")
            if paragraph_index is None:
                original_text = clause.get("description", "")
                paragraph_index = self._find_paragraph_index_by_text(
                    doc, original_text
                )
                logger.info(f"[RevisionDoc] Missing clause '{clause.get('title', 'N/A')}' - found paragraph_index: {paragraph_index}")

            if paragraph_index is not None and paragraph_index < len(doc.paragraphs):
                missing_matched += 1
                comment_text = self._format_missing_clause_comment(clause)
                if paragraph_index not in para_comments:
                    para_comments[paragraph_index] = []
                if comment_text not in para_comments[paragraph_index]:
                    para_comments[paragraph_index].append(comment_text)
                    self._add_comment_to_paragraph(
                        doc.paragraphs[paragraph_index],
                        "AI 审查",
                        comment_text,
                        "medium"
                    )

        # 处理修改建议
        for suggestion in review_result.get("suggestions", []):
            paragraph_index = suggestion.get("paragraph_index")
            if paragraph_index is None:
                original_text = suggestion.get("original_text", "")
                paragraph_index = self._find_paragraph_index_by_text(
                    doc, original_text
                )

            if paragraph_index is not None and paragraph_index < len(doc.paragraphs):
                suggestion_matched += 1
                comment_text = self._format_suggestion_comment(suggestion)
                if paragraph_index not in para_comments:
                    para_comments[paragraph_index] = []
                if comment_text not in para_comments[paragraph_index]:
                    para_comments[paragraph_index].append(comment_text)
                    self._add_comment_to_paragraph(
                        doc.paragraphs[paragraph_index],
                        "AI 审查",
                        comment_text,
                        "low"
                    )

        logger.info(f"[RevisionDoc] Matched - risk: {risk_matched}, missing: {missing_matched}, suggestion: {suggestion_matched}")

        # 在文档末尾添加审查批注摘要部分
        self._add_review_comments_summary(doc, review_result)

        # 保存到字节流
        output = io.BytesIO()
        doc.save(output)
        output.seek(0)
        doc_bytes = output.read()

        # 如果有批注，添加到文档中（使用 OOXML 格式）
        if self._comments:
            logger.info(f"[RevisionDoc] Adding {len(self._comments)} comments to document")
            doc_bytes = self._add_comment_to_docx(doc_bytes, self._comments)
            self._comments = []  # 清空批注数据
        else:
            logger.info(f"[RevisionDoc] No comments to add")

        return doc_bytes

    def _find_paragraph_index_by_text(
        self,
        doc: Document,
        search_text: str,
        min_match_length: int = 10
    ) -> Optional[int]:
        """
        通过文本内容查找段落索引

        Args:
            doc: Word 文档对象
            search_text: 要搜索的文本
            min_match_length: 最小匹配长度，避免短文本匹配错误

        Returns:
            段落索引，如果未找到返回 None
        """
        import logging
        logger = logging.getLogger(__name__)

        if not search_text or len(search_text) < min_match_length:
            logger.info(f"[RevisionDoc] Search text too short: '{search_text[:20]}...'")
            return None

        # 规范化文本：去除多余空白字符
        normalized_search = re.sub(r'\s+', '', search_text)

        # 优先精确匹配（包括规范化后的匹配）
        for idx, para in enumerate(doc.paragraphs):
            para_text = para.text
            normalized_para = re.sub(r'\s+', '', para_text)

            # 精确匹配
            if search_text in para_text:
                logger.info(f"[RevisionDoc] Exact match at paragraph {idx}")
                return idx

            # 规范化后匹配
            if normalized_search and normalized_search in normalized_para:
                logger.info(f"[RevisionDoc] Normalized match at paragraph {idx}")
                return idx

        # 尝试模糊匹配 - 检查是否存在至少20个连续字符匹配
        match_length = 20
        for idx, para in enumerate(doc.paragraphs):
            para_text = re.sub(r'\s+', '', para.text)
            # 滑动窗口匹配
            for i in range(len(normalized_search) - match_length + 1):
                chunk = normalized_search[i:i + match_length]
                if chunk in para_text:
                    logger.info(f"[RevisionDoc] Fuzzy match (chunk '{chunk[:10]}...') at paragraph {idx}")
                    return idx

        # 尝试关键词匹配（针对中文）
        keywords = [search_text[j:j+4] for j in range(0, min(len(search_text), 40), 4)]
        for keyword in keywords[:5]:  # 最多尝试5个4字词
            for idx, para in enumerate(doc.paragraphs):
                if keyword in para.text:
                    logger.info(f"[RevisionDoc] Keyword match '{keyword}' at paragraph {idx}")
                    return idx

        logger.info(f"[RevisionDoc] No match found for search text: '{search_text[:30]}...'")
        return None

    def _format_risk_clause_comment(self, clause: Dict[str, Any]) -> str:
        """格式化风险条款批注 - 只保留风险说明和修改建议"""
        parts = []
        if clause.get("risk_description"):
            parts.append(f"【风险说明】{clause['risk_description']}")
        if clause.get("suggestion"):
            parts.append(f"【修改建议】{clause['suggestion']}")
        if clause.get("legal_reference"):
            parts.append(f"【法律依据】{clause['legal_reference']}")
        return "\n".join(parts) if parts else clause.get("original_text", "")

    def _format_missing_clause_comment(self, clause: Dict[str, Any]) -> str:
        """格式化缺失条款批注 - 只保留说明和建议"""
        parts = []
        if clause.get("description"):
            parts.append(f"【缺失说明】{clause['description']}")
        if clause.get("suggestion"):
            parts.append(f"【修改建议】{clause['suggestion']}")
        if clause.get("legal_reference"):
            parts.append(f"【法律依据】{clause['legal_reference']}")
        return " | ".join(parts) if parts else ""

    def _format_suggestion_comment(self, suggestion: Dict[str, Any]) -> str:
        """格式化建议批注 - 只保留建议内容"""
        if suggestion.get("content"):
            return f"【建议内容】{suggestion['content']}"
        return ""

    def _add_review_comments_summary(
        self,
        doc: Document,
        review_result: Dict[str, Any]
    ) -> None:
        """
        在文档末尾添加审查批注摘要部分

        包含所有风险条款、缺失条款和修改建议的完整列表
        """
        from docx.shared import RGBColor, Pt
        from docx.enum.text import WD_ALIGN_PARAGRAPH

        # 添加分页
        doc.add_page_break()

        # 添加标题（使用普通段落 + 大字体）
        title = doc.add_paragraph()
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = title.add_run('=== AI 合同审查批注摘要 ===')
        run.font.size = Pt(16)
        run.font.bold = True
        run.font.color.rgb = RGBColor(0x21, 0x21, 0x21)

        # 添加风险条款
        risk_clauses = review_result.get("risk_clauses", [])
        if risk_clauses:
            # 小标题
            p = doc.add_paragraph()
            run = p.add_run(f'【风险条款】({len(risk_clauses)} 条)')
            run.font.size = Pt(14)
            run.font.bold = True
            run.font.color.rgb = RGBColor(0xC6, 0x28, 0x28)

            for i, clause in enumerate(risk_clauses, 1):
                # 条款标题
                p = doc.add_paragraph()
                run = p.add_run(f'{i}. {clause.get("title", "风险条款")}')
                run.font.bold = True
                run.font.color.rgb = RGBColor(0xC6, 0x28, 0x28)

                # 原始文本
                if clause.get("original_text"):
                    p = doc.add_paragraph()
                    run = p.add_run('原文：')
                    run.bold = True
                    p.add_run(clause.get("original_text"))

                # 风险说明
                if clause.get("risk_description"):
                    p = doc.add_paragraph()
                    run = p.add_run('风险说明：')
                    run.bold = True
                    p.add_run(clause.get("risk_description"))

                # 修改建议
                if clause.get("suggestion"):
                    p = doc.add_paragraph()
                    run = p.add_run('修改建议：')
                    run.bold = True
                    p.add_run(clause.get("suggestion"))

                # 法律依据
                if clause.get("legal_reference"):
                    p = doc.add_paragraph()
                    run = p.add_run('法律依据：')
                    run.bold = True
                    run2 = p.add_run(clause.get("legal_reference"))
                    run2.font.color.rgb = RGBColor(0x15, 0x65, 0xC0)

                doc.add_paragraph()  # 空行

        # 添加缺失条款
        missing_clauses = review_result.get("missing_clauses", [])
        if missing_clauses:
            p = doc.add_paragraph()
            run = p.add_run(f'【缺失条款】({len(missing_clauses)} 条)')
            run.font.size = Pt(14)
            run.font.bold = True
            run.font.color.rgb = RGBColor(0xE6, 0x51, 0x00)

            for i, clause in enumerate(missing_clauses, 1):
                p = doc.add_paragraph()
                run = p.add_run(f'{i}. {clause.get("title", "缺失条款")}')
                run.font.bold = True
                run.font.color.rgb = RGBColor(0xE6, 0x51, 0x00)

                if clause.get("description"):
                    p = doc.add_paragraph()
                    run = p.add_run('说明：')
                    run.bold = True
                    p.add_run(clause.get("description"))

                if clause.get("suggestion"):
                    p = doc.add_paragraph()
                    run = p.add_run('建议：')
                    run.bold = True
                    p.add_run(clause.get("suggestion"))

                if clause.get("legal_reference"):
                    p = doc.add_paragraph()
                    run = p.add_run('法律依据：')
                    run.bold = True
                    run2 = p.add_run(clause.get("legal_reference"))
                    run2.font.color.rgb = RGBColor(0x15, 0x65, 0xC0)

                doc.add_paragraph()

        # 添加修改建议
        suggestions = review_result.get("suggestions", [])
        if suggestions:
            p = doc.add_paragraph()
            run = p.add_run(f'【修改建议】({len(suggestions)} 条)')
            run.font.size = Pt(14)
            run.font.bold = True
            run.font.color.rgb = RGBColor(0x15, 0x65, 0xC0)

            for i, suggestion in enumerate(suggestions, 1):
                p = doc.add_paragraph()
                run = p.add_run(f'{i}. {suggestion.get("title", "建议")}')
                run.font.bold = True
                run.font.color.rgb = RGBColor(0x15, 0x65, 0xC0)

                if suggestion.get("content"):
                    p = doc.add_paragraph()
                    p.add_run(suggestion.get("content"))

                doc.add_paragraph()

    def _add_colored_comment_to_paragraph(
        self,
        para,
        comment: str,
        risk_level: str = ""
    ) -> None:
        """
        为段落添加真正的 Word 批注

        此方法已更新为使用 OOXML 批注格式，替代了之前在段落末尾
        添加彩色文字的方式。

        Args:
            para: 段落对象
            comment: 批注内容
            risk_level: 风险等级（high/medium/low）
        """
        # 调用真正的批注方法
        self._add_comment_to_paragraph(
            para,
            author="AI 审查",
            comment=comment,
            risk_level=risk_level
        )


# 全局实例
revision_doc_generator = RevisionDocGenerator()
