"""知识空间 CRUD。"""

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.workspace import Workspace, WorkspaceCreate, WorkspaceUpdate
from app.services import workspace_service

# 知识空间子路由，用在 api_router 挂载 /workspaces
router = APIRouter(prefix="/workspaces")


@router.post(
    "",
    response_model=Workspace,
    status_code=status.HTTP_201_CREATED,
    summary="创建知识空间",
)
# 创建知识空间，用在前端空间列表的新建入口
def create_workspace(
    payload: WorkspaceCreate,
    db: Session = Depends(get_db),
) -> Workspace:
    # 新建后的 ORM 记录，用在转成 Workspace 响应
    record = workspace_service.create_workspace(db, payload)
    return Workspace.model_validate(record)


@router.get(
    "",
    response_model=list[Workspace],
    summary="列出知识空间",
)
# 列出全部知识空间，用在前端空间列表页
def list_workspaces(db: Session = Depends(get_db)) -> list[Workspace]:
    # 查询到的空间记录，用在批量转成响应模型
    records = workspace_service.list_workspaces(db)
    return [Workspace.model_validate(item) for item in records]


@router.get(
    "/{workspace_id}",
    response_model=Workspace,
    summary="获取知识空间详情",
)
# 按 id 取空间详情，用在前端空间详情页头信息
def get_workspace(workspace_id: str, db: Session = Depends(get_db)) -> Workspace:
    # 命中的空间记录，用在转成 Workspace 响应
    record = workspace_service.get_workspace_or_404(db, workspace_id)
    return Workspace.model_validate(record)


@router.patch(
    "/{workspace_id}",
    response_model=Workspace,
    summary="更新知识空间",
)
# 更新空间名称或描述，用在前端详情页编辑表单
def update_workspace(
    workspace_id: str,
    payload: WorkspaceUpdate,
    db: Session = Depends(get_db),
) -> Workspace:
    # 更新后的空间记录，用在转成 Workspace 响应
    record = workspace_service.update_workspace(db, workspace_id, payload)
    return Workspace.model_validate(record)


@router.delete(
    "/{workspace_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除知识空间（级联删除来源）",
)
# 删除空间及其来源，用在前端列表/详情的删除确认
def delete_workspace(workspace_id: str, db: Session = Depends(get_db)) -> Response:
    workspace_service.delete_workspace(db, workspace_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
