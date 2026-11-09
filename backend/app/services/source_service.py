"""来源业务逻辑（多类型创建 + Owner 隔离 + 级联删向量）。"""

import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.source import SourceRecord
from app.schemas.enums import SourceStatus, SourceType
from app.schemas.source import Source, SourceCreate, SourceListItem, SourceUpdate
from app.services import vector_cleanup, workspace_service

# 来源相关配置，用在预览长度、标题截断与默认标题
_settings = get_settings()


# 返回当前 UTC 时间，用在创建/更新来源时间戳
def _now() -> datetime:
    return datetime.now(timezone.utc)


# 截断正文生成预览，用在详情/列表响应的 contentPreview
def _preview(content: str) -> str:
    # 配置的预览最大长度，用在切片判断
    length = _settings.content_preview_length
    if len(content) <= length:
        return content
    return content[:length]


# 未传标题时生成默认标题，用在创建来源
def _default_title(content: str, source_url: str | None) -> str:
    # 取正文前缀的长度，用在切片生成标题
    prefix_len = _settings.default_source_title_prefix_length
    # 正文前缀片段，用在有内容时作为标题
    snippet = (content or "")[:prefix_len].strip()
    if snippet:
        return snippet
    if source_url:
        return source_url[:prefix_len]
    return _settings.default_untitled_source_title


# ORM 转详情契约（含全文），用在创建/详情/更新接口响应
def to_source_detail(record: SourceRecord) -> Source:
    return Source(
        id=record.id,
        workspace_id=record.workspace_id,
        owner_id=record.owner_id,
        type=SourceType(record.type),
        title=record.title,
        status=SourceStatus(record.status),
        created_at=record.created_at,
        updated_at=record.updated_at,
        content=record.content,
        content_preview=_preview(record.content or ""),
        source_url=record.source_url,
        error_message=record.error_message,
    )


# ORM 转列表项（无全文），用在来源列表接口响应
def to_source_list_item(record: SourceRecord) -> SourceListItem:
    return SourceListItem(
        id=record.id,
        workspace_id=record.workspace_id,
        owner_id=record.owner_id,
        type=SourceType(record.type),
        title=record.title,
        status=SourceStatus(record.status),
        created_at=record.created_at,
        updated_at=record.updated_at,
        content_preview=_preview(record.content or ""),
        source_url=record.source_url,
        error_message=record.error_message,
    )


# 列出某空间下来源，用在 sources 列表接口
def list_sources(
    db: Session,
    workspace_id: str,
    owner_id: str,
) -> list[SourceRecord]:
    workspace_service.get_workspace_for_owner_or_404(db, workspace_id, owner_id)
    # 按空间过滤并倒序的查询，用在 scalars 取结果
    stmt = (
        select(SourceRecord)
        .where(SourceRecord.workspace_id == workspace_id)
        .order_by(SourceRecord.created_at.desc())
    )
    return list(db.scalars(stmt).all())


# 按空间与来源 id 取值，越权统一 404，用在详情/更新/删除
def get_source_or_404(
    db: Session,
    workspace_id: str,
    source_id: str,
    owner_id: str,
) -> SourceRecord:
    workspace_service.get_workspace_for_owner_or_404(db, workspace_id, owner_id)
    # 按主键查到的来源，用在归属校验后返回
    record = db.get(SourceRecord, source_id)
    if (
        record is None
        or record.workspace_id != workspace_id
        or record.owner_id != owner_id
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="来源不存在",
        )
    return record


# 创建来源并置 pending，用在 sources POST；立即返回由 worker 入库
def create_source(
    db: Session,
    workspace_id: str,
    owner_id: str,
    payload: SourceCreate,
) -> SourceRecord:
    # 所属空间，用在 bump sourceCount
    workspace = workspace_service.get_workspace_for_owner_or_404(
        db,
        workspace_id,
        owner_id,
    )
    # 创建时刻，用在 created_at/updated_at
    now = _now()
    # 初始正文：web_page 可空，其余已校验非空
    content = payload.content or ""
    # 网页 URL，用在 web_page
    source_url = payload.url if payload.type == SourceType.WEB_PAGE else None
    # 最终写入的标题，用在 SourceRecord.title
    title = payload.title or _default_title(content, source_url)
    if len(title) > _settings.title_max_length:
        title = title[: _settings.title_max_length]

    # 待写入的来源实体，用在 commit 后返回
    record = SourceRecord(
        id=str(uuid.uuid4()),
        workspace_id=workspace_id,
        owner_id=owner_id,
        type=payload.type.value,
        title=title,
        status=SourceStatus.PENDING.value,
        content=content,
        source_url=source_url,
        error_message=None,
        ingest_attempt_count=0,
        created_at=now,
        updated_at=now,
    )
    db.add(record)
    workspace_service.bump_workspace_source_count(db, workspace, 1)
    db.commit()
    db.refresh(record)
    return record


# 更新标题或正文；改正文则重新 pending 入库，用在 sources PATCH
def update_source(
    db: Session,
    workspace_id: str,
    source_id: str,
    owner_id: str,
    payload: SourceUpdate,
) -> SourceRecord:
    # 待更新的来源，用在写回字段
    record = get_source_or_404(db, workspace_id, source_id, owner_id)
    # 所属空间，用在同步 updated_at
    workspace = workspace_service.get_workspace_for_owner_or_404(
        db,
        workspace_id,
        owner_id,
    )

    if payload.title is not None:
        record.title = payload.title
    # 是否需要重新入库，用在改正文后重置状态
    reingest = False
    if payload.content is not None:
        record.content = payload.content
        reingest = True

    if reingest:
        vector_cleanup.delete_vectors_for_source(record.id)
        for old in list(record.chunks):
            db.delete(old)
        record.status = SourceStatus.PENDING.value
        record.error_message = None
        record.ingest_attempt_count = 0

    record.updated_at = _now()
    workspace.updated_at = _now()
    db.commit()
    db.refresh(record)
    return record


# 删除来源：先清向量再删业务行并减计数，用在 sources DELETE
def delete_source(
    db: Session,
    workspace_id: str,
    source_id: str,
    owner_id: str,
) -> None:
    # 待删除的来源，用在向量清理与 db.delete
    record = get_source_or_404(db, workspace_id, source_id, owner_id)
    # 所属空间，用在 bump sourceCount
    workspace = workspace_service.get_workspace_for_owner_or_404(
        db,
        workspace_id,
        owner_id,
    )
    vector_cleanup.delete_vectors_for_source(record.id)
    db.delete(record)
    workspace_service.bump_workspace_source_count(db, workspace, -1)
    db.commit()
