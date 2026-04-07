import { test, expect } from '@playwright/test'

test.describe('Authentication', () => {
  test('login page renders correctly', async ({ page }) => {
    await page.goto('/login')

    // Verify page elements
    await expect(page.getByPlaceholder('邮箱')).toBeVisible()
    await expect(page.getByPlaceholder('密码')).toBeVisible()
    await expect(page.getByRole('button', { name: '登录' })).toBeVisible()
    await expect(page.getByText('注册账号')).toBeVisible()
  })

  test('successful login redirects to workspace', async ({ page }) => {
    await page.goto('/login')

    // Mock successful login
    await page.route('**/api/v1/auth/login', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          access_token: 'mock-jwt-token',
          user: {
            id: 'user-123',
            email: 'test@example.com',
            name: 'Test User',
          },
        }),
      })
    })

    // Fill login form
    await page.getByPlaceholder('邮箱').fill('test@example.com')
    await page.getByPlaceholder('密码').fill('password123')
    await page.getByRole('button', { name: '登录' }).click()

    // Verify redirect to workspace
    await page.waitForURL('**/workspace', { timeout: 5000 })
    await expect(page).toHaveURL(/\/workspace/)
  })

  test('failed login shows error message', async ({ page }) => {
    await page.goto('/login')

    // Mock failed login
    await page.route('**/api/v1/auth/login', async (route) => {
      await route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: JSON.stringify({
          detail: '邮箱或密码错误',
        }),
      })
    })

    await page.getByPlaceholder('邮箱').fill('wrong@example.com')
    await page.getByPlaceholder('密码').fill('wrongpassword')
    await page.getByRole('button', { name: '登录' }).click()

    // Verify error toast appears
    await expect(page.getByText('登录失败')).toBeVisible()
  })

  test('protected routes redirect to login when not authenticated', async ({ page }) => {
    // Clear any existing auth
    await page.evaluate(() => localStorage.clear())
    await page.goto('/workspace')

    // Should redirect to login
    await page.waitForURL('**/login', { timeout: 5000 })
  })

  test('register page renders correctly', async ({ page }) => {
    await page.goto('/register')

    await expect(page.getByPlaceholder('邮箱')).toBeVisible()
    await expect(page.getByPlaceholder('密码')).toBeVisible()
    await expect(page.getByPlaceholder('公司名称')).toBeVisible()
    await expect(page.getByRole('button', { name: '注册' })).toBeVisible()
  })
})
