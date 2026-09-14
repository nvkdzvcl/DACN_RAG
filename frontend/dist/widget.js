(() => {
  const origin = new URL(document.currentScript.src).origin;
  if (origin !== location.origin) { console.error('RAG widget requires same-origin hosting.'); return; }
  function mount() {
    if (document.getElementById('rag-support-launcher')) return;
    const button = document.createElement('button');
    button.id = 'rag-support-launcher';
    button.textContent = 'Hỗ trợ';
    button.type = 'button';
    button.setAttribute('aria-expanded', 'false');
    button.setAttribute('aria-controls', 'rag-support-frame');
    button.style.cssText = 'position:fixed;right:20px;bottom:20px;z-index:10001;border:0;border-radius:28px;padding:14px 24px;background:#128873;color:white;font:600 15px Segoe UI,sans-serif;box-shadow:0 5px 20px #193d3633;cursor:pointer;min-height:48px';
    const frame = document.createElement('iframe');
    frame.id = 'rag-support-frame';
    frame.title = 'Trò chuyện với bộ phận hỗ trợ';
    frame.hidden = true;
    frame.style.cssText = 'position:fixed;right:16px;bottom:84px;z-index:10000;width:min(400px,calc(100vw - 32px));height:min(640px,calc(100dvh - 100px));border:1px solid #b4c6bc;border-radius:16px;box-shadow:0 15px 60px #193d3633;background:#f7f8f6';
    function close() { frame.hidden = true; button.setAttribute('aria-expanded', 'false'); button.textContent = 'Hỗ trợ'; button.focus(); }
    frame.addEventListener('load', () => frame.contentWindow.addEventListener('keydown', event => { if (event.key === 'Escape') close(); }));
    button.addEventListener('click', () => {
      if (!frame.hidden) { close(); return; }
      if (!frame.src) frame.src = `${origin}/chat`;
      frame.hidden = false; button.setAttribute('aria-expanded', 'true'); button.textContent = 'Đóng trò chuyện'; frame.focus();
    });
    document.body.append(frame, button);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mount, { once: true }); else mount();
})();
