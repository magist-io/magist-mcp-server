import assert from 'node:assert/strict';
import { readFileSync, mkdtempSync, writeFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { checkReceipt, canonicalReceiptBytes } from '../tools/receipt-integrity-v9.mjs';

const here = dirname(fileURLToPath(import.meta.url));
const receipt = JSON.parse(readFileSync(join(here, 'fixtures/receipt-v9-synthetic.json'), 'utf8'));
const rows = [];
function run(name, action) { action(); rows.push({ name, outcome: 'PASS' }); }
function changed(action) { const copy = structuredClone(receipt); action(copy); return copy; }

run('authored-synthetic-fixture-known-independent-hash-and-bytes', () => {
  const got = checkReceipt(receipt);
  assert.equal(got.hashIntegrityValid, true);
  assert.equal(got.recomputedHash, 'd52e673d841355da615c18bb992c7065449a903278adffbea872ef405eb473bd');
  assert.equal(got.canonicalBytes, 664);
});
run('semantic-feature-tamper-detected', () => {
  assert.equal(checkReceipt(changed(r => r.inputs.features.push('synthetic-additional-feature'))).hashIntegrityValid, false);
});
run('output-count-tamper-detected', () => {
  assert.equal(checkReceipt(changed(r => r.outputs.controlCount++)).hashIntegrityValid, false);
});
run('corpus-version-tamper-detected', () => {
  assert.equal(checkReceipt(changed(r => r.corpusVersion = '0'.repeat(64))).hashIntegrityValid, false);
});
run('corpus-count-is-covered-by-hash', () => {
  assert.equal(checkReceipt(changed(r => r.corpus.regulationCount++)).hashIntegrityValid, false);
});
run('excluded-generated-time-and-gates-do-not-change-hash', () => {
  assert.equal(checkReceipt(changed(r => {
    r.generatedAt = '2030-01-01T00:00:00Z'; r.gates.embargo = !r.gates.embargo;
  })).hashIntegrityValid, true);
});
run('object-key-order-does-not-change-hash', () => {
  const reordered = Object.fromEntries(Object.entries(receipt).reverse());
  reordered.inputs = Object.fromEntries(Object.entries(reordered.inputs).reverse());
  assert.equal(checkReceipt(reordered).hashIntegrityValid, true);
});
run('scope-array-order-is-preserved-not-silently-normalized', () => {
  assert.equal(checkReceipt(changed(r => r.scope.controlsInScope.reverse())).hashIntegrityValid, false);
});
run('recomputed-hash-on-forged-copy-does-not-authenticate-or-replay', () => {
  const forged = changed(r => r.inputs.features.push('synthetic-additional-feature'));
  forged.hash = createHash('sha256').update(canonicalReceiptBytes(forged)).digest('hex');
  const got = checkReceipt(forged);
  assert.equal(got.hashIntegrityValid, true);
  assert.equal(got.originAuthenticated, false);
  assert.equal(got.engineReplayed, false);
});
run('unsupported-wire-version-is-not-certified', () => {
  assert.throws(() => checkReceipt(changed(r => r.receiptVersion = 6)), /Only receiptVersion 9/);
});
const scratch = mkdtempSync(join(tmpdir(), 'magist-receipt-unit-'));
try {
  run('CLI-mismatch-exits-one-with-explicit-false', () => {
    const p = join(scratch, 'MUTATED-TEST-FIXTURE-NOT-GENUINE.json');
    writeFileSync(p, JSON.stringify(changed(r => r.inputs.features.push('synthetic-additional-feature'))));
    const got = spawnSync(process.execPath, [join(here, '../tools/receipt-integrity-v9.mjs'), p], { encoding: 'utf8' });
    assert.equal(got.status, 1);
    assert.equal(JSON.parse(got.stdout).hashIntegrityValid, false);
  });
  run('CLI-malformed-json-exits-two', () => {
    const p = join(scratch, 'MALFORMED-TEST-FIXTURE.json');
    writeFileSync(p, '{not json');
    const got = spawnSync(process.execPath, [join(here, '../tools/receipt-integrity-v9.mjs'), p], { encoding: 'utf8' });
    assert.equal(got.status, 2);
    assert.equal(JSON.parse(got.stderr).scope, 'receipt-v9-content-integrity-only');
  });
} finally { rmSync(scratch, { recursive: true }); }
process.stdout.write(JSON.stringify({
  scope: 'authored-synthetic-unit-fixture-only-no-live-engine',
  node: process.version, tests: rows.length, pass: rows.length, fail: 0,
  rows, privateMagistEngineExecuted: false, networkCalls: 0, engineReplayed: false,
}, null, 2) + '\n');
