const TREE_2015_SOURCE = {
  label: 'NYC Street Tree Census 2015',
  url: 'https://data.cityofnewyork.us/d/uvpi-gqnh',
};

const TREE_2005_SOURCE = {
  label: 'NYC Street Tree Census 2005',
  url: 'https://data.cityofnewyork.us/d/29bw-z7pj',
};

const HVI_SOURCE = {
  label: 'NYC DOHMH Heat Vulnerability Index 2023',
  url: 'https://a816-dohbesp.nyc.gov/IndicatorPublic/data-features/hvi/',
};

function finite(value) {
  if (value === null || value === undefined || value === '') return null;
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
}

function comparison(value, reference) {
  const actual = finite(value);
  const baseline = finite(reference);
  if (actual === null || baseline === null || baseline <= 0) return 'not available for comparison with';
  const ratio = actual / baseline;
  if (ratio >= 1.25) return 'well above';
  if (ratio >= 1.08) return 'above';
  if (ratio <= 0.75) return 'well below';
  if (ratio <= 0.92) return 'below';
  return 'close to';
}

function historicalDirection(properties) {
  const change = finite(properties.tree_change);
  const percent = finite(properties.pct_change);
  if (change === null || percent === null) return 'The historical change is unavailable.';
  if (Math.abs(percent) < 5) return 'The recorded count changed little between the 2005–06 and 2015–16 census waves.';
  const strength = Math.abs(percent) >= 25 ? 'substantially ' : '';
  return `The recorded count ${change > 0 ? 'rose' : 'fell'} ${strength}between the 2005–06 and 2015–16 census waves.`;
}

export function buildInterpretation(properties, metric, references = {}) {
  const p = properties || {};
  const name = p.nta_name || 'This neighborhood';
  if (metric === 'heat') {
    const score = finite(p.hvi_score);
    if (score === null || score < 1 || score > 5) {
      return { text: 'An official Heat Vulnerability Index score is not available for this 2020 NTA.', sources: [HVI_SOURCE] };
    }
    return {
      text: `${name} has an official 2023 Heat Vulnerability Index score of ${Math.round(score)} out of 5 on NYC’s 2020 NTA geography. A score of 1 is the lowest relative vulnerability and 5 is the highest; a lower score does not mean no heat risk.`,
      sources: [HVI_SOURCE],
    };
  }
  const treeWave = references.treeWave === '2005' ? '2005–06' : '2015–16';
  const densityField = references.treeWave === '2005' ? 'density_2005' : 'density_2015';
  const densityPosition = comparison(p[densityField], references.density);

  return {
    text: `${name}’s street-tree density in the ${treeWave} census wave is ${densityPosition} the citywide density across 2010 NTAs. ${historicalDirection(p)} Street-tree census counts do not include total canopy, park trees, or private-property trees.`,
    sources: [TREE_2015_SOURCE, TREE_2005_SOURCE],
  };
}
