"""SSE 心跳事件。"""

import asyncio
from collections.abc import AsyncIterator
from datetime import datetime, timezone

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.config import get_settings
from app.schemas.events import ConnectedEvent, HeartbeatEvent

# SSE 事件子路由，用在 api_router 挂载 /events
router = APIRouter(prefix="/events")
# 心跳相关配置，用在间隔秒数与事件推送
_settings = get_settings()

# SSE Content-Type，用在 StreamingResponse media_type
SSE_CONTENT_TYPE = "text/event-stream"
# 禁用缓存头值，用在 SSE 响应 Cache-Control
CACHE_CONTROL_NO_CACHE = "no-cache"
# 关闭 nginx 缓冲，用在 SSE 响应 X-Accel-Buffering
X_ACCEL_BUFFERING_OFF = "no"


# 返回当前 UTC 时间，用在 heartbeat 事件时间戳
def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


# 拼装单条 SSE 文本帧，用在心跳生成器 yield
def _format_sse(event: str, data: str) -> str:
    return f"event: {event}\ndata: {data}\n\n"


# 持续产出 connected/heartbeat，用在 heartbeat_stream 的流式响应
async def _heartbeat_generator(request: Request) -> AsyncIterator[str]:
    # 连接成功事件载荷，用在首帧 connected
    connected = ConnectedEvent(message="connected")
    yield _format_sse("connected", connected.model_dump_json(by_alias=True))

    # 心跳间隔秒数，用在 asyncio.sleep
    interval = _settings.sse_heartbeat_interval_seconds
    while True:
        if await request.is_disconnected():
            break

        # 本轮心跳时间，用在 HeartbeatEvent
        now = _utc_now()
        # 心跳事件载荷，用在本帧 data
        payload = HeartbeatEvent(ts=now, server_time=now)
        yield _format_sse("heartbeat", payload.model_dump_json(by_alias=True))

        try:
            await asyncio.sleep(interval)
        except asyncio.CancelledError:
            break

        if await request.is_disconnected():
            break


@router.get(
    "/heartbeat",
    summary="SSE 心跳流",
    responses={
        200: {
            "description": "Server-Sent Events 流（connected + 周期性 heartbeat）",
            "content": {
                "text/event-stream": {
                    "schema": {
                        "type": "string",
                        "example": (
                            'event: connected\ndata: {"message":"connected"}\n\n'
                            'event: heartbeat\ndata: {"ts":"2026-11-09T06:00:00.000Z",'
                            '"serverTime":"2026-11-09T06:00:00.000Z"}\n\n'
                        ),
                    }
                }
            },
        }
    },
)
# 对外 SSE 心跳接口，用在前端顶栏连接状态展示
async def heartbeat_stream(request: Request) -> StreamingResponse:
    return StreamingResponse(
        _heartbeat_generator(request),
        media_type=SSE_CONTENT_TYPE,
        headers={
            "Cache-Control": CACHE_CONTROL_NO_CACHE,
            "Connection": "keep-alive",
            "X-Accel-Buffering": X_ACCEL_BUFFERING_OFF,
        },
    )
