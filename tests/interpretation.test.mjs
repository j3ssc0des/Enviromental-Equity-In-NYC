import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import { buildInterpretation } from '../assets/interpretation.mjs';

const snapshot = JSON.parse(await readFile(new URL('../data/processed/nta_environmental_snapshot.geojson', import.meta.url), 'utf8'));
const rows = snapshot.features.map(feature => feature.properties);
const eligible = rows.filter(row => row.investment_eligible === true);
const median = values => {
  const sorted = values.slice().sort((a, b) => a - b);
  const middle = Math.floor(sorted.length / 2);
  return sorted.length % 2 ? sorted[middle] : (sorted[middle - 1] + sorted[middle]) / 2;
};
const references = {
  density: eligible.reduce((sum, row) => sum + row.trees_2015, 0)
    / eligible.reduce((sum, row) => sum + row.area_km2, 0),
  income: median(eligible.map(row => row.median_income)),
};

test('tree interpretation compares conditions, describes history, and states scope', () => {
  const row = eligible.find(item => item.nta_code === 'BK93');
  const result = buildInterpretation(row, 'trees', references);
  assert.match(result.text, /Starrett City’s street-tree density is/);
  assert.match(result.text, /between 2005 and 2015/);
  assert.match(result.text, /do not include total canopy/);
  assert.deepEqual(result.sources.map(source => source.label), [
    'NYC Street Tree Census 2015',
    'NYC Street Tree Census 2005',
  ]);
});

test('income interpretation distinguishes context from explanation', () => {
  const row = eligible.find(item => item.nta_code === 'BK93');
  const result = buildInterpretation(row, 'income', references);
  assert.match(result.text, /eligible-area median/);
  assert.match(result.text, /does not explain why environmental conditions differ/);
  assert.match(result.text, /ACS approximation/);
  assert.match(result.sources[0].url, new RegExp(`/${row.income_source_year}/acs/acs5\\.html$`));
});

test('missing numeric values are not silently treated as zero', () => {
  const row = { ...eligible[0], median_income: null };
  const result = buildInterpretation(row, 'income', references);
  assert.match(result.text, /estimate is not available/);
  assert.doesNotMatch(result.text, /below the eligible-area median/);
});

test('score interpretations expose their components and guardrails', () => {
  const row = eligible.find(item => item.nta_code === 'BK93');
  const score = buildInterpretation(row, 'equity', references).text;
  assert.match(score, /combines tree density/);
  assert.match(score, /not to make a funding decision/);
});

test('context-only areas never receive a screening conclusion', () => {
  const row = rows.find(item => item.investment_eligible !== true);
  for (const metric of ['trees', 'income', 'equity']) {
    const result = buildInterpretation(row, metric, references);
    assert.match(result.text, /shown for (geographic )?context/);
    assert.match(result.text, /excluded/);
    assert.equal(result.sources.length, 0);
  }
});

test('every published neighborhood and metric produces safe, bounded prose', () => {
  for (const row of rows) {
    for (const metric of ['trees', 'income', 'equity']) {
      const result = buildInterpretation(row, metric, references);
      assert.ok(result.text.length >= 70 && result.text.length <= 520, `${row.nta_code}:${metric} has unexpected length`);
      assert.doesNotMatch(result.text, /should receive|caused by|safe limit|hazardous/i);
      assert.ok(result.sources.every(source => source.url.startsWith('https://')));
    }
  }
});
