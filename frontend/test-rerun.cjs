const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();

  // 监听控制台错误
  const errors = [];
  page.on('console', msg => {
    if (msg.type() === 'error') {
      errors.push(msg.text());
    }
  });

  page.on('response', response => {
    const url = response.url();
    if (url.includes('rerun-review')) {
      console.log('<<< Response:', response.status(), url);
    }
  });

  // 登录
  console.log('Navigating to login page...');
  await page.goto('http://localhost:5176/login');
  await page.waitForTimeout(2000);

  // 使用之前注册的用户登录
  await page.fill('#email', 'playwright_test@test.com');
  await page.fill('#password', 'testpassword123');
  await page.click('button[type="submit"]');

  // 等待跳转到 workspace
  await page.waitForURL('**/workspace', { timeout: 10000 });
  console.log('Logged in, now at workspace');

  // 导航到一个已有的合同进行审查
  // 先获取合同列表
  const contractsLink = await page.$('a[href*="/contracts/"]');
  if (contractsLink) {
    await contractsLink.click();
    await page.waitForTimeout(2000);
    console.log('Navigated to contracts page');
  }

  // 截图
  await page.screenshot({ path: 'test-rerun-result.png', fullPage: true });
  console.log('Screenshot saved to test-rerun-result.png');

  // 打印控制台错误
  if (errors.length > 0) {
    console.log('Console errors:', errors.slice(0, 5));
  } else {
    console.log('No console errors');
  }

  await browser.close();
})().catch(console.error);
