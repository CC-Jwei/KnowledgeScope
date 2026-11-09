"""纯文字来源业务逻辑。"""

import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.source import SourceRecord
from app.schemas.enums import SourceStatus, SourceType
from app.schemas.source import (
    PlainTextSourceCreate,
    PlainTextSourceUpdate,
    Source,
    SourceListItem,
)
from app.services import workspace_service

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


# 未传标题时生成默认标题，用在创建纯文字来源
def _default_title(content: str) -> str:
    # 取正文前缀的长度，用在切片生成标题
    prefix_len = _settings.default_source_title_prefix_length
    # 正文前缀片段，用在有内容时作为标题
    snippet = content[:prefix_len].strip()
    if snippet:
        return snippet
    return _settings.default_untitled_source_title


# ORM 转详情契约（含全文），用在创建/详情/更新接口响应
def to_source_detail(record: SourceRecord) -> Source:
    return Source(
        id=record.id,
        workspace_id=record.workspace_id,
        type=SourceType(record.type),
        title=record.title,
        status=SourceStatus(record.status),
        created_at=record.created_at,
        updated_at=record.updated_at,
        content=record.content,
        content_preview=_preview(record.content),
    )


# ORM 转列表项（无全文），用在来源列表接口响应
def to_source_list_item(record: SourceRecord) -> SourceListItem:
    return SourceListItem(
        id=record.id,
        workspace_id=record.workspace_id,
        type=SourceType(record.type),
        title=record.title,
        status=SourceStatus(record.status),
        created_at=record.created_at,
        updated_at=record.updated_at,
        content_preview=_preview(record.content),
    )


# 列出某空间下来源，用在 sources 列表接口
def list_sources(db: Session, workspace_id: str) -> list[SourceRecord]:
    workspace_service.get_workspace_or_404(db, workspace_id)
    # 按空间过滤并倒序的查询，用在 scalars 取结果
    stmt = (
        select(SourceRecord)
        .where(SourceRecord.workspace_id == workspace_id)
        .order_by(SourceRecord.created_at.desc())
    )
    return list(db.scalars(stmt).all())


# 按空间与来源 id 取值，不匹配则 404，用在详情/更新/删除
def get_source_or_404(
    db: Session,
    workspace_id: str,
    source_id: str,
) -> SourceRecord:
    workspace_service.get_workspace_or_404(db, workspace_id)
    # 按主键查到的来源，用在归属校验后返回
    record = db.get(SourceRecord, source_id)
    if record is None or record.workspace_id != workspace_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="来源不存在",
        )
    return record


# 创建 plain_text 来源并增加 sourceCount，用在 sources POST 接口
def create_plain_text_source(
    db: Session,
    workspace_id: str,
    payload: PlainTextSourceCreate,
) -> SourceRecord:
    # 所属空间，用在 bump sourceCount
    workspace = workspace_service.get_workspace_or_404(db, workspace_id)
    # 创建时刻，用在 created_at/updated_at
    now = _now()
    # 最终写入的标题，用在 SourceRecord.title
    title = payload.title or _default_title(payload.content)
    if len(title) > _settings.title_max_length:
        title = title[: _settings.title_max_length]

    # 待写入的来源实体，用在 commit 后返回
    record = SourceRecord(
        id=str(uuid.uuid4()),
        workspace_id=workspace_id,
        type=SourceType.PLAIN_TEXT.value,
        title=title,
        status=SourceStatus.READY.value,
        content=payload.content,
        created_at=now,
        updated_at=now,
    )
    db.add(record)
    workspace_service.bump_workspace_source_count(db, workspace, 1)
    db.commit()
    db.refresh(record)
    return record


# 更新来源标题或正文，用在 sources PATCH 接口
def update_plain_text_source(
    db: Session,
    workspace_id: str,
    source_id: str,
    payload: PlainTextSourceUpdate,
) -> SourceRecord:
    # 待更新的来源，用在写回字段
    record = get_source_or_404(db, workspace_id, source_id)
    # 所属空间，用在同步 updated_at
    workspace = workspace_service.get_workspace_or_404(db, workspace_id)

    if payload.title is not None:
        record.title = payload.title
    if payload.content is not None:
        record.content = payload.content

    record.updated_at = _now()
    workspace.updated_at = _now()
    db.commit()
    db.refresh(record)
    return record


# 删除来源并减少 sourceCount，用在 sources DELETE 接口
def delete_source(db: Session, workspace_id: str, source_id: str) -> None:
    # 待删除的来源，用在 db.delete
    record = get_source_or_404(db, workspace_id, source_id)
    # 所属空间，用在 bump sourceCount
    workspace = workspace_service.get_workspace_or_404(db, workspace_id)
    db.delete(record)
    workspace_service.bump_workspace_source_count(db, workspace, -1)
    db.commit()
