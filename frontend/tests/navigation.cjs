// Run: node frontend/tests/navigation.cjs (bundled Playwright via NODE_PATH).
const assert = require('node:assert/strict');
const path = require('node:path');
const fs = require('node:fs');
const { pathToFileURL } = require('node:url');
const { chromium } = require('playwright');

(async () => {
  const root = path.resolve(__dirname, '..');
  const { createServer } = await import(pathToFileURL(path.join(root, 'node_modules/vite/dist/node/index.js')));
  const server = await createServer({ root, server: { host: '127.0.0.1', port: 0 }, logLevel: 'error' });
  const output = path.resolve(root, '../output/ui-followup'); fs.mkdirSync(output, { recursive: true });
  let browser;
  try {
    await server.listen();
    const url = server.resolvedUrls.local[0];
    browser = await chromium.launch({ channel: process.env.BROWSER_CHANNEL || 'msedge', headless: true });
    const context = await browser.newContext({ viewport: { width: 390, height: 844 } });
    const page = await context.newPage(); const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    const chats = ['one', 'two'].map((id, index) => ({ conversation_id: id, customer_id: 'customer', customer_name: `Khách ${index + 1}`,
      channel: 'website', status: 'assigned', assigned_agent_id: 'staff', priority: 'normal', unread_count: 1,
      created_at: '2026-10-09T08:00:00Z', last_activity_at: '2026-10-09T09:00:00Z',
      last_message: { content: `Nội dung ${id}`, sender_type: 'customer' }, sla: null }));
    const user = { id: 'staff', username: 'staff', display_name: 'Nhân viên thử', role: 'admin' };
    const customer = { id: 'customer', display_name: 'Khách có tên dài để thử mobile', email: 'customer-long-address@example.test', conversation_count: 2, order_count: 1 };
    const order = { id: 'ORD-MOBILE', customer_id: customer.id, customer_name: customer.display_name, status: 'shipping', tracking_code: 'TRACKING-LONG-CODE-12345678901234567890' };
    let reads = 0, staffLogin = true, customerLogin = true;
    await page.route('**/api/v1/**', async route => {
      const request = route.request(), requestUrl = new URL(request.url()), endpoint = requestUrl.pathname;
      let body, status = 200;
      if (endpoint === '/api/v1/auth/me') { body = user; if (!staffLogin) { status = 401; body = {}; } }
      else if (endpoint === '/api/v1/inbox/conversations') {
        const items = chats.filter(chat => requestUrl.searchParams.get('unread_only') !== 'true' || chat.unread_count);
        body = { conversations: items, total: items.length, has_more: false };
      } else if (/\/inbox\/conversations\/(one|two)\/read$/.test(endpoint)) {
        const id = endpoint.split('/').at(-2); reads++; chats.find(chat => chat.conversation_id === id).unread_count = 0;
        body = { conversation_id: id, message_id: `${id}-message` };
      } else if (/\/inbox\/conversations\/(one|two)$/.test(endpoint)) {
        const id = endpoint.split('/').at(-1);
        body = { ...chats.find(chat => chat.conversation_id === id), message_page: { before: null, has_more: false }, tickets: [],
          messages: [{ id: `${id}-message`, sender_type: 'customer', content: `Nội dung ${id}`, created_at: '2026-10-09T09:00:00Z' }] };
      } else if (endpoint === '/api/v1/workspace/customers') body = { items: [customer], total: 1 };
      else if (endpoint === '/api/v1/workspace/customers/customer') body = { ...customer, conversations: [], orders: [order] };
      else if (endpoint === '/api/v1/workspace/orders') body = { items: [order], total: 1 };
      else if (endpoint === '/api/v1/widget/session') {
        if (!customerLogin) { body = {}; status = 401; }
        else body = { conversation_id: 'guest', display_name: 'Khách', status: 'open', order_access: [], account: null,
          message_page: { before: null, has_more: false }, messages: [{ id: 'g1', sender_type: 'customer', content: 'Chào cửa hàng', created_at: '2026-10-09T09:00:00Z' }] };
      } else { status = 404; body = {}; }
      await route.fulfill({ status, contentType: 'application/json', body: JSON.stringify(body) });
    });
    const noOverflow = () => page.evaluate(() => document.documentElement.scrollWidth <= innerWidth);
    const toggle = name => page.getByRole('button', { name, exact: true }).filter({ visible: true }).first();
    await page.goto(url + '?unreadOnly=1'); await page.locator('.chat').first().waitFor();
    assert.deepEqual(await page.evaluate(async () => {
      const { readNavigation } = await import('/src/navigation.js');
      const invalid = readNavigation(location.origin + '/?page=invalid&selectedId=' + 'x'.repeat(65) + '&offset=-1&assignment=invalid&unreadOnly=invalid&search=' + 'x'.repeat(161));
      return [invalid.page, invalid.selectedId, invalid.offset, invalid.assignment, invalid.unreadOnly, invalid.search];
    }), ['inbox', null, 0, 'all', false, '']);
    await page.waitForTimeout(500); assert.equal(reads, 0, 'Unread queue must not mark an automatic selection read');
    await page.locator('.chat').first().click();
    await page.waitForFunction(() => document.querySelectorAll('.chat').length === 1);
    assert.equal(await page.locator('.messageContent').innerText(), 'Nội dung one');
    const draft = page.getByRole('textbox', { name: 'Tin nhắn nhân viên' }); await draft.fill('Bản nháp giữ qua Back');
    assert.equal(await page.evaluate(() => {
      const event = new Event('beforeunload', { cancelable: true }); window.dispatchEvent(event); return event.defaultPrevented;
    }), true);
    await toggle('Về danh sách hội thoại').click(); await page.locator('.chat').click();
    await page.waitForFunction(() => document.querySelector('.messageContent')?.textContent === 'Nội dung two');
    await page.goBack(); assert.equal(await page.locator('.showConversation').count(), 0);
    await page.goBack(); await page.waitForFunction(() => document.querySelector('.messageContent')?.textContent === 'Nội dung one');
    assert.equal(await draft.inputValue(), 'Bản nháp giữ qua Back'); await draft.fill('');
    await page.screenshot({ path: path.join(output, 'inbox-mobile.png') });
    for (const [width, height] of [[320, 700], [390, 500], [768, 900]]) {
      await page.setViewportSize({ width, height });
      assert.equal(await noOverflow(), true);
      assert.ok(await draft.evaluate(element => element.getBoundingClientRect().bottom <= innerHeight));
    }
    await page.setViewportSize({ width: 390, height: 844 }); await toggle('Về danh sách hội thoại').click();
    await page.getByRole('textbox', { name: 'Tìm kiếm hội thoại' }).fill('Khách');
    await page.reload(); await page.getByRole('textbox', { name: 'Tìm kiếm hội thoại' }).waitFor();
    assert.equal(await page.getByRole('textbox', { name: 'Tìm kiếm hội thoại' }).inputValue(), 'Khách');
    assert.equal(await page.getByRole('checkbox', { name: 'Chỉ tin khách chưa đọc' }).isChecked(), true);
    await page.locator('.mobileNav').getByRole('button', { name: 'Khách hàng', exact: true }).click();
    await page.getByRole('textbox', { name: 'Tìm khách hàng' }).fill('Tên');
    await page.reload(); await page.getByRole('table', { name: 'Danh sách khách hàng' }).waitFor();
    assert.equal(await page.getByRole('textbox', { name: 'Tìm khách hàng' }).inputValue(), 'Tên');
    assert.equal(await page.locator('.recordTable').evaluate(element => getComputedStyle(element).minWidth), '0px');
    assert.equal(await noOverflow(), true);
    await page.screenshot({ path: path.join(output, 'customers-mobile.png') });
    await page.getByRole('button', { name: customer.display_name, exact: true }).click();
    await page.getByRole('button', { name: 'Xem đơn của khách', exact: false }).click();
    await page.getByRole('table', { name: 'Danh sách đơn hàng' }).waitFor();
    assert.equal(new URL(page.url()).searchParams.get('customerFilter'), 'customer');
    assert.equal(await noOverflow(), true);
    await page.screenshot({ path: path.join(output, 'orders-mobile.png') });
    await page.goBack(); await page.getByRole('region', { name: 'Chi tiết bản ghi' }).waitFor();
    assert.equal(new URL(page.url()).searchParams.get('page'), 'customers');
    await toggle('Chuyển sang giao diện tối').click();
    staffLogin = false; await page.goto(url); await page.getByLabel('Tên đăng nhập', { exact: true }).waitFor();
    assert.equal(await page.locator('html').getAttribute('data-theme'), 'dark');
    await page.screenshot({ path: path.join(output, 'login-dark.png') });
    await page.goto(url + 'chat'); await page.getByRole('textbox', { name: 'Tin nhắn của bạn' }).waitFor();
    assert.equal(await page.locator('html').getAttribute('data-theme'), 'dark');
    assert.equal(await noOverflow(), true);
    for (const [width, height] of [[320, 700], [390, 500], [768, 900], [1366, 900]]) {
      await page.setViewportSize({ width, height });
      assert.equal(await noOverflow(), true);
      assert.ok(await page.getByRole('textbox', { name: 'Tin nhắn của bạn' }).evaluate(element => element.getBoundingClientRect().bottom <= innerHeight));
    }
    await page.setViewportSize({ width: 390, height: 844 });
    await page.screenshot({ path: path.join(output, 'customer-chat-dark.png') });
    await toggle('Chuyển sang giao diện sáng').click();
    assert.equal(await page.locator('html').getAttribute('data-theme'), 'light');
    customerLogin = false; await page.reload(); await page.getByLabel('Email', { exact: true }).waitFor();
    await toggle('Chuyển sang giao diện tối').click();
    assert.equal(await page.locator('html').getAttribute('data-theme'), 'dark');
    assert.equal(await noOverflow(), true);
    staffLogin = true; chats.forEach(chat => chat.unread_count = 1);
    await page.setViewportSize({ width: 1366, height: 900 });
    await page.goto(url + '?unreadOnly=1'); await page.locator('.chat').first().waitFor();
    assert.equal(await noOverflow(), true);
    await page.screenshot({ path: path.join(output, 'inbox-desktop-dark.png') });
    await toggle('Chuyển sang giao diện sáng').click();
    await page.waitForTimeout(200); // Allow background-color transition to finish before visual QA.
    await page.screenshot({ path: path.join(output, 'inbox-desktop.png') });
    await page.goto(url + '?page=customers'); await page.getByRole('table', { name: 'Danh sách khách hàng' }).waitFor();
    assert.equal(await page.locator('.recordTable').evaluate(element => getComputedStyle(element).display), 'table');
    assert.deepEqual(errors, []);
    console.log('PASS: unread queue, retained chat/draft, Back, reload/filters, mobile cards/viewport, shared login/customer theme');
  } finally { await browser?.close(); await server.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
