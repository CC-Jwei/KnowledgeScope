"""统一滑动窗口分块。"""

from app.config import get_settings

# 分块配置，用在窗口大小/重叠/最短块
_settings = get_settings()


# 按字符滑动窗口切分正文，用在入库管道
def split_text(content: str) -> list[str]:
    # 去首尾后的正文，用在切分
    text = content.strip()
    if not text:
        return []
    # 窗口大小，用在切片
    size = _settings.chunk_size_chars
    # 重叠长度，用在步进计算
    overlap = _settings.chunk_overlap_chars
    # 最短保留长度，用在丢弃过短块
    min_chars = _settings.chunk_min_chars
    if overlap >= size:
        overlap = max(0, size // 4)
    # 步进，用在滑动
    step = max(1, size - overlap)
    # 结果块列表，用在写入 ChunkRecord
    chunks: list[str] = []
    # 当前起始下标，用在循环切片
    start = 0
    # 正文总长，用在边界判断
    length = len(text)
    while start < length:
        # 当前块结束下标，用在切片
        end = min(start + size, length)
        # 当前块文本，用在最短阈值过滤
        piece = text[start:end].strip()
        if len(piece) >= min_chars:
            chunks.append(piece)
        if end >= length:
            break
        start += step
    return chunks
