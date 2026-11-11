/**
 * @knowledgescope/shared public entry.
 *
 * front:
 *   import type { Workspace, SourceCreateInput, AskMessageResponse } from '@knowledgescope/shared'
 *   import { ApiPaths, SourceTypeValue, SseEventName } from '@knowledgescope/shared'
 */

export type * from './schema.ts'

export {
  ANSWER_MODE_STRICT,
  API_V1_PREFIX,
  CREATABLE_SOURCE_TYPES,
  HEALTH_PATH,
  INITIAL_SOURCE_STATUS,
  MessageRoleValue,
  ModelPurposeValue,
  MVP_SOURCE_STATUS,
  MVP_SOURCE_TYPE,
  OPENAPI_PATH,
  SourceStatusValue,
  SourceTypeValue,
  SSE_ACCESS_TOKEN_QUERY_PARAM,
  STRICT_NO_EVIDENCE_REPLY,
  SseEventName,
} from './constants.ts'

export type { SseEventNameValue } from './constants.ts'

export { ApiPaths } from './paths.ts'
