import { test, expect } from '@playwright/test';

test.describe('Citizen Fraud Verification Portal (Live Production)', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('TC-01: Sovereign branding, bilingual typography and status badges render', async ({ page }) => {
    // 1. Verify page title
    await expect(page).toHaveTitle(/Project Hares/i);

    // 2. Verify branding header and bilingual crest
    await expect(page.locator('h1')).toContainText('PROJECT HARES');
    await expect(page.locator('header').getByText('مشروع حارس', { exact: true })).toBeVisible();
    await expect(page.locator('header').getByText('SOVEREIGN', { exact: true })).toBeVisible();

    // 3. Verify footer zero PII retention guarantee
    await expect(page.locator('footer').getByText('ZERO CITIZEN PII RETENTION (FR-4.1)', { exact: true })).toBeVisible();

    // 4. Verify live GST time clock
    const clock = page.locator('header').getByText(/GST:/);
    await expect(clock).toBeVisible();
  });

  test('TC-02: Multi-modal triage tabs switch and render active inputs', async ({ page }) => {
    // 1. Text SMS tab (default active)
    const textTab = page.getByRole('button', { name: /Forwarded Text & SMS/i });
    await expect(textTab).toBeVisible();
    await expect(page.getByPlaceholder(/Dubai Police fine is overdue/i)).toBeVisible();

    // 2. Phishing URL tab
    const urlTab = page.getByRole('button', { name: /Link & Domain Inspector/i });
    await urlTab.click();
    await expect(page.getByPlaceholder(/e\.g\. https:\/\/ecrime\.ae or http:\/\/salik-recharge\.cc/i)).toBeVisible();

    // 3. Audio Voice Note tab
    const audioTab = page.getByRole('button', { name: /Voice Note \/ Audio/i });
    await audioTab.click();
    await expect(page.getByRole('button', { name: /Record Voice Note/i })).toBeVisible();
    await expect(page.getByText(/Upload Opus \/ Audio File/i)).toBeVisible();

    // 4. Screenshot Image tab
    const imageTab = page.getByRole('button', { name: /Screenshot Image OCR/i });
    await imageTab.click();
    await expect(page.getByText(/Upload Screenshot Image/i)).toBeVisible();
    await expect(page.getByText(/Select Screenshot File/i)).toBeVisible();
  });

  test('TC-03: Theme toggle switches between Dark and Light modes cleanly', async ({ page }) => {
    const themeBtn = page.getByTitle(/Switch to (Dark|Light) Mode/i);
    await expect(themeBtn).toBeVisible();

    const html = page.locator('html');
    const isInitiallyDark = (await html.getAttribute('class'))?.includes('dark');

    await themeBtn.click();
    await page.waitForTimeout(300);

    if (isInitiallyDark) {
      await expect(html).toHaveClass(/light/);
    } else {
      await expect(html).toHaveClass(/dark/);
    }

    await themeBtn.click();
    await page.waitForTimeout(300);
  });

  test('TC-04: High-risk Dubai Police smishing lure triggers RED verdict with e-Crime escalation', async ({ page }) => {
    // Load high-risk preset or fill prompt
    const salikPresetBtn = page.getByRole('button', { name: /Salik Cyrillic Spoof/i });
    if (await salikPresetBtn.isVisible()) {
      await salikPresetBtn.click();
    } else {
      const textarea = page.getByPlaceholder(/Dubai Police fine is overdue/i);
      await textarea.fill('[E2E-CANARY] Dubai Police: Pay fine AED 500 immediately at http://police-fine-dubai.cc');
    }

    const submitBtn = page.getByRole('button', { name: /Verify Authenticity • فحص وتصنيف/i });
    await expect(submitBtn).toBeEnabled();
    await submitBtn.click();

    // Verify RED verdict
    const verdictBanner = page.getByText(/HIGH RISK \/ CONFIRMED FRAUD/i).first();
    await expect(verdictBanner).toBeVisible({ timeout: 35000 });
    await expect(page.getByText('Call 901')).toBeVisible();
    await expect(page.getByText(/Report to eCrime\.ae/i)).toBeVisible();
    await expect(page.getByText(/FR-4.1/i).first()).toBeVisible();
  });

  test('TC-05: Authenticated official government portal returns GREEN verified destination', async ({ page }) => {
    // Click official DEWA preset button
    const dewaPresetBtn = page.getByRole('button', { name: /Official DEWA Link/i });
    await dewaPresetBtn.click();

    const submitBtn = page.getByRole('button', { name: /Verify Authenticity • فحص وتصنيف/i });
    await submitBtn.click();

    // Verify GREEN verdict
    const verifiedBanner = page.getByText(/VERIFIED SAFE \/ OFFICIAL/i).first();
    await expect(verifiedBanner).toBeVisible({ timeout: 35000 });
    await expect(page.getByText(/dewa\.gov\.ae/i).first()).toBeVisible();
  });

  test('TC-06: Novel ambiguous delivery notice returns AMBER caution notice', async ({ page }) => {
    const urlTab = page.getByRole('button', { name: /Link & Domain Inspector/i });
    await urlTab.click();

    const urlInput = page.getByPlaceholder(/e\.g\. https:\/\/ecrime\.ae or http:\/\/salik-recharge\.cc/i);
    await urlInput.fill('http://unverified-tracker-portal.net/shipment');

    const submitBtn = page.getByRole('button', { name: /Verify Authenticity • فحص وتصنيف/i });
    await submitBtn.click();

    // Verify AMBER verdict
    const cautionBanner = page.getByText(/UNVERIFIED \/ CAUTION/i).first();
    await expect(cautionBanner).toBeVisible({ timeout: 35000 });
  });
});
