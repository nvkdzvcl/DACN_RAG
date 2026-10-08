// Run: node frontend/tests/message-input.cjs (Playwright available via NODE_PATH).
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
    const url = server.resolvedUrls.local[0];
    browser = await chromium.launch({ channel: process.env.BROWSER_CHANNEL || 'msedge', headless: true });
    const page = await browser.newPage();
    await page.route('**/composer-check.html', async route => route.fulfill({ contentType: 'text/html', body: await server.transformIndexHtml('/composer-check.html', `
      <div id="root"></div><script type="module">
      import React, {useState} from 'react';
      import {createRoot} from 'react-dom/client';
      import MessageInput from '/src/MessageInput.jsx';
      import '/src/styles.css'; import '/src/widget.css'; import '/src/admin-theme.css';
      window.sent=[];
      function Check(){const [value,setValue]=useState('');const [disabled,setDisabled]=useState(false);
        return React.createElement(React.Fragment,null,
          React.createElement('button',{id:'toggle',onClick:()=>setDisabled(v=>!v)},'Toggle'),
          React.createElement('form',{className:'composer',style:{width:'500px'},onSubmit:e=>{e.preventDefault();window.sent.push(value);setValue('')}},
            React.createElement(MessageInput,{value,onChange:e=>setValue(e.target.value),'aria-label':'Message'}),
            React.createElement('button',{type:'submit',disabled:disabled||!value.trim()},'Send')))}
      createRoot(document.getElementById('root')).render(React.createElement(Check));
      </script>`) }));
    await page.goto(url + 'composer-check.html');
    const input = page.getByRole('textbox');
    await input.waitFor();
    const height = () => input.evaluate(e => e.getBoundingClientRect().height);
    const initial = await height();
    await input.fill('Dòng 1'); await input.press('Shift+Enter'); await input.press('x');
    assert.equal(await input.inputValue(), 'Dòng 1\nx');
    assert.ok(await height() > initial);
    assert.equal(await page.evaluate(() => sent.length), 0);
    await input.press('Enter');
    assert.deepEqual(await page.evaluate(() => sent), ['Dòng 1\nx']);
    assert.equal(await input.inputValue(), ''); assert.equal(await height(), initial);
    await input.fill(Array(30).fill('Nội dung nhiều dòng').join('\n'));
    assert.ok(await height() <= 160);
    assert.ok(await input.evaluate(e => e.scrollHeight > e.clientHeight));
    await input.fill('Giữ bản nháp'); await page.locator('#toggle').click(); await input.press('Enter');
    assert.equal(await page.evaluate(() => sent.length), 1); assert.equal(await input.inputValue(), 'Giữ bản nháp');
    await page.locator('#toggle').click();
    await input.dispatchEvent('keydown', {key:'Enter',isComposing:true});
    await input.dispatchEvent('keydown', {key:'Enter',keyCode:229});
    await input.dispatchEvent('keydown', {key:'Enter',repeat:true});
    assert.equal(await page.evaluate(() => sent.length), 1);
    await input.fill('   '); await input.press('Enter'); assert.equal(await page.evaluate(() => sent.length), 1);
    await input.fill('Một câu dài tự ngắt dòng '.repeat(8));
    const wide = await height();
    await page.locator('form').evaluate(e => e.style.width='260px');
    await page.waitForFunction(w => document.querySelector('textarea').getBoundingClientRect().height > w, wide);
    await input.fill('Ngắn'); assert.equal(await height(), initial);
    // Same shared input and stylesheet in the customer composer.
    await page.locator('form').evaluate(e => {e.className='widgetComposer';e.parentElement.className='customerWidget'});
    await input.fill('Một\nHai\nBa'); assert.ok(await height() > initial);
    await input.press('Enter'); assert.equal(await page.evaluate(() => sent.length), 2);
    console.log('PASS: Enter, Shift+Enter, IME, repeat, disabled/blank, grow/shrink/cap, wrapping, customer/staff styles');
  } finally { await browser?.close(); await server.close(); }
})().catch(error => { console.error(error); process.exitCode=1; });
