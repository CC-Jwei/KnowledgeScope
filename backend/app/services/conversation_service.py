"""会话与严格边界问答。"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.constants import STRICT_NO_EVIDENCE_REPLY, STRICT_SYSTEM_PROMPT
from app.models.chunk import ChunkRecord
from app.models.conversation import ConversationRecord
from app.models.message import MessageRecord
from app.models.source import SourceRecord
from app.schemas.conversation import (
    AskMessageRequest,
    AskMessageResponse,
    Citation,
    Conversation,
    ConversationCreate,
    ConversationDetail,
    Message,
)
from app.schemas.enums import MessageRole, ModelPurpose
from app.services import llm_client, model_profile_service, vector_store, workspace_service

# 问答相关配置，用在历史条数/检索 TopK/引用上限
_settings = get_settings()


# 返回当前 UTC 时间，用在会话与消息时间戳
def _now() -> datetime:
    return datetime.now(timezone.utc)


# 解析 citations_json，用在 Message 响应
def _parse_citations(raw: str | None) -> list[Citation]:
    if not raw:
        return []
    try:
        # 反序列化后的列表，用在构造 Citation
        data = json.loads(raw)
    except json.JSONDecodeError:
        return []
    # Citation 对象列表，用在助手消息
    items: list[Citation] = []
    for item in data:
        items.append(Citation.model_validate(item))
    return items


# ORM 转 Message 契约，用在详情与提问响应
def to_message(record: MessageRecord) -> Message:
    return Message(
        id=record.id,
        conversation_id=record.conversation_id,
        role=MessageRole(record.role),
        content=record.content,
        citations=_parse_citations(record.citations_json),
        created_at=record.created_at,
    )


# ORM 转 Conversation 契约，用在列表
def to_conversation(record: ConversationRecord) -> Conversation:
    return Conversation.model_validate(record)


# ORM 转含消息的详情，用在 GET /conversations/{id}
def to_conversation_detail(record: ConversationRecord) -> ConversationDetail:
    return ConversationDetail(
        id=record.id,
        workspace_id=record.workspace_id,
        owner_id=record.owner_id,
        title=record.title,
        created_at=record.created_at,
        updated_at=record.updated_at,
        messages=[to_message(item) for item in record.messages],
    )


# 列出空间下会话，用在 GET workspaces/{id}/conversations
def list_conversations(
    db: Session,
    workspace_id: str,
    owner_id: str,
) -> list[ConversationRecord]:
    workspace_service.get_workspace_for_owner_or_404(db, workspace_id, owner_id)
    # 倒序查询，用在会话列表
    stmt = (
        select(ConversationRecord)
        .where(
            ConversationRecord.workspace_id == workspace_id,
            ConversationRecord.owner_id == owner_id,
        )
        .order_by(ConversationRecord.updated_at.desc())
    )
    return list(db.scalars(stmt).all())


# 创建会话，用在 POST workspaces/{id}/conversations
def create_conversation(
    db: Session,
    workspace_id: str,
    owner_id: str,
    payload: ConversationCreate,
) -> ConversationRecord:
    workspace_service.get_workspace_for_owner_or_404(db, workspace_id, owner_id)
    # 创建时刻，用在时间戳
    now = _now()
    # 待写入会话，用在 commit
    record = ConversationRecord(
        id=str(uuid.uuid4()),
        workspace_id=workspace_id,
        owner_id=owner_id,
        title=payload.title,
        created_at=now,
        updated_at=now,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


# 按 id 取自己的会话，用在详情/删除/提问
def get_conversation_for_owner_or_404(
    db: Session,
    conversation_id: str,
    owner_id: str,
) -> ConversationRecord:
    # 按主键查到的会话，用在归属校验
    record = db.get(ConversationRecord, conversation_id)
    if record is None or record.owner_id != owner_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在",
        )
    return record


# 删除会话与消息（不动 Source），用在 DELETE /conversations/{id}
def delete_conversation(db: Session, conversation_id: str, owner_id: str) -> None:
    # 待删除会话，用在 db.delete
    record = get_conversation_for_owner_or_404(db, conversation_id, owner_id)
    db.delete(record)
    db.commit()


# 检索并生成严格边界回答，写回 user/assistant 消息，用在 POST .../messages
def ask(
    db: Session,
    conversation_id: str,
    owner_id: str,
    payload: AskMessageRequest,
) -> AskMessageResponse:
    # 当前会话，用在写消息与取 workspace
    conversation = get_conversation_for_owner_or_404(db, conversation_id, owner_id)
    workspace_service.get_workspace_for_owner_or_404(
        db,
        conversation.workspace_id,
        owner_id,
    )

    # 聊天模型，用在生成回答
    chat_model = model_profile_service.resolve_model(
        db,
        owner_id,
        ModelPurpose.CHAT,
        payload.chat_model_profile_id,
    )
    # 嵌入模型，用在问题向量化检索
    embed_model = model_profile_service.resolve_model(
        db,
        owner_id,
        ModelPurpose.EMBEDDING,
        payload.embedding_model_profile_id,
    )

    # 用户消息实体，用在先落库
    user_message = MessageRecord(
        id=str(uuid.uuid4()),
        conversation_id=conversation.id,
        role=MessageRole.USER.value,
        content=payload.content,
        citations_json=None,
        created_at=_now(),
    )
    db.add(user_message)
    db.flush()

    if not conversation.title:
        # 首问前缀标题，用在自动命名会话
        prefix = payload.content[: _settings.conversation_title_from_question_prefix]
        conversation.title = prefix

    # 问题向量，用在向量检索
    query_vectors = llm_client.create_embeddings(embed_model, [payload.content])
    if not query_vectors:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="嵌入服务未返回向量",
        )
    # 检索命中，用在拼证据与 Citation
    hits = vector_store.query_vectors(
        embedding=query_vectors[0],
        workspace_id=conversation.workspace_id,
        top_k=_settings.retrieval_top_k,
    )
    # 分数过滤后的命中，用在严格模式空检索判断
    filtered = [
        hit
        for hit in hits
        if float(hit.get("score") or 0.0) >= _settings.retrieval_min_score
    ]

    # 引用列表，用在助手消息
    citations: list[Citation] = []
    # 拼给模型的证据文本，用在 system/user 上下文
    evidence_blocks: list[str] = []
    for hit in filtered[: _settings.citation_max_count]:
        # 元数据，用在取 chunk/source id
        meta = hit.get("metadata") or {}
        # chunk id，用在查业务库补标题
        chunk_id = str(meta.get("chunk_id") or hit.get("id") or "")
        # source id，用在 Citation
        source_id = str(meta.get("source_id") or "")
        # 业务库分块，用在预览与标题
        chunk = db.get(ChunkRecord, chunk_id) if chunk_id else None
        # 来源标题，用在 Citation.title
        title = "未命名来源"
        if source_id:
            # 来源记录，用在取 title
            source = db.get(SourceRecord, source_id)
            if source is not None:
                title = source.title
        # 片段预览，用在 Citation.snippet
        snippet = (
            chunk.content_preview
            if chunk is not None
            else str(hit.get("document") or "")[: _settings.content_preview_length]
        )
        citations.append(
            Citation(
                source_id=source_id or "unknown",
                chunk_id=chunk_id or "unknown",
                title=title,
                snippet=snippet,
            )
        )
        evidence_blocks.append(
            f"[chunk={chunk_id} source={source_id} title={title}]\n{hit.get('document') or ''}"
        )

    if not evidence_blocks:
        # 无证据固定文案，用在严格模式短答
        answer_text = STRICT_NO_EVIDENCE_REPLY
        citations = []
    else:
        # 历史消息（含刚写入的用户问），用在多轮上下文
        history_stmt = (
            select(MessageRecord)
            .where(MessageRecord.conversation_id == conversation.id)
            .order_by(MessageRecord.created_at.desc())
            .limit(_settings.chat_history_message_limit)
        )
        # 时间正序历史，用在拼 messages
        history = list(reversed(list(db.scalars(history_stmt).all())))
        # 发给聊天模型的消息列表，用在 create_chat_completion
        chat_messages: list[dict[str, str]] = [
            {"role": "system", "content": STRICT_SYSTEM_PROMPT},
            {
                "role": "system",
                "content": "知识片段：\n\n" + "\n\n---\n\n".join(evidence_blocks),
            },
        ]
        for item in history:
            if item.role == MessageRole.SYSTEM.value:
                continue
            chat_messages.append({"role": item.role, "content": item.content})
        answer_text = llm_client.create_chat_completion(chat_model, chat_messages)
        if not answer_text:
            answer_text = STRICT_NO_EVIDENCE_REPLY
            citations = []

    # 助手消息实体，用在落库
    assistant_message = MessageRecord(
        id=str(uuid.uuid4()),
        conversation_id=conversation.id,
        role=MessageRole.ASSISTANT.value,
        content=answer_text,
        citations_json=json.dumps(
            [item.model_dump(by_alias=True) for item in citations],
            ensure_ascii=False,
        )
        if citations
        else None,
        created_at=_now(),
    )
    db.add(assistant_message)
    conversation.updated_at = _now()
    db.commit()
    db.refresh(user_message)
    db.refresh(assistant_message)
    return AskMessageResponse(
        user_message=to_message(user_message),
        assistant_message=to_message(assistant_message),
    )
