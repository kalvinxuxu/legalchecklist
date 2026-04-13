"""
知识检索管理器 - 支持多类型分区检索

用于合同审查时并行检索法律知识和公司政策
"""
from typing import Dict, List, Any, Optional
from app.services.rag.retriever import retriever
import logging

logger = logging.getLogger(__name__)


class KnowledgeRetrievalManager:
    """知识检索管理器 - 支持多种 content_type 分区检索"""

    # 默认配置：可扩展添加更多类型
    DEFAULT_CONTENT_TYPES_CONFIG = {
        "law": {
            "top_k": 5,
            "label": "法律依据",
            "query_template": "{contract_type} 合同审查 法律规定 条款要求"
        },
        "company_policy": {
            "top_k": 3,
            "label": "公司政策",
            "query_template": "{contract_type} 合同条款 公司政策 合规要求 管理制度"
        }
    }

    def __init__(self, content_types_config: Optional[Dict[str, Dict]] = None):
        """
        初始化知识检索管理器

        Args:
            content_types_config: 内容类型配置，格式如上
                                  默认为 DEFAULT_CONTENT_TYPES_CONFIG
        """
        self.config = content_types_config or self.DEFAULT_CONTENT_TYPES_CONFIG

    async def retrieve_all(
        self,
        contract_type: str,
        tenant_id: Optional[str] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        检索所有配置的知识类型

        Args:
            contract_type: 合同类型
            tenant_id: 租户 ID

        Returns:
            分区知识字典，key 为 content_type，value 为检索结果列表
        """
        import asyncio
        partitioned_results = {}

        # 构建所有检索任务
        tasks = []
        content_types = []
        for content_type, config in self.config.items():
            query = config["query_template"].format(contract_type=contract_type)
            top_k = config["top_k"]
            content_types.append(content_type)

            task = self._retrieve_single(
                content_type=content_type,
                query=query,
                top_k=top_k,
                tenant_id=tenant_id
            )
            tasks.append(task)

        # 并行执行所有检索
        results_list = await asyncio.gather(*tasks, return_exceptions=True)

        # 整理结果
        for content_type, result in zip(content_types, results_list):
            if isinstance(result, Exception):
                logger.error(f"[KnowledgeManager] Failed to retrieve '{content_type}': {result}")
                partitioned_results[content_type] = []
            else:
                partitioned_results[content_type] = result
                logger.info(
                    f"[KnowledgeManager] Retrieved {len(result)} items for type '{content_type}'"
                )

        return partitioned_results

    async def _retrieve_single(
        self,
        content_type: str,
        query: str,
        top_k: int,
        tenant_id: Optional[str]
    ) -> List[Dict[str, Any]]:
        """检索单个内容类型"""
        try:
            results = await retriever.retrieve(
                query=query,
                content_type=content_type,
                top_k=top_k,
                tenant_id=tenant_id
            )
            return results
        except Exception as e:
            logger.error(f"[KnowledgeManager] Error retrieving '{content_type}': {e}")
            raise


# 全局实例
knowledge_manager = KnowledgeRetrievalManager()
