# Magist Desktop MCP bundle

This unsigned experimental `.mcpb` bundles the exact public
`@magist/mcp-server@0.1.1` bridge and its existing MIT license. It has no runtime
package dependencies and performs no package installation or download. Node.js
18 or newer is required; Claude Desktop may provide that runtime. The bridge
forwards MCP messages to `https://magist.io/api/mcp`. It reads no local data
files and requires no API key. It is a connector, not the research skill plugin.

For private Desktop testing, use Settings > Extensions > Advanced settings >
Install Extension and select the `.mcpb`. Installation, host runtime support,
tool discovery and actual workflows must be tested; the ZIP/schema checks are
not a host compatibility certificate. Do not bypass administrator restrictions
or trust prompts. Claude's current directory does not accept MCPB submissions;
use the remote connector and the separate Claude plugin for directory review.

## Privacy Policy

All tool arguments contact Magist and may generate telemetry. Use only public
or synthetic inputs, never personal, privileged or proprietary information.
Eight tools read public data or verify a proof; `compute_requirements` also
creates or refreshes a public report retained for up to 90 days. Do not invoke
it if the user refuses that effect. The host itself may retain conversations
under its own settings. Magist's policy: https://magist.io/privacy.

Research documentation: https://magist.io/mcp. Support:
https://github.com/magist-io/magist-mcp-server/issues. The bundled code is MIT;
the corpus is CC BY-SA 4.0, and the hosted platform is separate. Preserve source
links, review status and disclaimers. Legal information for research and
attorney handoff, not legal advice or a compliance certificate.
