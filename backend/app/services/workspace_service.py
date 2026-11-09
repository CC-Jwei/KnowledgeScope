"""知识空间业务逻辑。"""

import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.workspace import WorkspaceRecord
from app.schemas.workspace import WorkspaceCreate, WorkspaceUpdate


# 返回当前 UTC 时间，用在创建/更新空间时间戳
def _now() -> datetime:
    return datetime.now(timezone.utc)


# 按创建时间倒序列出全部空间，用在 workspaces 列表接口
def list_workspaces(db: Session) -> list[WorkspaceRecord]:
    # 列表查询语句，用在 scalars 取结果
    stmt = select(WorkspaceRecord).order_by(WorkspaceRecord.created_at.desc())
    return list(db.scalars(stmt).all())


# 按 id 取空间，不存在则 404，用在详情/更新/删除与来源校验
def get_workspace_or_404(db: Session, workspace_id: str) -> WorkspaceRecord:
    # 按主键查到的空间，用在后续业务或抛错
    workspace = db.get(WorkspaceRecord, workspace_id)
    if workspace is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="知识空间不存在",
        )
    return workspace


# 持久化新建知识空间，用在 workspaces 创建接口
def create_workspace(db: Session, payload: WorkspaceCreate) -> WorkspaceRecord:
    # 创建时刻，用在 created_at/updated_at
    now = _now()
    # 待写入的空间实体，用在 commit 后返回
    workspace = WorkspaceRecord(
        id=str(uuid.uuid4()),
        name=payload.name,
        description=payload.description,
        created_at=now,
        updated_at=now,
        source_count=0,
    )
    db.add(workspace)
    db.commit()
    db.refresh(workspace)
    return workspace


# 更新空间名称或描述，用在 workspaces PATCH 接口
def update_workspace(
    db: Session,
    workspace_id: str,
    payload: WorkspaceUpdate,
) -> WorkspaceRecord:
    # 待更新的空间实体，用在写回字段并提交
    workspace = get_workspace_or_404(db, workspace_id)
    if payload.name is not None:
        workspace.name = payload.name
    if "description" in payload.model_fields_set:
        workspace.description = payload.description
    workspace.updated_at = _now()
    db.commit()
    db.refresh(workspace)
    return workspace


# 硬删除空间（级联来源），用在 workspaces DELETE 接口
def delete_workspace(db: Session, workspace_id: str) -> None:
    # 待删除的空间实体，用在 db.delete
    workspace = get_workspace_or_404(db, workspace_id)
    db.delete(workspace)
    db.commit()


# 增减 sourceCount 并刷新 updatedAt，用在来源创建/删除后同步空间
def bump_workspace_source_count(
    db: Session,
    workspace: WorkspaceRecord,
    delta: int,
) -> None:
    workspace.source_count = max(0, workspace.source_count + delta)
    workspace.updated_at = _now()
