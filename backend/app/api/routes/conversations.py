"""会话与问答路由。"""

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models.user import UserRecord
from app.schemas.conversation import (
    AskMessageRequest,
    AskMessageResponse,
    Conversation,
    ConversationCreate,
    ConversationDetail,
)
from app.services import conversation_service

# 会话相关路由集合，用在 api_router 挂载
router = APIRouter(tags=["conversations"])


@router.post(
    "/workspaces/{workspace_id}/conversations",
    response_model=Conversation,
    status_code=status.HTTP_201_CREATED,
    summary="创建会话",
)
# 在空间下创建会话，用在前端会话页新建
def create_conversation(
    workspace_id: str,
    payload: ConversationCreate,
    db: Session = Depends(get_db),
    current_user: UserRecord = Depends(get_current_user),
) -> Conversation:
    # 新建会话记录，用在转成响应
    record = conversation_service.create_conversation(
        db,
        workspace_id,
        current_user.id,
        payload,
    )
    return conversation_service.to_conversation(record)


@router.get(
    "/workspaces/{workspace_id}/conversations",
    response_model=list[Conversation],
    summary="列出会话",
)
# 列出空间下会话，用在前端会话侧栏
def list_conversations(
    workspace_id: str,
    db: Session = Depends(get_db),
    current_user: UserRecord = Depends(get_current_user),
) -> list[Conversation]:
    # 会话记录列表，用在批量转响应
    records = conversation_service.list_conversations(
        db,
        workspace_id,
        current_user.id,
    )
    return [conversation_service.to_conversation(item) for item in records]


@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationDetail,
    summary="会话详情（含消息）",
)
# 获取会话及消息，用在前端会话主区
def get_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: UserRecord = Depends(get_current_user),
) -> ConversationDetail:
    # 命中的会话，用在转成含消息详情
    record = conversation_service.get_conversation_for_owner_or_404(
        db,
        conversation_id,
        current_user.id,
    )
    return conversation_service.to_conversation_detail(record)


@router.delete(
    "/conversations/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除会话（不动来源）",
)
# 删除会话与消息，用在前端会话删除确认
def delete_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: UserRecord = Depends(get_current_user),
) -> Response:
    conversation_service.delete_conversation(db, conversation_id, current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=AskMessageResponse,
    summary="提问（严格边界检索 + 生成）",
)
# 用户提问并返回答案与引用，用在前端会话输入框
def ask_message(
    conversation_id: str,
    payload: AskMessageRequest,
    db: Session = Depends(get_db),
    current_user: UserRecord = Depends(get_current_user),
) -> AskMessageResponse:
    return conversation_service.ask(
        db,
        conversation_id,
        current_user.id,
        payload,
    )
