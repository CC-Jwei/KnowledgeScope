"""纯文字来源 CRUD。"""

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.source import (
    PlainTextSourceCreate,
    PlainTextSourceUpdate,
    Source,
    SourceListItem,
)
from app.services import source_service

# 空间下来源子路由，用在 api_router 挂载 /workspaces/{id}/sources
router = APIRouter(prefix="/workspaces/{workspace_id}/sources")


@router.post(
    "",
    response_model=Source,
    status_code=status.HTTP_201_CREATED,
    summary="创建纯文字来源",
)
# 向空间投递纯文字来源，用在前端详情页投递表单
def create_source(
    workspace_id: str,
    payload: PlainTextSourceCreate,
    db: Session = Depends(get_db),
) -> Source:
    # 新建来源 ORM 记录，用在转成详情响应
    record = source_service.create_plain_text_source(db, workspace_id, payload)
    return source_service.to_source_detail(record)


@router.get(
    "",
    response_model=list[SourceListItem],
    summary="列出空间下来源",
)
# 列出空间内来源（仅预览），用在前端详情页来源列表
def list_sources(
    workspace_id: str,
    db: Session = Depends(get_db),
) -> list[SourceListItem]:
    # 查询到的来源记录，用在转成列表项
    records = source_service.list_sources(db, workspace_id)
    return [source_service.to_source_list_item(item) for item in records]


@router.get(
    "/{source_id}",
    response_model=Source,
    summary="获取来源详情（含全文）",
)
# 获取来源全文详情，用在前端来源详情或抽屉
def get_source(
    workspace_id: str,
    source_id: str,
    db: Session = Depends(get_db),
) -> Source:
    # 命中的来源记录，用在转成详情响应
    record = source_service.get_source_or_404(db, workspace_id, source_id)
    return source_service.to_source_detail(record)


@router.patch(
    "/{source_id}",
    response_model=Source,
    summary="更新纯文字来源标题或正文",
)
# 更新来源标题或正文，用在前端来源编辑
def update_source(
    workspace_id: str,
    source_id: str,
    payload: PlainTextSourceUpdate,
    db: Session = Depends(get_db),
) -> Source:
    # 更新后的来源记录，用在转成详情响应
    record = source_service.update_plain_text_source(
        db,
        workspace_id,
        source_id,
        payload,
    )
    return source_service.to_source_detail(record)


@router.delete(
    "/{source_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除来源",
)
# 删除单条来源，用在前端列表删除确认
def delete_source(
    workspace_id: str,
    source_id: str,
    db: Session = Depends(get_db),
) -> Response:
    source_service.delete_source(db, workspace_id, source_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
