# Magist Research for Claude

Research product regulations, typical Controls and historical enforcement with
Magist's cited regulatory reference. This plugin pairs a research skill with
the public remote MCP connector at `https://magist.io/api/mcp`. It runs no local
programs, downloads no packages and needs no API key. The service is subject to
rate limits. The skill and connector are separate components: connect Magist
from the plugin's Connectors tab after installing the plugin.

## Install for personal testing

Upload the Claude plugin ZIP at Customize > Plugins > Add > Upload plugin.
Open a new conversation, check that the Magist research skill appears, and
connect the bundled Magist connector. A successful ZIP parse does not establish
that the skill or connector works in a conversation. For Claude Code, load this
folder with `claude --plugin-dir /absolute/path/to/integrations/claude`.

For connector-only use, add a custom web connector named Magist with the URL
`https://magist.io/api/mcp` and no sign-in. Use the same endpoint for the plugin
and connector so they can be associated rather than duplicated.

## Research workflow and data effects

Start with a public law name such as COPPA, inspect the returned record and
source links, and request its typical Controls. For product scoping, discover
the supported catalog IDs first. Do not substitute guessed IDs or infer
missing product facts.

Every remote tool sends its arguments to Magist and may generate tool-call
telemetry. Do not send personal, confidential, privileged or proprietary facts,
including in search queries. Eight tools read public data or verify a proof.
`compute_requirements` additionally creates or refreshes a public report link
retained for up to 90 days. Use public or synthetic inputs only, with authority
for that public-report effect. If a user refuses a public report, offer cited
read-only research instead. The package declares no local-file or chat-history
retrieval tool, hooks or host-setting changes. Its skill uses the conversation
context supplied by the host; this is not a conversation-isolation promise.

Preserve the returned disclaimer, named attribution, review status, dates and
source links. Coverage and freshness are bounded; some content remains draft.
The deterministic engine operates on structured inputs and versioned data;
free-text interpretation by the host is separate. Signature verification proves
what Magist served, not legal correctness or applicability. No genuine proof
token means positive signature verification is unavailable.

## Privacy Policy

The hosted service's policy is at https://magist.io/privacy. Documentation is
at https://magist.io/mcp, and package support is available through
https://github.com/magist-io/magist-mcp-server/issues. The plugin makes only the
declared connection to Magist. The policy and live service determine server
retention and processing; this package does not promise zero retention or
attest to private provider agreements.

## Status and license

Experimental package for installed-host testing. It has not been accepted into
the Claude directory. Local package checks, MCP protocol tests and directory
review are separate. Submit the remote MCP connector and this plugin folder
separately from the same intended publisher account when their gates are met.
The optional Desktop `.mcpb` is for private installation, not the current
directory submission route.

This package is MIT licensed. The hosted platform is separate; the corpus is
CC BY-SA 4.0. Outputs are legal information for research and attorney handoff,
not legal advice or compliance certification. Consult a licensed attorney
before relying on the research for a launch decision.
