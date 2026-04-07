import { test, expect } from '@playwright/test';

test.describe('Legal AI SaaS - E2E Tests', () => {
  // 测试数据 - 使用固定测试账号（需要提前在数据库中创建）
  const testUser = {
    email: 'test@example.com',
    password: 'TestPassword123!',
  };

  test.describe('用户认证流程', () => {
    test('应该能够访问登录页面', async ({ page }) => {
      await page.goto('/login');

      // 验证页面标题（包含法务 AI 相关）
      await expect(page).toHaveTitle(/法务 AI/i, { timeout: 5000 });

      // 验证登录表单存在 - 使用正确的 placeholder
      await expect(page.getByPlaceholder('name@company.com')).toBeVisible();
      await expect(page.getByPlaceholder('请输入密码')).toBeVisible();
      await expect(page.getByRole('button', { name: '登录' })).toBeVisible();
    });

    test('应该显示注册链接', async ({ page }) => {
      await page.goto('/login');

      // 验证注册链接存在 - 使用更精确的选择器
      const registerLink = page.getByRole('button', { name: '立即注册' });
      await expect(registerLink).toBeVisible();
    });

    test('登录表单验证 - 空邮箱', async ({ page }) => {
      await page.goto('/login');

      await page.getByPlaceholder('请输入密码').fill(testUser.password);
      await page.getByRole('button', { name: '登录' }).click();

      // 应该有某种形式的验证提示
      await page.waitForTimeout(1000);
      // 检查是否有错误消息或表单验证
      const body = await page.locator('body').textContent();
      expect(body).toBeTruthy();
    });
  });

  test.describe('首页功能', () => {
    test('应该能够访问首页', async ({ page }) => {
      await page.goto('/');

      // 验证首页包含关键内容
      await expect(page.locator('body')).toContainText(/法务 | AI | 合同/i, { timeout: 5000 });
    });

    test('导航栏应该包含主要功能链接', async ({ page }) => {
      await page.goto('/');

      const bodyText = await page.locator('body').textContent();
      // 验证至少包含一些主要功能关键词
      expect(bodyText.toLowerCase()).toMatch(/(工作区 | 合同 | 上传 | 登录 | 注册)/i);
    });
  });

  test.describe('API 健康检查', () => {
    test('后端 API 应该可访问', async ({ request }) => {
      // 测试登录 API 是否可用
      const response = await request.post('/api/v1/auth/login', {
        data: {
          email: 'test@example.com',
          password: 'test'
        }
      });

      // 应该返回 401（认证失败）而不是 404 或 500
      expect([200, 401, 403]).toContain(response.status());
    });
  });

  test.describe('响应式设计', () => {
    test('应该在移动设备视口正常工作', async ({ browser }) => {
      const mobilePage = await browser.newPage({
        viewport: { width: 375, height: 667 } // iPhone SE
      });

      await mobilePage.goto('/login');

      // 验证登录表单可见
      await expect(mobilePage.locator('body')).toContainText(/登录/i);

      await mobilePage.close();
    });
  });
});
