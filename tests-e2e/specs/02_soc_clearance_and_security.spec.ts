import { test, expect } from '@playwright/test';

test.describe('Municipal Security Clearance & SOC Passkey Access Control (Live Production)', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('TC-07: Clicking SOC Analyst Hub triggers security clearance passkey gate', async ({ page }) => {
    const socTab = page.getByRole('button', { name: /SOC Analyst Hub/i });
    await expect(socTab).toBeVisible();
    await socTab.click();

    // Verify authentication modal appears
    await expect(page.getByText('Municipal Security Clearance Required')).toBeVisible();
    await expect(page.getByText('تصريح أمني مطلوب للدخول')).toBeVisible();
    await expect(page.getByPlaceholder(/Enter admin security passkey/i)).toBeVisible();
  });

  test('TC-08: Invalid passkey is rejected with security denial alert', async ({ page }) => {
    const socTab = page.getByRole('button', { name: /SOC Analyst Hub/i });
    await socTab.click();

    const passkeyInput = page.getByPlaceholder(/Enter admin security passkey/i);
    await passkeyInput.fill('invalid_clearance_token_xyz');

    const submitBtn = page.getByRole('button', { name: /Authenticate & Enter/i });
    await submitBtn.click();

    // Assert rejection alert
    await expect(page.getByText(/Access Denied: Invalid Security Clearance Passkey/i)).toBeVisible();
  });

  test('TC-09: Valid Master SOC Admin Passkey unlocks operations center', async ({ page }) => {
    const socTab = page.getByRole('button', { name: /SOC Analyst Hub/i });
    await socTab.click();

    const passkeyInput = page.getByPlaceholder(/Enter admin security passkey/i);
    await passkeyInput.fill('APPledbx@33#hinxtolnimda');

    const submitBtn = page.getByRole('button', { name: /Authenticate & Enter/i });
    await submitBtn.click();

    // Assert modal closes and SOC Hub header renders
    await expect(page.getByText('Municipal Threat Operations & Forensics')).toBeVisible({ timeout: 15000 });
    await expect(page.getByText('STIX 2.1 Feeds Active')).toBeVisible();

    // Assert the 6 workbenches navigation bar is present
    await expect(page.getByRole('button', { name: /1\. Overview & Heatmap/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /2\. Active Campaigns/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /3\. IoC Repository/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /4\. Domain Spoof Radar/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /5\. Synthetic Audio Lab/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /6\. Model & Engine Telemetry/i })).toBeVisible();
  });

  test('TC-10: Lock SOC button revokes session and returns to Citizen Verification', async ({ page }) => {
    // 1. Authenticate into SOC mode
    const socTab = page.getByRole('button', { name: /SOC Analyst Hub/i });
    await socTab.click();

    const passkeyInput = page.getByPlaceholder(/Enter admin security passkey/i);
    await passkeyInput.fill('APPledbx@33#hinxtolnimda');
    await page.getByRole('button', { name: /Authenticate & Enter/i }).click();

    await expect(page.getByText('Municipal Threat Operations & Forensics')).toBeVisible({ timeout: 15000 });

    // 2. Click Lock SOC button
    const lockBtn = page.getByRole('button', { name: /Lock SOC/i });
    await expect(lockBtn).toBeVisible();
    await lockBtn.click();

    // 3. Verify returned to citizen portal and SOC is re-locked
    await expect(page.getByText('Citizen Verification')).toBeVisible();
    await expect(page.getByText('LOCKED')).toBeVisible();
  });
});
