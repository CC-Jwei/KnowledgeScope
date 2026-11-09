"""Pydantic 契约模型（OpenAPI 真相源）。"""

from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserPublic
from app.schemas.conversation import (
    AskMessageRequest,
    AskMessageResponse,
    Citation,
    Conversation,
    ConversationCreate,
    ConversationDetail,
    Message,
)
from app.schemas.enums import MessageRole, ModelPurpose, SourceStatus, SourceType
from app.schemas.events import ConnectedEvent, HeartbeatEvent
from app.schemas.model_profile import ModelProfile, ModelProfileCreate, ModelProfileUpdate
from app.schemas.source import Source, SourceCreate, SourceListItem, SourceUpdate
from app.schemas.workspace import Workspace, WorkspaceCreate, WorkspaceUpdate

# 对外导出的契约符号，用在 main 合并 OpenAPI 与外部 import
__all__ = [
    "AskMessageRequest",
    "AskMessageResponse",
    "Citation",
    "ConnectedEvent",
    "Conversation",
    "ConversationCreate",
    "ConversationDetail",
    "HeartbeatEvent",
    "LoginRequest",
    "Message",
    "MessageRole",
    "ModelProfile",
    "ModelProfileCreate",
    "ModelProfileUpdate",
    "ModelPurpose",
    "RegisterRequest",
    "Source",
    "SourceCreate",
    "SourceListItem",
    "SourceStatus",
    "SourceType",
    "SourceUpdate",
    "TokenResponse",
    "UserPublic",
    "Workspace",
    "WorkspaceCreate",
    "WorkspaceUpdate",
]
