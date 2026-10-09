// Run: node frontend/tests/productivity.cjs (bundled Playwright via NODE_PATH).
const assert = require('node:assert/strict');
const path = require('node:path');
const fs = require('node:fs');
const { pathToFileURL } = require('node:url');
const { chromium } = require('playwright');

(async () => {
  const root = path.resolve(__dirname, '..');
  const { createServer } = await import(pathToFileURL(path.join(root, 'node_modules/vite/dist/node/index.js')));
  const server = await createServer({ root, server: { host: '127.0.0.1', port: 0 }, logLevel: 'error' });
  const output = path.resolve(root, '../output/ui-productivity'); fs.mkdirSync(output, { recursive: true });
  let browser;
  try {
    await server.listen(); const url = server.resolvedUrls.local[0];
    browser = await chromium.launch({ channel: process.env.BROWSER_CHANNEL || 'msedge', headless: true });
    const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
    const errors = []; page.on('pageerror', error => errors.push(error.message));
    page.on('dialog', dialog => dialog.accept());
    let staffId = 'staff', staffExpired = false, widgetId = 'guest', widgetExpired = false;
    let unread = 1, summaryCalls = 0, queueCalls = 0, summaryFail = false;
    let holdRead = false, releaseRead, onReadStarted;
    let holdSend = false, releaseSend, onSendStarted, failStaffSend = false;
    const events = [], widgetSends = [], staffSends = [];
    const chat = () => ({ conversation_id: 'one', customer_id: 'customer', customer_name: 'Khách thử', channel: 'website',
      status: 'assigned', assigned_agent_id: staffId, priority: 'normal', unread_count: unread,
      last_customer_message_id: 'customer-message', created_at: '2026-10-09T08:00:00Z',
      last_activity_at: '2026-10-09T09:00:00Z', last_message: { content: 'Cần hỗ trợ', sender_type: 'customer' }, sla: null });
    const snapshot = () => ({ conversation_id: widgetId, display_name: 'Khách thử', status: 'open', order_access: [],
      account: { email: `${widgetId}@example.test`, email_verified: true }, message_page: { before: null, has_more: false },
      messages: [{ id: 'welcome', sender_type: 'ai', content: 'Chào bạn', created_at: '2026-10-09T09:00:00Z' }] });
    await page.route('**/api/v1/**', async route => {
      const request = route.request(), u = new URL(request.url()), endpoint = u.pathname;
      let body = {}, status = 200;
      if (endpoint === '/api/v1/auth/me' || endpoint === '/api/v1/auth/login') {
        if (endpoint.endsWith('/login')) staffExpired = false;
        if (staffExpired) status = 401;
        else body = { id: staffId, username: staffId, display_name: 'Nhân viên thử', role: 'admin' };
      } else if (endpoint === '/api/v1/auth/logout') { staffExpired = true; }
      else if (endpoint === '/api/v1/inbox/conversations') {
        if (staffExpired) status = 401;
        else { const items = u.searchParams.get('unread_only') === 'true' && !unread ? [] : [chat()];
          if (u.searchParams.has('limit') && u.searchParams.get('limit') === '1') queueCalls++;
          body = { conversations: items, total: items.length, has_more: false }; }
      } else if (endpoint === '/api/v1/inbox/conversations/one') {
        body = { ...chat(), messages: [{ id: 'customer-message', sender_type: 'customer', content: 'Cần hỗ trợ', created_at: '2026-10-09T09:00:00Z' },
          { id: 'ai-message', sender_type: 'ai', content: 'Đã chuyển yêu cầu hỗ trợ', created_at: '2026-10-09T09:00:01Z' },
          { id: 'agent-message', sender_type: 'agent', content: 'Cửa hàng đang hỗ trợ bạn', created_at: '2026-10-09T09:00:02Z' }],
          tickets: [{ id: 'ticket', status: 'assigned', priority: 'normal' }], message_page: { before: null, has_more: false } };
      } else if (endpoint.endsWith('/one/read')) {
        events.push('read-start'); onReadStarted?.();
        if (holdRead) await new Promise(resolve => { releaseRead = resolve; });
        unread = 0; events.push('read-end'); body = { message_id: 'customer-message' };
      } else if (endpoint.endsWith('/one/unread')) { events.push('unread'); unread = 1; body = { unread_from_message_id: 'customer-message' }; }
      else if (endpoint.endsWith('/one/messages')) {
        staffSends.push(request.postDataJSON()); status = failStaffSend ? 503 : 200; body = status === 200 ? { id: 'reply' } : { detail: 'Tạm mất kết nối' };
      } else if (endpoint === '/api/v1/workspace/summary') {
        summaryCalls++; status = summaryFail ? 503 : 200;
        body = summaryFail ? { detail: 'Tạm mất kết nối' } : { totals: { conversations: 1, customers: 1, orders: 0, documents: 0 },
          conversation_statuses: { assigned: 1 }, order_statuses: {}, start: '2026-10-02', end: '2026-10-09',
          period: { sla: {}, channels: {}, daily: [], mean_response_minutes: null, sla_met_percent: null } };
      } else if (endpoint === '/api/v1/widget/session' || endpoint === '/api/v1/widget/account/login') {
        if (endpoint.endsWith('/login')) widgetExpired = false;
        status = widgetExpired ? 401 : 200; body = status === 200 ? snapshot() : {};
      } else if (endpoint === '/api/v1/widget/messages') {
        widgetSends.push(request.postDataJSON()); onSendStarted?.();
        if (holdSend) await new Promise(resolve => { releaseSend = resolve; });
        body = snapshot();
      } else if (endpoint === '/api/v1/widget/account/logout') { widgetExpired = true; }
      else { status = 404; }
      await route.fulfill({ status, contentType: 'application/json', body: JSON.stringify(body) }).catch(error => {
        if (!/closed|cancelled|Invalid InterceptionId/i.test(error.message)) throw error;
      });
    });
    const draft = page.getByRole('textbox', { name: 'Tin nhắn nhân viên', exact: true });
    await page.goto(url + '?selectedId=one&mobileConversation=1'); await draft.fill('Nháp nhân viên');
    await page.locator('.finishPanel > summary').click(); await page.getByLabel('Ghi chú hoàn tất (nội bộ)').fill('Ghi chú nháp');
    await page.reload(); await draft.waitFor(); assert.equal(await draft.inputValue(), 'Nháp nhân viên');
    await page.locator('.finishPanel > summary').click(); assert.equal(await page.getByLabel('Ghi chú hoàn tất (nội bộ)').inputValue(), 'Ghi chú nháp');
    failStaffSend = true; await page.getByRole('button', { name: 'Gửi', exact: true }).click();
    await page.getByRole('button', { name: 'Gửi lại tin chưa xác nhận' }).waitFor(); await page.reload(); await draft.waitFor();
    failStaffSend = false; await draft.fill('Nháp tiếp theo'); await page.getByRole('button', { name: 'Gửi lại tin chưa xác nhận' }).click();
    await page.waitForFunction(() => !document.querySelector('.composer button').disabled);
    assert.deepEqual(staffSends[0], staffSends[1]); assert.equal(await draft.inputValue(), 'Nháp tiếp theo');
    staffId = 'other'; await page.reload(); await draft.waitFor(); assert.equal(await draft.inputValue(), '');
    staffId = 'staff'; staffExpired = true; await page.reload(); await page.getByLabel('Tên đăng nhập', { exact: true }).fill('staff');
    await page.getByLabel('Mật khẩu', { exact: true }).fill('test-password'); await page.locator('.authSubmit').click();
    await draft.waitFor(); assert.equal(await draft.inputValue(), 'Nháp tiếp theo');
    // Wait for an existing read before resetting cursor; no cancelled request may overtake unread.
    holdRead = true; const readStarted = new Promise(resolve => { onReadStarted = resolve; });
    await page.reload(); await draft.waitFor(); await readStarted;
    await page.getByRole('button', { name: 'Đánh dấu chưa đọc', exact: true }).click();
    await page.waitForTimeout(100); assert.equal(events.includes('unread'), false);
    holdRead = false; releaseRead();
    await page.waitForFunction(() => new URL(location.href).searchParams.get('unreadOnly') === '1' && !new URL(location.href).searchParams.has('selectedId'));
    assert.deepEqual(events.slice(-3), ['read-start', 'read-end', 'unread']);
    await page.waitForTimeout(400); assert.equal(unread, 1);
    await page.locator('.chat').click(); await draft.waitFor(); assert.equal(await draft.inputValue(), 'Nháp tiếp theo');
    const profileToggle = page.getByRole('button', { name: 'Hiện thông tin khách hàng', exact: true });
    await profileToggle.click(); const dialog = page.getByRole('dialog', { name: 'Thông tin khách hàng', exact: true }); await dialog.waitFor();
    for (let i = 0; i < 12; i++) { await page.keyboard.press(i % 2 ? 'Shift+Tab' : 'Tab');
      assert.equal(await dialog.evaluate(element => element.contains(document.activeElement)), true); }
    await page.screenshot({ path: path.join(output, 'profile-dialog-mobile.png') });
    await page.keyboard.press('Escape'); assert.equal(await dialog.count(), 0); assert.equal(await profileToggle.evaluate(element => element === document.activeElement), true);
    await page.setViewportSize({ width: 1366, height: 900 }); await profileToggle.click();
    await page.getByRole('checkbox', { name: 'Chỉ tin khách chưa đọc' }).uncheck(); await page.locator('.chat').waitFor();
    // Contrast samples use computed foreground and nearest opaque background, light and dark.
    for (const theme of ['light', 'dark']) {
      if (await page.locator('html').getAttribute('data-theme') !== theme)
        await page.getByRole('button', { name: theme === 'dark' ? 'Chuyển sang giao diện tối' : 'Chuyển sang giao diện sáng', exact: true }).filter({ visible: true }).first().click();
      await page.waitForTimeout(250);
      const ratios = await page.evaluate(() => {
        const rgb = color => color.match(/[\d.]+/g).map(Number);
        const lum = color => rgb(color).slice(0, 3).map(v => { v /= 255; return v <= .04045 ? v / 12.92 : ((v + .055) / 1.055) ** 2.4; }).reduce((sum, v, i) => sum + v * [.2126, .7152, .0722][i], 0);
        return ['.chatPreview', '.chatMeta > span', '.avatar', '.bubble b', '.bubble time', '.messageContent', '.composerHint'].flatMap(selector => [...document.querySelectorAll(selector)].filter(e => e.getBoundingClientRect().height && e.textContent.trim()).map(element => {
          let parent = element, bg = 'rgb(255, 255, 255)';
          while (parent) { const color = getComputedStyle(parent).backgroundColor, values = rgb(color); if (values.length === 3 || values[3] === 1) { bg = color; break; } parent = parent.parentElement; }
          const fg = getComputedStyle(element).color, a = lum(fg), b = lum(bg);
          return { selector, fg, bg, ratio: (Math.max(a, b) + .05) / (Math.min(a, b) + .05) };
        }));
      });
      fs.writeFileSync(path.join(output, `contrast-${theme}.json`), JSON.stringify(ratios, null, 2));
      assert.deepEqual(ratios.filter(sample => sample.ratio < 4.5), [], `${theme} text samples require 4.5:1`);
      await page.screenshot({ path: path.join(output, `inbox-${theme}.png`) });
    }
    await page.goto(url + '?page=overview'); await page.locator('.dashboardSync time').waitFor();
    const calls = summaryCalls, queues = queueCalls;
    await page.evaluate(() => { window.dispatchEvent(new Event('focus')); document.dispatchEvent(new Event('visibilitychange')); });
    await page.waitForFunction(() => !document.querySelector('.dashboardSync').textContent.includes('Đang cập nhật'));
    await page.waitForTimeout(300); assert.equal(summaryCalls, calls + 1); assert.equal(queueCalls, queues + 2);
    summaryFail = true; await page.getByRole('button', { name: 'Làm mới', exact: true }).click();
    await page.getByText('Dữ liệu hiển thị có thể đã cũ.', { exact: false }).waitFor();
    assert.equal(await page.locator('.workspaceStats').count(), 1); await page.screenshot({ path: path.join(output, 'dashboard-stale.png') });
    await page.goto(url + '?selectedId=one&mobileConversation=1'); await draft.waitFor();
    await page.getByRole('button', { name: 'Đăng xuất', exact: true }).filter({ visible: true }).first().click(); await page.getByLabel('Tên đăng nhập', { exact: true }).waitFor();
    assert.equal(await page.evaluate(() => sessionStorage.getItem('rag-drafts:staff:staff')), null);
    await page.goto(url + 'chat'); const customerDraft = page.getByRole('textbox', { name: 'Tin nhắn của bạn', exact: true }); await customerDraft.fill('Tin khách');
    await page.reload(); await customerDraft.waitFor(); assert.equal(await customerDraft.inputValue(), 'Tin khách');
    holdSend = true; const sendStarted = new Promise(resolve => { onSendStarted = resolve; });
    await page.getByRole('button', { name: 'Gửi tin nhắn', exact: true }).click(); await sendStarted;
    assert.equal(await customerDraft.isEnabled(), true); await customerDraft.fill('Tin tiếp theo');
    await page.keyboard.press('Enter'); assert.equal(widgetSends.length, 1);
    await page.reload(); await customerDraft.waitFor(); assert.equal(await customerDraft.inputValue(), 'Tin tiếp theo');
    holdSend = false; releaseSend(); await page.getByRole('button', { name: 'Gửi lại tin chưa xác nhận' }).click();
    await page.waitForFunction(() => !document.querySelector('.widgetComposer button').disabled);
    assert.deepEqual(widgetSends[0], widgetSends[1]); assert.equal(await customerDraft.inputValue(), 'Tin tiếp theo');
    holdSend = true; const secondSendStarted = new Promise(resolve => { onSendStarted = resolve; });
    await page.getByRole('button', { name: 'Gửi tin nhắn', exact: true }).click(); await secondSendStarted;
    await customerDraft.fill('Tin mới khi AI xử lý'); holdSend = false; releaseSend();
    await page.waitForFunction(() => !document.querySelector('.widgetComposer button').disabled);
    assert.equal(await customerDraft.inputValue(), 'Tin mới khi AI xử lý');
    widgetId = 'other-customer'; await page.reload(); await customerDraft.waitFor(); assert.equal(await customerDraft.inputValue(), '');
    widgetId = 'guest'; widgetExpired = true; await page.reload(); await page.getByLabel('Email', { exact: true }).fill('guest@example.test');
    await page.getByLabel('Mật khẩu', { exact: true }).fill('test-password'); await page.locator('.authSubmit').click();
    await customerDraft.waitFor(); assert.equal(await customerDraft.inputValue(), 'Tin mới khi AI xử lý');
    await page.getByRole('button', { name: 'Chat mới', exact: true }).click(); await customerDraft.waitFor(); assert.equal(await customerDraft.inputValue(), '');
    await customerDraft.fill('Xóa khi đăng xuất'); await page.getByRole('button', { name: 'Đăng xuất', exact: true }).click();
    await page.getByLabel('Email', { exact: true }).waitFor(); assert.equal(await page.evaluate(() => sessionStorage.getItem('rag-drafts:widget')), null);
    widgetExpired = false; await page.goto(url + 'chat'); await customerDraft.waitFor();
    await page.evaluate(() => sessionStorage.setItem('rag-drafts:widget', JSON.stringify({ drafts: { guest: 'Nháp hết hạn' }, notes: {}, pending: {}, savedAt: Date.now() - 86400001 })));
    await page.reload(); await customerDraft.waitFor(); assert.equal(await customerDraft.inputValue(), '');
    assert.equal(await page.evaluate(() => sessionStorage.getItem('rag-drafts:widget')), null);
    await page.evaluate(() => sessionStorage.setItem('rag-drafts:widget', '{broken'));
    await page.reload(); await page.getByText('Không lưu hoặc khôi phục được nháp.', { exact: false }).waitFor();
    await page.evaluate(() => { Storage.prototype.setItem = () => { throw new DOMException('Blocked', 'SecurityError'); }; });
    await customerDraft.fill('Giữ trong bộ nhớ khi storage lỗi'); assert.equal(await customerDraft.inputValue(), 'Giữ trong bộ nhớ khi storage lỗi');
    assert.equal(await page.getByText('Không lưu hoặc khôi phục được nháp.', { exact: false }).count(), 1);
    for (const [width, height] of [[320, 700], [390, 500], [768, 900], [1366, 900]]) {
      await page.setViewportSize({ width, height });
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
      assert.ok(await customerDraft.evaluate(element => element.getBoundingClientRect().bottom <= innerHeight));
    }
    await page.screenshot({ path: path.join(output, 'customer-draft.png') });
    assert.deepEqual(errors, []);
    console.log('PASS: persisted drafts/notes, account isolation, session expiry/logout, retry UUID, compose during AI, unread/read ordering, native modal keyboard, sampled contrast, dashboard focus/stale data, blocked/corrupt storage, simulated mobile');
  } finally { await browser?.close(); await server.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
