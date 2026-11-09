"""Pydantic 契约模型（OpenAPI 真相源）。"""

from app.schemas.enums import SourceStatus, SourceType
from app.schemas.events import ConnectedEvent, HeartbeatEvent
from app.schemas.source import (
    PlainTextSourceCreate,
    PlainTextSourceUpdate,
    Source,
    SourceListItem,
)
from app.schemas.workspace import Workspace, WorkspaceCreate, WorkspaceUpdate

# 对外导出的契约符号，用在 main 合并 OpenAPI 与外部 import
__all__ = [
    "ConnectedEvent",
    "HeartbeatEvent",
    "PlainTextSourceCreate",
    "PlainTextSourceUpdate",
    "Source",
    "SourceListItem",
    "SourceStatus",
    "SourceType",
    "Workspace",
    "WorkspaceCreate",
    "WorkspaceUpdate",
]
