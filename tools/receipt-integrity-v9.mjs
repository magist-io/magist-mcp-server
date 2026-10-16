#!/usr/bin/env node
/**
 * Offline receipt-v9 content-integrity check. No engine or project imports.
 * Recursively sorted JSON keys, preserved arrays, explicit v9 exclusions.
 * This does not authenticate a sender or rerun the engine.
 */
import { readFileSync, statSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { pathToFileURL } from 'node:url';

export const EXCLUDED_FIELDS = new Set([
  'generatedAt', 'hash', 'assessments', 'scenarioRefinement', 'signature',
  'timestamp', 'provenanceSeal', 'dismissalProvenance', 'expectedRegulationIds',
  'inferredFacts', 'statedFacts', 'pasteAnchor', 'gates',
]);

function object(value) {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}

export function canonicalJson(value) {
  if (value === null || typeof value !== 'object') {
    const text = JSON.stringify(value);
    if (text === undefined) throw new TypeError('Non-JSON value');
    return text;
  }
  if (Array.isArray(value)) return '[' + value.map(canonicalJson).join(',') + ']';
  return '{' + Object.keys(value).sort().map(
    key => JSON.stringify(key) + ':' + canonicalJson(value[key])
  ).join(',') + '}';
}

export function canonicalReceiptBytes(receipt) {
  if (!object(receipt)) throw new TypeError('Receipt must be an object');
  const body = Object.fromEntries(Object.entries(receipt).filter(
    ([key]) => !EXCLUDED_FIELDS.has(key)
  ));
  return Buffer.from(canonicalJson(body), 'utf8');
}

export function checkReceipt(receipt) {
  if (!object(receipt) || receipt.receiptVersion !== 9) {
    throw new TypeError('Only receiptVersion 9 is covered by this checker');
  }
  if (!/^[a-f0-9]{64}$/.test(receipt.hash ?? '') ||
      !/^[a-f0-9]{64}$/.test(receipt.corpusVersion ?? '') ||
      typeof receipt.engineVersion !== 'string' || !receipt.engineVersion ||
      !Number.isInteger(receipt.scoringVersion) ||
      !object(receipt.inputs) || !object(receipt.scope) || !object(receipt.outputs) ||
      !['regulationsInScope', 'controlsInScope'].every(
        key => Array.isArray(receipt.scope[key]) &&
          receipt.scope[key].every(value => typeof value === 'string')
      )) {
    throw new TypeError('Receipt lacks the bounded v9 structural profile');
  }
  const bytes = canonicalReceiptBytes(receipt);
  const recomputedHash = createHash('sha256').update(bytes).digest('hex');
  return {
    scope: 'receipt-v9-content-integrity-only',
    hashIntegrityValid: recomputedHash === receipt.hash,
    claimedHash: receipt.hash,
    recomputedHash,
    canonicalBytes: bytes.length,
    coveredFields: Object.keys(receipt).filter(key => !EXCLUDED_FIELDS.has(key)).sort(),
    excludedPresentFields: Object.keys(receipt).filter(key => EXCLUDED_FIELDS.has(key)).sort(),
    receiptVersion: receipt.receiptVersion,
    engineVersionClaimed: receipt.engineVersion,
    corpusVersionClaimed: receipt.corpusVersion,
    signatureBlockPresent: object(receipt.signature),
    originAuthenticated: false,
    engineReplayed: false,
    liveVersionsChecked: false,
    legalAccuracyVerified: false,
    warning: 'An unkeyed hash is self-consistency evidence; a changed body with a recomputed hash can also pass.',
  };
}

function main(args) {
  if (args.length !== 1) throw new TypeError('Usage: node receipt-integrity-v9.mjs RECEIPT.json');
  const size = statSync(args[0]).size;
  if (size > 1024 * 1024) throw new RangeError('Receipt exceeds 1 MiB limit');
  const result = checkReceipt(JSON.parse(readFileSync(args[0], 'utf8')));
  process.stdout.write(JSON.stringify(result, null, 2) + '\n');
  process.exitCode = result.hashIntegrityValid ? 0 : 1;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  try { main(process.argv.slice(2)); }
  catch (error) {
    process.stderr.write(JSON.stringify({ scope: 'receipt-v9-content-integrity-only', error: error.message }) + '\n');
    process.exitCode = 2;
  }
}
