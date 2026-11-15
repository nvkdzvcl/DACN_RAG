import React from 'react';

// Policy documents mark the scope of each rule as **bold**; AI answers quote them verbatim.
// Render only that marker as <strong> (React elements, never HTML), keep everything else as text.
export function RichText({ text }) {
  if (!text) return null;
  return String(text).split(/\*\*(.+?)\*\*/gs).map((part, index) => index % 2 ? <strong key={index}>{part}</strong> : part);
}

export function plainText(text) {
  // Previews may be cut mid-marker, so drop unpaired ** too.
  return String(text ?? '').replace(/\*\*(.+?)\*\*/gs, '$1').replaceAll('**', '');
}
