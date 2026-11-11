import { SourceStatusValue, type SourceStatus } from '@knowledgescope/shared'

// 状态中文文案，用在来源列表与抽屉徽标
export const SOURCE_STATUS_LABEL: Record<SourceStatus, string> = {
  [SourceStatusValue.Pending]: '待入库',
  [SourceStatusValue.Processing]: '入库中',
  [SourceStatusValue.Ready]: '可检索',
  [SourceStatusValue.Failed]: '入库失败',
}

// 状态对应的 Element Plus 标签类型，用在视觉区分
export function sourceStatusTagType(
  status: SourceStatus,
): 'success' | 'warning' | 'info' | 'danger' {
  if (status === SourceStatusValue.Ready) {
    return 'success'
  }
  if (status === SourceStatusValue.Failed) {
    return 'danger'
  }
  if (status === SourceStatusValue.Processing) {
    return 'warning'
  }
  return 'info'
}

// 是否仍需轮询的状态集合，用在来源列表定时刷新
export function isSourceInProgress(status: SourceStatus): boolean {
  return status === SourceStatusValue.Pending || status === SourceStatusValue.Processing
}

// 来源类型中文短名，用在投递选项与列表标签
export const SOURCE_TYPE_LABEL = {
  plain_text: '纯文字',
  markdown: 'Markdown',
  web_page: '网页',
} as const
