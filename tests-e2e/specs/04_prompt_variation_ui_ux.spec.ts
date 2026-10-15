import { test, expect } from '@playwright/test';
import fs from 'node:fs';
import path from 'node:path';

// Load prompt variations corpus
const corpusPath = path.resolve(process.cwd(), 'data', 'prompts_corpus_500.json');
const allPrompts = JSON.parse(fs.readFileSync(corpusPath, 'utf-8'));

test.describe('Tester Army: Large-Scale Prompt Variation UI/UX Verification', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/', { waitUntil: 'networkidle', timeout: 30000 });
    await expect(page.getByText(/Verify UAE Public Communications/i)).toBeVisible({ timeout: 15000 });
    // Assert hydration of citizen input portal
    await expect(page.getByPlaceholder(/Dubai Police fine is overdue/i)).toBeVisible({ timeout: 15000 });
  });

  test('PV-01: Class 1 - Legitimate Citizen Official Verification via UI/UX (Arabic & English)', async ({ page }) => {
    const legitPrompts = allPrompts.filter((p: any) => p.user_class === 'legit_citizen');
    const sample = legitPrompts[0];

    // Select Forwarded Text & SMS tab
    const textTab = page.getByRole('button', { name: /Forwarded Text & SMS/i });
    await textTab.click();

    // Type prompt text and verify value retained
    const textInput = page.getByPlaceholder(/Dubai Police fine is overdue/i);
    await textInput.fill(sample.input_text);
    await expect(textInput).toHaveValue(sample.input_text);

    // Click Verify Authenticity
    const verifyBtn = page.getByRole('button', { name: /Verify Authenticity • فحص وتصنيف/i });
    await verifyBtn.click();

    // Wait for scan to complete and assert GREEN verdict
    const greenVerdict = page.getByText(/VERIFIED SAFE \/ OFFICIAL/i).first();
    await expect(greenVerdict).toBeVisible({ timeout: 60000 });

    // Assert allowlist verified entity badge
    await expect(page.getByText(/Dubai Government|UAE Verified Entity|Official|dubaipolice\.gov\.ae/i).first()).toBeVisible({ timeout: 15000 });
  });

  test('PV-02: Class 2 - Cybercriminal Urgent Traffic Fine & Parcel Smishing via UI/UX', async ({ page }) => {
    const scamPrompts = allPrompts.filter((p: any) => p.user_class === 'cybercriminal_scam');
    const sample = scamPrompts[0];

    const textTab = page.getByRole('button', { name: /Forwarded Text & SMS/i });
    await textTab.click();

    const textInput = page.getByPlaceholder(/Dubai Police fine is overdue/i);
    await textInput.fill(sample.input_text);
    await expect(textInput).toHaveValue(sample.input_text);

    const verifyBtn = page.getByRole('button', { name: /Verify Authenticity • فحص وتصنيف/i });
    await verifyBtn.click();

    // Assert RED high-risk fraud verdict
    const redVerdict = page.getByText(/HIGH RISK \/ CONFIRMED FRAUD/i).first();
    await expect(redVerdict).toBeVisible({ timeout: 60000 });

    // Assert Dubai Police 901 and eCrime escalation options appear
    await expect(page.getByText('Call 901')).toBeVisible({ timeout: 15000 });
    await expect(page.getByText(/Report to eCrime\.ae/i)).toBeVisible({ timeout: 15000 });
  });

  test('PV-03: Class 3 - Adversarial Prompt Injection & System Override Defense via UI/UX', async ({ page }) => {
    const evasionPrompts = allPrompts.filter((p: any) => p.user_class === 'adversarial_evasion');
    const sample = evasionPrompts.find((p: any) => p.category.includes('Prompt Injection')) || evasionPrompts[0];

    const textTab = page.getByRole('button', { name: /Forwarded Text & SMS/i });
    await textTab.click();

    const textInput = page.getByPlaceholder(/Dubai Police fine is overdue/i);
    await textInput.fill(sample.input_text);
    await expect(textInput).toHaveValue(sample.input_text);

    const verifyBtn = page.getByRole('button', { name: /Verify Authenticity • فحص وتصنيف/i });
    await verifyBtn.click();

    // System defenses must prevent GREEN classification; must return RED or AMBER
    await expect(
      page.locator('body').getByText(/HIGH RISK \/ CONFIRMED FRAUD|UNVERIFIED \/ CAUTION/i).first()
    ).toBeVisible({ timeout: 60000 });

    const greenVerdict = page.getByText(/VERIFIED SAFE \/ OFFICIAL/i);
    expect(await greenVerdict.count()).toBe(0);
  });

  test('PV-04: Class 3 - Cyrillic IDN Homograph Punycode Spoof via Link Inspector UI/UX', async ({ page }) => {
    // Select Link & Domain Inspector tab
    const urlTab = page.getByRole('button', { name: /Link & Domain Inspector/i });
    await urlTab.click();

    const urlInput = page.getByPlaceholder(/e\.g\. https:\/\/ecrime\.ae or http:\/\/salik-recharge\.cc/i);
    if (!await urlInput.isVisible().catch(() => false)) {
      await page.waitForTimeout(400);
      await urlTab.click();
    }
    await expect(urlInput).toBeVisible({ timeout: 15000 });
    await urlInput.fill('https://dubaıpolice-traffic.ae/settle');
    await expect(urlInput).toHaveValue('https://dubaıpolice-traffic.ae/settle');

    const verifyBtn = page.getByRole('button', { name: /Verify Authenticity • فحص وتصنيف/i });
    await verifyBtn.click();

    // Assert RED verdict for lookalike/punycode spoof
    const redVerdict = page.getByText(/HIGH RISK \/ CONFIRMED FRAUD/i).first();
    await expect(redVerdict).toBeVisible({ timeout: 60000 });
  });

  test('PV-05: Class 4 - Ambiguous E-Commerce Tracking & Caution Fallback via UI/UX', async ({ page }) => {
    const urlTab = page.getByRole('button', { name: /Link & Domain Inspector/i });
    await urlTab.click();

    const urlInput = page.getByPlaceholder(/e\.g\. https:\/\/ecrime\.ae or http:\/\/salik-recharge\.cc/i);
    if (!await urlInput.isVisible().catch(() => false)) {
      await page.waitForTimeout(400);
      await urlTab.click();
    }
    await expect(urlInput).toBeVisible({ timeout: 15000 });
    await urlInput.fill('http://unverified-tracker-portal.net/shipment');
    await expect(urlInput).toHaveValue('http://unverified-tracker-portal.net/shipment');

    const verifyBtn = page.getByRole('button', { name: /Verify Authenticity • فحص وتصنيف/i });
    await verifyBtn.click();

    // Assert AMBER caution notice
    const amberVerdict = page.getByText(/UNVERIFIED \/ CAUTION/i).first();
    await expect(amberVerdict).toBeVisible({ timeout: 60000 });
  });

  test('PV-06: Class 5 - Multi-Modal Voice Note Transcript Triage via UI/UX', async ({ page }) => {
    // 1. Inspect Voice Note tab UI
    const voiceTab = page.getByRole('button', { name: /Voice Note \/ Audio/i });
    await voiceTab.click();

    const recordBtn = page.getByRole('button', { name: /Record Voice Note/i });
    if (!await recordBtn.isVisible().catch(() => false)) {
      await page.waitForTimeout(400);
      await voiceTab.click();
    }
    await expect(recordBtn).toBeVisible({ timeout: 15000 });

    // 2. Click Voice Note Lure preset
    const voicePresetBtn = page.getByRole('button', { name: /Central Bank Voice Note Lure/i });
    await voicePresetBtn.click();

    const verifyBtn = page.getByRole('button', { name: /Verify Authenticity • فحص وتصنيف/i });
    await verifyBtn.click();

    // Assert non-green (RED or AMBER) cautious verdict for Central Bank voice note impersonator
    const fraudOrCautionVerdict = page.locator('body').getByText(/HIGH RISK \/ CONFIRMED FRAUD|UNVERIFIED \/ CAUTION/i).first();
    await expect(fraudOrCautionVerdict).toBeVisible({ timeout: 60000 });

    const greenVerdict = page.getByText(/VERIFIED SAFE \/ OFFICIAL/i);
    expect(await greenVerdict.count()).toBe(0);
  });
});
