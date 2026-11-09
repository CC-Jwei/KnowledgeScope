// 把 ISO 时间格式化为本地可读字符串，用在列表与详情的时间列
export function formatDateTime(value: string | null | undefined): string {
  if (!value) {
    return '-'
  }

  // 解析后的日期对象，用在本地化格式化
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value
  }

  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  })
}
