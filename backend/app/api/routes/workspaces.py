"""知识空间 CRUD（需登录 + Owner 隔离）。"""

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models.user import UserRecord
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
# 创建知识空间并绑定当前用户为 Owner，用在前端空间列表新建
def create_workspace(
    payload: WorkspaceCreate,
    db: Session = Depends(get_db),
    current_user: UserRecord = Depends(get_current_user),
) -> Workspace:
    # 新建后的 ORM 记录，用在转成 Workspace 响应
    record = workspace_service.create_workspace(db, current_user.id, payload)
    return Workspace.model_validate(record)


@router.get(
    "",
    response_model=list[Workspace],
    summary="列出我的知识空间",
)
# 列出当前用户的知识空间，用在前端空间列表页
def list_workspaces(
    db: Session = Depends(get_db),
    current_user: UserRecord = Depends(get_current_user),
) -> list[Workspace]:
    # 查询到的空间记录，用在批量转成响应模型
    records = workspace_service.list_workspaces(db, current_user.id)
    return [Workspace.model_validate(item) for item in records]


@router.get(
    "/{workspace_id}",
    response_model=Workspace,
    summary="获取知识空间详情",
)
# 按 id 取自己的空间详情，用在前端空间详情页头信息
def get_workspace(
    workspace_id: str,
    db: Session = Depends(get_db),
    current_user: UserRecord = Depends(get_current_user),
) -> Workspace:
    # 命中的空间记录，用在转成 Workspace 响应
    record = workspace_service.get_workspace_for_owner_or_404(
        db,
        workspace_id,
        current_user.id,
    )
    return Workspace.model_validate(record)


@router.patch(
    "/{workspace_id}",
    response_model=Workspace,
    summary="更新知识空间",
)
# 更新自己的空间名称或描述，用在前端详情页编辑表单
def update_workspace(
    workspace_id: str,
    payload: WorkspaceUpdate,
    db: Session = Depends(get_db),
    current_user: UserRecord = Depends(get_current_user),
) -> Workspace:
    # 更新后的空间记录，用在转成 Workspace 响应
    record = workspace_service.update_workspace(
        db,
        workspace_id,
        current_user.id,
        payload,
    )
    return Workspace.model_validate(record)


@router.delete(
    "/{workspace_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除知识空间（级联来源/会话/向量）",
)
# 删除自己的空间及其下资源，用在前端列表/详情的删除确认
def delete_workspace(
    workspace_id: str,
    db: Session = Depends(get_db),
    current_user: UserRecord = Depends(get_current_user),
) -> Response:
    workspace_service.delete_workspace(db, workspace_id, current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
