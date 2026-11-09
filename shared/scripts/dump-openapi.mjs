/**
 * Dump OpenAPI JSON snapshot from backend into shared/openapi/openapi.json.
 *
 * Default: import FastAPI app via backend/.venv (server need not be running).
 * Optional: --from-url or OPENAPI_URL to fetch from a live server.
 */

import { spawnSync } from 'node:child_process'
import { mkdirSync, writeFileSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const sharedRoot = path.resolve(__dirname, '..')
const repoRoot = path.resolve(sharedRoot, '..')
const backendRoot = path.join(repoRoot, 'backend')
const outDir = path.join(sharedRoot, 'openapi')
const outFile = path.join(outDir, 'openapi.json')

const DEFAULT_OPENAPI_URL = 'http://127.0.0.1:8000/openapi.json'

function resolveBackendPython() {
  const win = path.join(backendRoot, '.venv', 'Scripts', 'python.exe')
  const nix = path.join(backendRoot, '.venv', 'bin', 'python')
  return process.platform === 'win32' ? win : nix
}

function dumpFromPython() {
  const python = resolveBackendPython()
  const code = [
    'import json',
    'from app.main import app',
    'print(json.dumps(app.openapi(), ensure_ascii=False, indent=2))',
  ].join('; ')

  const result = spawnSync(python, ['-c', code], {
    cwd: backendRoot,
    encoding: 'utf8',
    maxBuffer: 16 * 1024 * 1024,
  })

  if (result.error) {
    throw new Error(
      `Cannot start backend Python (${python}): ${result.error.message}\n` +
        'Create .venv and install deps per backend/README.md first.',
    )
  }
  if (result.status !== 0) {
    throw new Error(
      `OpenAPI dump failed (exit ${result.status}):\n${result.stderr || result.stdout}`,
    )
  }
  return result.stdout
}

async function dumpFromUrl(url) {
  const response = await fetch(url)
  if (!response.ok) {
    throw new Error(`Fetch OpenAPI failed: HTTP ${response.status} ${url}`)
  }
  const data = await response.json()
  return `${JSON.stringify(data, null, 2)}\n`
}

function parseArgs(argv) {
  const fromUrl = argv.includes('--from-url')
  const urlFlagIndex = argv.indexOf('--url')
  const url =
    process.env.OPENAPI_URL ||
    (urlFlagIndex >= 0 ? argv[urlFlagIndex + 1] : undefined) ||
    DEFAULT_OPENAPI_URL
  return { fromUrl, url }
}

async function main() {
  const { fromUrl, url } = parseArgs(process.argv.slice(2))
  mkdirSync(outDir, { recursive: true })

  const raw = fromUrl || process.env.OPENAPI_URL ? await dumpFromUrl(url) : dumpFromPython()
  const normalized = raw.endsWith('\n') ? raw : `${raw}\n`
  writeFileSync(outFile, normalized, 'utf8')

  const schema = JSON.parse(normalized)
  const pathCount = Object.keys(schema.paths ?? {}).length
  const schemaCount = Object.keys(schema.components?.schemas ?? {}).length
  console.log(`OpenAPI written: ${path.relative(repoRoot, outFile)}`)
  console.log(`  title=${schema.info?.title} version=${schema.info?.version}`)
  console.log(`  paths=${pathCount} schemas=${schemaCount}`)
  if (fromUrl || process.env.OPENAPI_URL) {
    console.log(`  source=url (${url})`)
  } else {
    console.log('  source=backend/.venv (app.openapi())')
  }
}

main().catch((error) => {
  console.error(error instanceof Error ? error.message : error)
  process.exit(1)
})
