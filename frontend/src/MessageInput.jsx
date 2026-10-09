import React, { useLayoutEffect, useRef } from 'react';

export default function MessageInput({ value, ...props }) {
  const input = useRef(null);
  useLayoutEffect(() => {
    const element = input.current;
    function resize() {
      element.style.height = 'auto';
      const style = getComputedStyle(element);
      element.style.height = `${element.scrollHeight + parseFloat(style.borderTopWidth) + parseFloat(style.borderBottomWidth)}px`;
    }
    resize();
    // ponytail: observe width only; CSS caps height and scrolls long drafts.
    let width = element.clientWidth;
    let frame;
    const observer = new ResizeObserver(() => {
      if (element.clientWidth !== width) {
        width = element.clientWidth; cancelAnimationFrame(frame); frame = requestAnimationFrame(resize);
      }
    });
    observer.observe(element);
    return () => { observer.disconnect(); cancelAnimationFrame(frame); };
  }, [value]);
  return <textarea {...props} ref={input} value={value} rows={1}
    title="Enter để gửi, Shift+Enter để xuống dòng"
    onKeyDown={event => {
      if (event.key !== 'Enter' || event.shiftKey || event.nativeEvent.isComposing || event.nativeEvent.keyCode === 229) return;
      event.preventDefault();
      if (!event.repeat && !event.ctrlKey && !event.altKey && !event.metaKey) {
        const form = event.currentTarget.form;
        const submit = form?.querySelector('button[type="submit"]');
        if (submit && !submit.disabled) form.requestSubmit(submit);
      }
    }} />;
}
