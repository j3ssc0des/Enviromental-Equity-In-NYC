const TREE_2015_SOURCE = {
  label: 'NYC Street Tree Census 2015',
  url: 'https://data.cityofnewyork.us/d/uvpi-gqnh',
};

const TREE_2005_SOURCE = {
  label: 'NYC Street Tree Census 2005',
  url: 'https://data.cityofnewyork.us/d/29bw-z7pj',
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

function scorePosition(value) {
  const score = finite(value);
  if (score === null) return 'unavailable';
  if (score >= 0.75) return 'higher';
  if (score >= 0.55) return 'elevated';
  if (score >= 0.35) return 'middle';
  return 'lower';
}

function incomeSource(properties) {
  const year = finite(properties.income_source_year);
  return {
    label: year === null ? 'ACS household income' : `ACS ${Math.round(year)} household income`,
    url: year === null
      ? 'https://www.census.gov/programs-surveys/acs'
      : `https://api.census.gov/data/${Math.round(year)}/acs/acs5.html`,
  };
}

function contextOnlyInterpretation(properties) {
  const name = properties.nta_name || 'This area';
  if (properties.area_context === 'Insufficient income coverage') {
    return `${name} is shown for context but excluded from comparisons because income coverage is below the project’s quality threshold. No screening conclusion is generated.`;
  }
  return `${name} is a non-residential planning area shown for geographic context. It is excluded from community comparisons so land-intensive places do not displace residential neighborhoods.`;
}

export function buildInterpretation(properties, metric, references = {}) {
  const p = properties || {};
  const name = p.nta_name || 'This neighborhood';
  if (p.investment_eligible !== true) {
    return { text: contextOnlyInterpretation(p), sources: [] };
  }

  const treeWave = references.treeWave === '2005' ? '2005–06' : '2015–16';
  const densityField = references.treeWave === '2005' ? 'density_2005' : 'density_2015';
  const densityPosition = comparison(p[densityField], references.density);
  const incomePosition = comparison(p.median_income, references.income);

  if (metric === 'income') {
    if (finite(p.median_income) === null) {
      return { text: 'A sufficiently covered household-income estimate is not available for this area.', sources: [incomeSource(p)] };
    }
    return {
      text: `${name}’s estimated median household income is ${incomePosition} the eligible-area median. This adds socioeconomic context to the tree patterns but does not explain why environmental conditions differ; the value is a household-weighted ACS approximation.`,
      sources: [incomeSource(p)],
    };
  }

  if (metric === 'equity') {
    return {
      text: `The project screening score places ${name} toward the ${scorePosition(p.underserved)} end of eligible areas. It combines tree density that is ${densityPosition} the ranked-area average with estimated income that is ${incomePosition} the eligible-area median; use it to identify questions, not to make a funding decision.`,
      sources: [TREE_2015_SOURCE, incomeSource(p)],
    };
  }

  return {
    text: `${name}’s street-tree density in the ${treeWave} census wave is ${densityPosition} the ranked-area average. ${historicalDirection(p)} Street-tree census counts do not include total canopy, park trees, or private-property trees.`,
    sources: [TREE_2015_SOURCE, TREE_2005_SOURCE],
  };
}
