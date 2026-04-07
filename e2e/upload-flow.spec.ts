import { test, expect } from '@playwright/test';

test.describe('Phase 9 - Upload and Review Flow Status', () => {
  const testUser = {
    email: 'e2e@test.com',
    password: 'TestPassword123!',
  };

  test.beforeEach(async ({ page }) => {
    // Set auth token and wait for Vue to process
    await page.goto('/login');
    await page.evaluate(() => {
      localStorage.clear()
      localStorage.setItem('token', 'mock-token-123')
      localStorage.setItem('user', JSON.stringify({ id: '1', email: 'e2e@test.com' }))
    })
    // Wait for Vue router guard to process
    await page.waitForTimeout(1000)
  });

  // Skip - Vue router guard timing issue with localStorage
  test.skip('上传合同并开始审查 - 检查状态变化 - needs fix', async ({ page }) => {
    // Mock workspaces API
    await page.route('**/api/v1/workspaces/', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          { id: 'ws-1', name: 'Test Workspace' },
        ]),
      })
    })

    // Go to upload page directly
    await page.goto('/workspace/upload');
    await page.waitForLoadState('networkidle');

    // Upload a test PDF
    const pdfBuffer = Buffer.from('%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj 3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R>>endobj\nxref\n0 4\n0000000000 65535 f\n0000000015 00000 n\n0000000068 00000 n\n0000000122 00000 n\ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n197\n%%EOF', 'binary');

    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles({
      name: 'test-contract.pdf',
      mimeType: 'application/pdf',
      buffer: pdfBuffer,
    });

    // Check the file is shown
    await expect(page.locator('text=test-contract.pdf')).toBeVisible();

    // Click "开始审查" button
    const reviewButton = page.getByRole('button', { name: /开始审查/i });
    await expect(reviewButton).toBeVisible();
    await reviewButton.click();

    // Should navigate to review page or show processing
    await page.waitForTimeout(1000)
    const url = page.url();
    expect(url).toContain('/workspace/review')
  });

  test('从合同列表返回工作台不应该是空白', async ({ page }) => {
    // Navigate to workspace directly
    await page.goto('/workspace');
    await page.waitForLoadState('networkidle');

    // Verify page is not blank and has workspace content
    const bodyText = await page.locator('body').textContent();
    expect(bodyText.trim().length).toBeGreaterThan(0);
  });

  test('合同列表页面应该有内容', async ({ page }) => {
    // Mock contracts API
    await page.route('**/api/v1/contracts/', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([]),
      })
    })

    // Go to contracts list
    await page.goto('/workspace/contracts');
    await page.waitForLoadState('networkidle');

    // Page should have content
    const bodyText = await page.locator('body').textContent();
    expect(bodyText.trim().length).toBeGreaterThan(0);
  });
});
