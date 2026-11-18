import React from 'react';

// Loading line and error box for a useData() state; keeps saying when shown data may be stale.
export default function LoadState({ state }) {
  return <>{state.loading && <p className="state" role="status">{state.data ? 'Đang cập nhật dữ liệu...' : 'Đang tải dữ liệu...'}</p>}{state.error && <div className="workspaceError" role="alert"><p>{state.error}{state.data && ' Dữ liệu hiển thị có thể đã cũ.'}</p><button onClick={state.reload}>Thử lại</button></div>}</>;
}
