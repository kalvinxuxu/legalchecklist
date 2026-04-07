import { test, expect } from '@playwright/test'

/**
 * E2E Test: Complete Contract Review Flow
 * Flow: Login -> Upload Contract -> Wait for Review -> View Report -> View Understanding
 */
test.describe('Contract Review Flow', () => {
  const testUser = {
    email: 'test@example.com',
    password: 'testpassword123',
  }

  const testContract = {
    filePath: './e2e/fixtures/sample-contract.pdf',
    type: 'NDA',
    workspaceName: 'Test Workspace',
  }

  test.beforeEach(async ({ page }) => {
    // Setup: Clear local storage and login
    await page.goto('/login')
    await page.evaluate(() => {
      localStorage.clear()
    })

    // Mock API calls for login
    await page.route('**/api/v1/auth/login', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          access_token: 'mock-token-123',
          user: { id: '1', email: testUser.email },
        }),
      })
    })

    // Fill login form
    await page.getByPlaceholder('邮箱').fill(testUser.email)
    await page.getByPlaceholder('密码').fill(testUser.password)
    await page.getByRole('button', { name: '登录' }).click()

    // Wait for redirect to workspace
    await page.waitForURL('**/workspace')
  })

  test('complete contract upload and review flow', async ({ page }) => {
    // ========== Step 1: Navigate to Upload ==========
    await page.goto('/workspace/upload')
    await expect(page.getByRole('heading', { name: '上传合同' })).toBeVisible()

    // Mock workspace API
    await page.route('**/api/v1/workspaces/', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          { id: 'ws-1', name: testContract.workspaceName },
        ]),
      })
    })

    // Mock upload API
    let uploadCalled = false
    await page.route('**/api/v1/contracts/upload', async (route) => {
      uploadCalled = true
      const formData = await route.request().formData()
      expect(formData.get('workspace_id')).toBe('ws-1')
      expect(formData.get('contract_type')).toBe(testContract.type)

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ id: 'contract-123' }),
      })
    })

    // Select workspace
    await page.locator('select').first().selectOption('ws-1')

    // Select contract type
    await page.locator('select').nth(1).selectOption(testContract.type)

    // Mock file input - create a test file programmatically
    const fileInput = page.locator('input[type="file"]')
    await expect(fileInput).toBeAttached()

    // Create a minimal PDF content for testing
    const pdfBuffer = Buffer.from('%PDF-1.4\n1 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\ntrailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n187\n%%EOF')

    await fileInput.setInputFiles({
      name: 'sample-contract.pdf',
      mimeType: 'application/pdf',
      buffer: pdfBuffer,
    })

    // Submit form
    await page.getByRole('button', { name: '开始审查' }).click()

    // Wait for navigation to review page
    await page.waitForURL('**/workspace/review/contract-123', { timeout: 5000 })

    // ========== Step 2: Review Page Loading ==========
    await expect(page.getByRole('heading', { name: '审查报告' })).toBeVisible()

    // Mock contract detail API
    await page.route('**/api/v1/contracts/contract-123', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'contract-123',
          file_name: 'sample-contract.pdf',
          contract_type: 'NDA',
          review_status: 'completed',
          content_text: '这是一份保密协议。甲方：XXX公司。乙方：YYY公司。保密期限为两年。',
          created_at: new Date().toISOString(),
        }),
      })
    })

    // Mock review result API
    await page.route('**/api/v1/contracts/contract-123/review', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'completed',
          confidence_score: 0.92,
          risk_clauses: [
            {
              title: '保密条款过严',
              original_text: '保密期限为两年',
              risk_description: '保密期限较长，建议缩短至一年',
              risk_level: 'medium',
              suggestion: '建议将保密期限调整为一年',
            },
          ],
          missing_clauses: [
            {
              title: '争议解决条款',
              description: '缺少争议解决方式约定',
              suggestion: '建议添加仲裁或诉讼条款',
            },
          ],
          suggestions: [
            { title: '添加保密期限调整', content: '将保密期限从两年调整为一年' },
          ],
        }),
      })
    })

    // Wait for review content to load
    await page.waitForSelector('.text-xl.font-bold:has-text("1")', { timeout: 5000 })

    // Verify risk clauses section
    await expect(page.getByText('风险条款')).toBeVisible()
    await expect(page.getByText('保密条款过严')).toBeVisible()

    // Verify missing clauses section
    await expect(page.getByText('缺失条款')).toBeVisible()
    await expect(page.getByText('争议解决条款')).toBeVisible()

    // Verify suggestions section
    await expect(page.getByText('修改建议')).toBeVisible()

    // ========== Step 3: Navigate to Contract Understanding ==========
    // Click on "合同理解" tab
    await page.getByRole('tab', { name: /合同理解/ }).click()

    // Mock understanding API
    await page.route('**/api/v1/contracts/contract-123/understanding', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          quick_cards: {
            contract_purpose: '技术保密',
            key_dates: ['2024-01-01', '2026-01-01'],
            payment_summary: '无付款条款',
            breach_summary: '违约方需赔偿损失',
            core_obligations: ['保密义务', '不得泄露'],
          },
          structure: {
            structure_summary: '本合同包含8个章节',
            sections: [
              { title: '第一章 总则', content: '本协议旨在...' },
              { title: '第二章 保密义务', content: '双方应...' },
            ],
          },
          summary: {
            key_clauses: [
              { title: '保密范围', summary: '涵盖所有商业机密', risk_benefit: 'neutral' },
              { title: '保密期限', summary: '两年', risk_benefit: 'risk' },
            ],
            payment_terms: { amount: '无', payment_method: '不适用' },
            breach_liability: { compensation_range: '实际损失' },
          },
        }),
      })
    })

    // Wait for understanding content
    await page.waitForSelector('text=合同目的', { timeout: 5000 })
    await expect(page.getByText('合同目的')).toBeVisible()
    await expect(page.getByText('技术保密')).toBeVisible()
  })

  test('review page shows loading state during processing', async ({ page }) => {
    // Navigate to review page with pending contract
    await page.goto('/workspace/review/processing-123')

    // Mock contract detail API - processing state
    await page.route('**/api/v1/contracts/processing-123', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'processing-123',
          file_name: 'processing.pdf',
          contract_type: 'NDA',
          review_status: 'processing',
          created_at: new Date().toISOString(),
        }),
      })
    })

    // Mock review result API - still processing
    await page.route('**/api/v1/contracts/processing-123/review', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'processing',
          risk_clauses: [],
          missing_clauses: [],
          suggestions: [],
        }),
      })
    })

    // Verify loading state
    await expect(page.getByText('正在审查合同')).toBeVisible()
    await expect(page.getByText(/这可能需要 30-60 秒/)).toBeVisible()

    // Verify progress bar exists
    await expect(page.locator('[role="progressbar"]')).toBeVisible()
  })

  test('review page shows error state on failure', async ({ page }) => {
    await page.goto('/workspace/review/failed-123')

    // Mock contract detail API - failed state
    await page.route('**/api/v1/contracts/failed-123', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'failed-123',
          file_name: 'failed.pdf',
          contract_type: 'NDA',
          review_status: 'failed',
          review_error: '文档解析失败，请上传有效的PDF或Word文档',
          created_at: new Date().toISOString(),
        }),
      })
    })

    // Mock review result API - no data
    await page.route('**/api/v1/contracts/failed-123/review', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'failed',
          risk_clauses: [],
          missing_clauses: [],
          suggestions: [],
        }),
      })
    })

    // Verify error state
    await expect(page.getByText('审查失败')).toBeVisible()
    await expect(page.getByText('文档解析失败')).toBeVisible()
  })
})

test.describe('Contract Upload Validation', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/workspace/upload')
    await page.evaluate(() => localStorage.setItem('token', 'mock-token'))
  })

  test('shows validation error when no file selected', async ({ page }) => {
    await page.getByRole('button', { name: '开始审查' }).click()

    // Should show toast or validation message
    await expect(page.getByText('请选择合同文件')).toBeVisible()
  })

  test('shows validation error when no workspace selected', async ({ page }) => {
    // Mock workspaces as empty
    await page.route('**/api/v1/workspaces/', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([]),
      })
    })

    // Upload a file first
    const pdfBuffer = Buffer.from('%PDF-1.4\n1 obj\n<< /Type /Catalog >>\nendobj\nxref\n0 2\n0000000000 65535 f\n0000000009 00000 n\ntrailer\n<< /Size 2 /Root 1 0 R >>\nstartxref\n50\n%%EOF')
    await page.locator('input[type="file"]').setInputFiles({
      name: 'test.pdf',
      mimeType: 'application/pdf',
      buffer: pdfBuffer,
    })

    await page.getByRole('button', { name: '开始审查' }).click()

    await expect(page.getByText('请选择工作区')).toBeVisible()
  })
})
