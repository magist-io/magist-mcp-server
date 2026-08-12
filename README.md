# @magist/mcp-server

Connect [Magist](https://magist.io) to your AI host over the Model Context
Protocol. Magist is an open, deterministic, cited **reference** for product
regulation: which laws apply to a product, the obligations and Controls they
imply, and the primary sources behind each. Open data (CC BY-SA 4.0), a
deterministic engine (same inputs produce the same outputs, no LLM in the path),
permanent citation URLs, and a named-practitioner attribution on every response.

This package is a thin **stdio bridge** to the hosted server at
`https://magist.io/api/mcp`. Remote-capable hosts can skip it and point straight
at that URL.

> **Beta: content under attorney review.** The server is live and the engine is
> stable; substantive attorney review of the regulation corpus is in progress.
> Entries carry a `contentReviewStatus` field (`reviewed` is human-verified,
> `draft` is AI-prepared and pending review). Magist returns legal **information**
> for research and attorney handoff, **not legal advice**. Consult a licensed
> attorney before relying on any output for a launch decision.

## One-line install

**Claude Code (CLI)** uses the remote transport directly (no npm install):

```bash
claude mcp add --transport http magist https://magist.io/api/mcp
```

**Claude Desktop / Cursor / Windsurf (npx)**: add the bridge to the host's
`mcpServers` config:

```json
{
  "mcpServers": {
    "magist": {
      "command": "npx",
      "args": ["-y", "@magist/mcp-server"]
    }
  }
}
```

- **Claude Desktop:** Settings -> Developer -> Edit Config (`claude_desktop_config.json`). Restart Claude after saving.
- **Cursor:** Settings -> MCP -> Add new server, or edit `~/.cursor/mcp.json`.
- **Windsurf:** edit `~/.codeium/windsurf/mcp_config.json`, then reload.
- **Codex:** add to `~/.codex/config.toml`:

  ```toml
  [mcp_servers.magist]
  command = "npx"
  args = ["-y", "@magist/mcp-server"]
  ```

**ChatGPT (Developer Mode / Connectors), Manus, and other remote-capable hosts:**
add a custom connector pointing at the Streamable-HTTP endpoint
`https://magist.io/api/mcp` (no npm package needed).

## Verify it works

A `200` with `name: "magist"` means the endpoint is live:

```bash
curl -s https://magist.io/api/mcp
```

List the tools (you should see seven):

```bash
curl -s -X POST https://magist.io/api/mcp \
  -H 'content-type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

In your host, once connected, ask Magist to look up COPPA and list its Controls.
A working connection returns a cited regulation record, not a refusal or a
no-such-tool error.

## Tools

| Tool | What it returns |
| --- | --- |
| `lookup_regulation(id)` | One regulation's structured record: citation, jurisdiction, status, review dates, plain-language summary, and the Controls that may satisfy it. |
| `search_regulations(query, filters?)` | Deterministic keyword + filter search over the corpus, with permanent citation URLs. |
| `compute_requirements(features, markets, audiences, businessModel?)` | Runs the deterministic engine: triggered regulations + Controls, complexity tier, blocker count, per-audience breakdown. Same inputs produce the same outputs. |
| `find_controls(regulationId)` | Controls that may satisfy a regulation, each with a priority signal and summary. |
| `find_vendors(controlId, jurisdiction?)` | Vendors and in-house approaches that implement a Control, with effort/cost and a source disclosure. Magist does not accept payment from vendors. |
| `get_enforcement(regulationId?, since?, limit?)` | Recent enforcement actions with penalties, authorities, and primary-source links. |
| `find_counsel(jurisdiction, practiceArea?, language?)` | Open counsel directory by jurisdiction and practice area. Inclusion is not endorsement. |

Read-only tools are free, unlimited, and unauthenticated; the per-IP rate limit
is abuse-prevention only.

## Self-hosting

Set `MAGIST_MCP_URL` to point the bridge at your own deployment of the open
corpus and engine:

```json
{
  "mcpServers": {
    "magist": {
      "command": "npx",
      "args": ["-y", "@magist/mcp-server"],
      "env": { "MAGIST_MCP_URL": "https://your-host.example.com/api/mcp" }
    }
  }
}
```

## For host LLM developers

Every tool response is wrapped in a canonical envelope. When you render a Magist
response to a user: render the `disclaimer.text` field verbatim; do not restate
outputs as directives or conclusions; surface the `practitioner` attribution and
the `verification` field; suggest a licensed attorney when `counsel_recommended`
is `true`; and prefer the `citations` links when you summarize.

## Links

- Docs: https://magist.io/mcp
- Open-data hub: https://magist.io/data
- License (this package): MIT. The corpus is CC BY-SA 4.0.
