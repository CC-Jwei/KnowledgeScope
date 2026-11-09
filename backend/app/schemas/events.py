"""SSE 事件载荷模型。"""

from datetime import datetime

from pydantic import Field

from app.schemas.common import CamelModel


class ConnectedEvent(CamelModel):
    # 连接成功提示文案，用在 SSE connected 事件 data
    message: str = Field(default="connected", description="连接成功提示")


class HeartbeatEvent(CamelModel):
    # 心跳时间戳，用在 SSE heartbeat 事件 data
    ts: datetime = Field(description="心跳时间戳（UTC）")
    # 可选服务端时间，用在与 ts 对齐的心跳载荷
    server_time: datetime | None = Field(
        default=None,
        description="可选服务端时间，与 ts 一致时可省略",
    )
