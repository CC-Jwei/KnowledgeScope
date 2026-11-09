"""领域枚举。"""

from enum import StrEnum


class SourceType(StrEnum):
    """来源类型。创建接口仅允许 plain_text，其余为后续预留。"""

    # 纯文字来源，用在 MVP 创建与存储默认值
    PLAIN_TEXT = "plain_text"
    # 网页链接预留，用在后续 SourceType 扩展
    WEB_PAGE = "web_page"
    # 视频链接预留，用在后续 SourceType 扩展
    VIDEO_URL = "video_url"
    # 图片文件预留，用在后续 SourceType 扩展
    IMAGE = "image"
    # 图片链接预留，用在后续 SourceType 扩展
    IMAGE_URL = "image_url"
    # Markdown 预留，用在后续 SourceType 扩展
    MARKDOWN = "markdown"
    # PDF 预留，用在后续 SourceType 扩展
    PDF = "pdf"
    # Word 预留，用在后续 SourceType 扩展
    WORD = "word"
    # Excel 预留，用在后续 SourceType 扩展
    EXCEL = "excel"
    # PowerPoint 预留，用在后续 SourceType 扩展
    POWERPOINT = "powerpoint"


class SourceStatus(StrEnum):
    """来源处理状态。MVP 创建后直接为 ready。"""

    # 可被后续检索使用，用在 MVP 创建后的默认状态
    READY = "ready"
    # 等待处理预留，用在后续采集管道
    PENDING = "pending"
    # 处理中预留，用在后续采集管道
    PROCESSING = "processing"
    # 处理失败预留，用在后续采集管道
    FAILED = "failed"
