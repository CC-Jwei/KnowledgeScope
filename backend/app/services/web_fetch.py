"""web_page 单页采集与正文提取。"""

from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from app.config import get_settings

# 采集相关配置，用在超时/体积/UA/scheme
_settings = get_settings()


# 校验 URL scheme 与 host，失败抛业务错误字符串，用在 normalize
def validate_url(url: str) -> None:
    # 解析结果，用在 scheme/netloc 检查
    parsed = urlparse(url)
    if parsed.scheme.lower() not in _settings.web_fetch_allowed_scheme_set:
        raise ValueError("仅支持 http/https URL")
    if not parsed.netloc:
        raise ValueError("URL 无效")


# 下载网页并提取可读正文，用在 web_page 规范化
async def fetch_page_text(url: str) -> str:
    validate_url(url)
    # 请求头，用在伪装 UA
    headers = {"User-Agent": _settings.web_fetch_user_agent}
    try:
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=_settings.web_fetch_timeout_seconds,
            headers=headers,
        ) as client:
            # HTTP 响应，用在体积与正文检查
            response = await client.get(url)
            response.raise_for_status()
            # 原始字节，用在体积上限校验
            raw = response.content
            if len(raw) > _settings.web_fetch_max_bytes:
                raise ValueError("网页体积超过限制")
            # 解码后的 HTML，用在 BeautifulSoup 解析
            html = raw.decode(response.encoding or "utf-8", errors="replace")
    except httpx.TimeoutException as exc:
        raise ValueError("网页抓取超时") from exc
    except httpx.HTTPError as exc:
        raise ValueError(f"网页抓取失败: {exc}") from exc

    # HTML 解析器，用在抽取文本
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    # 提取正文，用在入库 content
    text = soup.get_text(separator="\n", strip=True)
    if not text:
        raise ValueError("未能从网页提取正文")
    return text


# 同步包装：供非 async worker 调用时转业务异常，用在 ingest
def fetch_page_text_sync(url: str) -> str:
    import anyio

    try:
        return anyio.run(fetch_page_text, url)
    except ValueError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise ValueError(str(exc)) from exc
