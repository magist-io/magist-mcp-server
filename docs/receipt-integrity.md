# Offline receipt-v9 content integrity

Check a saved receipt's body hash without a network call or a requirement-engine run:

```sh
node tools/receipt-integrity-v9.mjs /absolute/path/to/receipt.json
```

Requires Node.js 18 or newer and no dependencies. This source utility is separate from the npm stdio bridge and the Claude/OpenAI plugin packages. It is not an additional MCP tool.

## Result

- Exit 0: the bounded v9 structural profile is present and the body hash matches.
- Exit 1: the recorded body hash does not match.
- Exit 2: unsupported format, malformed JSON, input larger than 1 MiB, or an I/O error.

The JSON output names the check `receipt-v9-content-integrity-only`. It does not certify every schema constraint or every historical wire version. An unsupported version is outside this utility's scope, not proof that the project's verifier rejects it.

The tool sorts object keys recursively, preserves array order, encodes the canonical JSON as UTF-8 and computes SHA-256. It excludes only these top-level fields:

```text
generatedAt hash assessments scenarioRefinement signature timestamp
provenanceSeal dismissalProvenance expectedRegulationIds inferredFacts
statedFacts pasteAnchor gates
```

Every other present field remains covered, including the `corpus` counts and any extra field. It does not repair or normalize the received body's arrays to make a hash pass.

## What passing means

A matching unkeyed hash establishes internal consistency. Anyone who edits a body can also recompute its hash. Passing therefore does not authenticate a sender, verify a signature or timestamp, rerun the engine, compare live editions or establish legal accuracy.

The separate [hosted verification surface](https://magist.io/verify) can perform its supported replay checks. This offline utility does not invoke it. Creating or sharing a public report has its own data effects; this utility only reads the local file and writes its result to stdout.

## Tests and package boundaries

```sh
node tests/receipt-integrity-v9.test.mjs
```

All test data is newly authored, explicitly synthetic unit-fixture data. Its invented IDs, editions and outputs are not an engine result and are never submitted to a service. The known test hash was independently derived for that restricted fixture using Python's JSON serializer and SHA-256. Tests cover changed inputs/outputs/versions/counts, intentional exclusions, ordering, failure exits and a rehashed forgery that remains unauthenticated.

The helper and tests carry this repository's existing MIT notice. They contain no captured production receipt or private engine implementation. This does not relicense corpus content, source material, trademarks or the hosted service.
