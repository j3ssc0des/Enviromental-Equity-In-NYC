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

const FVI_SOURCE = {
  label: 'NYC Flood Vulnerability Index',
  url: 'https://data.cityofnewyork.us/d/mrjc-v9pm',
};

function finite(value) {
  if (value === null || value === undefined || value === '') return null;
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
}

function median(values) {
  const sorted = values.map(finite).filter(value => value !== null).sort((a, b) => a - b);
  if (!sorted.length) return null;
  const middle = Math.floor(sorted.length / 2);
  return sorted.length % 2 ? sorted[middle] : (sorted[middle - 1] + sorted[middle]) / 2;
}

function percentile(value, values) {
  const actual = finite(value);
  const valid = values.map(finite).filter(item => item !== null).sort((a, b) => a - b);
  if (actual === null || !valid.length) return null;
  const below = valid.filter(item => item < actual).length;
  const equal = valid.filter(item => item === actual).length;
  return Math.max(1, Math.min(99, Math.round(100 * (below + 0.5 * equal) / valid.length)));
}

function relativePhrase(value, reference) {
  const actual = finite(value);
  const baseline = finite(reference);
  if (actual === null || baseline === null) return 'not available';
  const tolerance = Math.max(Math.abs(baseline) * 0.03, 0.1);
  if (actual > baseline + tolerance) return 'above';
  if (actual < baseline - tolerance) return 'below';
  return 'close to';
}

function formatNumber(value, digits = 0) {
  const number = finite(value);
  return number === null ? 'not available' : number.toLocaleString(undefined, {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

function treeInterpretation(p, references) {
  const name = p.nta_name || 'This area';
  const code = String(p.nta_code || '');
  const treeWave = references.treeWave === '2005' ? '2005–06' : '2015–16';
  const densityField = references.treeWave === '2005' ? 'density_2005' : 'density_2015';
  const treeField = references.treeWave === '2005' ? 'trees_2005' : 'trees_2015';
  const density = finite(p[densityField]);

  if (/(98|99)$/.test(code)) {
    return {
      text: `${name} is an official special-purpose 2010 NTA, not a standard residential-neighborhood comparison area. Its ${treeWave} Street Tree Census record remains visible, but it is excluded from neighborhood rankings because street-tree counts do not measure all trees or shade in parks, cemeteries, airports, or institutional areas.`,
      sources: [TREE_2015_SOURCE, TREE_2005_SOURCE],
    };
  }

  const rows = Array.isArray(references.rows) ? references.rows : [];
  const comparable = rows.filter(row => !/(98|99)$/.test(String(row.nta_code || '')));
  const cityPercentile = percentile(density, comparable.map(row => row[densityField]));
  const boroughRows = comparable.filter(row => (row.boro_name || row.borough) === (p.boro_name || p.borough));
  const boroughTrees = boroughRows.reduce((sum, row) => sum + (finite(row[treeField]) || 0), 0);
  const boroughArea = boroughRows.reduce((sum, row) => sum + (finite(row.area_km2) || 0), 0);
  const boroughDensity = boroughArea > 0 ? boroughTrees / boroughArea : null;
  const change = finite(p.tree_change);
  const percentChange = finite(p.pct_change);
  const trend = change === null || percentChange === null
    ? 'Historical change is unavailable.'
    : `The recorded count ${change >= 0 ? 'rose' : 'fell'} by ${formatNumber(Math.abs(change))} trees (${formatNumber(Math.abs(percentChange), 1)}%) between the 2005–06 and 2015–16 census waves.`;
  const rankText = cityPercentile === null
    ? 'A citywide percentile is unavailable.'
    : `That is higher than about ${cityPercentile}% of standard neighborhood NTAs`;

  return {
    text: `${name} recorded ${formatNumber(density)} street trees per km² in the ${treeWave} census wave. ${rankText} and is ${relativePhrase(density, boroughDensity)} its borough’s area-weighted density of ${formatNumber(boroughDensity)}. ${trend} These census counts exclude total canopy, park trees, and private-property trees, so they do not establish total shade or explain why the pattern exists.`,
    sources: [TREE_2015_SOURCE, TREE_2005_SOURCE],
  };
}

function heatInterpretation(p, references) {
  const name = p.nta_name || 'This area';
  const score = finite(p.hvi_score);
  if (score === null || score < 1 || score > 5) {
    return { text: 'An official Heat Vulnerability Index score is not available for this 2020 NTA.', sources: [HVI_SOURCE] };
  }
  const rows = Array.isArray(references.heatRows) ? references.heatRows : [];
  const sameScore = rows.filter(row => finite(row.hvi_score) === score).length;
  const surfaceMedian = median(rows.map(row => row.surface_temp_f));
  const greenMedian = median(rows.map(row => row.greenspace_pct));
  const acMedian = median(rows.map(row => row.households_ac_pct));
  const components = [
    `surface temperature is ${relativePhrase(p.surface_temp_f, surfaceMedian)} the HVI-area median (${formatNumber(p.surface_temp_f, 1)}°F vs ${formatNumber(surfaceMedian, 1)}°F)`,
    `green space is ${relativePhrase(p.greenspace_pct, greenMedian)} the median (${formatNumber(p.greenspace_pct, 1)}% vs ${formatNumber(greenMedian, 1)}%)`,
    `households with AC are ${relativePhrase(p.households_ac_pct, acMedian)} the median (${formatNumber(p.households_ac_pct, 1)}% vs ${formatNumber(acMedian, 1)}%)`,
  ];
  const distribution = sameScore ? `; ${sameScore} of ${rows.length} covered NTAs share that score` : '';

  return {
    text: `${name} has an official 2023 Heat Vulnerability Index score of ${Math.round(score)} out of 5${distribution}. Among the same official HVI records, its published ${components.join(', and ')}. These are descriptive comparisons on 2020 NTA geography: a lower score does not mean no heat risk, and the data do not predict an individual health outcome or establish causation.`,
    sources: [HVI_SOURCE],
  };
}

function floodInterpretation(p, references) {
  const name = p.tract_name || `Census tract ${p.geoid || ''}`;
  const present = finite(p.ss_cur);
  const fshri = finite(p.fshri);
  const rows = Array.isArray(references.floodRows) ? references.floodRows : [];
  if (present === null) {
    return {
      text: `${name} has no published present storm-surge FVI score in NYC’s dataset. That is missing scenario coverage, not a score of zero and not evidence that the tract has no flood risk. Its published Flood Susceptibility to Harm and Recovery Index is ${formatNumber(fshri)} out of 5.`,
      sources: [FVI_SOURCE],
    };
  }
  const covered = rows.filter(row => finite(row.ss_cur) !== null);
  const sameScore = covered.filter(row => finite(row.ss_cur) === present).length;
  return {
    text: `${name} has an official present storm-surge Flood Vulnerability Index score of ${formatNumber(present)} out of 5; ${sameScore} of ${covered.length} tracts with a published present-scenario score share that rank. Its Flood Susceptibility to Harm and Recovery Index is ${formatNumber(fshri)} out of 5. These are relative tract-level indices, not a property-level flood forecast, insurance determination, or guarantee of safety.`,
    sources: [FVI_SOURCE],
  };
}

export function buildInterpretation(properties, metric, references = {}) {
  const p = properties || {};
  if (metric === 'heat') return heatInterpretation(p, references);
  if (metric === 'flood') return floodInterpretation(p, references);
  return treeInterpretation(p, references);
}
