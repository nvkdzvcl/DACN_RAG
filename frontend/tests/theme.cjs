// Run: node frontend/tests/theme.cjs (Playwright available via NODE_PATH).
const assert = require('node:assert/strict');
const path = require('node:path');
const { pathToFileURL } = require('node:url');
const { chromium } = require('playwright');
(async () => {
  const root = path.resolve(__dirname, '..');
  const { createServer } = await import(pathToFileURL(path.join(root, 'node_modules/vite/dist/node/index.js')));
  const server = await createServer({ root, server: { host: '127.0.0.1', port: 0 } });
  let browser;
  try {
    await server.listen();
    browser = await chromium.launch({ channel: process.env.BROWSER_CHANNEL || 'msedge', headless: true });
    const page = await browser.newPage({ viewport: { width: 1440, height: 900 }, colorScheme: 'dark' });
    const errors = []; page.on('pageerror', error => errors.push(error.message));
    const conversation = { conversation_id: 'demo', customer_id: 'KH001', customer_name: 'Nguyễn Minh Anh', customer_email: 'minhanh@example.test', channel: 'website', status: 'assigned', assigned_agent_id: 'agent', priority: 'normal', created_at: '2026-10-08T09:00:00Z', sla: null };
    await page.route('**/api/v1/**', route => {
      const pathname = new URL(route.request().url()).pathname;
      let body;
      if (pathname === '/api/v1/auth/me') body = { id: 'agent', display_name: 'Nguyễn Văn Khánh', role: 'admin', username: 'qa' };
      else if (pathname === '/api/v1/inbox/conversations') body = { conversations: [conversation], total: 1, has_more: false };
      else if (pathname === '/api/v1/inbox/conversations/demo') body = { ...conversation, message_page: { before: null, has_more: false }, tickets: [], messages: [
        { id: 'm1', sender_type: 'customer', content: 'Chào shop, mình muốn hỏi chính sách đổi trả bình giữ nhiệt.', created_at: '2026-10-08T09:00:00Z' },
        { id: 'm2', sender_type: 'ai', content: 'Bạn có thể đổi trả trong vòng 7 ngày kể từ ngày nhận hàng.', citations: [{ source: 'Chính sách đổi trả.pdf', quote: 'Đổi trả trong vòng 7 ngày.', chunk_id: 'c1' }], created_at: '2026-10-08T09:01:00Z' },
        { id: 'm3', sender_type: 'agent', content: 'Mình đã tiếp nhận yêu cầu. Bạn gửi giúp mình mã đơn hàng nhé.', created_at: '2026-10-08T09:02:00Z' },
      ] };
      else return route.fulfill({ status: 404, contentType: 'application/json', body: '{}' });
      return route.fulfill({ contentType: 'application/json', body: JSON.stringify(body) });
    });
    const theme = () => page.locator('.shell').getAttribute('data-theme');
    await page.goto(server.resolvedUrls.local[0]);
    await page.locator('.bubble.staff').waitFor(); assert.equal(await theme(), 'dark');
    await page.emulateMedia({ colorScheme: 'light' });
    await page.waitForFunction(() => document.querySelector('.shell')?.dataset.theme === 'light');
    await page.emulateMedia({ colorScheme: 'dark' });
    await page.waitForFunction(() => document.querySelector('.shell')?.dataset.theme === 'dark');
    assert.equal(await page.locator('.shell').evaluate(e => getComputedStyle(e).colorScheme), 'dark');
    const input = page.getByRole('textbox', { name: 'Tin nhắn nhân viên' });
    await input.fill('Bản nháp giữ khi đổi giao diện');
    await page.locator('aside').getByRole('button', { name: 'Chuyển sang giao diện sáng' }).click();
    assert.equal(await theme(), 'light'); assert.equal(await input.inputValue(), 'Bản nháp giữ khi đổi giao diện');
    await page.reload(); await page.locator('.shell').waitFor(); assert.equal(await theme(), 'light');
    await page.locator('aside').getByRole('button', { name: 'Chuyển sang giao diện tối' }).click();
    await page.reload(); await page.locator('.bubble.staff').waitFor(); assert.equal(await theme(), 'dark');
    await page.emulateMedia({ colorScheme: 'light' }); assert.equal(await theme(), 'dark');
    if (process.env.QA_SCREENSHOTS) await page.screenshot({ path: path.join(process.env.QA_SCREENSHOTS, 'theme-dark.png') });
    await page.setViewportSize({ width: 390, height: 844 });
    await page.locator('.chat').click();
    await page.getByRole('button', { name: 'Về danh sách hội thoại', exact: true }).click();
    const toggle = page.locator('.mobileNav').getByRole('button', { name: 'Chuyển sang giao diện sáng' });
    await toggle.focus(); await page.keyboard.press('Enter'); assert.equal(await theme(), 'light');
    await page.locator('.mobileNav').getByRole('button', { name: 'Chuyển sang giao diện tối' }).click();
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
    if (process.env.QA_SCREENSHOTS) await page.screenshot({ path: path.join(process.env.QA_SCREENSHOTS, 'theme-mobile.png') });
    await page.addInitScript(() => { Storage.prototype.getItem = () => { throw new Error('blocked'); }; Storage.prototype.setItem = () => { throw new Error('blocked'); }; });
    await page.reload(); await page.locator('.shell').waitFor(); assert.equal(await theme(), 'light');
    await page.locator('.mobileNav').getByRole('button', { name: 'Chuyển sang giao diện tối' }).click(); assert.equal(await theme(), 'dark');
    assert.deepEqual(errors, []);
    console.log('PASS: system theme, live system changes, toggle, persisted override, draft retention, keyboard/mobile, blocked storage');
  } finally { await browser?.close(); await server.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
