"""认证路由：注册 / 登录 / 当前用户。"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models.user import UserRecord
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserPublic
from app.services import auth_service

# 认证子路由，用在 api_router 挂载 /auth
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=TokenResponse,
    summary="注册（手机号+密码）",
)
# 注册并返回 Access Token，用在登录页注册表单
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> TokenResponse:
    return auth_service.register_user(db, payload)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="登录（手机号+密码）",
)
# 登录并返回 Access Token，用在登录页
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    return auth_service.login_user(db, payload)


@router.get(
    "/me",
    response_model=UserPublic,
    summary="当前用户",
)
# 返回当前登录用户资料，用在前端启动鉴权
def me(current_user: UserRecord = Depends(get_current_user)) -> UserPublic:
    return auth_service.to_user_public(current_user)
