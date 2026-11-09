"""密码哈希与 JWT 签发校验。"""

from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.config import get_settings

# 模块配置，用在 JWT 与密码哈希
_settings = get_settings()


# 对明文密码做 bcrypt 哈希，用在注册写库
def hash_password(plain_password: str) -> str:
    # 编码后的明文，用在 bcrypt.hashpw
    password_bytes = plain_password.encode("utf-8")
    # 哈希结果，用在存入 users.password_hash
    hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    return hashed.decode("utf-8")


# 校验明文与哈希是否匹配，用在登录
def verify_password(plain_password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        password_hash.encode("utf-8"),
    )


# 签发 Access Token，用在登录/注册响应
def create_access_token(subject_user_id: str) -> str:
    # 过期时刻，用在 JWT exp 声明
    expire_at = datetime.now(timezone.utc) + timedelta(
        minutes=_settings.jwt_access_token_expire_minutes,
    )
    # JWT 载荷，用在 encode
    payload = {
        "sub": subject_user_id,
        "exp": expire_at,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(
        payload,
        _settings.jwt_secret_key,
        algorithm=_settings.jwt_algorithm,
    )


# 解析并校验 Token，返回用户 id；失败抛 ValueError，用在 deps
def decode_access_token(token: str) -> str:
    try:
        # 解码后的载荷，用在取 sub
        payload = jwt.decode(
            token,
            _settings.jwt_secret_key,
            algorithms=[_settings.jwt_algorithm],
        )
    except jwt.PyJWTError as exc:
        raise ValueError("无效或过期的令牌") from exc
    # 用户 id，用在加载当前用户
    subject = payload.get("sub")
    if not subject or not isinstance(subject, str):
        raise ValueError("令牌缺少主体")
    return subject
