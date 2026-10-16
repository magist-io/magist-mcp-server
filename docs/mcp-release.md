# MCP distribution and submission handoff

The shared endpoint is `https://magist.io/api/mcp`. Authentication is not
required for the public MCP tools. The authenticated REST API and its signed
grounding proofs are separate; do not request or embed an API key for normal
MCP setup. All inputs go to Magist, and product computation persists a public
report retained for up to 90 days. Use only public or synthetic inputs.

## Artifacts

| Destination | Source | Package | Status boundary |
| --- | --- | --- | --- |
| Claude plugin | `integrations/claude` | `magist-research-claude-0.1.0.zip` | Local package checks; installed-host workflows and portal scan pending |
| Claude custom or directory connector | Hosted endpoint above | No ZIP required | Add to the intended account, exercise tools, then submit separately from the plugin |
| Claude Desktop private extension | `integrations/claude-desktop/manifest.json` plus pinned public bridge | `magist-research-desktop-0.1.1.mcpb` | Unsigned, Node.js >=18, private installation only; not a current directory submission format |
| OpenAI portable plugin | Root `plugin.json`, `mcp.json`, public skill and icon | `magist-research-openai-0.1.1.zip` | Listing metadata and proposed 5 positive/3 negative cases supplied; host runs, recording, scans and submission pending |

The plugin ZIPs intentionally differ. Claude uses `type: http` in `.mcp.json`
and `.claude-plugin/plugin.json`; the portable format uses
`type: streamable-http` in `mcp.json` and root `plugin.json`. Do not rename or
interchange the manifests. Do not upload the entire bridge repository as the
Claude plugin: its root `bin/` is unsuitable for chat and Cowork. Submit the
`integrations/claude` folder instead.

## One operator session

1. Use the intended existing publisher accounts. Magist LLC and the
   `magist-io` GitHub organization are the settled publisher facts. A GitHub
   connection does not establish either host's publisher verification. Use the
   correct Claude organization before submitting: the first organization to
   submit a repository/folder owns that listing. Do not purchase or upgrade a
   plan to complete this checklist.
2. On Claude, upload the Claude plugin ZIP through Customize > Plugins > Add
   > Upload plugin. Start a new conversation, check the skill is available,
   and connect Magist from its Connectors tab with no sign-in. Exercise the
   nine tools using public or synthetic data. A malformed-token negative does
   not establish positive signature verification; record that limitation.
   Plugin evals consume model usage; defer them until an authorized plan has
   capacity. No model eval has been performed for this package.
3. Use `https://claude.ai/directory/manage` for two submissions: first MCP
   connector with the hosted URL, then Plugin bundle from
   `magist-io/magist-mcp-server`, path `integrations/claude`, tracked branch
   `main`. Connect GitHub in that same Claude organization. Run portal
   Validate, save the commit and findings, and resolve actual blocking results.
   The remote connector and plugin should be paired in that organization.
4. Review the connector's annotations before declaring it passes every
   directory criterion. The observed compute tool is idempotent, writes a
   public report, and declares `readOnlyHint: false`, `destructiveHint: false`.
   Claude's current checklist describes destructive hints for tools that
   modify data. That wording needs a portal/reviewer disposition; neither
   pretend the tool is read-only nor silently change its semantics to make a
   checkbox pass.
5. For OpenAI, install the complete portable plugin in the intended host and
   open a new conversation. Record the five positive and three negative
   scenarios in `plugin.json`, retaining actual outputs and refusals. The
   cases are proposed expected behavior, not completed tests. Supply a
   reviewer-accessible installed-plugin walkthrough URL; the website demo
   does not replace it. Use the intended existing publisher account and complete
   any required publisher verification, the actual domain challenge and tool/skill scans. Inspect the imported
   listing metadata before review submission.
6. In the same session, sign into existing Smithery and claim the existing
   Glama listing if the account supports it. Do not create duplicate servers.
   The existing curated remote-directory PR remains a separate upstream review.
   PulseMCP's observed access block remains a hold, not a reason to bypass it.
7. Read the actual data-handling, contact and policy questions in each portal.
   Record factual answers and any remaining private account/provider facts;
   do not invent a completed attorney review, functioning mailbox, zero
   retention promise, verified identity or test result. Required contractual
   acknowledgments remain an operator action. Save actual submission IDs,
   validation/scan results, review decisions and publication URLs separately.

No credentials belong in these packages or in a public issue. The anonymous
connector needs no dummy test account. If a portal insists on account fields,
use the truthful no-auth reviewer-access explanation and resolve the actual
form requirement without fabricating credentials.

## Shared listing text

Name: **Magist Research**. Publisher: **Magist LLC**. Short description:
**Cited regulatory research**. Documentation: `https://magist.io/mcp`.
Privacy: `https://magist.io/privacy`. Terms: `https://magist.io/terms`.
Package support: `https://github.com/magist-io/magist-mcp-server/issues`.
The primary contact email must be a real reachable existing address entered
privately by the operator. No contact email is invented in this package.

Description: Research product regulations, typical Controls, enforcement
history and implementation options using Magist's cited reference and
deterministic tools. Coverage and freshness are bounded, and review status
varies. Use only public or synthetic inputs. Product computation creates or
refreshes a public report retained for up to 90 days. Legal information for
research and attorney handoff, not legal advice or compliance certification.

## Evidence and publication

Package-boundary tests and a local HTTP fixture check the bundled bridge
without Claude or a hosted API call. Official JSON schemas cover the portable
manifests and MCPB; these do not replace Claude portal validation, OpenAI scans,
installed-host workflows or directory acceptance. The bridge is byte-bound to
the published npm 0.1.1 artifact. No package installation step is hidden in the
Desktop bundle.

The official MCP Registry listing and public GitHub previews are independent
publication outcomes. They do not automatically list the integration in
Claude, OpenAI, Smithery or Glama. Press screenshots are historical previews;
refresh the press kit after the page redesign is final. The current integrations
do not declare an interactive MCP App, so do not manufacture an MCP App carousel
or treat the press refresh as an unconditional connector submission requirement.

Official references, checked 2026-10-16:

- https://claude.com/docs/plugins/build
- https://claude.com/docs/directory/publish
- https://claude.com/docs/plugins/pre-submission-checklist
- https://claude.com/docs/connectors/building/review-criteria
- https://claude.com/docs/connectors/building/submission
- https://claude.com/docs/plugins/submit
- https://developers.openai.com/plugins/build/plugins
- https://developers.openai.com/plugins/deploy/submission

The existing Magist mark is reproduced from the public website for Magist's
own listing. Package MIT licensing does not grant trademark rights or license
the hosted platform. The corpus's CC BY-SA license is separate.
