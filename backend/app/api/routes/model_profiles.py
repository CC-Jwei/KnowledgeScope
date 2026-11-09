"""模型配置档路由。"""

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models.user import UserRecord
from app.schemas.model_profile import ModelProfile, ModelProfileCreate, ModelProfileUpdate
from app.services import model_profile_service

# 模型配置档子路由，用在 api_router 挂载 /model-profiles
router = APIRouter(prefix="/model-profiles", tags=["model-profiles"])


@router.get(
    "",
    response_model=list[ModelProfile],
    summary="列出系统默认 + 我的模型档（Key 脱敏）",
)
# 列出模型档，用在前端模型设置页
def list_model_profiles(
    db: Session = Depends(get_db),
    current_user: UserRecord = Depends(get_current_user),
) -> list[ModelProfile]:
    return model_profile_service.list_profiles(db, current_user.id)


@router.post(
    "",
    response_model=ModelProfile,
    status_code=status.HTTP_201_CREATED,
    summary="创建个人模型档",
)
# 创建用户模型档，用在模型设置页新增
def create_model_profile(
    payload: ModelProfileCreate,
    db: Session = Depends(get_db),
    current_user: UserRecord = Depends(get_current_user),
) -> ModelProfile:
    return model_profile_service.create_profile(db, current_user.id, payload)


@router.patch(
    "/{profile_id}",
    response_model=ModelProfile,
    summary="更新个人模型档（Key 不传则保留）",
)
# 更新用户模型档，用在模型设置页编辑
def update_model_profile(
    profile_id: str,
    payload: ModelProfileUpdate,
    db: Session = Depends(get_db),
    current_user: UserRecord = Depends(get_current_user),
) -> ModelProfile:
    return model_profile_service.update_profile(
        db,
        profile_id,
        current_user.id,
        payload,
    )


@router.delete(
    "/{profile_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除个人模型档（不可删系统默认）",
)
# 删除用户模型档，用在模型设置页删除
def delete_model_profile(
    profile_id: str,
    db: Session = Depends(get_db),
    current_user: UserRecord = Depends(get_current_user),
) -> Response:
    model_profile_service.delete_profile(db, profile_id, current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
