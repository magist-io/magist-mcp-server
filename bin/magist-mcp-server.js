#!/usr/bin/env node
// @magist/mcp-server — a thin stdio bridge to the hosted Magist MCP server.
//
// MCP stdio hosts (Claude Desktop, Cursor, Windsurf, …) launch this binary and
// speak the stdio transport: newline-delimited JSON-RPC 2.0 messages on stdin,
// responses on stdout. This process forwards each message to the hosted
// Streamable-HTTP endpoint (https://magist.io/api/mcp) and writes the response
// back. The hosted server is stateless (no session id), so the bridge needs no
// session handling — it is a pure pass-through.
//
// Self-hosting: set MAGIST_MCP_URL to point at your own /api/mcp deployment.
//
// No runtime dependencies (Node >= 18 global fetch + readline). Returns legal
// INFORMATION for research and attorney handoff, never legal advice.

import { createInterface } from 'node:readline'

const ENDPOINT = process.env.MAGIST_MCP_URL || 'https://magist.io/api/mcp'

function writeMessage(obj) {
  // One complete JSON object per line — the stdio transport framing.
  process.stdout.write(JSON.stringify(obj) + '\n')
}

// Build a JSON-RPC error keyed to the request id(s). A notification (no `id`)
// gets no error reply — you cannot respond to a notification.
function errorFor(message, code, msg) {
  const one = (m) =>
    m && typeof m === 'object' && !Array.isArray(m) && m.id !== undefined
      ? { jsonrpc: '2.0', id: m.id, error: { code, message: msg } }
      : null
  if (Array.isArray(message)) {
    const errs = message.map(one).filter(Boolean)
    return errs.length ? errs : null
  }
  return one(message)
}

async function forward(message) {
  let res
  try {
    res = await fetch(ENDPOINT, {
      method: 'POST',
      headers: { 'content-type': 'application/json', accept: 'application/json' },
      body: JSON.stringify(message),
    })
  } catch (err) {
    return errorFor(message, -32000, `Transport error: ${err?.message || 'request failed'}`)
  }
  // 202 = the request was only notifications/responses — nothing to return.
  if (res.status === 202) return null
  const text = await res.text()
  if (!text) {
    // A non-202 with an empty body shouldn't happen (the server always returns
    // a JSON-RPC body on non-202), but synthesize an error rather than silently
    // drop the response and leave the host waiting on the request id.
    return errorFor(message, -32603, `Empty response from server (HTTP ${res.status}).`)
  }
  try {
    return JSON.parse(text)
  } catch {
    return errorFor(message, -32700, 'Invalid JSON in server response.')
  }
}

async function handleLine(line) {
  const trimmed = line.trim()
  if (!trimmed) return
  let message
  try {
    message = JSON.parse(trimmed)
  } catch {
    writeMessage({ jsonrpc: '2.0', id: null, error: { code: -32700, message: 'Parse error.' } })
    return
  }
  const response = await forward(message)
  if (response !== null && response !== undefined) writeMessage(response)
}

// Process lines strictly in order: chain each handler so responses are written
// in request order and never interleave on the wire, even for large payloads.
let chain = Promise.resolve()
const rl = createInterface({ input: process.stdin })
rl.on('line', (line) => {
  chain = chain.then(() => handleLine(line)).catch(() => {})
})
// When the host closes stdin, finish any in-flight work, then exit cleanly.
rl.on('close', () => {
  chain.finally(() => process.exit(0))
})
