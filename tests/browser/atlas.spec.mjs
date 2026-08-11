import { expect, test } from '@playwright/test';
import { readFile } from 'node:fs/promises';

async function waitForAtlas(page) {
  await page.goto('/');
  await expect(page.locator('#data-status')).toContainText('VALIDATED');
  await page.waitForFunction(() => document.documentElement.dataset.treeReady === 'true' &&
    document.documentElement.dataset.heatReady === 'true' && document.documentElement.dataset.floodReady === 'true');
  const mapFrame = page.frameLocator('#map-frame');
  await expect(mapFrame.locator('.leaflet-container')).toBeVisible();
  await page.waitForFunction(() => {
    const frame = document.querySelector('#map-frame');
    return Boolean(frame && frame.contentWindow && frame.contentWindow.__dbInjected &&
      frame.contentWindow.__layerMap && frame.contentWindow.__layerMap['Tree Density (2015)']);
  });
}

async function selectTreeNeighborhood(page, name = 'Starrett City') {
  await page.locator('#nta-search').fill(name);
  await page.locator('#nta-search').press('Enter');
  await expect(page.locator('#nta-name')).toHaveText(name);
  await expect(page.locator('#nta-data')).toHaveClass(/visible/);
}

test('metric switch preserves location and synchronizes the heat legend', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name.startsWith('mobile'), 'covered by desktop interaction test');
  await waitForAtlas(page);
  await selectTreeNeighborhood(page);
  const originalTreeName = await page.locator('#nta-name').textContent();

  await page.locator('.mtab[data-tab="heat"]').click();
  await expect(page).toHaveURL(/#heat=/);
  await expect(page.locator('#tp-heat-score')).not.toHaveText('—');
  await expect(page.locator('#nta-boro')).not.toHaveText('');

  const mapFrame = page.frameLocator('#map-frame');
  await expect(mapFrame.locator('#leg-heat')).toBeVisible();
  await expect(mapFrame.locator('#leg-density')).toBeHidden();
  const layers = await page.locator('#map-frame').evaluate(frame => {
    const win = frame.contentWindow;
    const map = Object.values(win).find(value => value && typeof value === 'object' && value.getZoom && value.hasLayer);
    return Object.fromEntries(Object.entries(win.__layerMap).map(([name, layer]) => [name, map.hasLayer(layer)]));
  });
  expect(layers['Heat Vulnerability Index (2023)']).toBe(true);
  expect(layers['Tree Density (2015)']).toBe(false);
  expect(layers['Tree Change 2005→2015']).toBe(false);

  await page.locator('.mtab[data-tab="trees"]').click();
  await expect(page).toHaveURL(/#nta=/);
  await expect(page.locator('#nta-name')).toHaveText(originalTreeName || '');
  await expect(mapFrame.locator('#leg-density')).toBeVisible();
});

test('map feature clicks open an official neighborhood record', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name.startsWith('mobile'), 'covered by desktop interaction test');
  await waitForAtlas(page);
  const point = await page.locator('#map-frame').evaluate(frame => {
    const win = frame.contentWindow;
    const layer = win.__layerMap['Tree Density (2015)'];
    const map = Object.values(win).find(value => value && typeof value === 'object' && value.getZoom && value.latLngToContainerPoint);
    let result = null;
    const visit = feature => {
      if (result) return;
      if (feature.feature && feature.getBounds) {
        const containerPoint = map.latLngToContainerPoint(feature.getBounds().getCenter());
        result = { x:containerPoint.x, y:containerPoint.y };
        return;
      }
      if (feature.eachLayer) feature.eachLayer(visit);
    };
    visit(layer);
    return result;
  });
  const mapBox = await page.frameLocator('#map-frame').locator('.leaflet-container').boundingBox();
  expect(point).toBeTruthy();
  expect(mapBox).toBeTruthy();
  await page.mouse.click(mapBox.x + point.x, mapBox.y + point.y);
  await expect(page.locator('#nta-data')).toHaveClass(/visible/);
  await expect(page.locator('#nta-name')).not.toHaveText('');
  await expect(page).toHaveURL(/#nta=/);
  const clickedTreeName = await page.locator('#nta-name').textContent();
  await page.locator('.mtab[data-tab="heat"]').click();
  await expect(page).toHaveURL(/#heat=/);
  await page.locator('.mtab[data-tab="trees"]').click();
  await expect(page).toHaveURL(/#nta=/);
  await expect(page.locator('#nta-name')).toHaveText(clickedTreeName || '');
});

test('repeated searches and metric switches do not reuse a stale location', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name.startsWith('mobile'), 'covered by desktop interaction test');
  await waitForAtlas(page);
  for (const treeName of ['Upper East Side-Carnegie Hill', 'Flushing', 'North Riverdale-Fieldston-Riverdale']) {
    await selectTreeNeighborhood(page, treeName);
    await page.locator('.mtab[data-tab="heat"]').click();
    await expect(page).toHaveURL(/#heat=/);
    await expect(page.locator('#tp-heat-score')).not.toHaveText('—');
    await page.locator('.mtab[data-tab="trees"]').click();
    await expect(page).toHaveURL(/#nta=/);
    await expect(page.locator('#nta-name')).toHaveText(treeName);
  }
});

test('predictive neighborhood search replaces the current value without manual clearing', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name.startsWith('mobile'), 'covered by desktop interaction test');
  await waitForAtlas(page);
  await selectTreeNeighborhood(page);
  const viewBeforeSearch = await page.locator('#map-frame').evaluate(frame => {
    const map = Object.values(frame.contentWindow).find(value => value && typeof value === 'object' && value.getZoom && value.getCenter);
    const center = map.getCenter();
    return { zoom:map.getZoom(), lat:center.lat, lng:center.lng };
  });
  const search = page.locator('#nta-search');
  await search.click();
  await page.keyboard.type('Upper East');
  await expect(search).toHaveValue('Upper East');
  const suggestions = page.locator('#nta-options .nta-option');
  await expect(suggestions.first()).toContainText('Upper East Side-Carnegie Hill');
  await suggestions.first().click();
  await expect(page.locator('#nta-name')).toHaveText('Upper East Side-Carnegie Hill');
  await expect(search).toHaveValue('Upper East Side-Carnegie Hill');
  const mapFrame = page.frameLocator('#map-frame');
  const selectedPath = mapFrame.locator('path.atlas-selected').first();
  await expect(selectedPath).toBeVisible();
  await expect(mapFrame.locator('.atlas-selected-label')).toHaveCount(0);
  const selectedColors = await selectedPath.evaluate(path => {
    const style = getComputedStyle(path);
    return { stroke:style.stroke, fill:style.fill };
  });
  expect(selectedColors.stroke).toBe('rgb(77, 216, 255)');
  expect(selectedColors.fill).not.toBe('rgb(77, 216, 255)');
  const viewAfterSearch = await page.locator('#map-frame').evaluate(frame => {
    const map = Object.values(frame.contentWindow).find(value => value && typeof value === 'object' && value.getZoom && value.getCenter);
    const center = map.getCenter();
    return { zoom:map.getZoom(), lat:center.lat, lng:center.lng };
  });
  expect(viewAfterSearch).toEqual(viewBeforeSearch);
});

test('clicking empty map space clears the selected neighborhood', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name.startsWith('mobile'), 'covered by desktop interaction test');
  await waitForAtlas(page);
  await selectTreeNeighborhood(page, 'Upper East Side-Carnegie Hill');
  const mapFrame = page.frameLocator('#map-frame');
  await expect(mapFrame.locator('path.atlas-selected').first()).toBeVisible();

  await page.locator('#map-frame').evaluate(frame => {
    const map = Object.values(frame.contentWindow).find(value =>
      value && typeof value === 'object' && value.fire && value.getContainer && value.getCenter
    );
    map.fire('click', {
      latlng:map.getCenter(),
      originalEvent:{ target:map.getContainer() },
    });
  });

  await expect(page.locator('#nta-data')).not.toHaveClass(/visible/);
  await expect(page.locator('#placeholder')).toBeVisible();
  await expect(page.locator('#nta-search')).toHaveValue('');
  await expect(mapFrame.locator('path.atlas-selected')).toHaveCount(0);
  await expect(page).not.toHaveURL(/#(?:nta|heat)=/);
});

test('reloading a selected neighborhood preserves the default map view', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name.startsWith('mobile'), 'covered by desktop interaction test');
  await waitForAtlas(page);
  const readView = () => page.locator('#map-frame').evaluate(frame => {
    const map = Object.values(frame.contentWindow).find(value =>
      value && typeof value === 'object' && value.getZoom && value.getCenter
    );
    const center = map.getCenter();
    return { zoom:map.getZoom(), lat:center.lat, lng:center.lng };
  });
  const defaultView = await readView();

  await selectTreeNeighborhood(page, 'Upper East Side-Carnegie Hill');
  await expect(page).toHaveURL(/#nta=MN40$/);
  await page.reload();
  await expect(page.locator('#data-status')).toContainText('VALIDATED');
  await page.waitForFunction(() => document.documentElement.dataset.treeReady === 'true');
  await expect(page.locator('#nta-data')).toHaveClass(/visible/);
  await expect(page.locator('#nta-name')).toHaveText('Upper East Side-Carnegie Hill');
  await page.waitForTimeout(900);

  expect(await readView()).toEqual(defaultView);
});

test('combined report contains separate tree and heat records', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name.startsWith('mobile'), 'covered by desktop interaction test');
  await waitForAtlas(page);
  await selectTreeNeighborhood(page);
  const downloadPromise = page.waitForEvent('download');
  await page.locator('#download-report').click();
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toMatch(/combined-environmental-report\.txt$/);
  const path = await download.path();
  const report = await readFile(path, 'utf8');
  expect(report).toContain('SECTION 1 - STREET TREES (NATIVE 2010 NTA)');
  expect(report).toContain('SECTION 2 - HEAT VULNERABILITY (NATIVE 2020 NTA)');
  expect(report).toContain('SECTION 3 - FLOOD VULNERABILITY (NATIVE CENSUS TRACT)');
  expect(report).toContain('2010 NTA code:');
  expect(report).toContain('2020 NTA code:');
  expect(report).not.toContain('No official tree NTA record could be resolved');
  expect(report).not.toContain('No official HVI NTA record could be resolved');
  expect(report).not.toContain('No official FVI census-tract record could be resolved');
});

test('flood mode preserves location and shows official tract data', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name.startsWith('mobile'), 'covered by desktop interaction test');
  await waitForAtlas(page);
  await selectTreeNeighborhood(page, 'Starrett City');
  await page.locator('.mtab[data-tab="flood"]').click();
  await expect(page).toHaveURL(/#flood=/);
  await expect(page.locator('#nta-boro')).toContainText('CENSUS TRACT');
  await expect(page.locator('#eq-badge')).toHaveText('OFFICIAL FVI');
  await expect(page.frameLocator('#map-frame').locator('#leg-flood')).toBeVisible();
  await expect(page.locator('#tp-flood-fshri')).toContainText('/ 5');
});

test('mobile layout keeps map controls and metric tabs usable', async ({ page }, testInfo) => {
  test.skip(!testInfo.project.name.startsWith('mobile'), 'mobile-only layout assertion');
  await waitForAtlas(page);
  await expect(page.locator('#map-frame')).toBeVisible();
  await expect(page.locator('.mtab[data-tab="trees"]')).toBeVisible();
  await expect(page.locator('.mtab[data-tab="heat"]')).toBeVisible();
  await expect(page.locator('.mtab[data-tab="flood"]')).toBeVisible();
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  expect(overflow).toBeLessThanOrEqual(1);
});
