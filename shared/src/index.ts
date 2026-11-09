/**
 * @knowledgescope/shared public entry.
 *
 * front:
 *   import type { Workspace, PlainTextSourceCreate } from '@knowledgescope/shared'
 *   import { ApiPaths, SseEventName } from '@knowledgescope/shared'
 */

export type {
  ConnectedEvent,
  HTTPValidationError,
  HeartbeatEvent,
  PlainTextSourceCreate,
  PlainTextSourceUpdate,
  Source,
  SourceListItem,
  SourceStatus,
  SourceType,
  ValidationError,
  Workspace,
  WorkspaceCreate,
  WorkspaceUpdate,
  components,
  operations,
  paths,
  Schemas,
} from './schema'

export {
  API_V1_PREFIX,
  HEALTH_PATH,
  MVP_SOURCE_STATUS,
  MVP_SOURCE_TYPE,
  OPENAPI_PATH,
  SseEventName,
} from './constants'

export type { SseEventNameValue } from './constants'

export { ApiPaths } from './paths'
