import { test, expect } from '@playwright/test';

test.describe('Municipal SOC Forensic Workbenches & Live Neon DB Streaming (Live Production)', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Authenticate into SOC Analyst Hub
    const socTab = page.getByRole('button', { name: /SOC Analyst Hub/i });
    await socTab.click();

    const passkeyInput = page.getByPlaceholder(/Enter admin security passkey/i);
    await passkeyInput.fill('APPledbx@33#hinxtolnimda');
    await page.getByRole('button', { name: /Authenticate & Enter/i }).click();

    await expect(page.getByText('Municipal Threat Operations & Forensics')).toBeVisible({ timeout: 15000 });
  });

  test('TC-11: Workbench 1 - Overview renders KPIs, SVG arrival curve, heatmap and live DB pulse', async ({ page }) => {
    // 1. Assert KPI summary cards
    await expect(page.getByText(/Scanned Messages \(24h\)/i)).toBeVisible();
    await expect(page.getByText(/High Risk \/ Red Verdicts/i)).toBeVisible();
    await expect(page.getByText(/Amber \/ Caution Fallbacks/i)).toBeVisible();
    await expect(page.getByText(/Average E2E Latency/i)).toBeVisible();

    // 2. Assert SVG Arrival Curve is present with viewBox and rendered paths
    const curveSvg = page.locator('svg[viewBox="0 0 720 220"]');
    await expect(curveSvg).toBeVisible();
    const curvePaths = curveSvg.locator('path');
    expect(await curvePaths.count()).toBeGreaterThanOrEqual(4);

    // 3. Assert 7-Day x 24-Hour Threat Velocity Heatmap
    await expect(page.getByText(/UAE Municipal Threat Velocity Heatmap/i)).toBeVisible();
    await expect(page.getByText('Mon', { exact: true })).toBeVisible();
    await expect(page.getByText('Sun', { exact: true })).toBeVisible();

    // 4. Assert Target Impersonation distribution
    await expect(page.getByText('Target Impersonation')).toBeVisible();
    await expect(page.getByText('Dubai Police').first()).toBeVisible();
    await expect(page.getByText('Salik Tolls').first()).toBeVisible();

    // 5. Test Live Database Manual Refresh Pulse
    const refreshBtn = page.getByRole('button', { name: /Force Sync/i });
    await expect(refreshBtn).toBeVisible();
    await refreshBtn.click();
    await expect(page.getByText(/Neon PostgreSQL 16 Database Telemetry/i)).toBeVisible();
  });

  test('TC-12: Workbench 2 - Active Campaigns renders STIX attack graph with stationary hover', async ({ page }) => {
    const campaignsTab = page.getByRole('button', { name: /2\. Active Campaigns/i });
    await campaignsTab.click();

    // 1. Assert Municipal Campaign Tracker header and table
    await expect(page.getByText(/Active Municipal Campaign Tracker/i)).toBeVisible();
    await expect(page.getByText(/Operation Fake Fine/i).first()).toBeVisible();
    await expect(page.getByText(/Emirates Post Delivery/i).first()).toBeVisible();

    // 2. Switch to Attack Graph View
    const attackGraphBtn = page.getByRole('button', { name: /Attack Graph View/i });
    await attackGraphBtn.click();

    // 3. Assert STIX Attack Graph SVG container
    const graphSvg = page.locator('svg[viewBox="0 0 960 380"]');
    await expect(graphSvg).toBeVisible();

    // 4. Verify stationary node behavior on hover (vibration fix verification)
    const nodeGroup = graphSvg.locator('g.cursor-pointer').first();
    await expect(nodeGroup).toBeVisible();

    // Scroll into view first so hover doesn't induce page scroll delta
    await nodeGroup.scrollIntoViewIfNeeded();
    await page.waitForTimeout(300);

    // Measure initial transform/bounding box
    const initialBox = await nodeGroup.boundingBox();
    expect(initialBox).not.toBeNull();

    // Hover over node
    await nodeGroup.hover();
    await page.waitForTimeout(400);

    // Confirm node center remains stationary within 2px tolerance (zero jitter/snapping)
    const hoveredBox = await nodeGroup.boundingBox();
    expect(hoveredBox).not.toBeNull();
    if (initialBox && hoveredBox) {
      expect(Math.abs(hoveredBox.x - initialBox.x)).toBeLessThanOrEqual(2);
      expect(Math.abs(hoveredBox.y - initialBox.y)).toBeLessThanOrEqual(2);
    }
  });

  test('TC-13: Workbench 3 - IoC Repository renders Class A indicators and search filtering', async ({ page }) => {
    const iocTab = page.getByRole('button', { name: /3\. IoC Repository/i });
    await iocTab.click();

    await expect(page.getByText(/Class A IoC Repository/i)).toBeVisible();

    // Assert table columns
    await expect(page.getByText('Normalized Class A Value')).toBeVisible();
    await expect(page.getByText('Risk Score').first()).toBeVisible();
    await expect(page.getByText('Verdict').first()).toBeVisible();

    // Test search filter input
    const searchInput = page.getByPlaceholder(/Search normalized indicator/i);
    await expect(searchInput).toBeVisible();
    await searchInput.fill('salik');
    await page.getByRole('button', { name: /Filter/i }).click();
    await page.waitForTimeout(500);

    // Assert filtered content appears
    await expect(page.getByText(/salik/i).first()).toBeVisible();
  });

  test('TC-14: Workbench 4 - Domain Spoof Radar inspects Punycode and enables TDRA ISP block', async ({ page }) => {
    const homographTab = page.getByRole('button', { name: /4\. Domain Spoof Radar/i });
    await homographTab.click();

    await expect(page.getByText(/Domain Spoof & IDN Homograph Radar/i)).toBeVisible();
    await expect(page.getByText(/Interactive Glyph-by-Glyph Unicode/i)).toBeVisible();

    // Test TDRA ISP block recommendation button
    const blockBtn = page.getByRole('button', { name: /Push to ISP Blocklist/i }).first();
    if (await blockBtn.isVisible()) {
      await blockBtn.click();
      await expect(page.getByText(/TDRA/i).first()).toBeVisible({ timeout: 5000 });
    }
  });

  test('TC-15: Workbench 5 - Synthetic Voice Note Forensic Workbench renders spectrogram and acoustic cards', async ({ page }) => {
    const audioTab = page.getByRole('button', { name: /5\. Synthetic Audio Lab/i });
    await audioTab.click();

    await expect(page.getByText(/Synthetic Voice Note Forensic Workbench/i)).toBeVisible();

    // Assert acoustic cards
    await expect(page.getByText(/Pitch Jitter \(F0 Stability\)/i)).toBeVisible();
    await expect(page.getByText(/Acoustic Shimmer/i)).toBeVisible();
    await expect(page.getByText(/Formants \(F1 - F3\)/i)).toBeVisible();

    // Assert audio canvas
    const canvas = page.locator('canvas').first();
    await expect(canvas).toBeVisible();
  });

  test('TC-16: Workbench 6 - Model & Engine Telemetry validates live Neon DB status and SLM specs', async ({ page }) => {
    const telemetryTab = page.getByRole('button', { name: /6\. Model & Engine Telemetry/i });
    await telemetryTab.click();

    await expect(page.getByText(/Sovereign AI & Database Metrics Command Center/i)).toBeVisible();

    // Assert Neon PostgreSQL persistence card
    await expect(page.getByText(/Total Audited Scans \(DB\)/i)).toBeVisible();
    await expect(page.getByText(/DB Synced/i).first()).toBeVisible();

    // Assert Qwen2.5-3B SLM card
    await expect(page.getByText(/Qwen2.5-3B-Instruct/i)).toBeVisible();
    await expect(page.getByText(/SafeTensors/i)).toBeVisible();

    // Assert Conformal Risk Calibration bound card
    await expect(page.getByText(/Conformal Guarantee/i)).toBeVisible();
    await expect(page.getByText(/Tri-Band/i)).toBeVisible();
  });
});
