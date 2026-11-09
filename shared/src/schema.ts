/**
 * Friendly aliases projected from generated OpenAPI types.
 * Do not hand-write conflicting fields; change backend Pydantic, then regenerate.
 */

import type { components, operations, paths } from '../generated/openapi'

export type { components, operations, paths }

export type Schemas = components['schemas']

/** Workspace */
export type Workspace = Schemas['Workspace']
export type WorkspaceCreate = Schemas['WorkspaceCreate']
export type WorkspaceUpdate = Schemas['WorkspaceUpdate']

/** Source */
export type Source = Schemas['Source']
export type SourceListItem = Schemas['SourceListItem']
export type PlainTextSourceCreate = Schemas['PlainTextSourceCreate']
export type PlainTextSourceUpdate = Schemas['PlainTextSourceUpdate']
export type SourceType = Schemas['SourceType']
export type SourceStatus = Schemas['SourceStatus']

/** SSE event data (explicitly mounted in OpenAPI components) */
export type ConnectedEvent = Schemas['ConnectedEvent']
export type HeartbeatEvent = Schemas['HeartbeatEvent']

/** FastAPI validation error body */
export type HTTPValidationError = Schemas['HTTPValidationError']
export type ValidationError = Schemas['ValidationError']
