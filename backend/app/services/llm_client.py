"""OpenAI 兼容 HTTP：嵌入与聊天。"""

import time
from typing import Any

import httpx
from fastapi import HTTPException, status

from app.config import get_settings
from app.services.model_profile_service import ResolvedModel

# 嵌入与聊天相关配置，用在超时、重试与生成参数
_settings = get_settings()

# 聊天采样温度，用在问答场景保持低随机性
CHAT_TEMPERATURE = 0.2

# 网络层被本机安全策略拒绝的错误码，用在识别出站被拦
SOCKET_ACCESS_DENIED_CODE = 10013

# 异常链下钻上限，用在防止异常自引用导致死循环
_EXCEPTION_CHAIN_LIMIT = 10


# 判断异常是否为本机安全策略拒绝出站连接，用在重试判断与错误文案
def _is_socket_denied(exc: BaseException) -> bool:
    # 当前待检异常节点，用在沿 __cause__ / __context__ 逐层下钻
    current: BaseException | None = exc
    # 已下钻层数，用在上限保护避免环
    depth = 0
    while current is not None and depth < _EXCEPTION_CHAIN_LIMIT:
        if isinstance(current, PermissionError) and getattr(current, "winerror", None) == SOCKET_ACCESS_DENIED_CODE:
            return True
        # 下钻到下一个异常节点，用在继续匹配套接字拒绝
        next_node = current.__cause__ or current.__context__
        if next_node is None and current.args:
            # args 里直接包的异常，用在 httpx 多层包装场景
            next_node = next((item for item in current.args if isinstance(item, BaseException)), None)
        current = next_node  # type: ignore[assignment]
        depth += 1
    return False


# 判断是否为可重试的失败，用在 _post_json 的尝试循环
def _should_retry(exc: httpx.HTTPError) -> bool:
    # 本机策略拒绝时重试只会重复被拦，用在直接失败
    if _is_socket_denied(exc):
        return False
    # 上游 5xx 视为偶发，用在重试
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code >= status.HTTP_500_INTERNAL_SERVER_ERROR
    # 仅建连阶段失败可重试，用在避免超时后重复长生成
    return isinstance(exc, (httpx.ConnectError, httpx.ConnectTimeout))


# 组装上游失败的 502 说明，用在嵌入与聊天异常分支
def _upstream_error_detail(label: str, base_url: str, exc: Exception) -> str:
    if isinstance(exc, httpx.HTTPStatusError):
        return f"{label}服务返回错误状态 {exc.response.status_code}（{base_url}）：{exc}"
    if _is_socket_denied(exc):
        return (
            f"{label}服务连接被本机拒绝（{base_url}）：{exc}"
            "该地址很可能被本机安全软件或网络策略拦截，"
            "请在「模型设置」新建指向可访问地址的同用途配置档，再在提问时选中它。"
        )
    return f"{label}服务调用失败（{base_url}）：{exc}"


# 统一发送 POST JSON 并按配置重试，用在嵌入与聊天调用
def _post_json(
    base_url: str,
    path: str,
    body: dict[str, Any],
    headers: dict[str, str],
    timeout: float,
    label: str,
) -> dict[str, Any]:
    # 已完成尝试次数，用在重试上限判断
    attempts = 0
    while True:
        attempts += 1
        try:
            with httpx.Client(timeout=timeout) as client:
                # HTTP 响应，用在解析 JSON
                response = client.post(f"{base_url}{path}", json=body, headers=headers)
                response.raise_for_status()
                # 响应 JSON，用在调用方取字段
                payload: dict[str, Any] = response.json()
                return payload
        except httpx.HTTPError as exc:
            if not _should_retry(exc) or attempts >= _settings.llm_max_attempts:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=_upstream_error_detail(label, base_url, exc),
                ) from exc
            # 退避等待秒数，用在两次尝试之间
            time.sleep(_settings.llm_retry_backoff_seconds * attempts)


# 调用嵌入接口，返回向量列表，用在入库与检索
def create_embeddings(model: ResolvedModel, texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    # 请求体，用在 OpenAI 兼容 API
    body = {"model": model.model_name, "input": texts}
    # 请求头，用在 Bearer 鉴权（不记录完整 Key）
    headers = {
        "Authorization": f"Bearer {model.api_key}",
        "Content-Type": "application/json",
    }
    # 上游响应，用在取 data
    payload = _post_json(
        model.base_url,
        "/embeddings",
        body,
        headers,
        _settings.embedding_request_timeout_seconds,
        "嵌入",
    )
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
    # 请求体，用在 OpenAI 兼容 API
    body = {
        "model": model.model_name,
        "messages": messages,
        "max_tokens": _settings.chat_max_output_tokens,
        "temperature": CHAT_TEMPERATURE,
    }
    # 请求头，用在 Bearer 鉴权
    headers = {
        "Authorization": f"Bearer {model.api_key}",
        "Content-Type": "application/json",
    }
    # 上游响应，用在取 choices
    payload = _post_json(
        model.base_url,
        "/chat/completions",
        body,
        headers,
        _settings.chat_request_timeout_seconds,
        "聊天",
    )
    # choices 列表，用在取第一条
    choices = payload.get("choices") or []
    if not choices:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="聊天服务未返回内容",
        )
    # 首条候选，用在读 message 与结束原因
    choice = choices[0]
    # 助手消息节点，用在取 content
    message = choice.get("message") or {}
    # 助手正文，用在写入 Message
    content = str(message.get("content") or "").strip()
    if content:
        return content
    # 结束原因，用在诊断空正文
    finish_reason = str(choice.get("finish_reason") or "")
    if finish_reason == "length":
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(
                "聊天服务未产出正文：输出上限 "
                f"{_settings.chat_max_output_tokens} tokens 已被推理内容占满，"
                "请调大 CHAT_MAX_OUTPUT_TOKENS 或改用非推理模型。"
            ),
        )
    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail=f"聊天服务未返回正文（finish_reason={finish_reason or 'unknown'}）",
    )
