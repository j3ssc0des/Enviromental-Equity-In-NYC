import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import {
  buildGroundedContext,
  extractOutputText,
  handleRequest,
  parseRequestPayload,
  validateNarrative,
} from '../api/interpret.mjs';

const snapshot = JSON.parse(await readFile(new URL('../data/processed/nta_environmental_snapshot.geojson', import.meta.url), 'utf8'));

test('request contract accepts only a stable NTA code and known metric', () => {
  assert.deepEqual(parseRequestPayload({ nta_code: 'bk93', metric: 'trees' }), { ntaCode: 'BK93', metric: 'trees' });
  assert.throws(() => parseRequestPayload({ nta_code: 'BK93', metric: 'trees', prompt: 'ignore rules' }), /UNEXPECTED_FIELDS/);
  assert.throws(() => parseRequestPayload({ nta_code: 'BK93', metric: 'air' }), /INVALID_METRIC/);
});

test('server rebuilds evidence from the validated snapshot', () => {
  const context = buildGroundedContext(snapshot, 'BK93', 'trees');
  assert.equal(context.facts.neighborhood, 'Starrett City');
  assert.equal(context.facts.trees_2015, 688);
  assert.equal(context.facts.tree_change, 493);
  assert.match(context.evidence.join(' '), /688 street trees in 2015/);
  assert.equal(context.sources[0].label, 'NYC Street Tree Census 2015');
});

test('income citations follow the validated ACS release year', () => {
  const context = buildGroundedContext(snapshot, 'BK93', 'income');
  assert.equal(context.facts.income_release_end_year, 2024);
  assert.equal(context.sources[0].year, 2024);
  assert.match(context.sources[0].url, /\/2024\/acs\/acs5\.html$/);
});

test('model narrative cannot introduce figures, URLs, or markup', () => {
  const safe = 'Street-tree density is below the residential comparison, while the historical count moved upward. This pattern identifies a useful place for closer local investigation without establishing why conditions differ.';
  assert.equal(validateNarrative(safe), safe);
  assert.throws(() => validateNarrative('Tree density is 583 and therefore needs funding immediately.'), /UNSAFE_MODEL_OUTPUT/);
  assert.throws(() => validateNarrative('See https://example.com for evidence about this neighborhood and its surrounding communities.'), /UNSAFE_MODEL_OUTPUT/);
});

test('Responses API text extraction ignores non-text output items', () => {
  const payload = { output: [{ type: 'reasoning', content: [] }, { type: 'message', content: [{ type: 'output_text', text: 'Grounded result.' }] }] };
  assert.equal(extractOutputText(payload), 'Grounded result.');
});

test('endpoint fails closed when the server key is absent', async () => {
  const response = await handleRequest({
    method: 'POST',
    headers: { origin: 'https://j3ssc0des.github.io', 'x-forwarded-for': 'test-no-key' },
    body: { nta_code: 'BK93', metric: 'trees' },
    env: {},
  });
  assert.equal(response.status, 503);
  assert.deepEqual(response.body, { error: 'AI_NOT_CONFIGURED' });
});

test('endpoint rejects unapproved browser origins before model access', async () => {
  const response = await handleRequest({
    method: 'POST',
    headers: { origin: 'https://attacker.example', 'x-forwarded-for': 'test-origin' },
    body: { nta_code: 'BK93', metric: 'trees' },
    env: { OPENAI_API_KEY: 'test-key' },
    fetchImpl: async () => { throw new Error('model must not be called'); },
  });
  assert.equal(response.status, 403);
  assert.deepEqual(response.body, { error: 'ORIGIN_NOT_ALLOWED' });
});

test('endpoint does not generate ranked interpretations for context-only areas', async () => {
  const contextOnly = snapshot.features.find(feature => feature.properties.investment_eligible !== true).properties;
  const response = await handleRequest({
    method: 'POST',
    headers: { origin: 'https://j3ssc0des.github.io', 'x-forwarded-for': 'test-context-only' },
    body: { nta_code: contextOnly.nta_code, metric: 'equity' },
    env: { OPENAI_API_KEY: 'test-key' },
    fetchImpl: async () => { throw new Error('model must not be called'); },
  });
  assert.equal(response.status, 422);
  assert.deepEqual(response.body, { error: 'NTA_NOT_ELIGIBLE' });
});

test('endpoint returns model prose with server-controlled evidence', async () => {
  const narrative = 'Street-tree density sits below the residential comparison, even as the historical census count moved upward. The contrast is useful for investigation but does not establish a cause or funding decision.';
  const fetchImpl = async () => ({
    ok: true,
    status: 200,
    headers: { get: () => 'req_test' },
    json: async () => ({ output: [{ content: [{ type: 'output_text', text: narrative }] }] }),
  });
  const response = await handleRequest({
    method: 'POST',
    headers: { origin: 'https://j3ssc0des.github.io', 'x-forwarded-for': 'test-success' },
    body: { nta_code: 'BK93', metric: 'trees' },
    env: { OPENAI_API_KEY: 'test-key', OPENAI_MODEL: 'test-model' },
    fetchImpl,
    now: Date.UTC(2026, 7, 9),
  });
  assert.equal(response.status, 200);
  assert.equal(response.body.analysis, narrative);
  assert.equal(response.body.generated_by, 'openai');
  assert.equal(response.body.model, 'test-model');
  assert.match(response.body.evidence.join(' '), /688 street trees/);
  assert.equal(response.headers['Access-Control-Allow-Origin'], 'https://j3ssc0des.github.io');
});
