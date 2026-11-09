"""OpenAI 兼容 HTTP：嵌入与聊天。"""

from typing import Any

import httpx
from fastapi import HTTPException, status

from app.config import get_settings
from app.services.model_profile_service import ResolvedModel

# 聊天相关配置，用在 max_tokens
_settings = get_settings()


# 调用嵌入接口，返回向量列表，用在入库与检索
def create_embeddings(model: ResolvedModel, texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    # 请求 URL，用在 POST embeddings
    url = f"{model.base_url}/embeddings"
    # 请求体，用在 OpenAI 兼容 API
    body = {"model": model.model_name, "input": texts}
    # 请求头，用在 Bearer 鉴权（不记录完整 Key）
    headers = {
        "Authorization": f"Bearer {model.api_key}",
        "Content-Type": "application/json",
    }
    try:
        with httpx.Client(timeout=60.0) as client:
            # HTTP 响应，用在解析 data
            response = client.post(url, json=body, headers=headers)
            response.raise_for_status()
            # 响应 JSON，用在提取 embedding
            payload: dict[str, Any] = response.json()
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"嵌入服务调用失败: {exc}",
        ) from exc
    # data 数组，用在按 index 取向量
    data = payload.get("data") or []
    # 按 index 排序后的向量，用在与 texts 对齐
    ordered = sorted(data, key=lambda item: item.get("index", 0))
    return [item["embedding"] for item in ordered]


# 调用聊天补全，返回助手文本，用在严格边界问答
def create_chat_completion(
    model: ResolvedModel,
    messages: list[dict[str, str]],
) -> str:
    # 请求 URL，用在 POST chat/completions
    url = f"{model.base_url}/chat/completions"
    # 请求体，用在 OpenAI 兼容 API
    body = {
        "model": model.model_name,
        "messages": messages,
        "max_tokens": _settings.chat_max_output_tokens,
        "temperature": 0.2,
    }
    # 请求头，用在 Bearer 鉴权
    headers = {
        "Authorization": f"Bearer {model.api_key}",
        "Content-Type": "application/json",
    }
    try:
        with httpx.Client(timeout=120.0) as client:
            # HTTP 响应，用在解析 choices
            response = client.post(url, json=body, headers=headers)
            response.raise_for_status()
            # 响应 JSON，用在取 content
            payload: dict[str, Any] = response.json()
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"聊天服务调用失败: {exc}",
        ) from exc
    # choices 列表，用在取第一条
    choices = payload.get("choices") or []
    if not choices:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="聊天服务未返回内容",
        )
    # 助手消息内容，用在写入 Message
    content = (choices[0].get("message") or {}).get("content") or ""
    return str(content).strip()
