"""
分区 Context 构建器 - 将分区知识转换为 Prompt 所需格式
"""
from typing import Dict, List, Any


class PartitionedContextBuilder:
    """分区 Context 构建器"""

    @staticmethod
    def _item_text(item: Dict[str, Any]) -> str:
        """Serialize one reranked candidate with auditable retrieval metadata."""
        audit = []
        for key in ("bm25_rank", "vector_rank", "fused_rank", "rerank_rank", "bm25_score", "vector_score", "fused_score", "semantic_score", "authority_score", "metadata_score", "rerank_score", "reranker_provider", "reranker_model", "fallback_reason"):
            if item.get(key) is not None:
                audit.append(f"{key}={item[key]}")
        source_id = item.get("evidence_id") or item.get("chunk_id") or item.get("id")
        prefix = f"[source_id={source_id}]" if source_id else "[source_id=unknown]"
        suffix = f"\n(retrieval: {', '.join(audit)})" if audit else ""
        return f"{prefix}\n{item.get('content', '')}{suffix}"

    @staticmethod
    def build_context_text(
        partitioned_context: Dict[str, List[Dict[str, Any]]],
        config: Dict[str, Dict]
    ) -> str:
        """
        构建分区上下文字符串

        Args:
            partitioned_context: 分区知识字典
            config: 内容类型配置

        Returns:
            格式化后的上下文字符串
        """
        sections = []

        for content_type, items in partitioned_context.items():
            if not items:
                continue

            type_config = config.get(content_type, {})
            label = type_config.get("label", content_type)

            section = f"## {label}\n"
            for item in items:
                title = item.get("title", item.get("content", "")[:50])
                content = PartitionedContextBuilder._item_text(item)
                score = item.get("score", 0)

                section += f"\n【{title}】\n{content}"
                if score:
                    section += f"\n(相关度: {score:.2f})"

            sections.append(section)

        return "\n\n".join(sections) if sections else "无相关依据"

    @staticmethod
    def build_law_context(law_items: List[Dict[str, Any]]) -> str:
        """
        构建法律依据上下文

        Args:
            law_items: 法律知识列表

        Returns:
            格式化后的法律依据字符串
        """
        if not law_items:
            return "无相关法律依据"

        sections = []
        for item in law_items:
            title = item.get("title", item.get("content", "")[:50])
            content = item.get("content", "")
            sections.append(f"【{title}】\n{PartitionedContextBuilder._item_text(item)}")

        return "\n\n".join(sections)

    @staticmethod
    def build_policy_context(policy_items: List[Dict[str, Any]]) -> str:
        """
        构建公司政策上下文

        Args:
            policy_items: 公司政策知识列表

        Returns:
            格式化后的公司政策字符串
        """
        if not policy_items:
            return "无相关公司政策"

        sections = []
        for item in policy_items:
            title = item.get("title", item.get("content", "")[:50])
            content = item.get("content", "")
            sections.append(f"【{title}】\n{PartitionedContextBuilder._item_text(item)}")

        return "\n\n".join(sections)

    @staticmethod
    def build_structured_context(
        partitioned_context: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, str]:
        """
        构建结构化上下文（便于 LLM 区分来源）

        Returns:
            字典，key 为 content_type，value 为格式化文本
        """
        result = {}
        for content_type, items in partitioned_context.items():
            if items:
                result[content_type] = "\n".join([
                    f"- {item.get('title', item['content'][:50])}: {item['content']}"
                    for item in items
                ])
        return result

    @staticmethod
    def build_contract_context(items: List[Dict[str, Any]]) -> str:
        if not items:
            return "未生成合同条款候选区"
        expanded = PartitionedContextBuilder.expand_parent_context(items)
        return "\n\n".join(
            f"【合同条款 source_id={item.get('chunk_id') or item.get('id')} "
            f"page={item.get('page_start')}-{item.get('page_end')}】\n"
            f"{PartitionedContextBuilder._item_text(item)}"
            for item in expanded
        )

    @staticmethod
    def expand_parent_context(items: List[Dict[str, Any]], max_parent_chars: int = 6000) -> List[Dict[str, Any]]:
        """Expand child retrieval hits with bounded parent-clause context without changing provenance IDs."""
        expanded = []
        for item in items:
            value = dict(item)
            parent_text = (item.get("parent_text") or "").strip()
            content = (item.get("content") or "").strip()
            if parent_text and parent_text != content:
                value["content"] = (
                    "[精准子条款]\n" + content +
                    "\n[完整父条款上下文]\n" + parent_text[:max_parent_chars]
                )
                value["parent_context_included"] = True
            expanded.append(value)
        return expanded
