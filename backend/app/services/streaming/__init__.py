"""
流式输出服务 - SSE (Server-Sent Events)
"""
import asyncio
import json
from typing import AsyncGenerator, Dict, Any
from fastapi.responses import StreamingResponse
import logging

logger = logging.getLogger(__name__)


class StreamingService:
    """流式输出服务"""

    @staticmethod
    def sse_event(data: Dict[str, Any], event_type: str = "message") -> str:
        """
        生成 SSE 格式事件

        Args:
            data: 要发送的数据
            event_type: 事件类型

        Returns:
            SSE 格式字符串
        """
        return f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"

    @staticmethod
    async def stream_review(
        content_generator: AsyncGenerator[str, None]
    ) -> StreamingResponse:
        """
        流式输出审查结果

        Args:
            content_generator: 内容生成器

        Returns:
            StreamingResponse (text/event-stream)
        """
        async def generate():
            try:
                async for chunk in content_generator:
                    yield f"data: {json.dumps({'type': 'token', 'content': chunk}, ensure_ascii=False)}\n\n"
                yield f"data: {json.dumps({'type': 'done'}, ensure_ascii=False)}\n\n"
            except Exception as e:
                logger.error(f"Stream error: {e}")
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )

    @staticmethod
    async def stream_json_events(
        events: AsyncGenerator[Dict[str, Any], None]
    ) -> StreamingResponse:
        """
        流式输出 JSON 事件序列

        Args:
            events: 事件生成器

        Returns:
            StreamingResponse
        """
        async def generate():
            try:
                async for event in events:
                    yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
            except Exception as e:
                logger.error(f"Stream error: {e}")
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive"
            }
        )


# 全局实例
streaming_service = StreamingService()
