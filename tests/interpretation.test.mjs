import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import { buildInterpretation } from '../assets/interpretation.mjs';

const snapshot = JSON.parse(await readFile(new URL('../data/processed/nta_environmental_snapshot.geojson', import.meta.url), 'utf8'));
const heatSnapshot = JSON.parse(await readFile(new URL('../data/processed/nta2020_heat_vulnerability.geojson', import.meta.url), 'utf8'));
const rows = snapshot.features.map(feature => feature.properties);
const heatRows = heatSnapshot.features.map(feature => feature.properties);
const standardRows = rows.filter(row => !/(98|99)$/.test(String(row.nta_code || '')));
const references = {
  density: standardRows.reduce((sum, row) => sum + row.trees_2015, 0)
    / standardRows.reduce((sum, row) => sum + row.area_km2, 0),
};

test('tree interpretation compares conditions, describes history, and states scope', () => {
  const row = rows.find(item => item.nta_code === 'BK93');
  const result = buildInterpretation(row, 'trees', references);
  assert.match(result.text, /Starrett City’s street-tree density in the 2015–16 census wave is/);
  assert.match(result.text, /between the 2005–06 and 2015–16 census waves/);
  assert.match(result.text, /do not include total canopy/);
  assert.deepEqual(result.sources.map(source => source.label), [
    'NYC Street Tree Census 2015',
    'NYC Street Tree Census 2005',
  ]);
});

test('tree interpretation follows the selected historical census wave', () => {
  const row = rows.find(item => item.nta_code === 'BK93');
  const historicalReferences = { ...references, treeWave: '2005', density: rows.reduce((sum, item) => sum + item.density_2005 * item.area_km2, 0) / rows.reduce((sum, item) => sum + item.area_km2, 0) };
  const result = buildInterpretation(row, 'trees', historicalReferences);
  assert.match(result.text, /2005–06 census wave/);
});

test('official HVI records retain their published geography and bounded scores', () => {
  assert.equal(heatRows.length, 197);
  assert.equal(new Set(heatRows.map(row => row.nta_code)).size, 197);
  for (const row of heatRows) {
    assert.equal(row.dataset_geography, 'NTA2020');
    assert.equal(row.geography_vintage, 2020);
    assert.equal(row.hvi_source_year, 2023);
    assert.ok(Number.isInteger(row.hvi_score) && row.hvi_score >= 1 && row.hvi_score <= 5);
    const result = buildInterpretation(row, 'heat');
    assert.match(result.text, /official 2023 Heat Vulnerability Index score/);
    assert.match(result.text, /2020 NTA geography/);
    assert.match(result.text, /does not mean no heat risk/);
    assert.equal(result.sources[0].label, 'NYC DOHMH Heat Vulnerability Index 2023');
  }
});

test('every published neighborhood and metric produces safe, bounded prose', () => {
  for (const row of rows) {
    for (const metric of ['trees']) {
      const result = buildInterpretation(row, metric, references);
      assert.ok(result.text.length >= 70 && result.text.length <= 520, `${row.nta_code}:${metric} has unexpected length`);
      assert.doesNotMatch(result.text, /should receive|caused by|safe limit|hazardous/i);
      assert.ok(result.sources.every(source => source.url.startsWith('https://')));
    }
  }
});
