"""FastAPI 依赖：当前用户与鉴权。"""

from fastapi import Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models.user import UserRecord
from app.security import decode_access_token

# Bearer 安全方案，用在 OpenAPI 与依赖注入
bearer_scheme = HTTPBearer(auto_error=False)
# 模块配置，用在 SSE 查询参数名
_settings = get_settings()


# 从 Authorization 头解析当前用户，用在受保护路由
def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> UserRecord:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未登录或令牌缺失",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        # Token 中的用户 id，用在加载 UserRecord
        user_id = decode_access_token(credentials.credentials)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    # 当前用户实体，用在 Owner 校验
    user = db.get(UserRecord, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在或已失效",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


# SSE 用：头或查询参数取 Token，用在 heartbeat 鉴权
def get_current_user_sse(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    access_token: str | None = Query(
        default=None,
        alias="access_token",
        description="EventSource 无法设头时用查询参数传 JWT",
    ),
    db: Session = Depends(get_db),
) -> UserRecord:
    # 最终使用的原始 Token，用在 decode
    raw_token: str | None = None
    if credentials is not None and credentials.scheme.lower() == "bearer":
        raw_token = credentials.credentials
    elif access_token:
        raw_token = access_token
    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未登录或令牌缺失",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        # Token 中的用户 id，用在加载 UserRecord
        user_id = decode_access_token(raw_token)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    # 当前用户实体，用在确认登录态后放行 SSE
    user = db.get(UserRecord, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在或已失效",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
